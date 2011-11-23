import cmd

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

    def do_images(self, s):
        print color.set('yellow') + "Getting Image List" + color.clear()
        self.images = self.api.images.list()
        if s == 'list':
            print color.set('yellow') + "Getting Server List" + color.clear()
            if self.servers is None:
                self.servers = self.api.servers.list()
            slist = {}
            for s in self.servers:
                slist[s.id] = s.name
            print color.set('yellow') + "Setting up table" + color.clear()
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

