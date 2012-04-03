# from openstack/bin/swift
# Copyright (c) 2010-2011 OpenStack, LLC.
# Apache License, Version 2.0

from urlparse import urlparse, urlunparse, urljoin

try:
    from eventlet.green.httplib import HTTPException, HTTPSConnection
except ImportError:
    from httplib import HTTPException, HTTPSConnection

# look for a real json parser first
try:
    # simplejson is popular and pretty good
    from simplejson import loads as json_loads
    from simplejson import dumps as json_dumps
except ImportError:
    try:
        # 2.6 will have a json module in the stdlib
        from json import loads as json_loads
        from json import dumps as json_dumps
    except ImportError:
        # fall back on local parser otherwise
        comments = compile(r'/\*.*\*/|//[^\r\n]*', DOTALL)

        def json_loads(string):
            '''
            Fairly competent json parser exploiting the python tokenizer and
            eval(). -- From python-cloudfiles

            _loads(serialized_json) -> object
            '''
            try:
                res = []
                consts = {'true': True, 'false': False, 'null': None}
                string = '(' + comments.sub('', string) + ')'
                for type, val, _junk, _junk, _junk in \
                        generate_tokens(StringIO(string).readline):
                    if (type == OP and val not in '[]{}:,()-') or \
                            (type == NAME and val not in consts):
                        raise AttributeError()
                    elif type == STRING:
                        res.append('u')
                        res.append(val.replace('\\/', '/'))
                    else:
                        res.append(val)
                return eval(''.join(res), {}, consts)
            except Exception:
                raise AttributeError()


us_authurl_v1_0 = "https://auth.api.rackspacecloud.com/v1.0"
uk_authurl_v1_0 = "https://lon.auth.api.rackspacecloud.com/v1.0"

us_authurl_v2_0 = "https://auth.api.rackspacecloud.com/v2.0/tokens"
uk_authurl_v2_0 = "https://lon.auth.api.rackspacecloud.com/v2.0/tokens"


class ClientException(Exception):

    def __init__(self, msg, http_scheme='', http_host='', http_port='',
                 http_path='', http_query='', http_status=0, http_reason='',
                 http_device=''):
        Exception.__init__(self, msg)
        self.msg = msg
        self.http_scheme = http_scheme
        self.http_host = http_host
        self.http_port = http_port
        self.http_path = http_path
        self.http_query = http_query
        self.http_status = http_status
        self.http_reason = http_reason
        self.http_device = http_device

    def __str__(self):
        a = self.msg
        b = ''
        if self.http_scheme:
            b += '%s://' % self.http_scheme
        if self.http_host:
            b += self.http_host
        if self.http_port:
            b += ':%s' % self.http_port
        if self.http_path:
            b += self.http_path
        if self.http_query:
            b += '?%s' % self.http_query
        if self.http_status:
            if b:
                b = '%s %s' % (b, self.http_status)
            else:
                b = str(self.http_status)
        if self.http_reason:
            if b:
                b = '%s %s' % (b, self.http_reason)
            else:
                b = '- %s' % self.http_reason
        if self.http_device:
            if b:
                b = '%s: device %s' % (b, self.http_device)
            else:
                b = 'device %s' % self.http_device
        return b and '%s: %s' % (a, b) or a


def http_connection(url, proxy=None):
    """
    Make an HTTPConnection or HTTPSConnection

    :param url: url to connect to
    :param proxy: proxy to connect through, if any; None by default; str of the
                  format 'http://127.0.0.1:8888' to set one
    :returns: tuple of (parsed url, connection object)
    :raises ClientException: Unable to handle protocol scheme
    """
    parsed = urlparse(url)
    proxy_parsed = urlparse(proxy) if proxy else None
    if parsed.scheme == 'http':
        conn = HTTPConnection((proxy_parsed if proxy else parsed).netloc)
    elif parsed.scheme == 'https':
        conn = HTTPSConnection((proxy_parsed if proxy else parsed).netloc)
    else:
        raise ClientException('Cannot handle protocol scheme %s for url %s' %
                              (parsed.scheme, repr(url)))
    if proxy:
        conn._set_tunnel(parsed.hostname, parsed.port)
    return parsed, conn


