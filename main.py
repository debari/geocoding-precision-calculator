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
import webapp2
import jinja2
import os
import json

from bq import (
    BqQuery,
    BqQueryResult,
)
from geocoding import (
    GeoCoder,
    GeoCodingResult,
)
from models import (
    Place,
    GeoCodedPlace,
    PlaceSummary,
)

PROJECT_ID = 'geocoding-precision-calculator'
DATASET_ID = 'places'
TABLE_ID = 'places'
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True
)


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

        bq = BqQuery(PROJECT_ID, DATASET_ID, TABLE_ID)
        bq.insert([result.as_bq()])

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


class BigQuerySelectHandler(webapp2.RequestHandler):
    def get(self):
        bq = BqQuery(PROJECT_ID, DATASET_ID, TABLE_ID)
        self.response.headers['Content-Type'] = 'application/json'
        res = bq.query(u'''SELECT
    address,
    AVG(lat) as lat,
    AVG(lng) as lng,
    AVG(
        SQRT(
            POW(RADIANS(ABS(lat - lat_origin)) *
            6335439.32708317 / POW(SQRT(1 - 0.00669438002301188 *
            POW(SIN(RADIANS((lat + lat_origin)/2)), 2)), 3), 2)
            +
            POW(RADIANS(ABS(lng - lng_origin)) * 6378137.000 /
            SQRT(1 - 0.00669438002301188 *
            POW(SIN(RADIANS((lat + lat_origin)/2)),2)) *
             COS(RADIANS((lat + lat_origin)/2)), 2)
        )
    ) AS distance
FROM places.places
group by address;''')
        r = BqQueryResult(res)
        for item in r.items():
            ps = PlaceSummary\
                .query(PlaceSummary.address == item['address'])\
                .get()
            if ps is None:
                ps = PlaceSummary.create_instance(**item)
            else:
                ps.update(**item)
            ps.put()
        self.response.write(json.dumps(r.as_dict()))


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/test', BigQuerySelectHandler),
    # ('/list.csv', DownloadHandler),
], debug=True)
