import sys
from os import path
import pandas as pd
import numpy as np
import googlemaps

import util


class DistanceClient(object):
    max_transit_time = 2 * 60 * 60  # seconds

    def __init__(self, n_days=5):
        self.dist_client = googlemaps.Client(util.APIKeys.distance)
        self.n_days = n_days

    def get_min_duration_matrix(self, city, interest_list):
        city_interest = CityAndInterests(city, interest_list, self.n_days)
        filename = city_interest.dist_mat_filename
        if path.exists(filename):
            return city_interest.distance_matrix
        df = city_interest.info
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
        for i, source in enumerate(coordinates[:-1]):
            res = self.get_durations(source, coordinates[i + 1:], mode)
            res = [np.NAN] * i + [0] + res
            result.append(res)
        result.append([np.NAN] * (n_len - 1) + [0])
        return result

    def get_durations(self, source, destinations, mode="walking"):
        dist_list = self.dist_client.distance_matrix(
            [source], destinations, mode=mode
        )
        elements = dist_list["rows"][0]["elements"]
        res = map(self._get_duration_safe, elements)
        return res

    def get_the_plan(self, city, interest_list):
        dist_matrix = DistanceMatrix(city, interest_list, self.n_days)
        _ = self.get_min_duration_matrix(city, interest_list)

        plans = dist_matrix.plan_the_trip()
        print plans

    def _get_duration_safe(self, q):
        duration = q.get("duration", {})
        return duration.get("value", self.max_transit_time)


class CityAndInterests(object):
    def __init__(self, city, interest_list, n_days):
        self.city = city
        self.interest_list = interest_list
        self.n_days = n_days

        # average number of sites people can visit per day
        self.visits_per_day = 2.5

        self.info_filename = self._get_filename()
        self.dist_mat_filename = self._get_filename("dist")
        self.plan_filename = self._get_filename("plan")

    @property
    def plan(self):
        return pd.read_csv(self.plan_filename, index_col=0)

    @util.lazy_property
    def info(self):
        if path.exists(self.info_filename):
            return pd.read_csv(self.info_filename, index_col=0)
        return self.get_aggregated_interest_sites()

    @util.lazy_property
    def distance_matrix(self):
        df = pd.read_csv(self.dist_mat_filename, index_col=0)
        df.index = df.index.astype(int)
        df.columns = df.columns.astype(int)
        return df

    def _get_filename(self, prefix=None):
        city_name = self.city if prefix is None else prefix + "-" + self.city
        return util.get_dump_filename(
            city_name,
            "{}-{}".format("-".join(self.interest_list), self.n_days), "csv"
        )

    def get_aggregated_interest_sites(self):
        all_sites = {
            interest: util.read_csv_city_interest(self.city, interest)
            for interest in self.interest_list
        }
        weights_by_total_popularity = {
            k: v["rating"].sum() for k, v in all_sites.items()
        }
        total_popularity = sum(weights_by_total_popularity.values())
        n_sites_total = self.n_days * self.visits_per_day
        weights_by_total_popularity = {
           k: max(int(v / total_popularity * n_sites_total), 1)
           for k, v in weights_by_total_popularity.items()
        }
        result = pd.concat(
            {k: all_sites[k].iloc[:n] for k, n
             in weights_by_total_popularity.items()}, names=["interest"]
        ).reset_index()
        result.to_csv(self.info_filename)
        return result


class DistanceMatrix(CityAndInterests):
    def __init__(self, city, interest_list, n_days):
        super(DistanceMatrix, self).__init__(city, interest_list, n_days)
        self.max_visits_per_day = int(self.visits_per_day) + 1
        self.plans_ = None

    @util.lazy_property
    def full_dist_matrix(self):
        # Fill the symmetric matrix
        n = self.n_interests
        mat = self.distance_matrix
        mat += np.eye(n) * DistanceClient.max_transit_time
        for i in range(n):
            mat.iloc[i, i + 1:] = mat.iloc[i + 1:, i].values
        return mat

    @property
    def n_interests(self):
        return len(self.distance_matrix)

    def plan_the_trip(self):
        self.plans_ = []
        df_dist = self.full_dist_matrix.copy()
        min_pairs = df_dist.idxmin()
        print self.full_dist_matrix
        min_pairs.index = min_pairs.index.astype(int)
        print min_pairs
        rest_candidates = set(range(self.n_interests))
        for i in range(self.n_days):
            col = df_dist.min().idxmin()
            row = df_dist[col].idxmin()
            self.plans_.append({row, col})
            rest_candidates = rest_candidates.difference({row, col})
            df_dist = df_dist.drop([row, col], 0).drop([row, col], 1)
        print rest_candidates
        while rest_candidates:
            print rest_candidates
            to_search = rest_candidates.pop()
            self._add_the_site(to_search)
        df = self.info.copy()
        df["day_plan"] = -1
        for i, group in enumerate(self.plans_):
            df.ix[list(group), "day_plan"] = i
        df.to_csv(self.plan_filename, index=None)
        return self.plans_

    def _add_the_site(self, site):
        dist_mat = self.full_dist_matrix.values
        min_day, min_duration = -1, DistanceClient.max_transit_time
        for i, day_plan in enumerate(self.plans_):
            if len(day_plan) == self.max_visits_per_day:
                continue
            current_min = min([dist_mat[site, p] for p in day_plan])
            if current_min < min_duration:
                min_day = i
                min_duration = current_min
        if min_day > -1:
            self.plans_[min_day].add(site)
        else:
            self.plans_.append({site})


if __name__ == "__main__":
    # python pybooking/distance_mat.py Paris outdoor_activity,museum 3
    city0 = sys.argv[1]
    interest_list0 = sys.argv[2].split(",")
    n_days0 = int(sys.argv[3])
    cl = DistanceClient(n_days0)
    cl.get_the_plan(city0, interest_list0)
