# coding: utf-8

import json
from google.appengine.api import urlfetch


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

    def __init__(self, geocoder, result=None):
        self.geocoder = geocoder
        self._result = result

    def json(self):
        return self.geocoder.result()['results']

    def result(self):
        try:
            if self._result is None:
                self._result = self.json()[0]
            return self._result
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
            # 'json': self.json(),
        }

    def as_bq(self):
        return {
            'address': self.address(),
            'lat': self.lat(),
            'lng': self.lng(),
            'lat_origin': self.geocoder.lat,
            'lng_origin': self.geocoder.lng,
        }
