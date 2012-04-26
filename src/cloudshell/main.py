import shlex
import readline

from cloudshell.base import base_shell
import cloudshell.auth
import cloudshell.dns
import cloudshell.dns.utils
import cloudshell.lb
import cloudshell.servers
import cloudshell.files
from cloudshell.utils import color

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
    is_uk = None

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

    def __init__(self, username, apikey, is_uk=False, snet=False,
                 auth_version="1.0"):
        base_shell.__init__(self)
        self.username = username
        self.apikey = apikey
        self.is_uk = is_uk
        self.snet = snet
        self.auth_version = auth_version
        self.do_auth("")

    def postloop(self):
        super(main_shell, self).postloop()
        try:
            readline.write_history_file(self._history_file)
        except IOError:
            pass

    def do_auth(self, s):
        "Auth and setup auth variables"
        args = shlex.split(s)
        if args:
            if len(args) < 2:
                print("usage: auth [username apikey] [is_uk] [snet] [auth_version]\n"
                      "with no args, reauths with current username and apikey\n"
                      "with args, at least username and apikey are required")
                return

            if not self.username == args[0]:
                readline.write_history_file(self._history_file)
                readline.clear_history()

            self.username = args[0]
            self.apikey = args[1]
            if len(args) > 2:
                self.is_uk = eval(args[2].capitalize())
            if len(args) > 3:
                self.snet = eval(args[3].capitalize())
            if len(args) > 4:
                self.auth_version = args[4]

        try:
            values = cloudshell.auth.get_auth(self.username, self.apikey,
                                              self.is_uk, self.snet,
                                              self.auth_version)
            (self.auth_token, self.server_url,
             self.files_url, self.files_cdn_url) = values
            
            self.set_prompt(self.username, [])
            
            self.dns = None
            self.servers = None
            self.lb = None
            self.files = None
            
            self._history_file = "%s-%s" % (self._history_file_base,
                                            self.username)        
            try:
                readline.read_history_file(self._history_file)
            except IOError:
                pass
                        
        except cloudshell.auth.ClientException:
            self.error("Auth failed for user %s with key %s" % \
                       (self.username, self.apikey))

    def do_showauth(self, s):
        print("X-Auth-Token: %s\nX-Storage-Url: %s\n"
              "X-Server-Management-Url: %s\nX-Cdn-Management-Url: %s" %
              (self.auth_token, self.files_url, self.server_url,
               self.files_cdn_url))

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

    def do_lb(self, s):
        "Maintain Cloud Load Balancers"
        if len(s) == 0:
            self.error("Load Balancers *require* a region.")
        else:
            region = s.split()[0]
            subcommand = " ".join(s.split()[1:])
            if region not in self.regions:
                self.error("Region not in the list of allowed regions")
            else:
                if self.lb == None:
                    self.lb = cloudshell.lb.lb_shell(self, region)
                if len(subcommand):
                    self.lb.onecmd(subcommand)
                else:
                    self.lb.cmdloop()
                    
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

