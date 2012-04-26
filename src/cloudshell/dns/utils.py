import sys
import contextlib
import traceback

import clouddns.utils
from clouddns.consts import dns_management_host
from clouddns.errors import ResponseError


def get_dns_url(servers_url):
    """
    Parse out DNS management URL based on the servers url and
    the dns_management_host const from clouddns.consts

    This is derived from clouddns.authenticate.Authentication.authenticate()
    """
    (pnetloc, pport, puri, pis_ssl) = clouddns.utils.parse_url(servers_url)
    puri = '/' + puri

    dns_management_url = []
    if pis_ssl:
        dns_management_url.append('https://')
    else:
        dns_management_url.append('http://')

    if 'lon.' in pnetloc:
        dns_management_url.append('lon.' + dns_management_host)
    else:
        dns_management_url.append(dns_management_host)

    dns_management_url.append(puri)
    return "".join(dns_management_url)

@contextlib.contextmanager
def error_handler(cls, s):
    try:
        yield
    except ResponseError, e:
        doc = eval("cls." + traceback.extract_tb(sys.exc_info()[2])[1][2] + ".__doc__")
        cls.error("request failed, arguments: ", s)
        cls.error("                 error code: ", str(e))
        cls.notice(doc)
    except IndexError, e:
        doc = eval("cls." + traceback.extract_tb(sys.exc_info()[2])[1][2] + ".__doc__")
        cls.error("Not enough arguments")
        cls.notice(doc)
    except Exception, e:
        doc = eval("cls." + traceback.extract_tb(sys.exc_info()[2])[1][2] + ".__doc__")
        cls.error("request failed, arguments: ", s)
        cls.error("                 error code: ", str(e))
        cls.notice(doc)
    else:
        cls.forceupdate = True
        cls.do_list('')
