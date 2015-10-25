#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import csv
import datetime
import uuid
import webapp2
import jinja2
import os
import logging
import json
import httplib2
from apiclient.discovery import build

from oauth2client.appengine import AppAssertionCredentials
from google.appengine.api import urlfetch

from models import (
    Place,
    GeoCodedPlace,
)

from local_settings import (
    PROJECT_NUMBER,
    DATASET_ID,
    TABLE_ID,
)

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

SCOPE = 'https://www.googleapis.com/auth/bigquery'


def bq_auth():
    credentials = AppAssertionCredentials(scope=SCOPE)
    http = credentials.authorize(httplib2.Http())
    bigquery = build('bigquery', 'v2', http=http)
    return bigquery


class GeoCoder(object):
    base = 'https://maps.googleapis.com/maps/api/geocode/json'

    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng
        self._result = None

    def reset(self):
        self.lat = None
        self.lng = None
        self._result = None

    def latlng(self):
        return '{lat},{lng}'.format(lat=self.lat, lng=self.lng)

    def build(self):
        yield 'latlng', self.latlng()
        yield 'language', 'ja'

    def query(self):
        return '&'.join(['{}={}'.format(k, v) for k, v in self.build()])

    def as_qs(self):
        return '{b}?{q}'.format(b=self.base, q=self.query())

    def fetch(self):
        res = urlfetch.fetch(self.as_qs())
        if res.status_code == 200:
            return json.loads(res.content)
        return None

    def result(self):
        if self._result is None:
            self._result = self.fetch()
        return self._result


class GeoCodingResult(object):

    def __init__(self, geocoder):
        self.geocoder = geocoder

    def json(self):
        return self.geocoder.result()['results']

    def result(self):
        try:
            return self.json()[0]
        except KeyError:
            return {}

    def address(self):
        return self.result().get('formatted_address', '')

    def geometry(self):
        return self.result().get('geometry', {})

    def location(self):
        return self.geometry().get('location', {})

    def lat(self):
        return self.location().get('lat')

    def lng(self):
        return self.location().get('lng')

    def type(self):
        return self.geometry().get('location_type', '')

    def as_dict(self):
        return {
            'address': self.address(),
            'lat': self.lat(),
            'lng': self.lng(),
            'json': self.json(),
        }

    def as_bq(self):
        return {
            'address': self.address(),
            'lat': self.lat(),
            'lng': self.lng(),
            'lat_origin': self.geocoder.lat,
            'lng_origin': self.geocoder.lng,
        }


class MainHandler(webapp2.RequestHandler):

    def render_response(self, _template, context):
        template = JINJA_ENVIRONMENT.get_template(_template)
        self.response.write(template.render(**context))

    def get(self):
        context = {'test': 'fugafuga'}
        self.render_response('templates/main.html', context)

    def post(self):
        lat = self.request.get('lat')
        lng = self.request.get('lng')

        place = Place.create_instance(lat=lat, lng=lng)
        future = place.put_async(use_memcache=True)
        geocoder = GeoCoder(lat, lng)
        result = GeoCodingResult(geocoder)
        res = result.as_dict()
        res['origin'] = future.get_result()
        coded = GeoCodedPlace.create_instance(**res)
        future = coded.put_async(use_memcache=True)
        context = {
            'place': place,
            'coded': coded
        }

        now = datetime.datetime.now()
        # created = now.strftime("%Y-%m-%d %H:%M:%S")
        insert_id = now.strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex
        insert_data = {
            'kind': 'bigquery#tableDataInsertAllRequest',
            'rows': [{'insertId': insert_id, 'json': result.as_bq()}]
        }
        bigquery = bq_auth()
        response = bigquery.tabledata().insertAll(
            projectId=PROJECT_NUMBER,
            datasetId=DATASET_ID,
            tableId=TABLE_ID,
            body=insert_data
        ).execute()
        self.render_response('templates/location.html', context)
        future.get_result()


class DownloadHandler(webapp2.RequestHandler):

    def get(self):
        self.response.headers['Content-Type'] = 'application/csv'
        writer = csv.writer(self.response.out)
        writer.writerow([
            'lat_origin', 'lng_origin',
            'lat', 'lng',
            'address',
        ])
        qry = GeoCodedPlace.query()
        for obj in qry.iter():
            origin = obj.origin.get()
            writer.writerow([
                origin.lat, origin.lng,
                obj.lat, obj.lng,
                obj.address.encode('utf-8'),
            ])

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    # ('/list.csv', DownloadHandler),
], debug=True)
