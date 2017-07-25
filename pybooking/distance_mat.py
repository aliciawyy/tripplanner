import googlemaps

import util


class DistanceClient(object):
    def __init__(self):
        self.dist_client = googlemaps.Client(util.APIKeys.distance)

    def get_distance_matrix(self, filename):
        pass
