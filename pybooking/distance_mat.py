import pandas as pd
import googlemaps

import util


class DistanceClient(object):
    def __init__(self, n_days=5):
        self.dist_client = googlemaps.Client(util.APIKeys.distance)
        self.n_days = n_days
        self.visits_per_day = 3

    def get_distance_matrix(self, city, interest_list, mode='walking'):
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
        duration_matrix = self.extract_duration_matrix(coordinates, mode)
        df0 = pd.DataFrame(duration_matrix)
        df0.to_csv("dist_matrix.csv")
        print duration_matrix

    def extract_duration_matrix(self, coordinates, mode="walking"):
        result = []
        for i, source in enumerate(coordinates[:-1]):
            dist_list = self.dist_client.distance_matrix(
                [source], coordinates[i + 1:], mode=mode
            )
            elements = dist_list["rows"][0]["elements"]
            res = [p["duration"]["value"] for p in elements]
            res = [None] * (i + 1) + res
            result.append(res)
        return result

if __name__ == "__main__":
    cl = DistanceClient()
    cl.get_distance_matrix("Paris", ["museum", 'outdoor_activity'])
