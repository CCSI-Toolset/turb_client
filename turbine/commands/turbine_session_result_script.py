#!/usr/bin/env python
##########################################################################
# $Id: turbine_session_script.py 4480 2013-12-20 23:20:21Z boverhof $
# Joshua R. Boverhof, LBNL
# See LICENSE.md for copyright notice!
#
#   $Author: boverhof $
#   $Date: 2013-12-20 15:20:21 -0800 (Fri, 20 Dec 2013) $
#   $Rev: 4480 $
#
###########################################################################
import urllib.request
import urllib.error
from urllib.parse import urljoin
import sys
import json
import optparse
import glob
import uuid
import os
import time
import time
import dateutil.parser
import datetime
import logging
from .requests_base import get_page, put_page, delete_page, post_page,\
    post_page_by_url, get_page_by_url, read_configuration,\
    RequestException, HTTPError, ConnectionError
from . import add_options, add_json_option,\
    _open_config, load_pages_json, _print_page,\
    _print_page, _print_numbered_lines, _print_as_json,\
    getFromConfigWithDefaults,\
    HEADER_CONTENT_TYPE_JSON
SECTION = "Session"
_log = logging.getLogger(__name__)

def main_session_result(args=None):
    """Retrives the results of the completed jobs in this session,
    if option result is specified the data for that page is returned
    else see if a new page is available and return the page number.
    If the page number doesn't change, it means there is no new Data
    availble.  Must check number of results against the number of jobs
    submitted to verify if all data has been returned.
    """
    op = optparse.OptionParser(usage="USAGE: %prog SESSIONID  CONFIG_FILE",
                               description=main_session_result.__doc__)

    add_options(op)
    op.add_option("--result",
                  action="store", dest="result", type=int, default=None,
                  help="GET result page number (>0, last path URL)")
    op.add_option("--resultid",
                  action="store", dest="result_id",
                  default='00000000-0000-0000-0000-000000000000',
                  help="GET result-id (last path URL)")
    (options, args) = op.parse_args(args)
    if len(args) < 1:
        op.error('expecting >= 1 arguments')
    if options.result == 0:
        op.error('result page number must be > 0')

    session_id = args[0]
    try:
        cp = _open_config(*args[1:])
    except Exception as ex:
        op.error(ex)

    kw = vars(options)
    result_id = kw['result_id']
    del kw['result_id']
    result_page = kw['result']
    del kw['result']
    url,auth,params = read_configuration(cp, SECTION, **kw)
    if result_page:
        l = get_session_result_page(
            url,
            auth,
            session_id,
            result_id,
            result_page=result_page,
            **params
        )
        assert type(l) is list
        print(json.dumps(l))
    else:
        page_numb = post_session_result(
            url,
            auth,
            session_id,
            result_id,
            **params
        )
        print(page_numb)


def post_session_result(url, auth, session_id,
        result_id, **kw) -> int:
    """Returns next page number
    POST session/{session_id}/result/{result_id}
    """
    result_url = '%s%s/result/%s' %(url, session_id, result_id)
    data = post_page_by_url(result_url, auth, **kw)

    page_numb = int(data.content)
    _log.debug("Result Page Number %d", page_numb)
    return page_numb

def get_session_result_page(url, auth, session_id, result_id, result_page, **kw) -> list:
    """ Gets jobs from the session, result, page number and return them as a list """
    result_page_url = '%s%s/result/%s/%d' %(url, session_id, result_id, result_page)
    data = get_page_by_url(result_page_url, auth, **kw)
    return json.loads(data)
