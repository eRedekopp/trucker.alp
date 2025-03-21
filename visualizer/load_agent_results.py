#

import datetime as dt
import pandas as pd
import geopandas as gpd
import numpy as np

from utils import gdf_concat, find_le, find_gt, find_lt
from constants import SIMULATION_START_DATE, ViolationType, NULL_TIME, RestType, DestinationType

START_SIMULATION_FILENAME = "StartSimulationEvent.csv"
START_DRIVING_FILENAME = "StartDrivingEvent.csv"
STOP_DRIVING_FILENAME = "StopDrivingEvent.csv"
START_NEW_TRIP_FILENAME = "StartNewTripEvent.csv"
HOURS_VIOL_FILENAME = "HoursViolationEvent.csv"
PARKING_VIOL_FILENAME = "ParkingViolationEvent.csv"
START_DRIVING_HOME_FILENAME = "StartDrivingHomeEvent.csv"
ARRIVE_AT_HOME_FILENAME = "ArriveAtHomeEvent.csv"

class AgentResults():
    def __init__(
            self,
            agent_id,
            start_sim_time,
            start_driving,
            start_driving_home,
            arrive_at_home,
            stop_driving,
            hours_viol,
            parking_viol,
            double_viol
    ):
        self.agent_id = agent_id
        self.start_sim_time = start_sim_time
        self.start_driving = start_driving
        self.start_driving_home = start_driving_home
        self.arrive_at_home = arrive_at_home
        self.stop_driving = stop_driving
        self.hours_viol = hours_viol
        self.parking_viol = parking_viol
        self.double_viol = double_viol

    def all_park_viols(self):
        return gdf_concat([self.parking_viol, self.double_viol])

    def all_hours_viols(self):
        return gdf_concat([self.hours_viol, self.double_viol])

    def num_park_viols(self, incl_dbl_viols=True):
        l = len(self.parking_viol)
        if incl_dbl_viols:
            l += self.num_dbl_viols()
        return l

    def num_hour_viols(self, incl_dbl_viols=True):
        l = len(self.hours_viol)
        if incl_dbl_viols:
            l += self.num_dbl_viols()
        return l

    def num_dbl_viols(self):
        return len(self.double_viol)

    def num_viols(self, violtype=None, incl_dbl_viols=True):
        if violtype is None:
            return (
                self.num_dbl_viols()
                + self.num_hour_viols(False)
                + self.num_park_viols(False)
            )
        if violtype == ViolationType.PARKING:
            return self.num_park_viols(incl_dbl_viols)
        if violtype == ViolationType.HOURS:
            return self.num_hour_viols(incl_dbl_viols)
        if violtype == ViolationType.DOUBLE:
            return self.num_dbl_viols()
        return 0


