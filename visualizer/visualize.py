# Visualize results

import os
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.gridspec import GridSpec
from matplotlib.font_manager import FontProperties
from matplotlib.animation import PillowWriter
from matplotlib.lines import Line2D
import geoplot as gplt
import geoplot.crs as gcrs
import fontawesome as fa

from describe_stops import generate_stop_description
from constants import ViolationType
from simulation_stats import ViolationStatistics


class Visualization():

    CRS = gcrs.WebMercator()

    DEFAULT_WIDTH_INCHES = 10
    DEFAULT_HEIGHT_INCHES = 10

    PARK_VIOL_MARKER = {
        "size": 5,
        "type": "D",
        "color": "orange",
        "label": "Parking violation"
    }
    HOUR_VIOL_MARKER = {
        "size": 5,
        "type": "s",
        "color": "dodgerblue",
        "label": "Hours violation"
    }
    DBL_VIOL_MARKER = {
        "size": 5,
        "type": "X",
        "color": "red",
        "label": "Double violation"
    }

    def __init__(self, sim_results, output_dir):
        self.sim_results = sim_results
        self.all_results = sim_results.results_by_agent
        self.locations = sim_results.all_locations
        self.highways = sim_results.highways
        self.output_dir = output_dir
        self.usa = gpd.read_file(gplt.datasets.get_path('contiguous_usa'))

        self.setup()

    def draw_pointplot(self, ax, data, marker, msize=None):
        if msize is None:
            msize = marker["size"]
        gplt.pointplot(
            data,
            ax=ax,
            extent=self.usa.total_bounds,
            color=marker["color"],
            s=msize,
            marker=marker["type"]
        )

    def draw_heatmap(self, ax, data):
        gplt.kdeplot(
            data,
            ax=ax,
            fill=True,
            extent=self.usa.total_bounds,
            zorder=0,
            #thresh=0,
            #levels=40,
            cmap="Reds"
        )

    def draw_bars(self, ax, xs, ys, xlabels=None):
        """
        ys is a dict {"label": [values]}. All values lists must be same length
        """

        is_multiple_bars = isinstance(ys, dict)

        def is_hist_bins():
            # If x array is 1 larger than y arrays, assume x is an array of
            # histogram bin edges
            ylen = len(list(ys.values())[0]) if is_multiple_bars else len(ys)
            xlen = len(xs)
            return xlen == ylen+1

        y_items = list(ys.items()) if is_multiple_bars else [("", ys)]
        num_categories = len(y_items)
        total_xbar_width = 1.0
        pad = total_xbar_width * 0.25
        bars_width = total_xbar_width - pad
        bar_width = bars_width / num_categories
        bar_locs = np.array([i * total_xbar_width for i in range(len(xs))])
        if is_hist_bins():
            bar_locs = bar_locs[:-1]
        max_y = max(max(y) for _, y in y_items)
        sliver_height = max_y / 80.0 # Show a little sliver for 0 values

        if xlabels is None:
            if is_hist_bins():
                xlabels = [
                    f"{xs[i]:.0f} to {xs[i+1]:.0f}"
                    for i in range(len(xs) - 1)
                ]
            else:
                xlabels = xs


        xtick_offset = 0
        xticklocs = np.array(bar_locs) + xtick_offset

        for i in range(num_categories):
            label, vals = y_items[i]
            vals = [
                sliver_height if y == 0 else y
                for y in vals
            ]
            bar_offset = bar_width * i
            ax.bar(
                bar_locs + bar_offset,
                vals,
                bar_width,
                label=label
            )

        ax.set_xticks(xticklocs, xlabels, ha="right")
        ax.tick_params(
            axis='x',
            labelrotation=60.0,
            labelsize="small"
        )

    def setup(self):
        os.makedirs(self.output_dir, exist_ok=True)

    def makefig(
            self,
            width=DEFAULT_WIDTH_INCHES,
            height=DEFAULT_HEIGHT_INCHES
    ):
        fig = plt.figure(
            figsize=(width, height)
        )
        return fig

    def draw_map(self, map_ax):
        gplt.polyplot(
            self.usa,
            extent=self.usa.total_bounds,
            ax=map_ax,
            zorder=1
        )
        if self.highways is not None:
            gplt.polyplot(
                self.highways,
                extent=self.usa.total_bounds,
                ax=map_ax
            )


