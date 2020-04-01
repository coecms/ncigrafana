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
import math
from pwd import getpwnam

from dataset import connect
import pandas as pd

class NotInDatabase(Exception):
    pass

class ProjectDataset(object):

    def __init__(self, project=None, dburl=None):
        if project is not None:
            self.project = project
            if dburl is None:
                dburl = "usage_{}.db".format(project)
        self.dburl = dburl
        self.db = connect(dburl)

    def adduser(self, user, fullname=None):
        """
        Add a unique user if it doesn't already exist. 
        Return a unique id
        """
        q = self.db['Users'].find_one(user=user)
        if q is None:
            uid = -1; gid = -1
            if fullname is None:
                try:
                    passwd = getpwnam(user)
                    fullname = passwd.pw_gecos
                    uid = passwd.pw_uid
                    gid = passwd.pw_gid
                except KeyError:
                    fullname = user
                    uid = -1
                    gid = -1
            data = dict(user=user, uid=uid, gid=gid, fullname=fullname)
            id = self.db['Users'].upsert(data, list(data.keys()))
        else:
            id = q['id']
        return id

    def addproject(self, project, description=None):
        """
        Add a unique project code if it doesn't already exist. 
        Return a unique id
        """
        q = self.db['Projects'].find_one(project=project)
        if q is None:
            if description is None:
                description = ''
            data = dict(project=project, description=description)
            id = self.db['Projects'].insert(data, ['project'])
        else:
            id = q['id']
        return id

    def addquarter(self, year, quarter, startdate=None, enddate=None):
        """
        Add a unique quarter
        Return a unique id
        """
        # Ensure year is a string, to match SQL table type
        if not isinstance(year, str):
            year = str(year)
        q = self.db['Quarters'].find_one(year=year,quarter=quarter)
        if q is None:
            if startdate is None or enddate is None:
                raise ValueError('Cannot define a new quarter without start and end dates')
            data = dict(year=year, quarter=quarter, start_date=startdate, end_date=enddate)
            id = self.db['Quarters'].insert(data, ['year', 'quarter'])
        else:
            id = q['id']
        return id

    def addsystem(self, system):
        """
        Add a unique system if one doesn't already exist
        Return a unique id
        """
        q = self.db['Systems'].find_one(system=system)
        if q is None:
            data = dict(system=system)
            id = self.db['Systems'].insert(data, ['system'])
        else:
            id = q['id']
        return id

    def addstoragepoint(self, system, storagepoint):
        """
        Add a unique system if one doesn't already exist
        Return a unique id
        """
        system_id = self.addsystem(system)
        q = self.db['StoragePoints'].find_one(system_id=system_id, storagepoint=storagepoint)
        if q is None:
            data = dict(system_id=system_id, storagepoint=storagepoint)
            id = self.db['StoragePoints'].insert(data, ['system_id', 'storagepoint'])
        else:
            id = q['id']
        return id

    def addscheme(self, scheme):
        """
        Add a unique schemeif one doesn't already exist
        Return a unique id
        """
        q = self.db['Schemes'].find_one(scheme=scheme)
        if q is None:
            data = dict(scheme=scheme)
            id = self.db['Schemes'].insert(data, ['scheme'])
        else:
            id = q['id']
        return id

    def addsystemqueue(self, system, queue, weight=None):
        """
        Add a unique system queue if one doesn't already exist
        Return a unique id
        """
        system_id = self.addsystem(system)
        q = self.db['SystemQueues'].find_one(system_id=system_id, queue=queue)
        if q is None:
            if weight is None:
                raise ValueError('Cannot define a new system queue without a value for weight')
            data = dict(system_id=system_id, queue=queue, chargeweight=float(weight))
            id = self.db['SystemQueues'].insert(data, ['system_id', 'queue'])
        else:
            id = q['id']
        return id

    def addusagegrant(self, project, system, scheme, year, quarter, date, allocation):
        """
        Grant is from a scheme for each project. It is per system and quarter,
        but allow (and track) changes to the grant by allowing more than one
        entry per quarter
        """
        project_id = self.addproject(project)
        system_id = self.addsystem(system)
        scheme_id = self.addscheme(scheme)
        quarter_id = self.addquarter(year, quarter)
        data = dict(project_id=project_id, 
                    system_id=system_id, 
                    scheme_id=scheme_id, 
                    quarter_id=quarter_id)
        q = list(self.db['UsageGrants'].find(**data))
        # Only update if there is a change to grant or no grant already defined
        if not q or q[-1]['allocation'] != allocation:
            data = dict(project_id=project_id, 
                        system_id=system_id, 
                        scheme_id=scheme_id, 
                        quarter_id=quarter_id, 
                        date=date, 
                        allocation=allocation)
            id = self.db['UsageGrants'].upsert(data, ['project_id', 'system_id', 'scheme_id', 'quarter_id', 'date'])
        else:
            id = q[-1]['id']
        return id

    def addstoragegrant(self, project, system, storagepoint, scheme, year, quarter, date, storagetype, grant):
        """
        Grant is from a scheme for each project. It is per system and quarter,
        but allow (and track) changes to the grant by allowing more than one
        entry per quarter
        """
        project_id = self.addproject(project)
        system_id = self.addsystem(system)
        storagepoint_id = self.addstoragepoint(system, storagepoint)
        scheme_id = self.addscheme(scheme)
        quarter_id = self.addquarter(year, quarter)
        data = dict(project_id=project_id, 
                    system_id=system_id, 
                    storagepoint_id=storagepoint_id, 
                    scheme_id=scheme_id, 
                    quarter_id=quarter_id)
        q = list(self.db['StorageGrants'].find(**data))
        # Only update if there is a change to grant or no grant already defined
        if ( not q 
            or storagetype not in q[-1]
            or q[-1][storagetype] is None
            or not math.isclose(q[-1][storagetype], grant, abs_tol=1024) ):
            data = dict(project_id=project_id, 
                        system_id=system_id, 
                        storagepoint_id=storagepoint_id, 
                        scheme_id=scheme_id, 
                        quarter_id=quarter_id, 
                        date=date)
            # Have to use key value pair as storagetype is a variable
            data.update({ storagetype: grant })
            # Need an upsert here as the same row will get update for capacity
            # and inodes separately. Consequently don't include storagetype in
            # the index
            id = self.db['StorageGrants'].upsert(data, ['project_id', 'system_id', 'storagepoint_id', 
                                                        'scheme_id', 'quarter_id', 'date'])
        else:
            id = q[-1]['id']
        return id

    def addschemeusage(self, project, system, scheme, date, cputime, walltime, su):
        """
        Add a project usage entry by system and queue
        """
        project_id = self.addproject(project)
        system_id = self.addsystem(system)
        scheme_id = self.addscheme(scheme)
        data = dict(project_id=project_id,
                    system_id=system_id,
                    scheme_id=scheme_id,
                    date=date,
                    usage_cpu=float(cputime),
                    usage_wall=float(walltime),
                    usage_su=float(su))
        return self.db['SchemeUsage'].upsert(data, ['project_id', 'systemqueue_id', 'scheme_id', 'date'])

    def addprojectusage(self, project, system, queue, date, cputime, walltime, su):
        """
        Add a project usage entry by system and queue
        """
        project_id = self.addproject(project)
        systemqueue_id = self.addsystemqueue(system, queue)
        data = dict(project_id=project_id,
                    systemqueue_id=systemqueue_id,
                    date=date,
                    usage_cpu=float(cputime),
                    usage_wall=float(walltime),
                    usage_su=float(su))
        return self.db['ProjectUsage'].upsert(data, ['project_id', 'systemqueue_id', 'date'])

    def addprojectstorage(self, project, system, storagepoint, date, size, inodes):
        """
        Add a project storage entry by system and storage point
        """
        project_id = self.addproject(project)
        system_id = self.addsystem(system)
        storagepoint_id = self.addstoragepoint(system, storagepoint)
        data = dict(project_id=project_id,
                    system_id=system_id,
                    storagepoint_id=storagepoint_id,
                    date=date,
                    size=float(size),
                    inodes=float(inodes))
        return self.db['ProjectStorage'].upsert(data, ['project_id', 'system_id', 'storagepoint_id', 'date'])

    def adduserusage(self, project, user, date, usecpu, usewall, usesu, efficiency):
        """
        Add user su usage record by project
        """
        project_id = self.addproject(project)
        user_id = self.adduser(user)
        data = dict(project_id=project_id, 
                    user_id=user_id, 
                    date=date, 
                    usage_cpu=float(usecpu), 
                    usage_wall=float(usewall), 
                    usage_su=float(usesu),
                    efficiency=float(efficiency))
        return self.db['UserUsage'].upsert(data, ['project_id', 'user_id', 'date'])

    def adduserstorage(self, project, user, system, storagepoint, scandate, folder, size, inodes):
        """
        Add user storage usage record by project and storage point
        """
        project_id = self.addproject(project)
        user_id = self.adduser(user)
        storagepoint_id = self.addstoragepoint(system, storagepoint)
        data = dict(project_id=project_id, 
                    user_id=user_id, 
                    storagepoint_id=storagepoint_id,
                    folder=folder, 
                    scandate=scandate, 
                    inodes=float(inodes), 
                    size=float(size))
        return self.db['UserStorage'].upsert(data, ['project_id', 'user_id', 'storagepoint_id', 'folder', 'scandate'])

    def getstartend(self, year, quarter, asdate=False):
        q = self.db['Quarters'].find_one(year=year, quarter=quarter)
        if q is None:
            raise NotInDatabase('No entries in database for {}.{}'.format(year,quarter))
        if asdate:
            return self.date2date(q['start_date']),self.date2date(q['end_date'])
        else:
            return q['start_date'],q['end_date']

    def getusagegrant(self, project, system, scheme, year, quarter):
        project_id = self.addproject(project)
        system_id = self.addsystem(system)
        scheme_id = self.addscheme(scheme)
        quarter_id = self.addquarter(year, quarter)
        data = dict(project_id=project_id, 
                    system_id=system_id, 
                    scheme_id=scheme_id, 
                    quarter_id=quarter_id)
        q = list(self.db['UsageGrants'].find(**data))[-1]
        if q is None:
            return None
        return float(q['allocation'])

    def getprojectusage(self, project, system, queue, year, quarter):
        project_id = self.addproject(project)
        systemqueue_id = self.addsystemqueue(system, queue)
        startdate, enddate = self.getstartend(year, quarter)
        qstring = """SELECT date, SUM(usage_su) AS totsu FROM ProjectUsage 
                     WHERE project_id={project}
                     AND systemqueue_id={system}
                     AND date between '{start}' AND '{end}' 
                     GROUP BY date ORDER BY date
                     """.format(project=project_id, system=systemqueue_id, start=startdate, end=enddate)
        q = self.db.query(qstring)
        if q is None:
            return None
        dates = []; usage = []
        for record in q:
            dates.append(self.date2date(record["date"]))
            usage.append(record["totsu"]/1000.)
        return dates, usage

    def getschemeusage(self, project, system, scheme, year, quarter):
        project_id = self.addproject(project)
        system_id = self.addsystem(system)
        scheme_id = self.addscheme(scheme)
        startdate, enddate = self.getstartend(year, quarter)
        qstring = """SELECT date, SUM(usage_su) AS totsu FROM SchemeUsage 
                     WHERE project_id={project}
                     AND system_id={system}
                     AND scheme_id={scheme}
                     AND date between '{start}' AND '{end}' 
                     GROUP BY date ORDER BY date
                     """.format(project=project_id, system=system_id, scheme=scheme_id, start=startdate, end=enddate)
        q = self.db.query(qstring)
        if q is None:
            return None
        dates = []; usage = []
        for record in q:
            dates.append(self.date2date(record["date"]))
            usage.append(record["totsu"]/1000.)
        return dates, usage

    def getuserusage(self, project, year, quarter, user, scale=None):
        project_id = self.addproject(project)
        startdate, enddate = self.getstartend(year, quarter)
        user_id = self.adduser(user)
        if user is None:
            raise Exception('User {} does not exist in project {}'.format(user, project))
        qstring = """SELECT date, SUM(usage_su) AS totsu FROM UserUsage 
                     WHERE project_id={project} AND 
                     date between '{start}' AND '{end}' AND 
                     user_id={user} GROUP BY date ORDER BY date
                     """.format(project=project_id, start=startdate, end=enddate, user=user_id)
        q = self.db.query(qstring)
        if q is None:
            return None
        dates = []; usage = []
        if scale is None: scale = 1.
        for record in q:
            dates.append(self.date2date(record["date"]))
            usage.append(record["totsu"]*scale)
        return dates, usage

    def getusershort(self, year, quarter, user):
        project_id = self.addproject(project)
        startdate, enddate = self.getstartend(year, quarter)
        user_id = self.adduser(use)
        qstring = """SELECT scandate, SUM(size) AS totsize FROM ShortUsage 
                     WHERE project={project} AND 
                     scandate between '{start}' AND '{end}' AND 
                     user={user} GROUP BY scandate ORDER BY scandate
                     """.format(project=project_id, start=startdate, end=enddate, user=user_id)
        q = self.db.query(qstring)
        if q is None:
            return None
        dates = []; usage = []
        for record in q:
            dates.append(self.date2date(record["scandate"]))
            usage.append(record["totsize"])
        return dates, usage

    def getusage(self, year, quarter, datafield='usage_su', namefield='user+name'):

        startdate, enddate = self.getstartend(year, quarter)

        if namefield == 'user+name':
            name_sql = 'printf("%s (%s)", Users.fullname, Users.user)'
        elif namefield == 'user':
            name_sql = 'Users.user'
        else:
            raise ValueError('Incorrect value of namefield: {} Valid values are "user+name" or "user"'.format(namefield))

        if datafield not in ('usage_su','usage_wall','usage_cpu'):
            raise ValueError('Incorrect value of datafield: {} Valid values are "usage_su", "usage_wall" or "usage_cpu"'.format(namefield))

        qstring = """SELECT {namefield} as Name, date as Date, SUM({datafield}) AS totsu
        FROM UserUsage
        LEFT JOIN Users ON UserUsage.user_id = Users.id 
        WHERE date between \'{start}\' AND \'{end}\' 
        GROUP BY Name, Date 
        ORDER BY Date"""

        # Pivot makes columns of all the individuals, rows are indexed by date
        try:
            df = pd.read_sql_query(qstring.format(namefield=name_sql,
                                                  datafield=datafield,
                                                  start=startdate,
                                                  end=enddate),
                                                  self.db.executable).pivot_table(index='Date',
                                                                                  columns='Name',
                                                                                  fill_value=0)
        except:
            print("No usage data available")
            return None

        # Get rid of the totsize labels in the multiindex
        df.columns = df.columns.get_level_values(1)
        # Convert date index from labels to datetime objects 
        df.index = pd.to_datetime(df.index, format="%Y-%m-%d")

        return df


    def getstorage(self, project, year, quarter, storagept='short', datafield='size', namefield='user+name'):

        startdate, enddate = self.getstartend(year, quarter)

        table = 'UserStorage'

        if namefield == 'user+name':
            name_sql = 'printf("%s (%s)", Users.fullname, Users.user)'
        elif namefield == 'user':
            name_sql = 'Users.user'
        else:
            raise ValueError('Incorrect value of namefield: {} Valid values are "user+name" or "user"'.format(namefield))

        if datafield not in ('size','inodes'):
            raise ValueError('Incorrect value of datafield: {} Valid values are "inodes" or "size"'.format(namefield))

        qstring = """SELECT {namefield} as Name, scandate as Date, SUM({datafield}) AS totsize 
        FROM {table}
        LEFT JOIN Users ON {table}.user_id = Users.id
        WHERE scandate between \'{start}\' AND \'{end}\'
        GROUP BY Name, Date
        ORDER BY Date"""

        # Pivot makes columns of all the individuals, rows are indexed by date
        try:
            df = pd.read_sql_query(qstring.format(namefield=name_sql,datafield=datafield,table=table,start=startdate,end=enddate), self.db.executable).pivot_table(index='Date',columns='Name',fill_value=0)
        except:
            print("No data available for {}".format(storagept))
            return None
            
        # Get rid of the totsize labels in the multiindex
        df.columns = df.columns.get_level_values(1)
        # Convert date index from labels to datetime objects 
        df.index = pd.to_datetime(df.index, format="%Y-%m-%d")

        # Make a new index from the beginning of the quarter
        newidx = pd.date_range(startdate,df.index[-1])

        # Reindex to beginning of quarter in case we're missing values from the beginning of the quarter
        df = df.reindex(newidx, method='backfill')

        return df

    def getshortusers(self, year, quarter):
        startdate, enddate = self.getstartend(year, quarter)
        qstring = "SELECT user FROM ShortUsage WHERE scandate between '{}' AND '{}' GROUP BY user ORDER BY SUM(size) desc".format(startdate,enddate)
        q = self.db.query(qstring)
        if q is None:
            return None
        users = []
        for record in q:
            users.append(self.db['Users'].find_one(id=record["user"])["user"])
        return users

    def getsuusers(self, year, quarter):
        startdate, enddate = self.getstartend(year, quarter)
        qstring = "SELECT user_id, MAX(usage_su) as maxsu FROM UserUsage WHERE date between '{}' AND '{}' GROUP BY user_id ORDER BY maxsu desc".format(startdate,enddate)
        q = self.db.query(qstring)
        if q is None:
            return None
        users = []
        for record in q:
            users.append(self.db['Users'].find_one(id=record["user_id"])["user"])
        return users

    def getuser(self, user=None):
        return self.db['Users'].find_one(user=user)

    def getusers(self):
        qstring = "SELECT user FROM Users"
        q = self.db.query(qstring)
        for user in q:
            yield user['user']

    def getqueue(self, system, queue):
        system_id = self.addsystem(system)
        return self.db['SystemQueues'].find_one(system_id=system_id, queue=queue)

    def getquarter(self):
        """
        Return (year, quarter) for the most recent entry in the DB table Quarters
        Make sure to cast year to integer as it is stored as a string in the postgres DB
        """
        q = self.db['Quarters'].find_one(order_by=['-year','-quarter'])
        return int(q['year']), q['quarter'] 

    def getsystems(self):
        """
        Return list of systems
        """
        return [d['system'] for d in self.db['Systems'].find()]

    def getschemes(self):
        """
        Return list of schemes
        """
        return [d['scheme'] for d in self.db['Schemes'].find()]

    def getprojects(self):
        """
        Return list of projects
        """
        return [d['project'] for d in self.db['Projects'].find()]

    def date2date(self, datestring):

        if type(datestring) == datetime.date:
            return datestring
        else:
            return datetime.datetime.strptime(datestring, "%Y-%m-%d").date()

    def getstoragepoints(self, system):
        system_id = self.addsystem(system)
        qstring = "SELECT DISTINCT storagepoint FROM StoragePoints WHERE system_id is '{}'".format(system_id)
        q = self.db.query(qstring)
        if q is None:
            return None
        storagepoints = []
        for record in q:
            storagepoints.append(record["storagepoint"])
        return storagepoints

    def getgdatastoragept(self, year, quarter):
        q = self.db['SystemStorage'].find_one(system='global', year=year, quarter=quarter)
        if q is None:
            return None
        return q["storagepoint"]

    def getstoragegrant(self, project, systemname, storagepoint, scheme, year, quarter):

        project_id = self.addproject(project)
        system_id = self.addsystem(systemname)
        storagepoint_id = self.addstoragepoint(systemname, storagepoint)
        scheme_id = self.addscheme(scheme)
        quarter_id = self.addquarter(year, quarter)
        data = dict(project_id=project_id, 
                    system_id=system_id, 
                    storagepoint_id=storagepoint_id, 
                    scheme_id=scheme_id, 
                    quarter_id=quarter_id)
        q = self.db['StorageGrants'].find_one(**data)
        if q is None:
            return (None,None)
        return float(q['capacity']),float(q['inodes'])

    def getsystemstorage(self, systemname, storagepoint, year, quarter):
        if storagepoint == 'gdata':
            # look up which gdata system this project is using. This is dumb, but it works
            point = self.getgdatastoragept(year, quarter)
        else:
            point = storagepoint
        q = self.db['SystemStorage'].find_one(system=systemname, storagepoint=point, year=year, quarter=quarter)
        if q is None:
            return (None,None)
        return float(q['grant']),float(q['igrant'])

    def getprojectstorage(self, project, system, storagepoint):
        """
        Add a project storage entry by system and storage point
        """
        project_id = self.addproject(project)
        system_id = self.addsystem(system)
        storagepoint_id = self.addstoragepoint(system, storagepoint)
        data = dict(project_id=project_id,
                    system_id=system_id,
                    storagepoint_id=storagepoint_id)
        q = self.db['ProjectStorage'].find_one(**data)
        if q is None:
            return (None,None)
        return float(q['size']),float(q['inodes'])

    def top_usage(self, year, quarter, storagepoint, measure='size', count=10, scale=1):
        """
        Return the top ``count`` users according to ``measure`` (either 'size'
        or 'inodes') on ``storagepoint`` for ``year`` and ``quarter``

        Returns pandas dataframe (fullname (user), usage)
        """

        if storagepoint not in ['short', 'gdata']:
            raise Exception(f"Unexpected storagepoint '{storagepoint}'")

        if measure not in ['size', 'inodes']:
            raise Exception(f"Unexpected measure '{measure}'")

        # Get the storage for this quarter, grab the last record, which corresponds
        # to the most recent scan date, sort, take the largest count records and
        # divide by scale
        return self.getstorage(year, 
                               quarter, 
                               storagept=storagepoint, 
                               datafield=measure).ix[-1].sort_values(ascending=False).head(count).divide(scale)
