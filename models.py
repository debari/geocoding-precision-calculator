# coding: utf8
from google.appengine.ext import ndb
# import logging


class Greeting(ndb.Model):
    """Models an individual Guestbook entry with content and date."""
    content = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def query_book(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(-cls.date)


class BaseModel(ndb.Model):
    version = ndb.IntegerProperty(required=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def create_instance(cls, **kwargs):
        kwargs.update({'version': cls.VERSION})
        return cls(**kwargs)

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Place(BaseModel):
    VERSION = 1
    lat = ndb.FloatProperty(u'緯度')
    lng = ndb.FloatProperty(u'経度')
    coded_at = ndb.DateTimeProperty(u'変換時間')

    @classmethod
    def create_instance(cls, **kwargs):
        kwargs['lat'] = float(kwargs['lat'])
        kwargs['lng'] = float(kwargs['lng'])
        return super(Place, cls).create_instance(**kwargs)


class GeoCodedPlace(BaseModel):
    VERSION = 1
    lat = ndb.FloatProperty(u'変換済み緯度')
    lng = ndb.FloatProperty(u'変換済み経度')
    origin = ndb.KeyProperty(u'返還前座標データ', kind='Place')
    json = ndb.JsonProperty(u'変換時JSON')
    address = ndb.StringProperty(u'ジオコーディング住所')


class PlaceSummary(BaseModel):
    VERSION = 1
    lat = ndb.FloatProperty(u'変換済み緯度')
    lng = ndb.FloatProperty(u'変換済み経度')
    distance = ndb.FloatProperty(u'平均誤差')
    address = ndb.StringProperty(u'住所')
