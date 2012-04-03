import cmd
import shlex

import clouddns.connection
from clouddns.consts import uk_authurl

from cloudshell.utils import color
from cloudshell.base import base_shell
from cloudshell.dns.domain import domain_shell
from cloudshell.dns.utils import error_handler


class dns_shell(base_shell):
    def __init__(self, main_shell):
        base_shell.__init__(self)
        self.main_shell = main_shell
        self.dns_url = main_shell.dns_url
        if main_shell.is_uk:
            self.api = clouddns.connection.Connection(username=main_shell.username, 
                                                      api_key=main_shell.apikey,
                                                      authurl=uk_authurl)
        else:
            self.api = clouddns.connection.Connection(username=main_shell.username, 
                                                      api_key=main_shell.apikey)
        self.set_prompt(main_shell.username, ['DNS'])
        self.domains = None

    def do_list(self, s):
        # Right now, the clouddns module doesn't do filtered search, get all of them
        if self.domains == None or 'refresh' in s:
            self.domains = self.api.get_domains()
        if s != '' and s in self.domains:
            print s, "is in the domain list"
        else:
            for x in self.domains:
                print x.id, ':', x.name

    def do_domain(self, s):
        """Load the Domain Shell for listed domain"""
        if self.domains == None:
            self.domains = self.api.get_domains()
        for x in self.domains:
            if s in x.name:
                d = self.api.get_domain(x.id)
                self.domain = domain_shell(self, d)
                self.domain.cmdloop()
                break
            elif int(s) == x.id:
                d = self.api.get_domain(x.id)
                self.domain = domain_shell(self, d)
                self.domain.cmdloop()
                break
    do_use = do_domain
    do_dom = do_domain

    def do_add(self, s):
        """Create a Domain on your account:

    Usage:
        add <name> <ttl> <email Address>
    """
        args = shlex.split(s)
        with error_handler(self, s):
            self.api.create_domain(args[0], args[1], args[2])

    def do_delete(self, s):
        """ Delete a domain from your account:
    **** This will NOT ask you to confirm ****

    Usage:
        delete <domain id>
    """
        if self.domains == None or 'refresh' in s:
            self.domains = self.api.get_domains()
        if s in self.domains:
            for x in self.domains:
                if s in x.name:
                    d = x.id
                    break
        else:
            d = s

        with error_handler(self, s):
            self.api.delete_domain(d)

