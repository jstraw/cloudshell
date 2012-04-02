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
        with error_handler(self, s):
            self.domain.create_record(args[1], args[2], args[0].upper(), 
                                      args[3], args[4])
    do_create = do_add

    def do_update(self, s):
        """Update a record:

    Usage:
        update comment <Record ID> <Comment> 
        update target <Record ID> <IP/Alias> 
        update ttl <Record ID>
    """
        args = shlex.split(s)
        if args[0] not in ('comment','target','ttl') or args[1] not in [ x.id for x in self.records]:
            return

        for x in self.records:
            if x.id == args[1]:
                record = x
                break
        with error_handler(self, s):
            if args[0] == 'comment':
                record.update(comment=args[2:].join(' '))
            elif args[0] == 'target':
                record.update(data=args[2])
            elif args[0] == 'ttl':
                record.update(ttl=args[2])

    def do_delete(self, s):
        """Delete a record:

    Usage:
        delete <Record ID>
    """
        with error_handler(self, s):
            self.domain.delete_record(s)
    do_del = do_delete

    def do_ttl(self, s):
        """Configure Domain-wide TTL
    
    Usage:
        ttl <seconds>
    """
        with error_handler(self, s):
            self.domain.update(ttl=s)

    def do_email(self, s):
        """Configure Email Address contact for domain
        
    Usage:
        email <user@domain.com>
    """
        with error_handler(self, s):
            self.domain.update(emailAddress=s)
