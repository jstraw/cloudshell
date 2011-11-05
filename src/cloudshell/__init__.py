# Example package with a console entry point

import argparse
import cmd

import cloudshell.utils
import cloudshell.auth
import cloudshell.dns
import cloudshell.lb
import cloudshell.servers
import cloudshell.files

class main_shell(cmd.Cmd,object):
    """
    Entry class for the command shell.

    This shell handles both auth and getting you into the product apis
    """
    api = None

    def __init__(self, username, apikey, isuk=False):
        cmd.Cmd.__init__(self)
        self.api = cloudshell.auth.auth(username, apikey, isuk)
        self.username = username
        self.apikey = apikey
        self.isuk = isuk
        color = cloudshell.utils.color()
        self.color = color
        self.prompt = color.set('blue') + 'CloudShell ' + \
                      color.set('cyan') + username + \
                      color.set('blue') + ' > ' + color.clear()

    def do_dns(self, s):
        "Maintain DNS entries"
        pass

    def do_servers(self, s):
        "Maintain Cloud Servers"
        pass

    def do_lb(self,s):
        "Maintain Cloud Load Balancers"
        pass

    def do_files(self, s):
        "Maintain Cloud Files"
        pass

    def do_EOF(self, s):
        return True

    def do_exit(self, s):
        return True


def main():
    parser = argparse.ArgumentParser(description="Rackspace Cloud API Shell`")
    parser.add_argument("-u", "--username", dest="username", 
                        help="Rackspace Cloud Username", required=True)
    parser.add_argument("-k", "--apikey", dest="apikey", 
                        help="Rackspace Cloud API Key", required=True)
    parser.add_argument("--uk", action="store_true", dest="isuk", 
                        help="Account is from Rackspace Cloud UK", 
                        default=False)
    args = parser.parse_args()

    shell = main_shell(args.username,args.apikey, args.isuk)
    shell.cmdloop('Welcome to Rackspace Cloud API Shell\nYou are logged in as: ' + args.username)
