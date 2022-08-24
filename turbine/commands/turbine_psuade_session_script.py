#!/usr/bin/env python
##########################################################################
# $Id: turbine_psuade_session_script.py 4480 2013-12-20 23:20:21Z boverhof $
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
import csv
import sys
import os
import shutil
import json
import optparse
import sys
import os
import time
from .requests_base import get_page, put_page, delete_page, post_page,\
    get_page_by_url, read_configuration,\
    RequestException, HTTPError, ConnectionError

from turbine.commands.turbine_psuade_script import *
from turbine.commands import add_options, _open_config
from turbine.commands.turbine_session_script import *
from configparser import ConfigParser
import dateutil.parser
import datetime


def psuade_launch(configFile, psuadeInFilename):
    """Takes a PSUADE file and submits all the jobs contained therein as a new session.
       Returns immediatly."""

    configFile.get(SECTION, 'url')
    samples = getInputsFromPSUADE_IO(configFile, psuadeInFilename)
    inputsJson = writeInputsToGatewayFormat(configFile, samples)

    # create the session
    sessionid = create_session(configFile)
    print(sessionid)

    # create all the jobs in the session
    batches = len(inputsJson) / 500
    if(len(inputsJson) % 500 > 0):
        batches += 1

    print("Num batches: ", batches)

    for ii in range(0, batches):
        start = (ii)*500
        end = ((ii+1)*500)
        tmparray = inputsJson[(ii)*500:((ii+1)*500)]
        print("batch:", ii, " start:", start, " end:",
              end, " size: ", tmparray.__len__())
        createJobsResult = create_jobs(configFile, sessionid, tmparray)
        submitJobsResult = start_jobs(configFile, sessionid)

    return sessionid


def local_launch(configFile, psuadeInFilename):
    """Takes a PSUADE file and actually launches PSUADE on it (in the background).  For locally run demo cases.
       Returns immediatly."""

    psuadeCommand = "psuade"
    if(configFile.has_section("PSUADE") and
       configFile.has_option("PSUADE", "PSUADE")):
        psuadeCommand = configFile.get("PSUADE", "PSUADE")

    import platform
    if platform.system() == 'Windows':
        from subprocess import Popen
        Popen("%s %s" % (psuadeCommand, psuadeInFilename), shell=True)
    else:
        os.system("%s %s &" % (psuadeCommand, psuadeInFilename))
    return "psuadeData"


def main_psuade_launch(args=None):
    """Takes a PSUADE file and submits all the jobs contained therein as a new session. Returns immediatly.
    """

    op = optparse.OptionParser(usage="USAGE: %prog PSUADE_IN CONFIG_FILE",
                               description=main_psuade_launch.__doc__)
    (options, args) = op.parse_args()
    assert(len(args) == 2)

    psuadeInFilename = args[0]
    configFilename = args[1]

    configFile = _open_config(configFilename)

    if(not configFile.has_section(SECTION) or
       not configFile.has_option(SECTION, "url") or
       configFile.get(SECTION, "url") == ""):
        # Local Psuade based run
        print(local_launch(configFile, psuadeInFilename))
    else:
        # Gateway run
        print(psuade_launch(configFile, psuadeInFilename))


def write_jobs_to_psuade(configFile, sessionid, psuadeInFilename, psuadeOutFilename, options):
    """ Gets all jobs from the session and writed them to a PSUADE file """

    runs = get_results(configFile, sessionid, options)

    # Now write the results out to PSUADE_OUT
    writeJson2Psuade(configFile, runs, psuadeInFilename, psuadeOutFilename)


def main_write_jobs_to_psuade(args=None):
    """ Gets all jobs from the session and writes them to a PSUADE file """

    op = optparse.OptionParser(usage="USAGE: %prog SESSIONID PSUADE_IN PSUADE_OUT CONFIG_FILE",
                               description=main_write_jobs_to_psuade.__doc__)

    add_options(op)

    (options, args) = op.parse_args()
    assert(len(args) >= 4)

    sessionid = args[0]
    psuadeInFilename = args[1]
    psuadeOutFilename = args[2]

    configFile = _open_config(args[3])

    if(not configFile.has_section(SECTION) or
       not configFile.has_option(SECTION, "url") or
       configFile.get(SECTION, "url") == ""):
        # Local Psuade based run
        shutil.copyfile("psuadeData", args[2])
    else:
        # Gateway run
        write_jobs_to_psuade(configFile, sessionid,
                             psuadeInFilename, psuadeOutFilename, options)

    print("Jobs written to", args[2])


