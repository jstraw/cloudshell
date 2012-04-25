import cmd
import shlex
import re
import urllib2
import json

import prettytable
import novaclient.v1_0.client

from cloudshell.base import base_shell
from cloudshell.utils import color
from cloudshell.auth import us_authurl_v1_0, uk_authurl_v1_0


class servers_shell(base_shell):
    def __init__(self, main_shell):
        base_shell.__init__(self)
        self.main_shell = main_shell
        if main_shell.is_uk:
            self.api = novaclient.v1_0.client.Client(main_shell.username, 
                                                     main_shell.apikey, 
                                                     None,
                                                     uk_authurl_v1_0)
            self.api.auth_url = uk_authurl_v1_0
        
        else:
            self.api = novaclient.v1_0.client.Client(main_shell.username, 
                                                     main_shell.apikey, 
                                                     None,
                                                     us_authurl_v1_0)
            self.api.auth_url = us_authurl_v1_0

        # prevent client from trying to auth, since we've already done so
        # _cs_request only auths if management_url is None
        self.api.management_url = main_shell.server_url
        self.api.auth_token = main_shell.auth_token

        self.set_prompt(main_shell.username, ['Servers'])
        self.servers = None
        self.images = None
        self.flavors = self.api.flavors.list()
        self.strip_refresh = re.compile('\brefresh\b')

    def do_list(self, s):
        """List Servers

        If an argument is provided it will only display servers 
        matching Server Name or a primary IP address.
        """
        if self.servers == None or 'refresh' in s:
            self.servers = self.api.servers.list()
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
    do_ls = do_list

    def do_tally(self, s):
        if self.servers == None or 'refresh' in s:
            self.servers = self.api.servers.list()
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
            self.images = self.api.images.list()
        if self.servers is None or 'refresh' in s:
            self.notice("Getting Server List")
            self.servers = self.api.servers.list()
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
            self.api.images.create(sid,iname)

    def do_flavors(self, s):
        """List Flavors"""
        self.flavors = self.api.flavors.list()
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
        meta = False
        files = False
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

        # TODO: metadata and file injection stuff
        self.api.servers.create(name, image, flavor)
        self.do_ls(name)

    do_create = do_boot

    def do_delete(self, s):
        """Delete a Server:
        Name or ID - Delete first server with corresponding name or ID
        """
        s = shlex.split(s)[0]
        if self.servers == None:
            self.servers = self.api.servers.list()
        for x in self.servers:
            if s == x.name or int(s) == x.id:
                yes = raw_input("Are you sure you want to delete server %s? " % x.id)
                if yes in ("Y", "y", "yes"):
                    self.api.servers.delete(x.id)
        self.servers = self.api.servers.list()

    do_rm = do_delete

    def do_python(self, s):
        import pdb; pdb.set_trace()
