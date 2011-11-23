import cmd

import clouddns.connection
from clouddns.consts import uk_authurl

from cloudshell.utils import color
from cloudshell.base import base_shell


class dns_shell(base_shell):
    def __init__(self, main_shell):
        base_shell.__init__(self)
        self.main_shell = main_shell
        self.dns_url = main_shell.dns_url
        if main_shell.isuk:
            self.api = clouddns.connection.Connection(username=main_shell.username, 
                                                      api_key=main_shell.apikey,
                                                      authurl=uk_authurl)
        else:
            self.api = clouddns.connection.Connection(username=main_shell.username, 
                                                      api_key=main_shell.apikey)
        self.set_prompt(main_shell.username, ['DNS'])
#        self.prompt = color.set('blue') + 'CloudShell ' + \
#                      color.set('cyan') + main_shell.username + \
#                      color.set('blue') + ' DNS > ' + color.clear()

    def do_list(self, s):
        # Right now, the clouddns module doesn't do filtered search, get all of them
        domains = self.api.get_domains()
        if s != '' and s in domains:
            print s, "is in the domain list"
        else:
            for x in domains:
                print x

    def do_exit(self, s):
        return True
    def do_EOF(self, s):
        return True

