import sys
from os import path
import pandas as pd
import numpy as np
import googlemaps

import util

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("dist")


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
        df_result = dist_matrix.plan.sort_values("day_plan")
        log.critical(
            "\nGet the plan to visit '{}' according to your interests {}"
            "during {} days:\n{}\n\n{}".format(
                city, interest_list, self.n_days, plans,
                df_result[["name", "rating", "day_plan", "place_types"]]
            )
        )
        return plans

    def _get_duration_safe(self, q):
        duration = q.get("duration", {})
        return duration.get("value", self.max_transit_time)


class CityAndInterests(object):
    def __init__(self, city, interest_list, n_days):
        self.city = city
        self.interest_list = interest_list
        self.n_days = n_days

        # average number of sites people can visit per day
        self.visits_per_day = 3.5

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

    def get_all_sites(self):
        return {
            interest: util.read_csv_city_interest(self.city, interest)
            for interest in self.interest_list
        }

    def get_aggregated_interest_sites(self):
        try:
            all_sites = self.get_all_sites()
        except IOError:
            from gmap import PlaceClient
            place_cl = PlaceClient()
            _ = [place_cl.places_nearby(self.city, interest) for
                 interest in self.interest_list]
            all_sites = self.get_all_sites()

        weights_by_total_popularity = {
            k: v["rating"].sum() for k, v in all_sites.items()
        }
        log.info(
            "Total popularity of each interest in {}:\n{}"
            "".format(self.city, weights_by_total_popularity)
        )
        total_popularity = sum(weights_by_total_popularity.values())
        # Allocate number of sites for each interest according to
        # its popularity of the given city
        n_sites_total = self.n_days * self.visits_per_day
        weights_by_total_popularity = {
           k: max(int(v / total_popularity * n_sites_total), 1)
           for k, v in weights_by_total_popularity.items()
        }

        result = pd.concat(
            {k: all_sites[k].iloc[:n] for k, n
             in weights_by_total_popularity.items()}, names=["interest"]
        ).reset_index()
        result = result.sort_values("rating", ascending=False)\
            .set_index("interest").reset_index()
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
        log.info(
            "\nAll the selected sites according to users' interests "
            "{}:\n{}\n".format(self.interest_list,
                               self.info[["name", "rating", "place_types"]])
        )
        interests = self.info["interest"]

        def other_interests(series):
            current_interest = interests[series.name]
            other_interests0 = \
                series[interests[series.index] != current_interest]
            if len(other_interests0) == 0:
                other_interests0 = series
            return other_interests0

        self.plans_ = []

        df_dist = self.full_dist_matrix.copy()
        log.info("Full distance matrix:\n{}\n\n{}".format(
            self.full_dist_matrix, interests
        ))
        rest_candidates = set(range(self.n_interests))

        # Match different interests nearby on priority
        for i in range(self.n_days):
            col = df_dist.apply(lambda p: other_interests(p).min()).idxmin()
            row = other_interests(df_dist[col]).idxmin()
            self.plans_.append({row, col})
            rest_candidates = rest_candidates.difference({row, col})
            df_dist = df_dist.drop([row, col], 0).drop([row, col], 1)
        while rest_candidates:
            to_search = rest_candidates.pop()
            self._add_the_site(to_search)

        # Visit most popular attractions first
        self.plans_ = sorted(self.plans_, key=min)
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
        self.plans_[min_day].add(site)


if __name__ == "__main__":
    # python pybooking/distance_mat.py Paris outdoor_activity,museum 3
    city0 = sys.argv[1]
    interest_list0 = sys.argv[2].split(",")
    n_days0 = int(sys.argv[3])
    cl = DistanceClient(n_days0)
    cl.get_the_plan(city0, interest_list0)
