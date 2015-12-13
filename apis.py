#!/usr/bin/env python
# coding: utf-8

import webapp2
import json

from bq import (
    BqQuery,
)
from geocoding import (
    GeoCoder,
    GeoCodingResult,
)
from models import (
    Place,
    GeoCodedPlace,
)

PROJECT_ID = 'geocoding-precision-calculator'
DATASET_ID = 'places'
TABLE_ID = 'places'


class APIPostHandler(webapp2.RequestHandler):

    def post(self):

        lat = self.request.get('lat')
        lng = self.request.get('lng')

        place = Place.create_instance(lat=lat, lng=lng)
        future = place.put_async(use_memcache=True)
        geocoder = GeoCoder(lat, lng)
        result = GeoCodingResult(geocoder, json.loads(self.request.get('json')))

        res = result.as_dict()

        res['origin'] = future.get_result()
        coded = GeoCodedPlace.create_instance(**res)

        future = coded.put_async(use_memcache=True)

        bq = BqQuery(PROJECT_ID, DATASET_ID, TABLE_ID)
        bq.insert([result.as_bq()])

        future.get_result()
        self.response.write('')
