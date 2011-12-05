import cmd
import shlex

import prettytable
import novaclient.v1_0.client
from clouddns.consts import uk_authurl, us_authurl

from cloudshell.base import base_shell
from cloudshell.utils import color


class servers_shell(base_shell):
    def __init__(self, main_shell):
        base_shell.__init__(self)
        self.main_shell = main_shell
        if main_shell.isuk:
            self.api = novaclient.v1_0.client.Client(main_shell.username, 
                                                     main_shell.apikey, 
                                                     None,
                                                     uk_authurl)

        else:
            self.api = novaclient.v1_0.client.Client(main_shell.username, 
                                                     main_shell.apikey, 
                                                     None,
                                                     us_authurl)
        self.set_prompt(main_shell.username, ['Servers'])
        self.servers = None
        self.images = None
        self.flavors = None

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
        for x in self.servers:
            if (len(s) == 0 or s in x.name or s in x.addresses['public'][0] 
                    or s in x.addresses['private'][0]):
                slist.add_row([x.id, x.name, x.status, 
                    '\n'.join(x.addresses['public']), 
                    '\n'.join(x.addresses['private'])])
        slist.printt(sortby='Server ID')
    do_ls = do_list

    def do_tally(self, s):
        if self.servers == None or 'refresh' in s:
            self.servers = self.api.servers.list()
        if self.flavors == None:
            self.flavors = self.api.flavors.list()
        f_ram = {}
        for flavor in self.flavors:
            f_ram[flavor.id] = flavor.ram
        tally = 0
        for server in self.servers:
            tally += f_ram[server.flavorId]
        print "Account is using", float(tally)/1024.0, "GB of RAM"

    def do_limits(self, s):
        pass

    def do_images(self, s):
        """Image Commands

        list - list all images (with parent server)
        create - (not complete) <server id or name> <name to call the image>
        """
        self.notice("Getting Image List")
        if self.images == None or 'refresh' in s:
            self.images = self.api.images.list()
        if self.servers is None:
            self.notice("Getting Server List")
            if self.servers is None:
                self.servers = self.api.servers.list()
        if s[:4] == 'list':
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
            image = args[1]
            flavor = args[2]
        except:
            self.error("boot/create requires at least 3 \
                    arguments: name image flavor")
            return
        if len(args) > 3:
            for x in args[3:]:
                if x == 'dometa':
                    meta = True
                elif x == 'dofiles':
                    files = True

    do_create = do_boot

    def do_python(self, s):
        import pdb; pdb.set_trace()
