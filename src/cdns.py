#!/usr/bin/python

import sys
import argparse
import clouddns
import cmd

global api # Need this to make it easy for the dns_cmd class
class dns_cmd(cmd.Cmd,object):
    def do_list(self, s):
        global api
        # Right now, the clouddns module doesn't do filtered search, get all of them
        domains = api.get_domains()
        if s != '' and s in domains:
            print s, "is in the domain list"
        else:
            for x in domains:
                print x



def main(api):
    dns = dns_cmd()
    dns.cmdloop('DNS $')
    







if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cloud DNS Shell Tool")
    parser.add_argument("-u", "--username", dest="username", help="Rackspace Cloud Username", required=True)
    parser.add_argument("-k", "--apikey", dest="apikey", help="Rackspace Cloud API Key", required=True)
    parser.add_argument("--uk", action="store_true", dest="isuk", 
            help="Account is from Rackspace Cloud UK", default=False)
    args = parser.parse_args()

    if not args.isuk:
        print args.username, args.apikey
        api = clouddns.connection.Connection(args.username,args.apikey)
    else:
        api = clouddns.connection.Connection(args.username,args.apikey,authurl=clouddns.consts.uk_authurl)
    main(api)
