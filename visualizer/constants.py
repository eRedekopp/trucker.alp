# Constants and Enums

from enum import StrEnum
import datetime as dt

ROADSIDE_STOP_ID = 1

NULL_TIME = -3.0

SIMULATION_START_DATE = dt.datetime(2000, 1, 1)

class AnalysisType(StrEnum):
    #HOME_TIME="home"
    #DESTINATIONS="destinations"
    #VIOLS_INDIVIDUAL="viols_ind"
    #VIOL_STATS="viol_stats"
    VIOLS_AGGREGATE="viols_agg"
    ANIMATIONS="animations"

    @staticmethod
    def values():
        return [t.value for t in AnalysisType]


class ViolationType(StrEnum):
    NONE="no violation"
    HOURS="hours violation"
    PARKING="parking violation"
    DOUBLE="double violation"

    @staticmethod
    def values():
        return [t.value for t in ViolationType]

class LocationType(StrEnum):
    TRUCK_STOP="truck stop"
    GAS_STATION="gas station"
    REST_AREA="rest area"
    CITY="city"

class RestType(StrEnum):
    RESET="RestartRest"
    SLEEPER="SleeperRest"
    SHORT="ShortRest"
    DETENTION="Detention"
    REFUEL="Refuel"
    HOME="Home"

class DestinationType(StrEnum):
    HOME="home"
    SHIPPER="shipper"
    RECVR="receiver"
