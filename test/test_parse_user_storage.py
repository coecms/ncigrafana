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
from ncigrafana.parse_user_storage_data import parse_file_report

# Set acceptable time zone strings so we can parse the 
# AEST timezone in the test file
os.environ['TZ'] = 'AEST-10AEDT-11,M10.5.0,M3.5.0'
time.tzset()
dbfileprefix = '.'
verbose = False

@pytest.fixture(scope='session')
def db():
    project = 'xx00'
    dbfile = "sqlite:///:memory:"
    # dbfile = "sqlite:///usage.db"
    return ProjectDataset(project,dbfile)

def test_parse_lquota(db):

    parse_file_report('test/2020-04-16T08:34:58.w35.scratch.dump', verbose=verbose, db=db)
    parse_file_report('test/2020-04-16T08:34:58.w35.gdata.dump', verbose=verbose, db=db)

def test_getstoragepoints(db):

    system = 'gadi'
    storagepts = sorted(db.getstoragepoints(system))
    assert storagepts == ['scratch']

    system = 'global'
    storagepts = sorted(db.getstoragepoints(system))
    assert storagepts == ['gdata']

def test_getstorage(db):

    project = 'w35'
    year = 2020
    quarter = 'q2'
    system = 'gadi'
    storagepoint = 'scratch'
    dp = db.getstorage(project, year, quarter, system, storagepoint, namefield='user')
    assert(len(dp) == 17)
    assert((dp.iloc[0,:].values == [837124096., 654982688768., 5983174656.,
                                    81819126988.8000030517578125, 1897922560., 
                                    40531821149388.796875]).all())

    system = 'global'
    storagepoint = 'gdata'
    dp = db.getstorage(project, year, quarter, system, storagepoint, namefield='user')
    assert(len(dp) == 17)
    assert((dp.iloc[0,:].values == [4209602560., 1891963632025.60009765625, 2846720.,
                                    101591390617.5999908447265625, 1329627922432.,
                                    7364434976768.]).all())

    # import pytest
    # pytest.set_trace()
    # print(dp)
