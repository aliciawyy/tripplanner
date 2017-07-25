from os import path

import pandas as pd
import googlemaps

OUTPUT_DIR = path.join(path.dirname(__file__), "..", "output")


class APIKeys(object):
    geocode = "AIzaSyBmkF_p89N8DjBO77oJ-QOUFebB3rQwG30"
    place = "AIzaSyDqUsNug8hrxQyTyk14y1euWlq5SFZGtRs"
    distance = "AIzaSyDqUsNug8hrxQyTyk14y1euWlq5SFZGtRs"


class GeoClient(object):
    client = googlemaps.Client(APIKeys.geocode)

    @classmethod
    def get_location(cls, city):
        result = cls.client.geocode(city)
        return get_coordinates(result[0])


def get_coordinates(info):
    xy = info['geometry']['location']
    return xy['lat'], xy["lng"]


def get_dump_filename(city, interest, ext="json"):
    return path.join(OUTPUT_DIR, "{}_{}.{}".format(city, interest, ext))


def read_csv_city_interest(city, interest, sort_by="rating", n_largest=10):
    df = pd.read_csv(
        get_dump_filename(city, interest, "csv"), index_col='name'
    )
    return df.sort_values(sort_by, ascending=False).iloc[:n_largest]