class ViolationsVisualization(Visualization):

    VIOL_MARKER_SIZE = 3

    def __init__(self, sim_results, output_dir):
        super().__init__(sim_results, output_dir)
        self.violstats = ViolationStatistics(sim_results)
        self.park_viols = self.violstats.park_viols
        self.hour_viols = self.violstats.hour_viols
        self.dbl_viols = self.violstats.dbl_viols
        self.combined_viols = self.violstats.combined_viols

    def plot_stats_text(self, text_ax):
        violtext = self.violstats.make_viol_stats_text()
        text_ax.set_axis_off()
        text_ax.text(0.0, 0.0, violtext)

    def plot_viols_map(self, pt_ax, ht_ax, viols, marker, label=None):
        self.draw_pointplot(pt_ax, viols, marker, msize=self.VIOL_MARKER_SIZE)
        if viols is not self.dbl_viols:
            self.draw_pointplot(
                pt_ax,
                self.dbl_viols,
                self.DBL_VIOL_MARKER,
                self.VIOL_MARKER_SIZE
            )
        self.draw_heatmap(ht_ax, viols)
        if label is not None:
            for ax in pt_ax, ht_ax:
                ax.set_title(f"{label} violations")

    def plot_combined_viols_map(self, pt_ax, ht_ax, label=None):
        self.draw_pointplot(
            pt_ax,
            self.park_viols,
            self.PARK_VIOL_MARKER,
            msize=self.VIOL_MARKER_SIZE
        )
        self.draw_pointplot(
            pt_ax,
            self.hour_viols,
            self.HOUR_VIOL_MARKER,
            msize=self.VIOL_MARKER_SIZE
        )
        self.draw_pointplot(
            pt_ax,
            self.dbl_viols,
            self.DBL_VIOL_MARKER,
            msize=self.VIOL_MARKER_SIZE
        )
        self.draw_heatmap(ht_ax, self.combined_viols)
        if label is not None:
            for ax in pt_ax, ht_ax:
                ax.set_title(f"{label} violations")

    def plot_viols_time_hist(self, ax):
        num_bins = 10
        all_viol_times = self.combined_viols.index
        bins = np.histogram_bin_edges(all_viol_times, num_bins)
        park_hist_vals, _= self.violstats.make_time_hist(
            ViolationType.PARKING,
            bins
        )
        hours_hist_vals, _ = self.violstats.make_time_hist(
            ViolationType.HOURS,
            bins
        )
        dbl_hist_vals, _ = self.violstats.make_time_hist(
            ViolationType.DOUBLE,
            bins
        )
        hists = {
            "Parking": park_hist_vals,
            "Hours": hours_hist_vals,
            "Double": dbl_hist_vals
        }

        bins_as_days = bins / 24.0
        self.draw_bars(ax, bins_as_days, hists)
        ax.legend()
        ax.set_xlabel("Time (days)")
        ax.set_ylabel("Violations")
        ax.set_title("Violations By Time")


    def plot_viols_agent_hist(self, ax):
        num_bins = 10
        all_violnums = [
            r.num_viols(vt)
            for r in self.all_results.values() for vt in ViolationType.values()
        ]
        bins = np.histogram_bin_edges(all_violnums, num_bins)

        park_vals, _ = self.violstats.make_agent_hist(
            ViolationType.PARKING,
            bins
        )
        hours_vals, _ = self.violstats.make_agent_hist(
            ViolationType.HOURS,
            bins
        )
        dbl_vals, _ = self.violstats.make_agent_hist(
            ViolationType.DOUBLE,
            bins
        )
        hists = {
            "Parking": park_vals,
            "Hours": hours_vals,
            "Double": dbl_vals
        }

        self.draw_bars(ax, bins, hists)
        ax.legend()
        ax.set_xlabel("Violations")
        ax.set_ylabel("Agents")
        ax.set_title("Violations By Agent")

    def plot_hours_viol_overrun_hist(self, ax):
        overruns_mins = self.violstats.get_hours_viol_overruns() * 60.0
        max_overrun = max(overruns_mins)

        # Use custom bin edges to show finer-grained details in lower range
        def hr(n):
            return n * 60
        bins = np.array([
            0.0, 5.0, 15.0, 30.0,
            *[ float(x) for x in range(hr(1), int(max_overrun), hr(1)) ]
        ])
        hist, bins = np.histogram(overruns_mins, bins)
        self.draw_bars(ax, bins, hist)
        ax.set_xlabel("Overrun (minutes)")
        ax.set_ylabel("Violations")
        ax.set_title("Severity of Hours Violations")


    def plot_aggregate_violations(self):
        # Figure has 2 rows 4 columns for map plots. Top row is heatmaps, bottom
        # row is pointplots. Columns are all, park, hours, double violation
        # locations. Below the plots is another row with some text, and
        # histograms describing violations
        grid = GridSpec(3, 4)
        fig = self.makefig(width=20, height=10)
        ht_row = [fig.add_subplot(grid[0, i]) for i in range(4)]
        pt_row = [fig.add_subplot(grid[1, i]) for i in range(4)]
        text_ax = fig.add_subplot(grid[2, 0])
        hours_viol_ax = fig.add_subplot(grid[2, 1])
        time_hist_ax = fig.add_subplot(grid[2, 2])
        agent_hist_ax = fig.add_subplot(grid[2, 3])
        combined_ht, park_ht, hours_ht, dbl_ht = ht_row
        combined_pt, park_pt, hours_pt, dbl_pt = pt_row

        fig.suptitle("Violations - All Truckers")
        for ax in [*ht_row, *pt_row]:
            self.draw_map(ax)

        self.plot_stats_text(text_ax)
        self.plot_viols_time_hist(time_hist_ax)
        self.plot_viols_agent_hist(agent_hist_ax)
        self.plot_hours_viol_overrun_hist(hours_viol_ax)

        self.plot_viols_map(
            park_pt,
            park_ht,
            self.park_viols,
            self.PARK_VIOL_MARKER,
            "Parking"
        )
        self.plot_viols_map(
            hours_pt,
            hours_ht,
            self.hour_viols,
            self.HOUR_VIOL_MARKER,
            "Hours"
        )
        self.plot_viols_map(
            dbl_pt,
            dbl_ht,
            self.dbl_viols,
            self.DBL_VIOL_MARKER,
            "Double"
        )
        self.plot_combined_viols_map(combined_pt, combined_ht, "All")

        fig.savefig(f"{self.output_dir}/violations.png")


