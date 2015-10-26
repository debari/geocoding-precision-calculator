# coding: utf-8
import datetime
import uuid
import logging
import httplib2
from apiclient.discovery import build

from oauth2client.appengine import AppAssertionCredentials


class BqQuery(object):
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

    def insert(self, data_list):
        tabledata = self.bigquery().tabledata()
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
