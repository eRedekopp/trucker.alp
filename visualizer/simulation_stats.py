#

import numpy as np
import pandas as pd

from constants import ViolationType
from utils import gdf_concat

class ViolationStatistics():

    def __init__(self, sim_results):
        self.sim_results = sim_results
        resultslist = sim_results.results_by_agent.values()
        self.park_viols = gdf_concat(
            [r.parking_viol for r in resultslist]
        )
        self.hour_viols = gdf_concat([
            r.hours_viol for r in resultslist
        ])
        self.dbl_viols = gdf_concat([
            r.double_viol for r in resultslist
        ])
        self.combined_viols = gdf_concat([
            self.park_viols, self.hour_viols, self.dbl_viols
        ])
        self.num_park_viols = len(self.park_viols)
        self.num_hour_viols = len(self.hour_viols)
        self.num_dbl_viols = len(self.dbl_viols)
        self.total_viols = (
            self.num_park_viols + self.num_hour_viols + self.num_dbl_viols
        )
        self.total_stops = sum(
            len(agent_results.stop_driving)
            for agent_results in resultslist
        )
        self.total_starts = sum(
            len(agent_results.start_driving)
            for agent_results in resultslist
        )
        self.sim_start_time = min(r.start_sim_time for r in resultslist)
        self.last_event_time = max([
            *[max(r.stop_driving.index) for r in resultslist],
            *[max(r.start_driving.index) for r in resultslist]
        ])
        self.sim_duration_hrs = self.last_event_time - self.sim_start_time
        self.num_agents = len(sim_results.results_by_agent)

    def get_hours_viol_overruns(self):
        return pd.concat([
            r.hours_viol["hoursOverrun"]
            for r in self.sim_results.results_by_agent.values()
        ])

    def get_viols(self, violtype=None):
        if violtype is None:
            return self.combined_viols
        if violtype == ViolationType.HOURS:
            return self.hour_viols
        if violtype == ViolationType.PARKING:
            return self.park_viols
        if violtype == ViolationType.DOUBLE:
            return self.dbl_viols
        raise Exception("Unknown type " + violtype)

    def make_time_hist(self, violtype=None, bins=30):
        violtimes = self.get_viols(violtype).index
        histvals, bin_edges = np.histogram(violtimes, bins)
        return histvals, bin_edges

    def make_agent_hist(self, violtype=None, bins=20):
        violnums = [
            r.num_viols(violtype)
            for r in self.sim_results.results_by_agent.values()
        ]
        histvals, bin_edges = np.histogram(violnums, bins)
        return histvals, bin_edges

    def make_viol_stats_sentences(self):

        def make_viols_text(label, nviols):
            sim_yrs = self.sim_duration_hrs / (24.0 * 365.0)
            ptpy = nviols / self.num_agents / sim_yrs
            return f"{label} violations: {nviols} ({ptpy:.2f}/trucker/year)"

        ntruckers_text = f"Truckers: {self.num_agents}"
        ndays = self.sim_duration_hrs / 24.0
        nhours_text = (
            f"Duration: {self.sim_duration_hrs:.0f} Hours "
            f"({ndays:.1f} Days)"
        )

        def make_viol_sentences():
            return [
                make_viols_text("Parking", self.num_park_viols),
                make_viols_text("Hours", self.num_hour_viols),
                make_viols_text("Double", self.num_dbl_viols)
            ]

        def make_hours_viol_sentence(limit):
            limit = limit * 60.0
            return make_viols_text(
                f"Hours (>{limit:.2f}min)",
                (self.hour_viols["hoursOverrun"] > limit).sum()
            )

        def make_overrun_stat_sentence(stat, label):
            return f"{label} hours violation: {stat:.2f} hrs"

        overruns = self.get_hours_viol_overruns()
        overrun_stat_sentences = [
            make_overrun_stat_sentence(min(overruns), "Min"),
            make_overrun_stat_sentence(max(overruns), "Max"),
            make_overrun_stat_sentence(overruns.mean(), "Mean"),
            make_overrun_stat_sentence(overruns.median(), "Median"),
            make_overrun_stat_sentence(overruns.std(), "Stdev")
        ]

        return [
            ntruckers_text,
            nhours_text,
            "\n",
            *overrun_stat_sentences,
            "\n",
            *make_viol_sentences(),
            "\n",
            make_hours_viol_sentence(0.25),
            make_hours_viol_sentence(0.5),
            make_hours_viol_sentence(0.75),
            make_hours_viol_sentence(1.0)
        ]

    def make_viol_stats_text(self):
        snts = self.make_viol_stats_sentences()
        return '\n'.join(snts)