def make_snet(url):
    parsed = list(urlparse(storage_url))
    # Second item in the list is the netloc
    parsed[1] = 'snet-' + parsed[1]
    return urlunparse(parsed)


def _get_auth_v1_0(url, user, key, snet):
    parsed, conn = http_connection(url)
    conn.request('GET', parsed.path, '',
                 {'X-Auth-User': user, 'X-Auth-Key': key})
    resp = conn.getresponse()
    resp.read()
    if resp.status < 200 or resp.status >= 300:
        raise ClientException('Auth GET failed', http_scheme=parsed.scheme,
                http_host=conn.host, http_port=conn.port,
                http_path=parsed.path, http_status=resp.status,
                http_reason=resp.reason)
    token = resp.getheader('x-auth-token')
    storage_url = resp.getheader('x-storage-url')
    if snet:
        storage_url = make_snet(storage_url)
    servers_url = resp.getheader('x-server-management-url')
    if snet:
        servers_url = make_snet(server_url)
    cdn_url = resp.getheader('x-cdn-management-url')
    return token, servers_url, storage_url, cdn_url


def _get_auth_v2_0(url, user, key, snet):

    def json_request(method, token_url, **kwargs):
        kwargs.setdefault('headers', {})
        if 'body' in kwargs:
            kwargs['headers']['Content-Type'] = 'application/json'
            kwargs['body'] = json_dumps(kwargs['body'])
        parsed, conn = http_connection(token_url)
        conn.request(method, parsed.path, **kwargs)
        resp = conn.getresponse()
        body = resp.read()
        if body:
            try:
                body = json_loads(body)
            except ValueError:
                pass
        else:
            body = None
        if resp.status < 200 or resp.status >= 300:
            raise ClientException('Auth GET failed', http_scheme=parsed.scheme,
                                  http_host=conn.host,
                                  http_port=conn.port,
                                  http_path=parsed.path,
                                  http_status=resp.status,
                                  http_reason=resp.reason)
        return resp, body
    body = {"auth": {"passwordCredentials": {"username": user, "password": key}}}
    resp, body = json_request("POST", url, body=body)

    token_id = None
    storage_url = None
    servers_url = None
    cdn_url = None

    try:
        token_id = body['access']['token']['id']
        catalogs = body['access']['serviceCatalog']
        for service in catalogs:
            if service['name'] == 'cloudFiles':
                storage_url = service['endpoints'][0]['publicURL']
                if snet:
                    storage_url = make_snet(storage_url)
            elif service['name'] == 'cloudServers':
                servers_url = service['endpoints'][0]['publicURL']
                if snet:
                    servers_url = make_snet(servers_url)
            elif service['name'] == 'cloudFilesCDN':
                cdn_url = service['endpoints'][0]['publicURL']
    except(KeyError, IndexError):
        raise ClientException("Error while getting answers from auth server")

    return token_id, servers_url, storage_url, cdn_url


def get_auth(user, key, is_uk=False, snet=False, auth_version="1.0"):
    """
    Get authentication/authorization credentials.

    The snet parameter is used for Rackspace's ServiceNet internal network
    implementation. In this function, it simply adds *snet-* to the beginning
    of the host name for the returned storage URL. With Rackspace Cloud Files,
    use of this network path causes no bandwidth charges but requires the
    client to be running on Rackspace's ServiceNet network.

    :param user: user to authenticate as
    :param key: key or password for authorization
    :param is_uk: use UK auth endpoint (default is US)
    :param snet: use SERVICENET internal network (see above), default is False
    :param auth_version: OpenStack authentication version (default is 1.0)
    :returns: tuple of (storage URL, auth token)
    :raises ClientException: HTTP GET request to auth URL failed
    """
    if auth_version == "1.0" or auth_version == "1":
        if is_uk:
            url = uk_authurl_v1_0
        else:
            url = us_authurl_v1_0
        return _get_auth_v1_0(url, user, key, snet)
    elif auth_version == "2.0" or auth_version == "2":
        if is_uk:
            url = uk_authurl_v2_0
        else:
            url = us_authurl_v2_0
        return _get_auth_v2_0(url, user, key, snet)

