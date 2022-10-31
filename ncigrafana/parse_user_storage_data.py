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
import sys
import requests
import pwd
import grp
import datetime

from .UsageDataset import *
from .DBcommon import date_range_from_quarter, datetoyearquarter
from .NCIAPI import prep_auth_header

databases = {}
dbfileprefix = '.'

def parse_file_report(nci_api_url: str, projects: str, filesystem: str, verbose: bool, db: ProjectDataset=None, dburl: str=None):


    if filesystem == 'scratch':
        system='gadi'
        project_option='project'
    elif filesystem.startswith("gdata"):
        system='global'
        project_option='group'
    else:
        exit(f"Invalid filesystem: {filesystem}")

    ### Derived from nci-files-report client (command.py)
    request_d={'fs':[filesystem],'filter':{'type':project_option,'values':projects.split(',')}}
    
    try:
        r=requests.post(nci_api_url,headers=prep_auth_header(),json=request_d)
    except:
        exit(f"{sys.exc_info()[0]} {sys.exc_info()[1]}")

    if r.status_code != 200:
        exit(f"Unable to retrieve data from NCI API: Status code: {r.status_code}, Error: {json.loads(r.content)['payload']}")

    all_data = json.loads(r.content)['payload']

    ### Lets pretend there are no cross-quarter entries...
    date = datetime.datetime.fromisoformat(all_data[0]['end_time'])
    year, quarter = datetoyearquarter(date)
    startdate, enddate = date_range_from_quarter(year,quarter)
    db.addquarter(year,quarter,startdate,enddate)

    for entry in all_data:
        user = pwd.getpwuid(entry['user']).pw_name
        db.adduser(user)
        # Swap folder and proj in the case of scratch as it is now accounted for by 
        # location, so folder never changes but project code can and subsequent entries 
        # overwrite previous ones unless values of folder and proj are swapped
        if filesystem == 'scratch':
            folder=grp.getgrgid(entry['group']).gr_name
            project=entry['project']
        else:
            folder=entry['project']
            project=grp.getgrgid(entry['group']).gr_name
        ### Derived from nci-files-report client (formatters/table.py)
        size = 512 * int(entry['blocks']['single'] + entry['blocks']['multi'])
        inodes = int(entry['count']['single'] + entry['count']['multi'])
        if verbose:
            ### Date comes out in iso format, first 10 characters will be YYYY-MM-DD
            print(f"Adding {project}, {user}, {system}, {filesystem}, {entry['end_time'][:10]}, {folder}, {size}, {inodes}")
        db.adduserstorage(project,user,system,filesystem,entry['end_time'][:10],folder,size,inodes)

def main(args):

    db = None
    if args.dburl:
        db = ProjectDataset(dburl=args.dburl)

    try:
        parse_file_report(args.nci_api_url,args.projects,args.filesystem,args.verbose,db=db)
    except:
        raise

def parse_args(args):
    """
    Parse arguments given as list (args)
    """
    parser = argparse.ArgumentParser(description="Parse file report dumps")
    parser.add_argument("-P","--projects",help="Comma-separated list of projects")
    parser.add_argument("-f","--filesystem",help="Filesystem")
    parser.add_argument("-v","--verbose", help="Verbose output", action='store_true')
    parser.add_argument("-db","--dburl", help="Database file url", default=None)
    parser.add_argument("nci_api_url", help="API", default=None)

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
