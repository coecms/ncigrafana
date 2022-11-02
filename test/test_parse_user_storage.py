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

    parse_file_report('test/2022-11-02T11:36:45.w40.scratch.json', verbose=verbose, db=db)
    parse_file_report('test/2022-11-02T11:36:45.w40.gdata.json', verbose=verbose, db=db)

def test_getstoragepoints(db):

    system = 'gadi'
    storagepts = sorted(db.getstoragepoints(system))
    assert storagepts == ['scratch']

    system = 'global'
    storagepts = sorted(db.getstoragepoints(system))
    assert storagepts == ['gdata']

def test_getstorage(db):

    project = 'w40'
    year = 2022
    quarter = 'q4'
    system = 'gadi'
    storagepoint = 'scratch'
    dp = db.getstorage(project, year, quarter, system, storagepoint, namefield='user')
    assert(len(dp) == 33)
    #assert((dp.iloc[0,:].values == [837124096., 654982688768., 5983174656.,
    #                                81819126988.8000030517578125, 1897922560., 
    #                                40531821149388.796875]).all())
    assert((dp.iloc[0,:].values == [         8192,   15037362176,          4096,          8192,
                                          6455296,          8192,   12555550720,         61440,
                                             8192,          8192,          8192,          8192,
                                             8192,          4096,          8192,   66303352832,
                                             8192,        425984,  401322278912,          8192,
                                           454656,   12024569856,          8192,          8192,
                                            98304,          8192,    6972870656, 1216239837184,
                                             8192,          8192,          8192,      13619200,
                                      11571253248,          8192,         24576,          8192,
                                             8192,         12288,          8192,          8192,
                                             8192,          8192,         12288,        983040,
                                             8192, 9566094172160, 6467893768192,         12288,
                                     509981904896,          8192,          8192,          8192,
                                            28672,         12288,          8192,          8192,
                                             8192,          8192,          8192,          8192,
                                            20480,         12288,       3584000,          8192,
                                             8192,          8192,          8192,          8192,
                                             8192,          8192,          8192,     159137792,
                                            16384,          8192,  121728925696,     215461888,
                                             8192,         16384, 2867015331840,          4096,
                                             8192,          8192,         40960,          8192,
                                     698904379392,  165306880000,          8192,          8192,
                                            28672,          8192,          8192,    2284138496,
                                            32768,         12288,          8192,          8192,
                                          2060288,          8192, 1274325000192,          8192,
                                             8192,          8192,        135168,          8192,
                                             8192,         65536,  288980849664,          8192,
                                             8192,          8192,         24576,          8192,
                                             8192,   29022916608,          8192,   64513818624,
                                           454656,          8192,          8192,          8192,
                                             8192,      10104832,    1819267072]).all())

    system = 'global'
    storagepoint = 'gdata'
    dp = db.getstorage(project, year, quarter, system, storagepoint, namefield='user')
    assert(len(dp) == 32)
    #assert((dp.iloc[0,:].values == [4209602560., 1891963632025.60009765625, 2846720.,
    #                                101591390617.5999908447265625, 1329627922432.,
    #                                7364434976768.]).all())
    assert((dp.iloc[0,:].values == [  378253836288,         139264,       19640320,     1785151488,
                                           8122368,          77824,      227143680,           4096,
                                              4096,  6244943798272, 34355089817600,           4096,
                                      338371608576,        2428928,     9422868480, 24785586880512,
                                              4096,           4096,  5369627049984,    12756226048,
                                      620734619648,  1225300582400,      195948544, 31176721473536,
                                     8375311802368,      919977984,       45187072,   561438191616,
                                        2595426304,      197181440,   832443146240,  1370082246656,
                                        5154693120, 40789091491840,   234704838656,          73728,
                                        5154811904,   146066354176,  9107041492992,  1369709383680,
                                            192512,     2779975680,  3248198533120,  1551341441024,
                                           1953792,    22146326528,    15386636288,           4096,
                                      704050032640,  4243776442368,    93698002944,  8605416587264,
                                      814183866368,          28672,    52714979328,    84480143360,
                                       15162470400,   185345052672,    65202511872,   342954827776,
                                              4096,      268537856]).all())

    # import pytest
    # pytest.set_trace()
    # print(dp)
