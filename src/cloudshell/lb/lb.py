import cmd
import datetime
import shlex

import prettytable
import clouddns.connection
from clouddns.consts import uk_authurl
from cloudlb.accesslist import NetworkItem

from cloudshell.utils import color
from cloudshell.base import base_shell


class lb_single_shell(base_shell):
    def __init__(self, lb_shell, lb):
        base_shell.__init__(self)
        self.lb_shell = lb_shell
        self.set_prompt(self.lb_shell.main_shell.username, ['Load Balancer', self.lb_shell.region, lb.name])
        self.lb = lb
        self.intro = color.set('yellow') + "If you make any updates, they are" + \
                " not finalized until you run update or commit" + color.clear()
    
    def do_show(self, s):
        table = prettytable.PrettyTable(['Field', 'Value'])
        table.aligns = ['l', 'l']
        vips = []
        for ip in self.lb.virtualIps:
            vips.append(str(ip.id) + ' - ' + ip.address + '(' + ip.ipVersion  + ')')

        nodes = []
        for ip in self.lb.nodes:
            if 'WEIGHTED' in self.lb.algorithm:
                nodes.append(str(ip.id) + ' - ' + ip.address + ' / ' +
                             ip.condition  + ' / ' + ip.status +
                             ' / at weight ' + 'None' if (ip.weight == None)
                             else ip.weight )
            else:
                nodes.append(str(ip.id) + ' - ' + ip.address + ' / ' + ip.condition)

        sources = []
        for key, value in self.lb.sourceAddresses.iteritems():
            if 'Public' in key: p = 'Public'
            else: p = 'ServiceNet'
            if '4' in key: v = 'IPv4'
            else: v = 'IPv6'
            sources.append("%s %s Address - %s" % (p, v, value))

        acls = []
        for x in self.lb.accesslist().list():
            acls.append("%s - %s from %s" % (x.id, x.type.lower(), x.address))
        if len(acls) == 0:
            acls = ['None']

        table.add_row(['ID / Name', str(self.lb.id) + ' / ' + self.lb.name])
        table.add_row(['Status', self.lb.status])
        table.add_row(['IPs', vips[0]])
        for x in vips[1:]:
            table.add_row(['', x])
        table.add_row(['Protocol', self.lb.protocol])
        table.add_row(['Port', self.lb.port])
        table.add_row(['Created', self.lb.created.strftime('%c')])
        table.add_row(['Updated', self.lb.updated.strftime('%c')])
        table.add_row(['Nodes', nodes[0]])
        for x in nodes[1:]:
            table.add_row(['', x])
        table.add_row(['Access Controls', acls[0]])
        for x in acls[1:]:
            table.add_row(['', x])
        table.add_row(['Algorithm', self.lb.algorithm])
        table.add_row(['Logging', self.lb.connectionLogging['enabled']])
        table.add_row(['Cluster', self.lb.cluster])
        table.add_row(['Sources', sources[0]])
        for x in sources[1:]:
            table.add_row(['', x])
        table.printt()

    def complete_algorithm(self, text, line, begidx, endidx):
        return [i for i in self.lb_shell.algorithms if i.startswith(text)]

    def do_algorithm(self, s):
        shorthand = {'rr': 'ROUND_ROBIN',
                    'rand': 'RANDOM',
                    'lc': 'LEAST_CONNECTIONS',
                    'wlc': 'WEIGHTED_LEAST_CONNECTIONS',
                    'wrr': 'WEIGHTED_ROUND_ROBIN'}

        for a in self.lb_shell.algorithms:
            if s == a:
                self.lb.algorithm = s
                return
        if s in shorthand.keys():
            self.lb.algorithm = shorthand[s]

    def do_rename(self,s):
        self.lb.name = s

    def complete_protocol(self, text, line, begidx, endidx):
        return [i for i in self.lb_shell.protocols if i.startswith(text)]

    def do_protocol(self, s):
        if s in self.lb_shell.protocols:
            self.lb.protocol = s

    def do_port(self, s):
        if int(s) in range(65535):
            self.lb.port = int(s)

    def do_errorpage(self, s):
        """Set or remove the error page:

    Usage:
        add file <filename>
        update file <filename
            Set the error page for the Load Balancer

        delete
            Remove the error page
        """
        errorpage = self.lb.errorpage()
        if len(s) == 0:
            print errorpage.get()
            return
        args = shlex.split(s)
        if args[0][0] == 'a' or args[0][0] == 'u':
            fileid = args.index('file')
            if fileid == 0:
                # TODO: Get lines and make a file out of them
                self.error("Currently, only loading error page from file is supported")
            else:
                html = open(args[fileid + 1], 'r').read()
                errorpage.add(html)
        elif args[0] == 'd':
            errorpage.delete()
        else:
            print errorpage.get()

    def do_logging(self, s):
        """Configure Load Balancer Logs

    Usage:
        enable - enable logging
        disable - disable logging
    """
        log = self.lb.connection_logging()
        if len(s) and s[0] == 'e':
            log.enable()
        elif len(s) and s[0] == 'd':
            log.disable()
        else:
            if log.get() == True:
                print "Logging Enabled"
            else:
                print "Logging Disabled"

    def do_accesslist(self, s):
        """Configure Access Lists.

Cloud Load Balancers will always *allow* and then *deny*, so to deny all but IPs, 
add a deny 0.0.0.0/0 then allow IPs as required.

    Usage:
        allow [ip|ip/mask|ACL ID] ...
        deny [ip|ip/mask] ...
        delete <ACL ID|all>
        
    Will List Access Controls otherwise
    """
        acl = self.lb.accesslist()
        args = shlex.split(s)
        if len(args) == 0:
            acl.list()
        elif args[0] == 'allow':
            new_acls = []
            for arg in args[1:]:
                if '.' in arg:
                    new_acls.append(NetworkItem(address=arg, type='ALLOW'))
                else:
                    print "This argument (", arg,") isn't an IP address and can't be loaded"
            acl.add(new_acls)
        elif args[0] == 'deny':
            new_acls = []
            for arg in args[1:]:
                if '.' in arg:
                    new_acls.append(NetworkItem(address=arg, type='DENY'))
                else:
                    print "This argument (", arg,") isn't an IP address and can't be loaded"
            acl.add(new_acls)
        elif args[0] == 'delete':
            if args[1] == 'all':
                acl.delete()
            else:
                for arg in args[1:]:
                    acl.delete(int(arg))

    def do_update(self, s):
        try:
            self.lb.update()
        except Exception as e:
            if 'Nothing' in str(e):
                self.notice("Nothing to Update, continue")
            else:
                raise

    do_commit = do_update

    def do_python(self, s):
        import pdb; pdb.set_trace()

