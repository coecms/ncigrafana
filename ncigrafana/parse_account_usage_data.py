#!/usr/bin/env python

"""
Copyright 2019 ARC Centre of Excellence for Climate Systems Science

author: Aidan Heerdegen <aidan.heerdegen@anu.edu.au>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import print_function

import argparse
import gzip
import datetime
import json
from math import log
import os
import pwd
import re
import shutil
import sys

from .UsageDataset import *
from .DBcommon import extract_num_unit, parse_size, mkdir, archive, parse_inodenum
from .DBcommon import datetoyearquarter, date_range_from_quarter

databases = {}
dbfileprefix = '.'

def parse_account_dump_file(filename, verbose, db=None, dburl=None):

    with open(filename) as f:

        insystem = False; instorage = False; inuser = False; inusage=False
        project = None
    
        parsing = False

        year = ''; quarter = ''
        system = ''; date = ''

        for line in f:
            line = line.rstrip(os.linesep)
            resources = None
            if verbose: print(line)
            if line.startswith("%%%%%%%%%%%%%%%%"):
                # Grab date string
                date = datetime.datetime.strptime(f.readline().rstrip(os.linesep), "%a %b %d %H:%M:%S %Z %Y").date()
                year, quarter = datetoyearquarter(date)
                startdate, enddate = date_range_from_quarter(year,quarter)
                if verbose: print('Adding quarter: ', year, quarter, startdate, enddate) 
                db.addquarter(year, quarter, startdate, enddate)
                parsing = True
            else:
                try:
                    resources = json.loads(line)
                except Exception as e:
                    parsing = False
                    print(e)
                    continue

                if resources['status'] == 200:
                    project = resources['project']

                system = 'gadi'
                # Make a bogus queue name called combine while we have no breakdown of usage by queue
                queue = 'combined'
                weight = 2
                db.addsystemqueue(system, queue, weight)

                usecpu = -999.
                usewall = -999.
                efficiency = '-999'

                for scheme in resources['usage']['stakeholders']:

                    if verbose: print('Add scheme ', project, scheme)
                    db.addscheme(scheme)

                    grantsu = resources['usage']['stakeholders'][scheme]['grant']
                    if verbose: print('Add scheme grants ', project, system, scheme, year, quarter, date, grantsu)
                    db.addusagegrant(project, system, scheme, year, quarter, date, grantsu)

                    su = resources['usage']['stakeholders'][scheme]['balance']
                    if verbose: print('Add scheme usage ', project, system, scheme, date, su)
                    db.addschemeusage(project, system, scheme, date, usecpu, usewall, su)

                usesu = resources['usage']['used']

                if verbose: print('Add project usage ',date,system,queue,usecpu,usewall,usesu)
                db.addprojectusage(project, system, queue, date, usecpu, usewall, usesu)

                for user in resources['usage']['users']:
                    usesu = resources['usage']['users'][user]['usage']

                    if verbose: print('Add usage ',date,user,usecpu,usewall,usesu,efficiency)
                    db.adduserusage(project, user, date, usecpu, usewall, usesu, efficiency)

                # if verbose: print('Add project storage grant',project, system, storagepoint, scheme, 
                #                    year, quarter, date, storagetype, parsed_value)
                # db.addstoragegrant(project, system, storagepoint, scheme, year, quarter, 
                #                    date, storagetype, parsed_value)
                                   
def main(args):

    verbose = args.verbose

    db = None
    if args.dburl:
        db = ProjectDataset(dburl=args.dburl)

    for f in args.inputs:
        if verbose: print(f)
        try:
            parse_account_dump_file(f, verbose, db=db)
        except:
            raise
        else:
            if not args.noarchive:
                archive(f)

def parse_args(args):
    """
    Parse arguments given as list (args)
    """
    parser = argparse.ArgumentParser(description="Parse usage dump files")
    parser.add_argument("-d","--directory", help="Specify directory to find dump files", default=".")
    parser.add_argument("-v","--verbose", help="Verbose output", action='store_true')
    parser.add_argument("-db","--dburl", help="Database file url", default=None)
    parser.add_argument("-n","--noarchive", help="Database file url", action='store_true')
    parser.add_argument("inputs", help="dumpfiles", nargs='+')

    return parser.parse_args()

def main_parse_args(args):
    """
    Call main with list of arguments. Callable from tests
    """
    # Must return so that check command return value is passed back to calling routine
    # otherwise py.test will fail
    return main(parse_args(args))

def main_argv():
    """
    Call main and pass command line arguments. This is required for setup.py entry_points
    """
    main_parse_args(sys.argv[1:])

if __name__ == "__main__":

    main_argv()

