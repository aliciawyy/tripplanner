import pandas as pd
import numpy as np
import googlemaps

import util


class DistanceClient(object):
    def __init__(self, n_days=5):
        self.dist_client = googlemaps.Client(util.APIKeys.distance)
        self.n_days = n_days
        self.visits_per_day = 4
        self.max_transit_time = 3 * 60 * 60  # seconds

    def get_distance_matrix(self, city, interest_list):
        n_per_interest = int(self.n_days * self.visits_per_day /
                             len(interest_list))
        df = pd.concat(
            map(lambda p: util.read_csv_city_interest(
                city, p, n_largest=n_per_interest
            ), interest_list),
            keys=interest_list, names=["interest"]
        ).reset_index()
        labels = df["interest"]
        print df[['name', "interest"]]
        coordinates = df[["x", "y"]].values
        duration_matrices = [
            self.extract_duration_matrix(coordinates, mode)
            for mode in ["walking", 'transit']
        ]
        df0_list = map(pd.DataFrame, duration_matrices)
        df0 = np.minimum(df0_list[0], df0_list[1])
        df0.to_csv("dist_matrix.csv")
        print df0

    def get_duration_safe(self, q):
        duration = q.get("duration", {})
        return duration.get("value", self.max_transit_time)

    def extract_duration_matrix(self, coordinates, mode="walking"):
        result = []
        for i, source in enumerate(coordinates[:-1]):
            res = self.get_durations(source, coordinates[i + 1:], mode)
            res = [None] * (i + 1) + res
            result.append(res)
        return result

    def get_durations(self, source, destinations, mode="walking"):
        dist_list = self.dist_client.distance_matrix(
            [source], destinations, mode=mode
        )
        elements = dist_list["rows"][0]["elements"]
        res = map(self.get_duration_safe, elements)
        return res

if __name__ == "__main__":
    cl = DistanceClient()
    cl.get_distance_matrix("Paris", ["museum", 'outdoor_activity'])
