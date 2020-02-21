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
from ncigrafana.parse_lquota import parse_lquota 

# Set acceptable time zone strings so we can parse the 
# AEST timezone in the test file
os.environ['TZ'] = 'AEST-10AEDT-11,M10.5.0,M3.5.0'
time.tzset()
dbfileprefix = '.'

@pytest.fixture(scope='session')
def db():
    project = 'xx00'
    # dbfile = "sqlite:///:memory:"
    dbfile = "sqlite:///usage.db"
    return ProjectDataset(project,dbfile)

def test_parse_lquota(db):

    parse_lquota('test/lquota.log', verbose=True, db=db)

def test_getstoragepoints(db):

    system = 'gadi'
    storagepts = sorted(db.getstoragepoints(system))
    assert storagepts == ['gdata', 'scratch']

def test_getstorage(db):

    system = 'gadi'
    project = 'vv5'
    dp = db.getprojectstorage(project, system, 'scratch')
    assert dp == (21506447439298.56, 9107665.0)
    dp = db.getprojectstorage(project, system, 'gdata')
    assert dp == (173766817653719.03, 7156412.0)

    project = 'wv0'
    dp = db.getprojectstorage(project, system, 'scratch')
    assert dp == (7905488603709.44, 703700.0)
    dp = db.getprojectstorage(project, system, 'gdata')
    assert dp == (83793781152808.95, 1805324.0)

