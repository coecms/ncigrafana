#!/usr/bin/env python

from __future__ import print_function

import pytest
import sys

from numpy.testing import assert_array_equal, assert_array_almost_equal
from numpy import arange

import os

from ncigrafana.DBcommon import *

import datetime

def test_parse_numbers_with_units():

    assert(extract_num_unit('100KB')==(100,'KB'))
    assert(parse_size('100KB')==102400)
    assert(parse_size('100 KB')==102400)
    assert(parse_size(' 100KB')==102400)
    assert(parse_size(' 100 KB')==102400)

    assert(parse_size('1MB')==1048576)
    assert(parse_size('1GB')==1073741824)
    assert(parse_size('1TB')==1099511627776)
    assert(parse_size('1PB')==1125899906842624)
    assert(parse_size('1EB')==1152921504606846976)

    assert(extract_num_unit('100KSU')==(100,'KSU'))
    assert(extract_num_unit('   100          KSU')==(100,'KSU'))
    assert(parse_size('100KSU')==100000)
    assert(parse_size('1000KSU')==1000000)
    assert(parse_size('1MSU')==1000000)
    assert(parse_size('1GSU')==1000000000)

    assert(parse_inodenum('10K')==10000)

    assert(parse_size('10B')==10)
    assert(parse_size('10SU',u='SU')==10)
    assert(parse_size('10.0 SU',u='SU')==10)


def test_date_range_from_quarter():

    assert(date_range_from_quarter(2020,'q1') ==
           (datetime.date(2020,1,1), datetime.date(2020,3,31)))

    assert(date_range_from_quarter(2166,'q2') ==
           (datetime.date(2166,4,1), datetime.date(2166,6,30)))

    assert(date_range_from_quarter(1066,'q3') ==
           (datetime.date(1066,7,1), datetime.date(1066,9,30)))

    assert(date_range_from_quarter(7,'q4') ==
           (datetime.date(7,10,1), datetime.date(7,12,31)))
