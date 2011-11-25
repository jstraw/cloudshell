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

    def do_list(self, s):
        self.servers = self.api.servers.list()
        slist = prettytable.PrettyTable(['Server ID', 'Server Name', 'Status', 'Public Address(es)', 'Private Address'])
        slist.set_field_align('Server ID', 'l')
        slist.set_field_align('Server Name', 'l')
        slist.set_field_align('Status', 'l')
        slist.set_field_align('Public Address(es)', 'l')
        slist.set_field_align('Private Address', 'l')
        for x in self.servers:
            slist.add_row([x.id, x.name, x.status, '\n'.join(x.addresses['public']), '\n'.join(x.addresses['private'])])
        slist.printt(sortby='Server ID')
    do_ls = do_list

    def do_images(self, s):
        self.notice("Getting Image List")
        self.images = self.api.images.list()
        if s[:4] == 'list':
            self.notice("Getting Server List")
            if self.servers is None:
                self.servers = self.api.servers.list()
            slist = {}
            for s in self.servers:
                slist[s.id] = s.name
            ilist = prettytable.PrettyTable(['Image ID', 'Image Name', 'Parent Server', 'Status'])
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

    def do_flavors(self, s):
        self.flavors = self.api.flavors.list()
        flist = prettytable.PrettyTable(['Flavor ID', 'Flavor Name', 'RAM', 'Disk'])
        flist.set_field_align('Flavor Name', 'l')
        flist.set_field_align('RAM', 'r')
        flist.set_field_align('Disk', 'r')
        for x in self.flavors:
            flist.add_row([x.id, x.name, str(x.ram) + ' (MB)', str(x.disk) + ' (GB)'])
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
            self.error("boot/create requires at least 3 arguments: name image flavor")
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
