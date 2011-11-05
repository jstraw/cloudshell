
import clouddns
from clouddns.consts import uk_authurl, us_authurl

# Use the Cloud DNS api to do auth
# TODO: Make an auth system that will allow us to auth to any Rackspace Product

def auth(username, apikey, isuk):
    """
    Simple Wrapper to Cloud DNS's auth system
    """
    return clouddns.connection.Connection(username,apikey,authurl = \
               (uk_authurl if isuk else us_authurl))
