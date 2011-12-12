# Example package with a console entry point
#

import sys
import os.path
import argparse


from cloudshell.base import base_shell
import cloudshell.auth
import cloudshell.dns
import cloudshell.dns.utils
import cloudshell.lb
import cloudshell.servers
import cloudshell.files
from cloudshell.utils import color

try:
    sys.path.append(os.path.join(os.path.expanduser('~'),'.cloudshell'))
    import csextensions
except NameError:
    # Build a psuedo extension that does nothing!
    # Also, Defines the methods needed for extensions
    class extend:
        pass
    print "Extensions Failed to Load"
    csextensions = extend()
    csextensions.args = None
    csextensions.funcs = {'servers': [], 'files': [], 'lb': [], 'dns': []}
    csextensions.shells = []
    csextensions.premain = None

class main_shell(base_shell):
    """
    Entry class for the command shell.

    This shell handles both auth and getting you into the product apis
    """
    # Setup names for shells (to keep the api if you exit/reenter a shell)
    dns = None
    servers = None
    lb = None
    files = None

    # Placeholders for required public variables
    username = None
    apikey = None
    isuk = None

    # Placeholders for required auth information, generated as we load API
    auth_token = None
    server_url = None
    files_url = None
    files_cdn_url = None
    dns_url = None
    user_id = None
    # Note, no LB url as it has to be generated per region

    # Load Balancer (and any other) regions
    regions = ['ord', 'dfw', 'lon']

    def __init__(self, username, apikey, isuk=False):
        base_shell.__init__(self)
        (self.auth_token, self.server_url, self.files_url, self.files_cdn_url) = \
                cloudshell.auth.auth(username, apikey, isuk)
        self.username = username
        self.apikey = apikey
        self.isuk = isuk
        self.set_prompt(username, [])

    def do_dns(self, s):
        "Maintain DNS entries"
        if self.dns == None:
            self.dns_url = cloudshell.dns.utils.get_dns_url(self.server_url)
            self.dns = cloudshell.dns.dns_shell(self)
        if len(s):
            self.dns.onecmd(s)
        else:
            self.dns.cmdloop()

    def do_servers(self, s):
        "Maintain Cloud Servers"
        if self.servers == None:
            self.servers = cloudshell.servers.servers_shell(self)
        if len(s):
            self.servers.onecmd(s)
        else:
            self.servers.cmdloop()

    def do_lb(self,s):
        "Maintain Cloud Load Balancers"
        if len(s) == 0:
            self.error("Load Balancers *require* a region.")
        else:
            region = s.split()[0]
            subcommand = " ".join(s.split()[1:])
            if region not in self.regions:
                print color.error("Region not in the list of allowed regions")
        pass

    def do_files(self, s):
        "Maintain Cloud Files"
        pass

    def do_colortest(self, s):
        for name in color.color_codes.keys():
            print "% 4s %s% 6s" % ('', color.set(name), name),
            print color.clear(), 'bg:',
            for x in color.color_codes.keys():
                print "%s% 6s" % (color.set(x, bg=name), x),
            print color.clear()
            print "% 4s %s% 6s" % ('bold', color.set(name, bold=True), name),
            print color.clear(), 'bg:', 
            for x in color.color_codes.keys():
                print "%s% 6s" % (color.set(x, bold=True, bg=name), x),
            print color.clear()

################################################################################
################################################################################
################################################################################
##### Create the shell do the needful on loading extensions and args! ##########


def main():
    parser = argparse.ArgumentParser(description="Rackspace Cloud API Shell`")
    parser.add_argument("-u", "--username", dest="username", 
                        help="Rackspace Cloud Username")
    parser.add_argument("-k", "--apikey", dest="apikey", 
                        help="Rackspace Cloud API Key")
    parser.add_argument("--uk", action="store_true", dest="isuk", 
                        help="Account is from Rackspace Cloud UK", 
                        default=False)
    if csextensions.args is not None:
        parser = csextensions.args(parser)
    args = parser.parse_args()
    try:
        shell = main_shell(args.username,args.apikey, args.isuk)
    except NameError:
        print "You must enter a Username and API Key to use Cloudshell"
    else:
        if csextensions.premain is not None:
            csextensions.premain(shell)
        shell.cmdloop('Welcome to Rackspace Cloud API Shell\nYou are logged in as: ' + args.username)
