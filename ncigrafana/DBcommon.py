#!/usr/bin/env python

"""
Copyright 2015 ARC Centre of Excellence for Climate Systems Science

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

import datetime
import gzip
import os
import re
import shutil
import sys

unit_base = { 'B' : 1024, 'SU' : 1000 }

def extract_num_unit(s):
    # Match a number (possibly floating point 100.00 style) and a unit
    try:
        size, unit = re.findall(r'(\d+.\d+|\d+)\s*(\D*)$',s)[0]
    except:
        print('Failed to match size string: ',s)
        sys.exit()
    return float(size), unit

def pretty_size(n,pow=0,b=1024,u='B',pre=['']+[p for p in'KMGTPEZY']):
    pow,n=min(int(log(max(n*b**pow,1),b)),len(pre)-1),n*b**pow
    return "%%.%if %%s%%s"%abs(pow%(-pow-1))%(n/b**float(pow),pre[pow],u)
        
def parse_size(size,b=1024,u='B',pre=['']+[p for p in'KMGTPEZY']):
    """Parse human readable file sizes, e.g. 16.4TB, 1000KSU"""
    intsize, unit = extract_num_unit(size)

    # Account for 10B vs 10KB when looking for base
    if len(unit) == len(u):
        base = unit
    else:
        base = unit[1:]

    # Check if we know this unit's base, otherwise use default
    if base in unit_base:
        b = unit_base[base]
    pow = { k+base:v for v, k in enumerate(pre) }

    return float(intsize)*(b**pow[unit])

def parse_inodenum(num):
    return parse_size(num,b=1000,u='')  

def mkdir(path):
    """Make a directory, without a race condition
    from http://stackoverflow.com/a/14364249
    """
    try: 
        os.mkdir(path)
    except OSError:
        if not os.path.isdir(path):
            raise

def archive(filepath,archive_dir='archive'):
    """Move dumpfile into archive directory, and compress it"""

    # Make sure we have a directory to archive to
    try:
        mkdir(archive_dir)
    except:
        print("Error making archive directory")
        return

    try:
        (dir, filename) = os.path.split(filepath)
        outfile = os.path.join(dir,archive_dir,filename)+'.gz'
        with open(filepath, 'rb') as f_in, gzip.open(outfile, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        print("Error archiving ",filepath)
        print(e)
    else:
        try:
            os.remove(filepath)
        except:
            print("Error removing ",filepath)

def datetoyearquarter(date):
    """Return NCI style year, quarter from date"""

    year = date.year

    # Convert month into year and quarter
    quarter = 'q{}'.format(int(((date.month) - 1) / 3) + 1)
    return year, quarter

def date_range_from_quarter(year, quarter):
    """
    Convenience routine to return a valid date range for a quarter
    when information not provided in a dump file as is case with 
    gadi. Allows backwards compatibility. Hard coded date ranges.
    """
    lookup = {
              'q1' : { 'smonth': 1, 'emonth': 3, 'sday': 1, 'eday': 31 },
              'q2' : { 'smonth': 4, 'emonth': 6, 'sday': 1, 'eday': 30 },
              'q3' : { 'smonth': 7, 'emonth': 9, 'sday': 1, 'eday': 30 },
              'q4' : { 'smonth': 10, 'emonth': 12, 'sday': 1, 'eday': 31 }
              }

    return((
            datetime.date(year,lookup[quarter]['smonth'],lookup[quarter]['sday']), 
            datetime.date(year,lookup[quarter]['emonth'],lookup[quarter]['eday'])
            ))