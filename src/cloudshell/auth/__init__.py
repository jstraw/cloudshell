
import urllib2

from clouddns.consts import uk_authurl, us_authurl

# TODO: Make an auth system that doesn't suck

def auth(username, apikey, isuk):
    headers = {'X-Auth-Key': apikey,
               'X-Auth-User': username
    }
    if isuk:
        req = urllib2.Request(uk_authurl, None, headers)
    else:
        req = urllib2.Request(us_authurl, None, headers)

    response = urllib2.urlopen(req)
    h = response.headers.dict
    return (h['x-auth-token'], h['x-storage-url'], 
            h['x-cdn-management-url'], h['x-server-management-url'])

