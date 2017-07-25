from os import path
import pandas as pd
import numpy as np
import googlemaps

import util


class DistanceClient(object):
    def __init__(self, n_days=5):
        self.dist_client = googlemaps.Client(util.APIKeys.distance)
        self.n_days = n_days
        self.visits_per_day = 3
        self.max_transit_time = 2 * 60 * 60  # seconds

    @property
    def n_total_sites(self):
        return self.n_days * self.visits_per_day

    def _regroup_interest_sites(self, city, interest_list):
        filename = util.get_dump_filename(
            'Paris', "-".join(interest_list), ext="csv"
        )
        n_remaining = self.n_total_sites
        n_interest = len(interest_list)
        n_current = int(n_remaining / n_interest)
        res = {}
        for i, interest in enumerate(interest_list, 1):
            res[interest] = util.read_csv_city_interest(
                city, interest, n_largest=n_current
            )
            # in case some interest is not so common nearby, we can adjust
            # the rest
            n_remaining -= len(res[interest])
            if i < n_interest:
                n_current = int(n_remaining / (n_interest - i))
        df = pd.concat(res, names=["interest"]).reset_index()
        df.to_csv(filename)
        return df

    def get_distance_matrix(self, city, interest_list):
        filename = util.get_dump_filename(
            'dist-Paris', "-".join(interest_list), ext="csv"
        )
        df = self._regroup_interest_sites(city, interest_list)
        if path.exists(filename):
            return pd.read_csv(filename, index_col=0)

        coordinates = df[["x", "y"]].values
        duration_matrices = [
            self.extract_duration_matrix(coordinates, mode)
            for mode in ["walking", 'transit']
        ]
        df0_list = map(pd.DataFrame, duration_matrices)
        df0 = np.minimum(df0_list[0], df0_list[1]).T
        df0.to_csv(filename)
        print df0

    def extract_duration_matrix(self, coordinates, mode="walking"):
        result = []
        n_len = len(coordinates)
        print n_len
        for i, source in enumerate(coordinates[:-1]):
            res = self.get_durations(source, coordinates[i + 1:], mode)
            res = [np.NAN] * i + [0] + res
            result.append(res)
        return result

    def get_durations(self, source, destinations, mode="walking"):
        dist_list = self.dist_client.distance_matrix(
            [source], destinations, mode=mode
        )
        elements = dist_list["rows"][0]["elements"]
        res = map(self._get_duration_safe, elements)
        return res

    def _get_duration_safe(self, q):
        duration = q.get("duration", {})
        return duration.get("value", self.max_transit_time)

if __name__ == "__main__":
    cl = DistanceClient()
    cl.get_distance_matrix("Paris", ['outdoor_activity', "museum"])
