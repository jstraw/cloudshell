import cmd
import shlex

import prettytable
import cloudlb

from cloudshell.utils import color
from cloudshell.base import base_shell
from cloudshell.lb.lb import lb_single_shell
from cloudshell.auth import us_authurl_v1_1, uk_authurl_v1_1

class lb_shell(base_shell):
    def __init__(self, main_shell, region):
        base_shell.__init__(self)
        self.main_shell = main_shell
        self.api = cloudlb.CloudLoadBalancer(username=main_shell.username, 
                                             api_key=main_shell.apikey,
                                             region=region)
        
        # prevent client from trying to auth, since we've already done so
        # _cloudlb_request only auths if management_url is None
        self.api.auth_token = main_shell.auth_token
        self.account_number = main_shell.server_url.split("/")[-1]
        self.region_account_url = "%s/%s" % (cloudlb.consts.REGION_URL % region,
                                             self.account_number)

        self.set_prompt(main_shell.username, ['Load Balancer', region])
        self.region = region
        self.lbs = None
        self.lb = None
        self.algorithms = self.api.get_algorithms()
        self.protocols = self.api.get_protocols()
        
    def update_lbs(self):
        self.lbs = self.api.loadbalancers.list()
        self.lbs.sort(key=lambda lb: lb.id)


    def do_list(self, s):
        if self.lbs == None or 'refresh' in s:
            self.update_lbs()
        lblist = prettytable.PrettyTable(['ID', 'Name', 'Port', 'Protocol', 'Algorithm', 'Nodes', 'IPs'])
        lblist.aligns = ['l' for f in range(7)]
        lblist.aligns[2] = 'c'
        lblist.aligns[3] = 'c'
        lblist.aligns[5] = 'c'
        for lb in self.lbs:
            ips = []
            if hasattr(lb, 'virtualIps'):
                for ip in lb.virtualIps:
                    ips.append(ip.address)
                lblist.add_row([lb.id, lb.name, lb.port, lb.protocol, lb.algorithm, len(lb.nodes), ', '.join(ips)])
        lblist.printt()

    def do_select(self, s):
        """Select an LB (and enter its shell)

    Usage:
        select [ID|Name|VIP|Node IP]
    
    Note: If there are multiple options, it will list those for you to choose between.
    """
        if len(s) == 0:
            self.error(self.do_select.__doc__)
            return
        if self.lbs == None:
            self.update_lbs()
        options = []
        for lb in self.lbs:
            if int(s) == lb.id or s in lb.name or s in lb.nodes or s in lb.virtualIps:
                options.append(lb)
        if len(options) == 0:
            self.warning("No Load Balancer found matching " + s)
        elif len(options) > 1:
            i = 0
            lblist = prettytable.PrettyTable(['#','ID','Name','IPs'])
            lblist.aligns = ['l' for f in range(4)]
            for o in options:
                ips = []
                if hasattr(o, 'virtualIps'):
                    for ip in o.virtualIps:
                        ips.append(ip.address)
                lblist.add_row([i, o.id, o.name, ', '.join(ips)])
                i += 1
            lblist.printt()
            lb = input("Please enter either a row number or Load Balancer ID: ")
            if lb < 10:
                options = [options[lb]]
            else:
                for o in options:
                    print lb, o.id
                    if lb == o.id:
                        print 'win'
                        options = [o]
                        break
        if len(options) == 1:
            lb = options[0]
            self.lb = lb_single_shell(self, lb)
            self.lb.cmdloop()
        
    do_use = do_select

    def do_python(self, s):
        import pdb; pdb.set_trace()

