import sys
import json
import googlemaps

import util


class PlaceClient(object):
    def __init__(self):
        self.client_geo = googlemaps.Client(util.APIKeys.geocode)
        self.client_place = googlemaps.Client(util.APIKeys.place)
        self.default_radius = 2000  # meters

    def get_location(self, city):
        result = self.client_geo.geocode(city)
        return util.get_coordinates(result[0])

    def places_nearby(self, city, interest):
        location = self.get_location(city)
        result = self.client_place.places(
            interest, location=location, radius=self.default_radius
        )
        all_places = sorted(
            result['results'], key=lambda p: p.get('rating', 2.5), reverse=True
        )
        filename_json = util.get_dump_filename(city, interest)
        json.dump(all_places, open(filename_json, "w"))


if __name__ == "__main__":
    # python pybooking/gmap.py Paris museum
    client = PlaceClient()
    city0, place_type0 = sys.argv[1:]
    client.places_nearby(city0, place_type0)
