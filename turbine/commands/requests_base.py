###############################################################################
# Carbon Caputure Simulation Initiative
# See LICENSE.md for copyright notice!
##############################################################################
"""
requests_base module is a drop-in replacement for Turbine Web Application
functions utilizing the python requests module.
"""
__author__ = 'Joshua Boverhof <jrboverhof@lbl.gov>'
import os,logging,requests,configparser
from requests.exceptions import RequestException, HTTPError, ConnectionError
from requests import Response

class HTTPStatusCode(Exception):
    def __init__(self, rsp:Response):
        self.response = rsp
        msg = 'HTTP(%d) - %s' %(rsp.status_code, rsp.content)
        super().__init__(self, msg)
    @property
    def code(self):
        return self.response.code

#def standard_options(url, options, **extra_query):
def read_configuration(configFile, section, **kw):
    """ Read the turbine configuration ConfigParser instance and
    build the URL.
    parameters:
        configFile : ConfigParser instance
        section : ConfigParser section
    keyword arguments:  (http query parameters):
        page
        rpp
        SignedUrl
    """
    assert type(configFile) is configparser.ConfigParser
    assert type(kw.get('SignedUrl', False)) is bool
    params = {}
    url = configFile.get(section, 'url')
    signed_url = configFile.getboolean(section, 'SignedUrl', fallback=None)
    logging.getLogger(__name__).debug('kw %s' %str(kw))
    for k,v in kw.items():
        if k == 'subresource' and v:
            url = '/'.join([url.strip('/'),v])
        elif callable(v):
            params[k] = v()
        else:
            params[k] = v
    logging.getLogger(__name__).debug('read_configuration signed_url: "%s"', signed_url)
    if 'SignedUrl' not in params and signed_url is not None:
        params['SignedUrl'] = signed_url
    if 'SignedUrl' in params and url.endswith('/input/configuration'):
        logging.getLogger(__name__).debug('configuration signed_url unsupported')
        del params['SignedUrl']
    signed_url = params.get('SignedUrl', False)
    assert type(signed_url) is bool
    verbose =  params.get('verbose', False)
    assert type(verbose) is bool
    rpp =  params.get('rpp', '0')
    if rpp is None:
        del params['rpp']
    assert rpp is None or type(int(rpp)) is int
    pagenum = params.get('page', '0')
    if pagenum is None:
        del params['page']
    assert pagenum is None or type(int(pagenum)) is int
    auth = (configFile.get('Authentication', 'username', raw=True),
        configFile.get('Authentication', 'password', raw=True))

    return (url, auth, params)

def delete_page(configFile, section, **kw):
    url,auth,params = read_configuration(configFile,section,**kw)
    r = _delete_page(url, auth, **params)
    if r.status_code != 200:
        raise HTTPStatusCode(r)
    return r.text

def _delete_page(url, auth, **params):
    """
    parameters:
        auth --- username and password tuple
    """
    assert type(auth) is tuple
    logging.getLogger(__name__).debug('_delete_page url: "%s"', url)
    return requests.delete(url, params=params, auth=auth)

def get_page(configFile, section, **kw):
    url,auth,params = read_configuration(configFile,section,**kw)
    r = _get_page(url, auth, **params)
    if r.status_code != 200:
        raise HTTPStatusCode(r)
    return r.text

def get_page_by_url(url, auth, **kw):
    r = _get_page(url, auth, **kw)
    if r.status_code != 200:
        raise HTTPStatusCode(r)
    return r.text

def _get_page(url, auth, **params):
    """
    parameters:
        auth --- username and password tuple
    keyword params
        -- SignedUrl, service will return signed S3 URL and it Will
        automatically be followed.
    """
    assert type(auth) is tuple
    logging.getLogger(__name__).debug('_get_page url: "%s"', url)
    return requests.get(url, params=params, auth=auth)

def put_page(configFile, section, data, content_type='', **kw):
    """
    """
    url,auth,params = read_configuration(configFile,section,**kw)
    headers = {'Content-Type': content_type}
    signed_url = params.get('SignedUrl', False)
    if url.split('/')[-2] == 'simulation':
        logging.getLogger(__name__).debug('upload simulation meta data')
        if 'SignedUrl' in params:
            del params['SignedUrl']
    elif signed_url is True:
        #logging.getLogger(__name__).debug('put_page signed_url: "%s" "%s"', url, str(params))
        r = _put_page(url, auth, data='', allow_redirects=False, **params)
        assert r.status_code == 302, "HTTP Status Code %d" %r.status_code
        url = r.headers.get('Location')
        auth = None
        del params['SignedUrl']
    #logging.getLogger(__name__).debug('put_page: "%s" "%s"', url, str(params))
    r = _put_page(url, auth, data, allow_redirects=True, headers=headers, **params)
    #if raw_data
    #    return r.raw
    logging.getLogger(__name__).debug('HTTP PUT(%s)', r.status_code)
    if r.status_code != 200:
        raise HTTPStatusCode(r)
    return r.text

def _put_page(url, auth, data=None, allow_redirects=False, headers={}, **params):
    """
    parameters:
        auth --- username and password tuple
    keyword params
        -- SignedUrl, service will return signed S3 URL and it Will
        automatically be followed.
    """
    assert type(auth) in (tuple,type(None)), '%s' %type(auth)
    logging.getLogger(__name__).debug('_put_page url: "%s" "%s"', url, params)
    return requests.put(url, data, allow_redirects=allow_redirects, params=params, auth=auth, headers=headers)


def post_page(configFile, section, data, **kw):
    """
    """
    url,auth,params = read_configuration(configFile,section,**kw)
    signed_url = params.get('SignedUrl', False)
    if url.split('/')[-2] == 'simulation':
        logging.getLogger(__name__).debug('upload simulation meta data')
        if 'SignedUrl' in params:
            del params['SignedUrl']
    elif signed_url is True:
        #logging.getLogger(__name__).debug('put_page signed_url: "%s" "%s"', url, str(params))
        r = _post_page(url, auth, data='', allow_redirects=False, **params)
        assert r.status_code == 302, "HTTP Status Code %d" %r.status_code
        url = r.headers.get('Location')
        auth = None
        del params['SignedUrl']
    #logging.getLogger(__name__).debug('put_page: "%s" "%s"', url, str(params))
    r = _post_page(url, auth, data, allow_redirects=True, **params)
    #if raw_data
    #    return r.raw
    logging.getLogger(__name__).debug('HTTP PUT(%s)', r.status_code)
    if r.status_code != 200:
        raise HTTPStatusCode(r)
    return r.text

def post_page_by_url(url, auth, data=None, allow_redirects=False, headers={}, **params):
    r = _post_page(url, auth, data=data, allow_redirects=allow_redirects, headers=headers, **params)
    if r.status_code != 200:
        raise HTTPStatusCode(r)
    return r

def _post_page(url, auth, data=None, allow_redirects=False, headers={}, **params):
    """
    parameters:
        auth --- username and password tuple
    keyword params
        -- SignedUrl, service will return signed S3 URL and it Will
        automatically be followed.
    """
    assert type(auth) in (tuple,type(None)), '%s' %type(auth)
    logging.getLogger(__name__).debug('_post_page url: "%s" "%s"', url, params)
    return requests.post(url, data, allow_redirects=allow_redirects, params=params, auth=auth, headers=headers)
