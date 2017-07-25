from os import path
import sys
import json
import operator
import googlemaps

import util


def _get_coordinates(info):
    xy = info['geometry']['location']
    return xy['lat'], xy["lng"]


class PlaceClient(object):
    def __init__(self):
        self.client_geo = googlemaps.Client(util.APIKeys.geocode)
        self.client_place = googlemaps.Client(util.APIKeys.place)
        self.default_radius = 2000  # meters

    def get_location(self, city):
        result = self.client_geo.geocode(city)
        return _get_coordinates(result[0])

    def places_nearby(self, city, place_type):
        location = self.get_location(city)
        result = self.client_place.places(
            place_type, location=location, radius=self.default_radius
        )
        all_places = sorted(
            result['results'], key=operator.itemgetter('rating'), reverse=True
        )
        filename = path.join(
            util.OUTPUT_DIR,
            '{}_{}.json'.format(city, place_type)
        )
        json.dump(all_places, open(filename, "w"))


if __name__ == "__main__":
    # python pybooking/gmap.py Paris museum
    client = PlaceClient()
    city, place_type0 = sys.argv[1:]
    client.places_nearby(city, place_type0)
