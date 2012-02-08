import cmd
import datetime
import shlex

import prettytable
import clouddns.connection
from clouddns.consts import uk_authurl

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
                nodes.append(str(ip.id) + ' - ' + ip.address + ' / ' + ip.condition  + ' / ' + ip.status + ' / at weight ' + ip.weight)
            else:
                nodes.append(str(ip.id) + ' - ' + ip.address + ' / ' + ip.condition)

        sources = []
        for key, value in self.lb.sourceAddresses.iteritems():
            if 'Public' in key: p = 'Public'
            else: p = 'ServiceNet'
            if '4' in key: v = 'IPv4'
            else: v = 'IPv6'
            sources.append("%s %s Address - %s" % (p, v, value))

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

    def do_accesslist(self, s):
        pass

    def do_update(self, s):
        self.lb.update()

    do_commit = do_update

    def do_python(self, s):
        import pdb; pdb.set_trace()

