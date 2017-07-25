import sys
from os import path
import pandas as pd
import numpy as np
import googlemaps

import util


class DistanceClient(object):
    max_transit_time = 2 * 60 * 60  # seconds
    visits_per_day = 2.5

    def __init__(self, n_days=5):
        self.dist_client = googlemaps.Client(util.APIKeys.distance)
        self.n_days = n_days

    @property
    def n_total_sites(self):
        return int(self.n_days * self.visits_per_day)

    def regroup_interest_sites(self, city, interest_list):
        filename = util.get_dump_filename(
            city, "-".join(interest_list), ext="csv"
        )
        if path.exists(filename):
            return pd.read_csv(filename, index_col=0)
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
            'dist-' + city, "-".join(interest_list), ext="csv"
        )
        if path.exists(filename):
            return pd.read_csv(filename, index_col=0)
        df = self.regroup_interest_sites(city, interest_list)
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
        _ = self.regroup_interest_sites(city, interest_list)
        _ = self.get_distance_matrix(city, interest_list)
        dist_matrix = DistanceMatrix(city, interest_list, self.n_days)
        plans = dist_matrix.plan_the_trip()
        print plans

    def _get_duration_safe(self, q):
        duration = q.get("duration", {})
        return duration.get("value", self.max_transit_time)


class DistanceMatrix(object):
    def __init__(self, city, interest_list, n_days):
        self.city = city
        self.interest_list = interest_list
        filename_info = util.get_dump_filename(
            city, "-".join(interest_list), ext="csv"
        )
        self.info = pd.read_csv(filename_info, index_col=0)
        filename_data = util.get_dump_filename(
            'dist-' + city, "-".join(interest_list), ext="csv"
        )
        self.data = pd.read_csv(filename_data, index_col=0)
        self.n_days = n_days
        self.max_visits_per_day = int(DistanceClient.visits_per_day) + 1
        self._data_matrix = None
        self.plans_ = None

    @property
    def data_matrix(self):
        if self._data_matrix is None:
            n = self.n_interests
            mat = self.data
            mat += np.eye(n) * DistanceClient.max_transit_time
            for i in range(n):
                mat.iloc[i, i + 1:] = self.data.iloc[i + 1:, i]
            self._data_matrix = mat
        return self._data_matrix

    @property
    def n_interests(self):
        return len(self.data)

    def plan_the_trip(self):
        self.plans_ = []
        mat = self.data_matrix
        min_pairs = mat.idxmin()
        min_pairs.index = min_pairs.index.astype(int)
        remaining_candidates = set(range(self.n_interests))
        for a, b in min_pairs.iteritems():
            if {a, b} <= remaining_candidates:
                self.plans_.append({a, b})
                remaining_candidates = remaining_candidates.difference({a, b})
                continue
            elif {a, b}.difference(remaining_candidates):
                continue
            to_search = a if a in remaining_candidates else b
            remaining_candidates.remove(to_search)
            self._add_the_site(to_search)

        while remaining_candidates:
            to_search = remaining_candidates.pop()
            self._add_the_site(to_search)
        filename_plan = util.get_dump_filename(
            "plan-" + self.city, "-".join(self.interest_list), ext="csv"
        )
        df = self.info.copy()
        df["day_plan"] = -1
        for i, group in enumerate(self.plans_):
            df.ix[list(group), "day_plan"] = i
        df.to_csv(filename_plan, index=None)
        return self.plans_

    def _add_the_site(self, site):
        dist_mat = self.data_matrix.values
        min_day, min_duration = -1, DistanceClient.max_transit_time
        for i, day_plan in enumerate(self.plans_):
            if len(day_plan) > self.max_visits_per_day:
                continue
            current_min = min([dist_mat[site, p] for p in day_plan])
            if current_min < min_duration:
                min_day = i
                min_duration = current_min
        if min_day > -1:
            self.plans_[min_day].add(site)

if __name__ == "__main__":
    cl = DistanceClient()

    city0 = sys.argv[1]
    interest_list0 = sys.argv[2].split(",")
    cl.get_the_plan(city0, interest_list0)