def main_do_psuade(args=None):
    """Takes a PSUADE file and submits all the jobs contained therein as a new session. Waits for it to return. Writes results to a new PSUADE file.  (To avoid overwriting the original) If a sessionId is supplied with -s, it is assumed the create and submit process has already happened, so it simply blocks waiting for results.
    """

    op = optparse.OptionParser(usage="USAGE: %prog PSUDADE_IN PSUADE_OUT CONFIG_FILE",
                               description=main_do_psuade.__doc__)

    add_options(op)
    (options, args) = op.parse_args()
    assert(len(args) >= 3)

    psuadeInFilename = args[0]
    psuadeOutFilename = args[1]
    configFilename = args[2]

    configFile = _open_config(configFilename)

    sessionid = options.session

    if(sessionid == None):
        sessionid = psuade_launch(configFile, psuadeInFilename)

    print("SessionID:", sessionid)
    # loop checking that the jobs haven't finished yet
    jobsLeft = 1
    while(jobsLeft > 0):
        jobsLeft = jobs_unfinished(configFile, sessionid)
        print(jobsLeft)
        if(jobsLeft > 0):
            time.sleep(jobsLeft*5)

    # Now that the jobs are complete, get them all
    write_jobs_to_psuade(configFile, sessionid,
                         psuadeInFilename, psuadeOutFilename)
    print("Jobs written to", psuadeOutFilename)


def local_unfinished(configFile, psuadeInFilename):

    psuadeInFile = open(psuadeInFilename, "r+")

    numinputs = 0
    numoutputs = 0
    numsamples = 0

    samples = []

    inIO = False

    while(not inIO):
        line = psuadeInFile.readline()
        linesplit = line.split()
        if(linesplit[0] == "PSUADE_IO"):
            inIO = True

    # print "We're in PSUADE_IO now"

    metaline = psuadeInFile.readline()
    metasplit = metaline.split()
    numinputs = int(metasplit[0])
    numoutputs = int(metasplit[1])
    numsamples = int(metasplit[2])

    numfinished = 0

    # print "%d %d %d" % (numinputs, numoutputs, numsamples)

    # make sure the psuade file and config file agree about the number of outputs
    #assert(configFile.items("OutputsOrder").__len__() == numoutputs)

    sampleNum = 0

    for sampleNum in range(1, numsamples+1):
        #    print sampleNum
        # Now advance the PSUADE File, if parsing goes wonky just bail and return what we have so far
        try:
            line = psuadeInFile.readline()
            linesplit = line.split()
            if(line == None or linesplit == None or sampleNum != int(linesplit[0])):
                return numsamples-numfinished
        except Exception:
            return numsamples-numfinished

        if(int(linesplit[1]) == 1):
            numfinished += 1

        for ii in range(0, numinputs + numoutputs):
            psuadeInFile.readline()  # skip all inputs and outputs

    return numsamples-numfinished


def main_psuade_jobs_unfinished(args=None):
    """Reports how many jobs remain unfinished in the session (Useful for UQ GUI)
    """
    op = optparse.OptionParser(usage="USAGE: %prog [options] SESSIONID CONFIG_FILE",
                               description=main_psuade_jobs_unfinished.__doc__)

    (options, args) = op.parse_args(args)
    if len(args) != 2:
        op.error('expecting 2 arguments')

    sessionid = args[0]

    configFile = _open_config(args[1])

    numunfinished = 0

    if(not configFile.has_section(SECTION) or
       not configFile.has_option(SECTION, "url")):
        # Local Psuade based run
        numunfinished = local_unfinished(configFile, "psuadeData")
    else:
        # Gateway run
        numunfinished = jobs_unfinished(configFile, sessionid)

    if(numunfinished < 0):
        numunfinished = 0

    print
    print("{unfinished:", numunfinished, "}")


def local_stop_jobs(configFile):
    os.system("killall psuade")
    return "killed all"


def main_psuade_stop_jobs(args=None):
    """session resource utility, stops jobs in session in state submit. Works for both local and gateway runs, so it's useful for the GUI.
    """
    op = optparse.OptionParser(usage="USAGE: %prog SESSIONID  CONFIG_FILE",
                               description=main_psuade_stop_jobs.__doc__)

    (options, args) = op.parse_args(args)
    if len(args) != 2:
        op.error('expecting 2 arguments')

    sessionid = args[0]
    configFile = _open_config(args[1])

    if(not configFile.has_section(SECTION) or
       not configFile.has_option(SECTION, "url")):
        # Local Psuade based run
        print(local_stop_jobs(configFile))
    else:
            # Gateway run
        print(stop_jobs(configFile, sessionid))


main = main_list
if __name__ == "__main__":
    main()
