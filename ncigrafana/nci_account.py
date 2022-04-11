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

Adapted from nci_account 
"""

import argparse
import json
import os
import pymunge
import requests
import sys
import urllib

SERVER='http://gadi-pbs-01.gadi.nci.org.au:8811/v0/nciaccount/'

def get_resource(project):
    """
    Wrap important bit in a function that can be accessed directly
    """

    url = SERVER + 'project/%s' % project
    token = pymunge.encode().decode('utf-8')

    request = urllib.request.Request(url)
    request.add_header("Authorization", "MUNGE %s" % (token))
    request.add_header("Content-Type", "application/json")

    try:
        rc = urllib.request.urlopen(request)
    except urllib.error.HTTPError as e:
        print("Could not fetch accounting report. Please try again later.\n")
        sys.exit(1)
    finally:
        res = rc.read().decode()
        rc.close()

    return res

def main(args):

    # Get project
    if args.project:
        project = args.project
    else:
        if 'PROJECT' in os.environ:
            project = os.environ['PROJECT']
        else:
            print("Please specify --project PROJECT with the project you'd like to view")
            sys.exit(1)

    print(get_resource(project))


def parse_args(args):
    """
    Parse arguments given as list (args)
    """
    parser = argparse.ArgumentParser('Return nci account data as json')
    parser.add_argument("-P", "--project", help="project to view")

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

