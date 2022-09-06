#!/usr/bin/env python
##########################################################################
# $Id: turbine_consumer_script.py 4480 2013-12-20 23:20:21Z boverhof $
# Joshua R. Boverhof, LBNL
# See LICENSE.md for copyright notice!
#
#   $Author: boverhof $
#   $Date: 2013-12-20 15:20:21 -0800 (Fri, 20 Dec 2013) $
#   $Rev: 4480 $
#
###########################################################################
import json
import optparse
import sys
import time
import dateutil.parser
import datetime
from urllib.error import HTTPError
# from turbine.commands import add_options, post_page, put_page, \
#     get_page, get_page_by_url, get_paging, _open_config, load_pages_json, \
#     _print_page, _print_numbered_lines, add_json_option, _print_as_json

from .requests_base import get_page, put_page, delete_page, post_page,\
    post_page_by_url, get_page_by_url, read_configuration,\
    RequestException, HTTPError, ConnectionError
from . import add_options,\
    _open_config, load_pages_json, _print_page,\
    _print_page, _print_numbered_lines, _print_as_json,\
    getFromConfigWithDefaults,\
    HEADER_CONTENT_TYPE_JSON

SECTION = "Consumer"


def main(args=None, func=_print_numbered_lines):
    """List all Consumer resources, by default print in human readable format.
    """
    op = optparse.OptionParser(usage="USAGE: %prog [options] CONFIG_FILE",
                               description=main.__doc__)

    # add_options(op)
    op.add_option("-v", "--verbose",
                  action="store_true", dest="verbose",
                  help="verbose output")
    """
    op.add_option("-p", "--page", type="int",
                  action="store", dest="page", default=0,
                  help="page number")
    op.add_option("-r", "--rpp", type="int",
                  action="store", dest="rpp", default=1000,
                  help="results per page")
    """
    op.add_option("-s", "--status",
                  action="store", dest="status",
                  help="query on status ['up'|'down'|'error']")
    add_json_option(op)

    (options, args) = op.parse_args(args)
    if len(args) != 1:
        op.error('expecting 1 argument')

    configFile = _open_config(args[0])

    query = {}
    if options.status:
        query['status'] = options.status

    # NOTE RESOURCE NOT SUPPORTING PAGING
    #pages = get_paging(configFile, SECTION, options, **query)
    #data = load_pages_json(pages)
    page = get_page(configFile, SECTION, **query)
    data = json.loads(page)
    if options.json:
        func = _print_as_json
    if func:
        func(data)
    return data


def main_get_consumer_by_guid(args=None, func=_print_page):
    """Retrieves consumer by GUID
    """
    op = optparse.OptionParser(usage="USAGE: %prog [options] CONSUMER_GUID CONFIG_FILE",
                               description=main.__doc__)

    (options, args) = op.parse_args(args)
    if len(args) != 2:
        op.error('expecting 2 arguments')
    configFile = _open_config(args[1])
    query = dict(subresource='/%s' % args[0])
    page = get_page(configFile, SECTION, **query)
    data = json.loads(page)
    if func:
        func(data)
    return data


def main_log(args=None, func=_print_page):
    """Retrieves logging messages from compute resource running the specified
    Consumer.  Log messages are printed to screen in order.  This functionality
    is not available in all deployments.
    """
    op = optparse.OptionParser(usage="USAGE: %prog [options] CONFIG_FILE",
                               description=main_log.__doc__)

    (options, args) = op.parse_args(args)
    if len(args) != 2:
        op.error('expecting 2 arguments')
    configFile = _open_config(args[1])
    query = dict(subresource='/%s/log' % args[0])
    page = get_page(configFile, SECTION, **query)
    if func:
        func(page)
    return page


def main_get_config(args=None, func=_print_page):
    """Return configuration settings for top-level Consumer resource, by default
    print as JSON.  These settings are utilized by an orchestrator process
    (deployment specific).  The AWS EC2 orchestator handles auto-scaling of instances.
    """
    op = optparse.OptionParser(usage="USAGE: %prog [options] CONFIG_FILE",
                               description=main_get_config.__doc__)

    # add_options(op)
    op.add_option("-v", "--verbose",
                  action="store_true", dest="verbose",
                  help="verbose output")

    (options, args) = op.parse_args(args)
    if len(args) != 1:
        op.error('expecting 1 argument')

    configFile = _open_config(args[0])
    query = dict(subresource='/config')
    page = get_page(configFile, SECTION, **query)
    if func:
        func(page)
    return page


def main_update_config_floor(args=None, func=_print_page):
    """Sets a floor for the number of Consumer processes that should remain running
    for a interval determined by the server.  Currently this is only supported in
    the AWS EC2 deployment.  By default prints entire resultant configuration in JSON.
    """
    op = optparse.OptionParser(usage="USAGE: %prog [options] INT CONFIG_FILE",
                               description=main_update_config_floor.__doc__)

    # add_options(op)
    op.add_option("-v", "--verbose",
                  action="store_true", dest="verbose",
                  help="verbose output")

    (options, args) = op.parse_args(args)
    if len(args) != 2:
        op.error('expecting 2 argument')

    configFile = _open_config(args[1])
    query = dict(subresource='/config')

    page = put_page(configFile, SECTION, json.dumps(
        dict(floor=int(args[0]))), **query)
    if func:
        func(page)
    return page


def main_update_config_instanceType(args=None, func=_print_page):
    """Sets the AWS EC2 instance type for new virtual machines.  This feature is only
    relevant for the AWS EC2 deployment.  By default prints entire resultant configuration in JSON.
    """
    op = optparse.OptionParser(usage="USAGE: %prog [options] [t1.micro | m1.small | c1.medium] CONFIG_FILE",
                               description=main_update_config_instanceType.__doc__)

    # add_options(op)
    op.add_option("-v", "--verbose",
                  action="store_true", dest="verbose",
                  help="verbose output")

    (options, args) = op.parse_args(args)
    if len(args) != 2:
        op.error('expecting 2 argument')

    configFile = _open_config(args[1])
    query = dict(subresource='/config')
    page = put_page(configFile, SECTION, json.dumps(
        dict(instance=args[0])), **query)
    if func:
        func(page)
    return page

def post_consumer_stop(url, auth, consumer_id,
        **kw) -> int:
    """Returns 1 if request to stop accepted
    POST consumer/{consumer_id}/stop
    """
    stop_url = '%s/%s/stop' %(url, consumer_id)
    is_stopped = post_page_by_url(stop_url, auth, **kw)
    return is_stopped


if __name__ == "__main__":
    main()
