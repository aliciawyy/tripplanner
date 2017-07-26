import sys
import json
import googlemaps
import pandas as pd

import util
from distance_mat import DistanceClient

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("place")


class PlaceClient(object):
    def __init__(self):
        self.client_place = googlemaps.Client(util.APIKeys.place)
        self.default_radius = 4000  # meters
        self.redundant_types = {'point_of_interest', 'establishment'}

    def places_nearby(self, city, interest):
        if "," in interest:
            interests = interest.split(",")
            for interest in interests:
                self.places_nearby(city, interest)
        location = util.GeoClient.get_location(city)
        result = self.client_place.places(
            interest, location=location, radius=self.default_radius
        )
        all_places = sorted(
            result['results'], key=lambda p: p.get('rating', 2.5), reverse=True
        )
        filename_json = util.get_dump_filename(city, interest)
        json.dump(all_places, open(filename_json, "w"))
        filename_csv = util.get_dump_filename(city, interest, "csv")
        df = self.extract_info_to_csv(location, all_places, filename_csv)
        log.info("\nFound sites for interest {} in city {}:\n{}"
                 "\n".format(interest, city, df))
        return df

    def extract_info_to_csv(self, city_location, all_places, filename_csv):
        place_dict = {}
        for info in all_places:
            name, res = self._extract_one_info(info)
            place_dict[name] = res
        df = pd.DataFrame.from_dict(place_dict, orient='index')

        dist_client = DistanceClient()
        df["transit_time"] = dist_client.get_durations(
            city_location, df[["x", "y"]].values, mode='transit'
        )
        df = df[df["transit_time"] < dist_client.max_transit_time]
        df = df.sort_values("rating", ascending=False)
        df.to_csv(filename_csv, index_label="name")
        return df

    def _extract_one_info(self, info):
        res = {"id": info["place_id"]}
        coord = util.get_coordinates(info)
        res["x"] = coord[0]
        res["y"] = coord[1]
        res["rating"] = info.get("rating", 2.5)
        photos = info.get("photos")
        if photos:
            res["photo_ref"] = photos[0]["photo_reference"]
        place_types = info.get("types")
        if place_types:
            place_types = set(place_types)
            place_types = place_types.difference(self.redundant_types)
            res["place_types"] = "|".join(place_types)
        name = info["name"].encode('utf-8').strip()
        return name, res


if __name__ == "__main__":
    # python pybooking/gmap.py Paris museum
    client = PlaceClient()
    city0, place_type0 = sys.argv[1:]
    client.places_nearby(city0, place_type0)
