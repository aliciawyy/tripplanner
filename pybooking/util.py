from os import path

import pandas as pd
import googlemaps

BASE_DIR = path.dirname(__file__)
OUTPUT_DIR = path.join(BASE_DIR, "..", "output")
KEYS_DIR = path.join(BASE_DIR, "..", "keys")


class APIKey(object):

    @classmethod
    def from_file(cls, filename):
        df = pd.read_csv(path.join(KEYS_DIR, filename), header=0, index_col=0)
        series = df['key']
        cls.geocode = series["geocode"]
        cls.place = series["place"]
        cls.distance = series["distance"]
        return cls


APIKeys = APIKey.from_file("api_key2.csv")


class GeoClient(object):
    client = googlemaps.Client(APIKeys.geocode)

    @classmethod
    def get_location(cls, city):
        result = cls.get_city_information(city)
        return get_coordinates(result[0])

    @classmethod
    def get_city_information(cls, city):
        return cls.client.geocode(city)


def get_coordinates(info):
    xy = info['geometry']['location']
    return xy['lat'], xy["lng"]


def get_dump_filename(city, interest, ext="json"):
    return path.join(OUTPUT_DIR, "{}_{}.{}".format(city, interest, ext))


def read_csv_city_interest(city, interest):
    df = pd.read_csv(
        get_dump_filename(city, interest, "csv"), index_col='name'
    )
    return df


def lazy_property(fn):
    """Decorator that makes a property lazy-evaluated."""
    attr_name = '_lazy_' + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazy_property
