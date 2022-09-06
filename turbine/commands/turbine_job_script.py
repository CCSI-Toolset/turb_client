#!/usr/bin/env python
##########################################################################
# $Id: turbine_job_script.py 6627 2014-10-09 23:00:13Z aaelbashandy $
# Joshua R. Boverhof, LBNL
# See LICENSE.md for copyright notice!
#
#   $Author: aaelbashandy $
#   $Date: 2014-10-09 16:00:13 -0700 (Thu, 09 Oct 2014) $
#   $Rev: 6627 $
#
###########################################################################
import urllib.request
import urllib.error
import csv
import sys
import os
import logging as _log
import json
import optparse
import sys
from configparser import ConfigParser
from urllib.error import HTTPError
from .requests_base import get_page,\
    get_page_by_url, read_configuration,\
    RequestException, HTTPError, ConnectionError
from turbine.commands import add_options, add_session_option, states, _open_config, load_pages_json,\
    _print_as_json
from turbine.utility import basic_job_stats

SECTION = "Job"


def write_basic_job_info(fd, d, verbose=False):
    """
    """
    skip = tuple()
    if not verbose:
        skip = ("Input", "Output")
    for k in filter(lambda i: i not in skip, d.keys()):
        print("%12s     %s" % (k, d[k]))
    basic_job_stats(sys.stdout, **d)


def main(args=None, func=_print_as_json):
    """Queries for job resources based on select criteria, by default prints JSON array of jobs.
    """
    global states
    op = optparse.OptionParser(usage="USAGE: %prog [options] CONFIG_FILE",
                               description=main.__doc__)

    op.add_option("-j", "--jobid",
                  action="store", dest="subresource", default=None,
                  help="JOB ID")
    op.add_option("-n", "--sim",
                  action="store", dest="simulation", default=None,
                  help="Simulation Name")
    op.add_option("-x", "--state",
                  action="store", dest="state", default=None,
                  help="Job Status to query: %s" % list(states))
    op.add_option("-c", "--consumer",
                  action="store", dest="consumer", default=None,
                  help="Consumer GUID to query")
    op.add_option("-b", "--basic",
                  action="store_true", dest="basic",
                  help="Print Basic Information About Job(s)")

    add_options(op)
    add_session_option(op)
    (options, args) = op.parse_args(args)

    configFile = _open_config(args[0])

    query = {}
    if options.session:
        query['session'] = options.session
    if options.simulation:
        query['simulation'] = options.simulation
    if options.subresource:
        query['subresource'] = options.subresource
    if options.state:
        query['state'] = options.state
    if options.consumer:
        query['consumer'] = options.consumer
    if options.verbose:
        query['verbose'] = options.verbose

    if options.subresource:
        page = get_page(configFile, SECTION, **query)
        job = json.loads(page)
        if options.basic:
            write_basic_job_info(sys.stdout, job, verbose=options.verbose)
        elif func is not None and callable(func):
            func(job, sys.stdout)

        return job

    try:
        pages = get_page(configFile, SECTION, **query)
    except HTTPError as ex:
        print(ex)
        print(ex.readlines())
        return

    #states = set(['submit', 'create', 'setup', 'running', 'success', 'warning', 'error', 'expired', 'cancel', 'terminate'])
    all = load_pages_json(pages)
    fstates = set(map(lambda e: e['State'], all))
    if not fstates.issubset(states):
        _log.debug('**NOTE: Unexpected State Found')
        states = states.union(fstates)

    if options.basic:
        print("Total JOBS: %d" % len(all))
        for state in states:
            if options.state is not None and options.state != state:
                continue
            flist = list(filter(lambda e: e['State'] == state, all))
            print("\t%s JOBS: %d" % (state.upper(), len(flist)))
            if options.verbose:
                for i in flist:
                    print
                    for k, v in i.items():
                        print("\t%12s -- %s" % (k, v))
            else:
                print("\t%s" % list(map(lambda m: m['Id'], flist)))
    elif func is not None and callable(func):
        _print_as_json(all)

    return all

# Extra Args are passed as string unless a special case is
# provided within parseExtraArgs


def parseExtraArgs(configFile):
    extraArgs = {}
    if(configFile.has_section("ExtraArgs")):
        extraArgs.update(configFile.items("ExtraArgs"))
        if configFile.has_option("ExtraArgs", "Initialize"):
            extraArgs["Initialize"] = configFile.getboolean(
                "ExtraArgs", "Initialize")
        if configFile.has_option("ExtraArgs", "Reset"):
            extraArgs["Reset"] = configFile.getboolean("ExtraArgs", "Reset")

    return extraArgs


def post_job_terminate(url, auth, job_id,
        **kw) -> int:
    """Returns 1 if request to stop accepted
    POST consumer/{consumer_id}/stop
    """
    uuid.UUID(job_id)
    terminate_url = '%s/%s/terminate' %(url, job_id)
    is_term = post_page_by_url(terminate_url, auth, **kw)
    return is_term


if __name__ == "__main__":
    main()
