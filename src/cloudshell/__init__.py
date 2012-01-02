# Example package with a console entry point
#

import sys
import os.path
import argparse

from cloudshell.main import main_shell



savepath = os.path.join(os.path.expanduser('~'),'.cloudshell')
extendpath = os.path.join(savepath,'csextensions')

try:
    sys.path.append(savepath)
    import csextensions
except ImportError:
    # Make that dir!
    os.makedirs(extendpath)
    csext_init = ['from types import MethodType\n\n','import cloudshell\n\n',
            'def args(parser):\n','    return parser\n\n',
            'def preshell(args):\n','    return args\n\n',
            'def premain(shell):\n','    return shell\n\n']
    open(os.path.join(extendpath,'__init__.py'), 'w').writelines(csext_init)
    print "Setup Default Extensions, please reconnect"
    sys.exit()


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

    args = csextensions.preshell(args)

    if len(args.username) > 0 and len(args.apikey) > 0:
        try:
            shell = main_shell(args.username,args.apikey, args.isuk)
        except NameError:
            print "You must enter a Username and API Key to use Cloudshell"
        else:
            if csextensions.premain is not None:
                csextensions.premain(shell)
            shell.cmdloop('Welcome to Rackspace Cloud API Shell\nYou are logged in as: ' + args.username)
    else:
        parser.print_help()
