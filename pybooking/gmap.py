import sys
import json
import googlemaps
import pandas as pd

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
        filename_csv = util.get_dump_filename(city, interest, "csv")
        self.extract_info_to_csv(all_places, filename_csv)

    @staticmethod
    def extract_info_to_csv(all_places, filename_csv):
        place_dict = {}
        for info in all_places:
            res = {"id": info["place_id"]}
            coord = util.get_coordinates(info)
            res["x"] = coord[0]
            res["y"] = coord[1]
            res["rating"] = info.get("rating", 2.5)
            photos = info.get("photos", None)
            if photos:
                res["photo_ref"] = photos[0]["photo_reference"]
            place_types = info.get("types", None)
            if place_types:
                place_types = set(place_types)
                place_types.discard('point_of_interest')
                res["place_types"] = "|".join(place_types)
            name = info["name"].encode('utf-8').strip()
            place_dict[name] = res

        df = pd.DataFrame.from_dict(place_dict, orient='index')
        df.to_csv(filename_csv, index_label="name")


if __name__ == "__main__":
    # python pybooking/gmap.py Paris museum
    client = PlaceClient()
    city0, place_type0 = sys.argv[1:]
    client.places_nearby(city0, place_type0)
