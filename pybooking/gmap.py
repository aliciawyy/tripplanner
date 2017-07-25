from os import path
import sys
import json
import operator
import googlemaps

import util


class PlaceClient(object):
    def __init__(self):
        self.client = googlemaps.Client(util.APIKeys.place)
        self.default_radius = 2000  # meters

    def places_nearby(self, location, place_type):
        result = self.client.places(
            place_type, location=location, radius=self.default_radius
        )
        all_places = sorted(
            result['results'], key=operator.itemgetter('rating'), reverse=True
        )
        filename = path.join(
            util.OUTPUT_DIR,
            '{}_{}.json'.format('-'.join(location), place_type)
        )
        json.dump(all_places, open(filename, "w"))


if __name__ == "__main__":
    # python pybooking/gmap.py 48.852737 2.350699 museum
    client = PlaceClient()
    x, y, place_type = sys.argv[1:]
    client.places_nearby((x, y), place_type)
