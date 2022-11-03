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
import json
import os
import sys
import pwd
import grp
import datetime

from .UsageDataset import *
from .DBcommon import date_range_from_quarter, datetoyearquarter, archive

databases = {}
dbfileprefix = '.'

def parse_file_report(filename, verbose, db=None, dburl=None):

    # Filename contains project and storage point information
    (_, _, storagepoint, _) = os.path.basename(filename).split('.')

    # Hard code the system based on storagepoint as this information
    # does not exist in the dumpfile. Not even sure NCI make this distinction
    # any longer, but we need this information for the database
    if storagepoint.startswith('gdata'):
        system = 'global'
    elif storagepoint == 'scratch':
        system = 'gadi'

    with open(filename) as f:
        all_data=json.loads(f.read())
        
    ### Grab timestamp - pretend there are no cross-quarter entries
    datestamp = datetime.datetime.fromisoformat(all_data[0]["scan_time"])
    year, quarter = datetoyearquarter(datestamp)
    startdate, enddate = date_range_from_quarter(year,quarter)
    db.addquarter(year,quarter,startdate,enddate)
    
    for entry in all_data:
        ### Handle uids that don't exist
        try:
            user = pwd.getpwuid(entry['uid']).pw_name
        except KeyError:
            user = str(entry['uid'])
        db.adduser(user)

        if storagepoint == 'scratch':
        # Swap folder and proj in the case of scratch as it is now accounted for by 
        # location, so folder never changes but project code can and subsequent entries 
        # overwrite previous ones unless values of folder and proj are swapped
            ### Handle gids that don't exist
            try:
                folder=grp.getgrgid(entry['gid']).gr_name
            except KeyError:
                folder=str(entry['gid'])
            project=entry['project']
        else:
            folder=entry['project']
            ### Handle gids that don't exist
            try:
                project=grp.getgrgid(entry['gid']).gr_name
            except KeyError:
                project=str(entry['gid'])

        ### Derived from nci-files-report client (formatters/table.py)
        size = 512 * int(entry['blocks']['single'] + entry['blocks']['multiple'])
        inodes = int(entry['count']['single'] + entry['count']['multiple'])

        if verbose:
            ### Date comes out in iso format, first 10 characters will be YYYY-MM-DD
            print(f"Adding {project}, {user}, {system}, {storagepoint}, {entry['scan_time'][:10]}, {folder}, {size}, {inodes}")
        db.adduserstorage(project,user,system,storagepoint,entry['scan_time'][:10],folder,size,inodes)

def main(args):

    db = None
    if args.dburl:
        db = ProjectDataset(dburl=args.dburl)

    for f in args.inputs:
        try:
            parse_file_report(f,args.verbose,db=db)
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
