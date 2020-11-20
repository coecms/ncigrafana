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
import pwd
import datetime
import os
import sys
import re
import shutil
from .UsageDataset import *
from .DBcommon import extract_num_unit, parse_size, mkdir, archive
from .DBcommon import date_range_from_quarter, datetoyearquarter

databases = {}
dbfileprefix = '.'

def parse_file_report(filename, verbose, db=None, dburl=None):

    # Filename contains project and storage point information
    (timestamp, project, storagepoint, tmp) = os.path.basename(filename).split('.')

    # Hard code the system based on storagepoint as this information
    # does not exist in the dumpfile. Not even sure NCI make this distinction
    # any longer, but we need this information for the database
    if storagepoint.startswith('gdata'):
        system = 'global'
    elif storagepoint == 'scratch':
        system = 'gadi'

    with open(filename) as f:

        print("Parsing {file}".format(file=filename))

        parsing_usage = False

        for line in f:
            if verbose: print("> ",line)
            if line.startswith("%%%%%%%%%%%%%%%%"):
                # Grab date string
                date = datetime.datetime.strptime(f.readline().strip(os.linesep), 
                                                  "%a %b %d %H:%M:%S %Z %Y").date()
                year, quarter = datetoyearquarter(date)
                startdate, enddate = date_range_from_quarter(year,quarter)
                db.addquarter(year, quarter, startdate, enddate)
                parsing_usage = True
                # Gobble header line
                line = f.readline()
                continue

            if parsing_usage:
                try:
                    (filesystem,scandate,folder,proj,user,size,filesize,inodes) = line.strip(os.linesep).split() 
                except:
                    if verbose: print('Finished parsing short usage')
                    parsing_usage = False
                    continue
                db.adduser(user)
                if verbose: print('Adding ', project, user, system, storagepoint, str(date), folder, 
                                             parse_size(size.upper(), u='', pre='BKMGTPEZY'), inodes)
                db.adduserstorage(project, 
                                  user, 
                                  system, 
                                  storagepoint, 
                                  str(date), 
                                  folder, 
                                  parse_size(size.upper(), u='', pre='BKMGTPEZY'), 
                                  inodes)

def main(args):

    verbose = args.verbose

    db = None
    if args.dburl:
        db = ProjectDataset(dburl=args.dburl)

    for f in args.inputs:
        try:
            parse_file_report(f, verbose, db=db)
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

