#!/usr/bin/env python
# coding: utf-8

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


class MainHandler(webapp2.RequestHandler):

    def render_response(self, _template, context):
        template = JINJA_ENVIRONMENT.get_template(_template)
        self.response.write(template.render(**context))

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


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/test', BigQuerySelectHandler),
    # ('/list.csv', DownloadHandler),
], debug=True)
