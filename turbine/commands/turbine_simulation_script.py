#!/usr/bin/env python
##########################################################################
# $Id: turbine_simulation_script.py 10089 2016-02-29 19:46:07Z aaelbashandy $
# Joshua R. Boverhof, LBNL
# See LICENSE.md for copyright notice!
#
#   $Author: aaelbashandy $
#   $Date: 2016-02-29 11:46:07 -0800 (Mon, 29 Feb 2016) $
#   $Rev: 10089 $
#
###########################################################################
import urllib.request
import urllib.error
import csv
import sys
import os
import json
import uuid
import logging
import optparse
from .requests_base import get_page, put_page, delete_page
from . import add_options, add_json_option,\
    _open_config, load_pages_json, _print_page

SECTION = "Simulation"
_log = logging.getLogger(__name__)

def _print_json(data, verbose=False, out=sys.stdout):
    if type(data) in (list, dict):
        json.dump(data, out)
    else:
        print(data, file=out)


def _print_simulation_list(all, verbose=False, out=sys.stdout):
    print("Total Simulations: %d" % len(all), file=out)
    for sim in all:
        if not verbose:
            print("\t%s" % (sim['Name']), file=out)
            continue
        print("=="*30, file=out)
        print("=="*30, file=out)
        print("%12s" % (sim['Name']), file=out)
        if verbose:
            for k, v in sim.items():
                print("\t%12s: %12s" % (k, v), file=out)


def main_create(args=None):
    """Create an empty Simulation Resource
    """
    op = optparse.OptionParser(usage="USAGE: %prog [options] SIMULATION_NAME|GUID APPLICATION_NAME CONFIG_FILE",
                               description=main_create.__doc__)
    op.add_option("-s", "--simulation",
                  action="store", dest="simulation_name", default=None,
                  help="override versioning system and specify the GUID identifier for a simulation ")

    (options, args) = op.parse_args(args)
    if len(args) != 3:
        op.error('expecting 3 arguments')

    cp = _open_config(args[2])
    application = args[1]
    subresource = args[0]
    simulation_name = None

    if options.simulation_name:
        uuid.UUID(subresource)
        simulation_name = options.simulation_name
    else:
        try:
            uuid.UUID(subresource)
        except ValueError:
            pass
        else:
            op.error('must use -s option when specifying a guid, see help')
        simulation_name = subresource

    kw = dict(subresource=subresource)
    data = json.dumps(dict(Application=application,
                           StagedInputs=[], Name=simulation_name))

    try:
        data = put_page(cp, SECTION, data,
                        content_type='application/json', **kw)
    except urllib.error.HTTPError as ex:
        _log.error(ex)
        if hasattr(ex, 'readlines'):
            _log.error("".join(ex.readlines()))
        elif hasattr(ex, 'read'):
            _log.error("".join(ex.read()))

        raise
    return json.loads(data)


def main_update(args=None):
    """Update simulation by essentially doing a PUT with the specified file to the resource or optionally sub-resource.
    """
    op = optparse.OptionParser(usage="USAGE: %prog [options] SIMULATION_NAME|GUID FILE_NAME CONFIG_FILE",
                               description=main_update.__doc__)

    op.add_option("-r", "--resource",
                  action="store", dest="resource",
                  help="select the staged input file name (matches Application)")

    (options, args) = op.parse_args(args)
    if len(args) != 3:
        op.error('expecting 3 arguments')

    _log.debug('main_update: %s' %args)

    file_name = args[1]
    if not os.path.isfile(file_name):
        op.error('expecting a file for argument 2')

    if options.resource is None:
        op.error('require resource option to be specified')

    configFile = _open_config(args[2])
    simulation = args[0]
    kw = {}
    out = sys.stdout

    kw['subresource'] = '%s/input/%s' % (simulation, options.resource)

    with open(file_name, 'rb') as fd:
        contents = fd.read()
        try:
            data = put_page(configFile, SECTION, contents, **kw)
        except urllib.error.HTTPError as ex:
            _log.error("HTTP Code %d :  %s", ex.code, ex.msg)
            if hasattr(ex, 'readlines'):
                _log.debug("".join(ex.readlines()))
            else:
                _log.debug("".join(ex.read()))
            raise
        except urllib.error.URLError as ex:
            _log.error("URLError :  %s", ex.reason)
            raise

    return data


def main_get(args=None, func=_print_json):
    """Retrieves the Simulation resource, by default prints as JSON.
    """
    op = optparse.OptionParser(usage="USAGE: %prog [options] SIMULATION_NAME CONFIG_FILE",
                               description=main_get.__doc__)

    # add_options(op)
    op.add_option("-r", "--resource",
                  action="store", dest="resource",
                  help="return only the specified input subresource")
    op.add_option("-s", "--save",
                  action="store_true", dest="save",
                  help="Save the resource as a file")

    (options, args) = op.parse_args(args)
    if len(args) != 2:
        op.error('expecting 2 arguments')

    configFile = _open_config(args[-1])
    simulation = args[0]

    query = {}
    fileName = 'simulation_%s' % (simulation)
    if options.resource:
        fileName += '_%s' % options.resource
        query['subresource'] = '%s/input/%s' % (simulation, options.resource)
        data = get_page(configFile, SECTION, **query)
    else:
        query['subresource'] = '%s' % (simulation)
        data = json.loads(get_page(configFile, SECTION, **query))

    if func:
        out = sys.stdout
        if options.save:
            out = open('%s.txt' % fileName, 'w')
        func(data, out=out)

    return data


def main_list(args=None, func=_print_simulation_list):
    """Retrieves list of all simulations, by default prints in human readable format.
    """
    op = optparse.OptionParser(usage="USAGE: %prog [options] CONFIG_FILE",
                               description=main_list.__doc__)
    add_options(op)
    add_json_option(op)
    (options, args) = op.parse_args(args)

    if len(args) != 1:
        op.error('expecting 1 argument')
    if options.json:
        func = _print_json

    configFile = _open_config(args[0])
    query = {}

    if options.verbose:
        query['verbose'] = options.verbose

    if options.page:
        query['page'] = options.page

    content = get_page(configFile, SECTION, **query)
    data = load_pages_json([content])
    if func:
        func(data, verbose=options.verbose)

    return data


def main_delete(args=None, func=_print_page):
    """Delete simulation
    """
    op = optparse.OptionParser(usage="USAGE: %prog SIMULATION_NAME  CONFIG_FILE",
                               description=main_delete.__doc__)

    (options, args) = op.parse_args(args)
    if len(args) < 1:
        op.error('expecting >= 1 arguments')

    simulationName = args[0]
    try:
        configFile = _open_config(*args[1:])
    except Exception as ex:
        op.error(ex)

    try:
        page = delete_page(configFile, SECTION,
                           subresource='%s' % simulationName)
    except urllib.error.HTTPError as ex:
        _log.error(ex)
        raise
    _log.debug("PAGE: %s" % page)

    return page


if __name__ == "__main__":
    main_list()
