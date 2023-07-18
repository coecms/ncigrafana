#!/usr/bin/env python

"""
Copyright 2020 ARC Centre of Excellence for Climate Systems Science

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
import pwd
import datetime
import os
import sys
import re
import shutil
from .UsageDataset import *
from .DBcommon import extract_num_unit, parse_size, mkdir, archive
from .DBcommon import datetoyearquarter, date_range_from_quarter

databases = {}
dbfileprefix = '.'
nfields = 7

def parse_lquota(filename, verbose, db=None, dburl=None):

    project = None

    year = None
    quarter = None
    date = None

    with open(filename) as f:

        print("Parsing {file}".format(file=filename))

        parsing_usage = False

        for line in f:

            if verbose: print("> ",line)
            if line.startswith("%%%%%%%%%%%%%%%%"):
                # Grab date string
                date = datetime.datetime.strptime(f.readline().strip(os.linesep), 
                                                  "%a %b %d %H:%M:%S %Z %Y")
                year, quarter = datetoyearquarter(date)
                startdate, enddate = date_range_from_quarter(year,quarter)
                db.addquarter(year, quarter, startdate, enddate)
                continue

            if line.lstrip().startswith("fs") and line.rstrip().endswith("iLimit"): 
                # Gobble the other header
                line = f.readline()
                parsing_usage = True
                continue

            if parsing_usage:

                if line.startswith('-----------'):
                    if verbose: print('Finished parsing short usage')
                    parsing_usage = False
                    continue

                project,storagepoint,size,size_quota,_,inodes,inodes_quota,_ = line.strip(os.linesep).split(maxsplit=nfields)
                size=float(size)
                size_quota=float(size_quota)
                inodes=int(inodes)
                inodes_quota=int(inodes_quota)
                #array = line.strip(os.linesep).split(maxsplit=nfields)
                #project = array[0]
                #storagepoint = array[1]
                #size=array[2]
                #size = parse_size((array[2]+array[3]), b=1024, u='iB')
                #size_quota = parse_size((array[4]+array[5]), b=1024, u='iB')
                #size_limit = parse_size((array[6]+array[7]), b=1024, u='iB')
                #inodes = int(array[8])
                #inodes_quota = int(array[9])
                #inodes_limit = int(array[10])

                #if len(array) == nfields:
                #    msg = array[nfields-1]
                #else:
                #    msg = None

                system = 'gadi'
                scheme = 'Combined'

                db.addscheme(scheme)

                if verbose: print('Add project storage ', project, system, storagepoint, date, size, inodes)
                db.addprojectstorage(project, system, storagepoint, date, size, inodes)

                storagetype = 'capacity'
                if verbose: print('Add project storage grant', project, system, storagepoint, scheme, 
                                   year, quarter, date, storagetype, size_quota)
                db.addstoragegrant(project, system, storagepoint, scheme, year, quarter, 
                                           str(date.date()), storagetype, size_quota)

                storagetype = 'inodes'
                if verbose: print('Add project storage grant', project, system, storagepoint, scheme, 
                                   year, quarter, date, storagetype, inodes_quota)
                db.addstoragegrant(project, system, storagepoint, scheme, year, quarter, 
                                           str(date.date()), storagetype, inodes_quota)

"""
--------------------------------------------------------------------------
           fs       Usage      Quota      Limit   iUsage   iQuota   iLimit
--------------------------------------------------------------------------
   vv5 scratch  19.56 TiB  109.0 TiB  218.0 TiB  9107665 44223147 88446294
   wv0 scratch   7.19 TiB  10.99 TiB  21.97 TiB   703700  1097000  2194000
   vv5   gdata 158.04 TiB 158.95 TiB 166.89 TiB  7156412  8468000  8891400
   wv0   gdata  76.21 TiB   80.0 TiB   84.0 TiB  1805324  5465000  5738250
--------------------------------------------------------------------------
"""

def main(args):

    verbose = args.verbose

    db = None
    if args.dburl:
        db = ProjectDataset(dburl=args.dburl)

    for f in args.inputs:
        try:
            parse_lquota(f, verbose, db=db)
        except:
            raise
        else:
            if not args.noarchive:
                archive(f)

def parse_args(args):
    """
    Parse arguments given as list (args)
    """
    parser = argparse.ArgumentParser(description="Parse file report dumps")
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

