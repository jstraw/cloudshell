import cmd
import datetime
import shlex

import prettytable
import clouddns.connection
from clouddns.consts import uk_authurl
from clouddns.errors import ResponseError

from cloudshell.utils import color
from cloudshell.base import base_shell
from cloudshell.dns.utils import error_handler


class domain_shell(base_shell):
    def __init__(self, dns_shell, domain):
        base_shell.__init__(self)
        self.dns_shell = dns_shell
        self.domain = domain
        self.set_prompt(self.dns_shell.main_shell.username, ['DNS', domain.name])
        self.records = None
        self.forceupdate = False

    def do_list(self, s):
        "List the records on this domain."
        # Right now, the clouddns module doesn't do filtered search, get all of them
        if self.records == None or self.forceupdate == True or 'refresh' in s:
            self.forceupdate = False
            self.records = self.domain.get_records()
        rlist = prettytable.PrettyTable(['ID', 'FQDN', 'Type', 'IP/Alias',
                                         'TTL', 'Created', 'Updated'])
        rlist.set_field_align('ID', 'l')
        rlist.set_field_align('FQDN', 'l')
        rlist.set_field_align('Type', 'c')
        rlist.set_field_align('IP/Alias', 'l')
        rlist.set_field_align('TTL', 'l')
        rlist.set_field_align('Created', 'l')
        rlist.set_field_align('Updated', 'l')
        for x in self.records:
            rlist.add_row([x.id, x.name, x.type, x.data, x.ttl, 
                           x.created.strftime('%c'), 
                           x.updated.strftime('%c')])
        rlist.printt()

    def do_add(self, s):
        """Create a new record:

    Usage:
        add <type> <fqdn> <IP/Alias> <TTL> [MX Priority]
    """
        args = shlex.split(s)
        if args[0].upper() == 'MX' and not len(args) == 5:
            self.error("You need an MX Priority when you make a MX record")
        elif len(args) < 5:
            args.append(None)
        try:
            self.domain.create_record(args[1], args[2], args[0].upper(), 
                                      args[3], args[4])
        except ResponseError, e:
            self.error("Creation failed, arguments: ", s)
            self.error("                 error code: ", str(e))
            self.notice(self.do_add.__doc__)
        except IndexError, e:
            self.error("Not enough arguments")
            self.notice(self.do_add.__doc__)
        except Exception, e: 
            self.error("Creation failed, arguments: ", s)
            self.error("                 error code: ", str(e))
            self.notice(self.do_add.__doc__)
        else:
            self.forceupdate = True
            self.do_list()

    do_create = do_add

    def do_delete(self, s):
        """Delete a record:

    Usage:
        delete <Record ID>
    """
        try:
            self.domain.delete_record(s)
        except ResponseError, e:
            self.error("Record Deletion Failed with status: ", e)
        else:
            self.forceupdate = True
            self.do_list()
    do_del = do_delete

    def do_ttl(self, s):
        """Configure Domain-wide TTL
    
    Usage:
        ttl <seconds>
    """
        try:
            self.domain.update(ttl=s)
        except ResponseError, e:
            self.error("TTL change failed with status status: ", e)
        else:
            self.forceupdate = True

    def do_email(self, s):
        """Configure Email Address contact for domain
        
    Usage:
        email <user@domain.com>
    """
        try:
            self.domain.update(emailAddress=s)
        except ResponseError, e:
            self.error("Email change failed with status status: ", e)
