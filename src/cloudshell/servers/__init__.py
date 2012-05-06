import cmd
import shlex
import re
import urllib2
import json
import contextlib
import traceback

import prettytable
import novaclient.v1_0.client
import novaclient.exceptions as s_exc

from cloudshell.base import base_shell
from cloudshell.utils import color
from cloudshell.auth import us_authurl_v1_0, uk_authurl_v1_0

@contextlib.contextmanager
def error_handler(cls, s):
    try:
        yield
    except s_exc.ClientException as e:
        doc = eval("cls." + traceback.extract_tb(sys.exc_info()[2])[1][2] + ".__doc__")
        cls.error("API returned an error on request:", s)
        cls.error("Error:", str(e))
        cls.notice(doc)

class servers_shell(base_shell):
    def __init__(self, main_shell):
        base_shell.__init__(self)
        self.main_shell = main_shell
        if main_shell.is_uk:
            self.auth_url = uk_authurl_v1_0
        else:
            self.auth_url = us_authurl_v1_0

        with error_handler(self, '(auth)'):
            self.api = novaclient.v1_0.client.Client(main_shell.username, 
                                                 main_shell.apikey, 
                                                 None,
                                                 self.auth_url)

        # prevent client from trying to auth, since we've already done so
        # _cs_request only auths if management_url is None
        self.api.management_url = main_shell.server_url
        self.api.auth_token = main_shell.auth_token

        self.set_prompt(main_shell.username, ['Servers'])
        self.servers = None
        self.images = None
        self.limits = None
        with error_handler(self, '(flavors)'):
            self.flavors = self.api.flavors.list()
        self.strip_refresh = re.compile('\brefresh\b')

    def do_list(self, s):
        """List Servers

        If an argument is provided it will only display servers 
        matching Server Name or a primary IP address.
        """
        if self.servers == None or 'refresh' in s:
            self._list_servers()
        if self.limits == None: 
            with error_handler(self, '(get limits)'):
                self._limits()
        slist = prettytable.PrettyTable(['Server ID', 'Server Name', 
                                         'Status', 'Public Address(es)', 
                                         'Private Address'])
        slist.set_field_align('Server ID', 'l')
        slist.set_field_align('Server Name', 'l')
        slist.set_field_align('Status', 'l')
        slist.set_field_align('Public Address(es)', 'l')
        slist.set_field_align('Private Address', 'l')
        s = self.strip_refresh.sub(' ', s)
        for x in self.servers:
            if (not s or
                int(s) == x.id or
                s in x.name or
                s in x.addresses['public'][0] or
                s in x.addresses['private'][0]):
                slist.add_row([x.id, x.name, x.status, 
                    '\n'.join(x.addresses['public']), 
                    '\n'.join(x.addresses['private'])])
                if s:
                    break
        slist.printt(sortby='Server ID')
        self.do_tally(s)
        print "Account Global Limit is:", float(self.limits['absolute']['maxTotalRAMSize'])/1024, 'GB'
    do_ls = do_list

    def do_show(self, s):
        """Show details about Server specified by name, id, or IP"""
        if len(s) == 0:
            self.error('Show requires a slice ID, name, or IP')
            return
        if self.servers == None:
            self._list_servers()
        for x in self.servers:
            if (int(s) == x.id or 
                s in x.name or 
                s in x.addresses['public'][0] or 
                s in x.addresses['public'][0]):
                self._show_server(x)
                break

    def do_tally(self, s):
        if self.servers == None or 'refresh' in s:
            self._list_servers()
        f_ram = {}
        for flavor in self.flavors:
            f_ram[flavor.id] = flavor.ram
        tally = 0
        for x in self.servers:
            if (len(s) == 0 or s in x.name or s in x.addresses['public'][0]
                   or s in x.addresses['private'][0]):
                tally += f_ram[x.flavorId]
        print "Account is using", float(tally)/1024.0, "GB of RAM"

    def do_limits(self, s):
        if self.limits == None:
            self._limits()
        print "    Server Limits (Absolute)"
        print "Total RAM:", float(self.limits['absolute']['maxTotalRAMSize'])/1024, 'GB'
        print "    Server Rate Limits:"
        for rate in self.limits['rate']:
            if rate['URI'] is '*':
                print rate['verb'], 'limit:', rate['remaining'], 'of', rate['value'], 'on any URI per', rate['unit'].lower()
            elif len(rate['URI']) > 1 and rate['URI'][0] == '*' and rate['URI'][-1] == '*':
                    print rate['verb'], 'limit:', rate['remaining'], 'of', rate['value'], 'with URI containing:', rate['URI'][1:-1], 'per', rate['unit'].lower()
            else:
                print rate['verb'], 'limit:', rate['remaining'], 'of', rate['value'], 'on URI:', rate['URI'], 'per', rate['unit'].lower()

    def do_images(self, s):
        """Image Commands

        list - list all images (with parent server)
        create - (not complete) <server id or name> <name to call the image>
        """
        if self.images == None or 'refresh' in s:
            self.notice("Getting Image List")
            with error_handler(self, s):
                self.images = self.api.images.list()
        if self.servers is None or 'refresh' in s:
            self.notice("Getting Server List")
            self._list_servers()
        if not s or s[:4] == 'list':
            slist = {}
            for s in self.servers:
                slist[s.id] = s.name
            ilist = prettytable.PrettyTable(['Image ID', 'Image Name', 
                                             'Parent Server', 'Status'])
            ilist.set_field_align('Image ID', 'l')
            ilist.set_field_align('Image Name', 'l')
            ilist.set_field_align('Parent Server', 'l')
            ilist.set_field_align('Status', 'l')
            for x in self.images:
                if hasattr(x, 'serverId'):
                    parent = slist[x.serverId] + '(' + str(x.serverId) + ')'
                else:
                    parent = 'None'
                ilist.add_row([x.id, x.name, parent, x.status])
            ilist.printt(sortby='Image ID')
        elif s[:6] == 'create':
            args = s.split()
            for server in self.servers:
                if args[0] == server.name:
                    sid = server
                    break
                elif args[0] == server.id:
                    sid = server
                    break
            iname = args[1]
            with error_handler(self, s):
                self.api.images.create(sid,iname)

    def do_flavors(self, s):
        """List Flavors"""
        flist = prettytable.PrettyTable(['Flavor ID', 'Flavor Name', 
                                         'RAM', 'Disk'])
        flist.set_field_align('Flavor Name', 'l')
        flist.set_field_align('RAM', 'r')
        flist.set_field_align('Disk', 'r')
        for x in self.flavors:
            flist.add_row([x.id, x.name, str(x.ram) + ' (MB)', 
                           str(x.disk) + ' (GB)'])
        print flist

    def do_boot(self, s):
        """Boot/Create a New Server:
        Name - 26 Characters or less, no spaces
        Image ID/Name - use images list to get a list of available options
        Flavor ID/RAM Size - use flavors to get a list of available options
                             This will take 1-7, or the #MB of ram, not a GB count
        optional flags: (not active)
        dometa - build a dictionary of metatags
        dofiles - create a fileset to inject into the server on create
        """
        args = shlex.split(s)
        meta = None
        files = None
        try:
            name = args[0]
            image = int(args[1])
            flavor = int(args[2])
        except:
            self.error("boot/create requires at least 3 " \
                       "arguments: name image flavor")
            return
        if len(args) > 3:
            for x in args[3:]:
                if x == 'dometa':
                    meta = True
                elif x == 'dofiles':
                    files = True
        if meta:
            print " --- Metadata ---"
            print "Type . as a key to end the list"
            meta = {}
            x = 1
            while True:
                k = raw_input("Metadata - Key %s: " % x)
                if k == '.': break
                v = raw_input("Metadata - Value %s: " % x)
                if len(k) > 255 or len(v) > 255:
                    print "Keys and Values must be under 255 characters"
                else:
                    meta[k] = v
                    x += 1
                if x == 5:
                    break

        if files:
            print " --- Files ---"
            print "Type . as a key to end the list"
            files = {}
            x = 1
            while True:
                k = raw_input("File - Name %s: " % x)
                if k == '.': break
                v = raw_input("File - path %s: " % x)
                with open(v, 'r') as f:
                    d = v.read()
                if len(d) > 10240:
                    print "File has to be under 10k in length"
                else:
                    files[k] = v
                    x += 1
                if x == 5:
                    break

        with error_handler(self, s):
            server = self.api.servers.create(name, image, flavor, meta=meta, files=files)
            self._show_server(server)
            self.do_ls(name)

    do_create = do_boot


    def do_delete(self, s):
        """Delete a Server:
        Name or ID - Delete first server with corresponding name or ID
        """
        s = shlex.split(s)[0]
        if self.servers == None:
            self._list_servers()
        for x in self.servers:
            if s == x.name or int(s) == x.id:
                yes = raw_input("Are you sure you want to delete server %s? " % x.id)
                if yes in ("Y", "y", "yes"):
                    with error_handler(self, s):
                        self.api.servers.delete(x.id)
                break
        self._list_servers()

    do_rm = do_delete

    def _list_servers(self):
        with error_handler(self, '(list servers)'):
            self.servers = self.api.servers.list()


    def _show_server(self, server):
        """Display the actual data for a server, assumes you are passing the actual object"""
        s = server._info # Provides a Dictionary to play with
        pt = prettytable.PrettyTable(['Property', 'Value'])
        pt.aligns = ['l', 'l']

        pt.add_row(['Server ID', s['id']])
        pt.add_row(['Server Name', s['name']])
        for (k,v) in s.iteritems():
            if k == 'addresses':
                pt.add_row(['Public IPs', v['public'][0]])
                if len(v['public']) > 1:
                    for x in v['public'][1:]:
                        pt.add_row(['', x])
                pt.add_row(['Private IPs', v['private'][0]])
                if len(v['private']) > 1:
                    for x in v['private'][1:]:
                        pt.add_row(['', x])
            elif k not in ('id', 'name'):
                pt.add_row([k.title(), v])
        pt.printt()

    def _limits(self):
        headers = {"X-Auth-Token": self.main_shell.auth_token,
                   "Accept":  'application/json'}
        req = urllib2.Request(self.main_shell.server_url + '/limits', None, headers)
        try:
            response = urllib2.urlopen(req)
            self.limits = json.loads(response.read())['limits']
        except urllib2.URLError:
            self.error("Failed to get limits")
            print self.main_shell.server_url + '/limits'
            raise

 
    def do_python(self, s):
        import pdb; pdb.set_trace()