class AgentResultsLoader():
    @staticmethod
    def load_sim_start_info(results_dir):
        try:
            data = pd.read_csv(
                f"{results_dir}/{START_SIMULATION_FILENAME}",
                index_col="time"
            )
        except FileNotFoundError as e:
            print(f"Sim start info not found in dir {results_dir}")
            raise e
        if len(data) > 1:
            raise ValueError(f"Sim start had {len(data)} rows")
        return data.index[0], data.iloc[0]["homeCityID"]

    @staticmethod
    def load_new_trips(results_dir):
        try:
            return pd.read_csv(
                f"{results_dir}/{START_NEW_TRIP_FILENAME}",
                index_col="time"
            )
        except FileNotFoundError as e:
            print(f"No new trip info found in dir {results_dir}")
            raise e

    @staticmethod
    def load_stops(results_dir):
        try:
            stop_driving = pd.read_csv(
                f"{results_dir}/{STOP_DRIVING_FILENAME}",
                index_col="time"
            )
            stop_driving = gpd.GeoDataFrame(
                stop_driving,
                geometry=gpd.points_from_xy(
                    stop_driving.lon,
                    stop_driving.lat
                )
            )
            arrive_at_home = pd.read_csv(
                f"{results_dir}/{ARRIVE_AT_HOME_FILENAME}",
                index_col="time"
            )
            return stop_driving, arrive_at_home
        except FileNotFoundError as e:
            print(f"Missing data in dir {results_dir}")
            raise e

    @staticmethod
    def load_starts(results_dir):
        start_driving = None
        try:
            start_driving = pd.read_csv(
                f"{results_dir}/{START_DRIVING_FILENAME}",
                index_col="time"
            )
        except FileNotFoundError as e:
            print(f"Missing data in dir {results_dir}")
            raise e
        start_driving_home = AgentResultsLoader.try_get_viols(
            f"{results_dir}/{START_DRIVING_HOME_FILENAME}"
        )
        return start_driving, start_driving_home

    @staticmethod
    def try_get_viols(path):
        try:
            return pd.read_csv(
                path,
                index_col="time"
            )
        except FileNotFoundError:
            return pd.DataFrame()


    @staticmethod
    def load_violations(results_dir, stop_driving, all_locations):
        hours_viol = AgentResultsLoader.try_get_viols(
            f"{results_dir}/{HOURS_VIOL_FILENAME}"
        )
        park_viol = AgentResultsLoader.try_get_viols(
            f"{results_dir}/{PARKING_VIOL_FILENAME}"
        )

        def get_loc(row):
            locid = row["nextStopID"]
            time = row.name
            if (locid == 1):
                return {
                    "lon": stop_driving.loc[time]["lon"],
                    "lat": stop_driving.loc[time]["lat"]
                }
            else:
                return {
                    "lon": all_locations.loc[locid]["longitude"],
                    "lat": all_locations.loc[locid]["latitude"]
                }
        def get_lon(row):
            return get_loc(row)["lon"]
        def get_lat(row):
            return get_loc(row)["lat"]

        hours_viol["lon"] = hours_viol.apply(get_lon, axis=1)
        hours_viol["lat"] = hours_viol.apply(get_lat, axis=1)
        hours_viol = gpd.GeoDataFrame(
            hours_viol,
            geometry=gpd.points_from_xy(
                hours_viol.lon,
                hours_viol.lat
            )
        )
        park_viol = gpd.GeoDataFrame(
            park_viol,
            geometry=gpd.points_from_xy(
                park_viol.lon,
                park_viol.lat
            )
        )

        shared_idxs = hours_viol.index.intersection(park_viol.index)
        unique_hours_idxs = hours_viol.index.difference(shared_idxs)
        unique_parking_idxs = park_viol.index.difference(shared_idxs)

        double_viol = hours_viol.loc[shared_idxs].copy()
        hours_viol = hours_viol.loc[unique_hours_idxs].copy()
        park_viol = park_viol.loc[unique_parking_idxs].copy()

        return hours_viol, park_viol, double_viol


    @staticmethod
    def get_event_datetime(sim_hrs):
        return SIMULATION_START_DATE + dt.timedelta(hours=sim_hrs)

    @staticmethod
    def add_info_to_stops(
            stop_driving,
            start_driving,
            arrive_at_home,
            start_new_trip,
            hours_viol,
            park_viol,
            double_viol
    ):
        stop_driving["datetime"] = stop_driving.apply(
            lambda row: AgentResultsLoader.get_event_datetime(row.name),
            axis=1
        )

        def get_rest_type(row):
            time = row.name
            if time in arrive_at_home.index:
                return RestType.HOME
            else:
                return row["restType"]
        stop_driving["restType"] = stop_driving.apply(get_rest_type, axis=1)

        def get_viol_type(row):
            time = row.name
            if time in double_viol.index:
                return ViolationType.DOUBLE
            elif time in hours_viol.index:
                return ViolationType.HOURS
            elif time in park_viol.index:
                return ViolationType.PARKING
            else:
                return ViolationType.NONE
        stop_driving["viol"] = stop_driving.apply(get_viol_type, axis=1)

        def get_prev_start_time(row):
            time = row.name
            rownum = stop_driving.index.get_loc(time)
            return start_driving.iloc[rownum].name
        def get_next_start_time(row):
            time = row.name
            rownum = stop_driving.index.get_loc(time)
            if rownum + 1 >= len(start_driving):
                return NULL_TIME
            else:
                return start_driving.iloc[rownum + 1].name
        stop_driving["next_start"] = stop_driving.apply(
            get_next_start_time,
            axis=1
        )
        stop_driving["prev_start"] = stop_driving.apply(
            get_prev_start_time,
            axis=1
        )

        trip_start_times = start_new_trip.index
        def get_trip_start_time(row):
            time = row.name
            return find_le(trip_start_times, time)
        def get_trip_end_time(row):
            next_trip_start = find_gt(trip_start_times, row["trip_start"])
            if next_trip_start == NULL_TIME:
                return NULL_TIME
            return find_lt(stop_driving.index, next_trip_start)
        def get_is_hauling(row):
            trip_starttime = row["trip_start"]
            if trip_starttime == NULL_TIME:
                return False
            else:
                return start_new_trip.loc[trip_starttime]["isHauling"]
        stop_driving["trip_start"] = stop_driving.apply(
            get_trip_start_time,
            axis=1
        )
        stop_driving["trip_end"] = stop_driving.apply(
            get_trip_end_time,
            axis=1
        )
        stop_driving["is_hauling"] = stop_driving.apply(
            get_is_hauling,
            axis=1
        )

    @staticmethod
    def add_info_to_starts(
            start_driving,
            stop_driving,
            start_new_trip,
            start_driving_home,
            arrive_at_home,
            home_city_id,
            all_locations
    ):
        start_driving["datetime"] = start_driving.apply(
            lambda row: AgentResultsLoader.get_event_datetime(row.name),
            axis=1
        )

        def get_next_stop_time(row):
            time = row.name
            rownum = start_driving.index.get_loc(time)
            if rownum >= len(stop_driving):
                return NULL_TIME
            else:
                return stop_driving.iloc[rownum].name
        def get_prev_stop_time(row):
            time = row.name
            rownum = start_driving.index.get_loc(time)
            if rownum <= 0:
                return NULL_TIME
            else:
                return stop_driving.iloc[rownum - 1].name
        start_driving["next_stop"] = start_driving.apply(
            get_next_stop_time,
            axis=1
        )
        start_driving["prev_stop"] = start_driving.apply(
            get_prev_stop_time,
            axis=1
        )

        start_driving["new_trip"] = start_driving.apply(
            lambda row: row.name in start_new_trip.index,
            axis=1
        )

        home_trips = list(zip(start_driving_home.index, arrive_at_home.index))
        new_trip_times = [*start_new_trip.index, np.inf]
        def get_dest_type(row):
            time = row.name
            for start_time, stop_time in home_trips:
                if start_time <= time <= stop_time:
                    return DestinationType.HOME

            for i in range(len(new_trip_times) - 1):
                last_time = new_trip_times[i]
                next_time = new_trip_times[i+1]
                if last_time <= time <= next_time:
                    if start_new_trip.loc[last_time]["isHauling"]:
                        return DestinationType.RECVR
                    else:
                        return DestinationType.SHIPPER
            raise Exception(f"Can't determine destination type for time {time}")

        start_driving["dest_type"] = start_driving.apply(get_dest_type, axis=1)

        def get_location(row):
            prev_stop_time = row["prev_stop"]
            if prev_stop_time == NULL_TIME:
                home = all_locations.loc[home_city_id]
                return {
                    "lat": home["latitude"],
                    "lon": home["longitude"]
                }
            else:
                return stop_driving.loc[prev_stop_time]
        def get_lat(row):
            return get_location(row)["lat"]
        def get_lon(row):
            return get_location(row)["lon"]
        start_driving["lat"] = start_driving.apply(get_lat, axis=1)
        start_driving["lon"] = start_driving.apply(get_lon, axis=1)

    @staticmethod
    def load_agent_results(agent_id, results_parent_dir, all_locations):
        results_dir = f"{results_parent_dir}/{agent_id}"

        start_sim_time, home_city_id = AgentResultsLoader.load_sim_start_info(
            results_dir
        )
        start_new_trip = AgentResultsLoader.load_new_trips(
            results_dir
        )
        stop_driving, arrive_at_home = AgentResultsLoader.load_stops(
            results_dir
        )
        start_driving, start_driving_home = AgentResultsLoader.load_starts(
            results_dir
        )
        hours_viol, park_viol, double_viol = AgentResultsLoader.load_violations(
            results_dir,
            stop_driving,
            all_locations
        )

        AgentResultsLoader.add_info_to_stops(
            stop_driving,
            start_driving,
            arrive_at_home,
            start_new_trip,
            hours_viol,
            park_viol,
            double_viol
        )

        AgentResultsLoader.add_info_to_starts(
            start_driving,
            stop_driving,
            start_new_trip,
            start_driving_home,
            arrive_at_home,
            home_city_id,
            all_locations
        )
        start_driving = gpd.GeoDataFrame(
            start_driving,
            geometry=gpd.points_from_xy(
                start_driving.lon,
                start_driving.lat
            )
        )

        return AgentResults(
            agent_id,
            start_sim_time,
            start_driving,
            start_driving_home,
            arrive_at_home,
            stop_driving,
            hours_viol,
            park_viol,
            double_viol
        )
