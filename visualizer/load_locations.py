#

import pandas as pd
import geopandas as gpd

from constants import LocationType
from utils import gdf_concat


CITIES_FILENAME = "USA_Major_Cities.csv"
ALLSTAYS_FILENAME = "allstays-truckstop-data.csv"
REST_AREAS_FILENAME = "rest-areas.csv"

def load_highways(osm_path):
    if osm_path is None: return None
    return gpd.read_file(
        osm_path,
        engine="pyogrio",
        layer="lines"
    )

def load_all_locations(locations_dir):
    return gdf_concat([
        load_cities(locations_dir),
        *load_truckstops_gasstations(locations_dir),
        load_rest_areas(locations_dir)
    ])

def load_cities(locations_dir):
    cities = pd.read_csv(
        f"{locations_dir}/{CITIES_FILENAME}",
        index_col="id"
    )
    cities.rename(
        columns={
            "X": "longitude",
            "Y": "latitude",
            "name": "NAME"
        },
        inplace=True
    )
    cities = gpd.GeoDataFrame(
        cities,
        geometry=gpd.points_from_xy(
            cities["latitude"],
            cities["longitude"]
        )
    )
    cities["type"] = LocationType.CITY
    return cities


def load_truckstops_gasstations(locations_dir):
    allstays = pd.read_csv(
        f"{locations_dir}/{ALLSTAYS_FILENAME}",
        index_col="id"
    )
    allstays = gpd.GeoDataFrame(
        allstays,
        geometry=gpd.points_from_xy(
            allstays.longitude,
            allstays.latitude
        )
    )
    truck_stops = allstays[allstays["parking"] > 1].copy()
    truck_stops["type"] = LocationType.TRUCK_STOP
    gas_stations = allstays[allstays["parking"] <= 1].copy()
    gas_stations["type"] = LocationType.GAS_STATION
    return (truck_stops, gas_stations)


def load_rest_areas(locations_dir):
    rest_areas = pd.read_csv(
        f"{locations_dir}/{REST_AREAS_FILENAME}",
        index_col="id"
    )
    rest_areas["type"] = LocationType.REST_AREA
    rest_areas = gpd.GeoDataFrame(
        rest_areas,
        geometry=gpd.points_from_xy(
            rest_areas.longitude,
            rest_areas.latitude
        )
    )
    return rest_areas
