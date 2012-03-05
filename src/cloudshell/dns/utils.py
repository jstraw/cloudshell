from clouddns.consts import dns_management_host
import clouddns.utils


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

def error_handler():
    pass
