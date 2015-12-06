# coding: utf-8
import datetime
import json
import uuid
import logging
import httplib2
from apiclient.discovery import build

from oauth2client.appengine import AppAssertionCredentials


class BqQueryError(Exception):
    pass


class BqQuery(object):
    u'''BigQuery クエリクラス'''

    scope = 'https://www.googleapis.com/auth/bigquery'
    _bigquery = None

    def __init__(self, project_id, dataset_id, table_id):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id

    @classmethod
    def bigquery(cls):
        if cls._bigquery is None:
            credentials = AppAssertionCredentials(scope=cls.scope)
            http = credentials.authorize(httplib2.Http())
            cls._bigquery = build('bigquery', 'v2', http=http)
        return cls._bigquery

    @classmethod
    def tabledata(cls):
        return cls.bigquery().tabledata()

    @classmethod
    def jobs(cls):
        return cls.bigquery().jobs()

    def insert_id(self):
        return '{}{}'.format(
            datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            uuid.uuid4().hex
        )

    def iter_insert_data(self, data_list):
        for data in data_list:
            yield {
                'insertId': self.insert_id(),
                'json': data
            }

    def build_insert_data(self, data_list):
        return [{
            'insertId': self.insert_id(),
            'json': data
        } for data in data_list]

    def insert(self, data_list):
        tabledata = self.tabledata()
        for insert_data in self.iter_insert_data(data_list):
            try:
                tabledata.insertAll(
                    projectId=self.project_id,
                    datasetId=self.dataset_id,
                    tableId=self.table_id,
                    body={
                        'kind': 'bigquery#tableDataInsertAllRequest',
                        'rows': [insert_data]
                    }
                ).execute()
            except:
                logging.exception('big query error')

    def insert_all(self, data_list):
        tabledata = self.tabledata()
        try:
            tabledata.insertAll(
                projectId=self.project_id,
                datasetId=self.dataset_id,
                tableId=self.table_id,
                body={
                    'kind': 'bigquery#tableDataInsertAllRequest',
                    'rows': self.build_insert_data(data_list),
                }
            ).execute()
        except:
            logging.exception('big query error')

    def query(self, query, timeout=10, dry_run=False, max_results=10):
        data = {
            'query': query,
            'timeoutMs': timeout * 1000,
            'dryRun': dry_run,
            'maxResults': max_results,
        }
        jobs = self.jobs()
        try:
            response = jobs.query(
                projectId=self.project_id, body=data
            ).execute()
        except:
            logging.exception('big query error')
        if not response.get('jobComplete'):
            raise BqQueryError
        return response


class BqQueryResult(object):
    u'''BiqQuery select文の結果整形のためのクラス。
    TODO: もうちょっとなんとかする
    '''

    def __init__(self, response):
        self.res = response
        self._items = []

    def schema(self):
        return self.res.get('schema', {})

    def fields(self):
        return self.schema().get('fields', {})

    def field_names(self):
        return [f['name'] for f in self.fields()]

    def rows(self):
        return self.res.get('rows', [])

    def totalRows(self):
        return self.res.get('totalRows')

    def items(self):
        if not self._items:
            for row in self.rows():
                self._items.append(
                    dict(self.zip(self.fields(), [r['v'] for r in row['f']]))
                )
        return self._items

    def zip(self, fields, values):
        ls = []
        for field, value in zip(fields, values):
            if field['type'] == u'FLOAT':
                ls.append((field['name'], float(value)))
            elif field['type'] == u'INTEGER':
                ls.append((field['name'], int(value)))
            else:
                ls.append((field['name'], value))
        return ls

    def attribute(self):
        return {
            'total': int(self.totalRows()),
            'count': len(self.items())
        }

    def as_dict(self):
        return {
            'result': {
                'attribute': self.attribute(),
                'items': self.items(),
            }
        }