class TruckAnimationVisualization(Visualization):

    FPS = 1

    ORIG_MARKER = {
        "size": 12,
        "type": f"${fa.icons['industry']}$",
        "color": "darkblue",
        "label": "Trip origin"
    }
    DEST_MARKER = {
        "size": ORIG_MARKER["size"],
        "type": ORIG_MARKER["type"],
        "color": ORIG_MARKER["color"],
        "label": "Trip destination"
    }
    HOME_MARKER = {
        "size": 7,
        "type": f"${fa.icons['home']}$",
        "color": "purple",
        "label": "Trucker's home city"
    }
    PAST_STOP_MARKER = {
        "size": 5,
        "type": "v",
        "color": "blue",
        "label": "Past stop"
    }
    FUTURE_STOP_MARKER = {
        "size": 5,
        "type": "^",
        "color": "blue",
        "label": "Future stop"
    }
    CUR_STOP_MARKER_LOADED = {
        "size": 8,
        "type": f"${fa.icons['truck']}$",
        "color": "red",
        "label": "Cur. location (hauling)"
    }
    CUR_STOP_MARKER_UNLOADED = {
        "size": CUR_STOP_MARKER_LOADED["size"],
        "type": CUR_STOP_MARKER_LOADED["type"],
        "color": "green",
        "label": "Cur. location (not hauling)"
    }
    ALL_MARKERS = [
        Visualization.PARK_VIOL_MARKER,
        Visualization.HOUR_VIOL_MARKER,
        Visualization.DBL_VIOL_MARKER,
        ORIG_MARKER,
        DEST_MARKER,
        HOME_MARKER,
        PAST_STOP_MARKER,
        FUTURE_STOP_MARKER,
        CUR_STOP_MARKER_LOADED,
        CUR_STOP_MARKER_UNLOADED
    ]

    def setup(self):
        super().setup()

        mpl.rcParams["mathtext.fontset"] = "custom"
        mpl.rcParams["mathtext.bf"] = "FontAwesome"
        mpl.rcParams["mathtext.bfit"] = "FontAwesome"
        mpl.rcParams["mathtext.default"] = "it"
        mpl.rcParams["mathtext.fallback"] = "cm"
        mpl.rcParams["mathtext.rm"] = "FontAwesome"
        mpl.rcParams["mathtext.it"] = "FontAwesome"
        mpl.rcParams["mathtext.bf"] = "FontAwesome"
        mpl.rcParams["mathtext.tt"] = "FontAwesome"
        mpl.rcParams["mathtext.sf"] = "FontAwesome"
        mpl.rcParams["mathtext.cal"] = "FontAwesome"

    def animate_all_trucker_paths(self, start_frame=None, stop_frame=None):
        for agent_id in self.all_results.keys():
            self.animate_single_trucker_path(
                agent_id,
                start_frame=start_frame,
                stop_frame=stop_frame
            )

    def animate_single_trucker_path(
            self,
            agent_id,
            start_frame=None,
            stop_frame=None,
            fps=FPS
    ):
        results = self.all_results[agent_id]
        num_stops = len(results.stop_driving)

        if start_frame is None:
            start_frame = 0
        if stop_frame is None or stop_frame > num_stops:
            stop_frame = num_stops

        fig = self.makefig()
        fig.suptitle(f"All Stops: Driver {agent_id}")
        fig.tight_layout()

        # Record Frames
        writer = PillowWriter(fps=fps)
        with writer.saving(
                fig,
                f"{self.output_dir}/Trucker_Trajectory_{agent_id}.gif",
                200
        ):
            for frame_num in range(start_frame, stop_frame):
                print(f"Rendering frame #{frame_num+1}")
                self.capture_map_frame(
                    frame_num,
                    results,
                    fig,
                    writer
                )

    def make_animation_subplots(
            self,
            fig,
            height_ratio=(2, 1),
            width_ratio=(1, 1)
    ):
        return fig.subplots(
            2, # rows
            1, # cols
            gridspec_kw={
                'height_ratios': height_ratio,
                'width_ratios': width_ratio
            }
        )

    def capture_map_frame(
            self,
            stop_num,
            results,
            fig,
            writer,
            numframes=1
    ):
        # Draw the plot
        map_ax, text_ax = self.make_animation_subplots(fig)
        map_cpts = self.plot_map_frame(map_ax, results, stop_num)
        text_cpts = self.draw_text_frame(text_ax, results, stop_num)
        legend_cpts = self.draw_map_legend(text_ax)

        # Capture the frame(s)
        for _ in range(numframes):
            writer.grab_frame()

        # Clean up
        for c in [*map_cpts, *text_cpts, *legend_cpts, map_ax, text_ax]:
            c.remove()

    def plot_map_frame(self, map_ax, results, stop_num):
        return [
            *self.draw_map(map_ax),
            *self.draw_home(map_ax, results),
            *self.draw_points(map_ax, results, stop_num)
        ]

    def draw_home(self, map_ax, results):
        self.draw_pointplot(
            map_ax,
            results[[0]],
            self.HOME_MARKER
        )
        return []

    def draw_points(self, map_ax, results, stop_num):
        stop_driving = results.stop_driving
        stop = stop_driving.iloc[stop_num]
        stop_time = stop.name
        is_hauling = stop["is_hauling"]
        trip_start_time = stop["trip_start"]
        trip_end_time = stop["trip_end"]

        cur_stop = stop_driving.iloc[[stop_num]]
        origin = results.start_driving.loc[[trip_start_time]]
        destination = (
            stop_driving.loc[[trip_end_time]]
            if trip_end_time > 0
            else None
        )

        def get_viol_stops(violtype):
            return stop_driving[stop_driving["viol"] == violtype]
        def get_past_stops(violtype=None):
            data = get_viol_stops(violtype) if violtype else stop_driving
            return data.loc[trip_start_time:stop_time]
        def get_future_stops(violtype=None, dropdest=True):
            data = get_viol_stops(violtype) if violtype else stop_driving
            data = data.loc[stop_time:trip_end_time]
            if dropdest and stop_time in data.index: data.drop(stop_time)
            return data
        def get_cur_stop_marker():
            if is_hauling:
                return self.CUR_STOP_MARKER_LOADED
            else:
                return self.CUR_STOP_MARKER_UNLOADED

        def draw_orig_dest():
            self.draw_pointplot(
                map_ax,
                origin,
                self.ORIG_MARKER
            )
            if destination is not None:
                self.draw_pointplot(
                    map_ax,
                    destination,
                    self.DEST_MARKER
                )
        def draw_past_stops():
            self.draw_pointplot(
                map_ax,
                get_past_stops(ViolationType.PARKING),
                self.PARK_VIOL_MARKER
            )
            self.draw_pointplot(
                map_ax,
                get_past_stops(ViolationType.HOURS),
                self.HOUR_VIOL_MARKER
            )
            self.draw_pointplot(
                map_ax,
                get_past_stops(ViolationType.DOUBLE),
                self.DBL_VIOL_MARKER
            )
            self.draw_pointplot(
                map_ax,
                get_past_stops(ViolationType.NONE),
                self.PAST_STOP_MARKER
            )
        def draw_future_stops():
            self.draw_pointplot(
                map_ax,
                get_future_stops(),
                self.FUTURE_STOP_MARKER
            )
        def draw_cur_stop():
            self.draw_pointplot(
                map_ax,
                cur_stop,
                get_cur_stop_marker()
            )


        draw_orig_dest()
        draw_past_stops()
        draw_future_stops()
        draw_cur_stop()

        return []

    def draw_map_legend(self, ax, loc="upper right"):
        def make_legend_entry(marker):
            return Line2D(
                [0],
                [0],
                marker=marker["type"],
                color=(0, 0, 0, 0), # RGBA transparent
                label=marker["label"],
                markerfacecolor=marker["color"],
                markersize=12
            )
        legend_elems = [make_legend_entry(mkr) for mkr in self.ALL_MARKERS]
        legend = ax.legend(handles=legend_elems, loc=loc)
        return [legend]

    def draw_text_frame(self, text_ax, results, stop_num):
        description_sentences = generate_stop_description(
            results,
            self.locations,
            stop_num
        )
        text = text_ax.text(
            0.1,
            0.1,
            '\n'.join(description_sentences)
        )
        return [text]


class Visualizer(TruckAnimationVisualization, ViolationsVisualization):
    def __init__(self, sim_results, output_dir):
        super().__init__(sim_results, output_dir)
