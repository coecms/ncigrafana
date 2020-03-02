#!/usr/bin/env python

from __future__ import print_function

import datetime
from numpy.testing import assert_array_equal, assert_array_almost_equal
from numpy import arange
import os
import pandas as pd
import pytest
import sys
import time

from ncigrafana.UsageDataset import *
from ncigrafana.DBcommon import datetoyearquarter
from ncigrafana.parse_account_usage_data import parse_account_dump_file

# Set acceptable time zone strings so we can parse the 
# AEST timezone in the test file
os.environ['TZ'] = 'AEST-10AEDT-11,M10.5.0,M3.5.0'
time.tzset()
dbfileprefix = '.'

@pytest.fixture(scope='session')
def db():
    project = 'xx00'
    dbfile = "sqlite:///:memory:"
    # dbfile = "sqlite:///usage.db"
    return ProjectDataset(project,dbfile)

def test_parse_lquota(db):

    parse_account_dump_file('test/nci_account.log', verbose=True, db=db)

# def test_getstoragepoints(db):
# 
#     system = 'gadi'
#     storagepts = sorted(db.getstoragepoints(system))
#     assert storagepts == ['gdata', 'scratch']

def test_getquarter(db):

    year, quarter = db.getquarter()

    assert(year == 2019)
    assert(quarter == 'q2')

def test_getsystems(db):

    systems = db.getsystems()
    assert(systems == ['gadi'])

def test_getschemes(db):

    schemes = db.getschemes()
    assert(schemes == ['MAS-FlagshipCLEX'])

def test_getprojects(db):

    projects = db.getprojects()
    assert(projects == ['v45'])

def test_getusagegrant(db):

    project = db.getprojects()[0]
    system = db.getsystems()[0]
    scheme = db.getschemes()[0]
    year, quarter = db.getquarter()
    assert( db.getusagegrant(project, system, scheme, year, quarter) == 4480000.0 )

def test_getschemeusage(db):

    project = db.getprojects()[0]
    system = db.getsystems()[0]
    scheme = db.getschemes()[0]
    year, quarter = db.getquarter()
    assert( db.getschemeusage(project, system, scheme, year, quarter) == 
            ([datetime.date(2019, 6, 27), datetime.date(2019, 6, 28)], [3404.119149, 3404.119149]) )

def test_getusers(db):

    assert ( len(list(db.getusers())) == 17 )
    
def test_getuserusage(db):

    project = db.getprojects()[0]
    system = db.getsystems()[0]
    scheme = db.getschemes()[0]
    year, quarter = db.getquarter()
    for user in db.getusers():
        for usage in db.getuserusage(project, year, quarter, user)[1]:
            assert(usage > 0)

""" 
Cannot currently test for this as no breakdown by queue is available

def test_getprojectusage(db):

    project = db.getprojects()[0]
    system = db.getsystems()[0]
    scheme = db.getschemes()[0]
    year, quarter = db.getquarter()
    assert( db.getprojectusage(project, system, scheme, year, quarter) == 4480000.0 )
 """