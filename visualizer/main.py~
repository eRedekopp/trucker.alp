# Parse args and start up the visualizer

import argparse

from load_simulation_results import load_results
from constants import AnalysisType
from visualize import Visualizer

PROGRAM_NAME = "Trucker Model Data Visualizer"
PROGRAM_DESCRIPTION = (
    "Generates maps and graphs showing the "
    "results of a Trucker Model execution"
)

parser = argparse.ArgumentParser(
    prog=PROGRAM_NAME,
    description=PROGRAM_DESCRIPTION
)
parser.add_argument(
    '-o',
    '--output_dir',
    help="The directory in which the results will be stored.",
    default="./AnalysisResults",
    required=False
)
parser.add_argument(
    '-d',
    '--results_dir',
    help="The parent directory containing results",
    default=".",
    required=False
)
parser.add_argument(
    '-i',
    '--ids',
    type=int,
    nargs='+',
    help="The IDs of the truckers whose results should be considered",
    default=[1],
    required=False
)
parser.add_argument(
    '-l',
    '--locations_dir',
    help='The directory containing the data files for the locations',
    default='.',
    required=False
)
parser.add_argument(
    '-a',
    '--analyses',
    type=AnalysisType,
    nargs='+',
    help='The names of the analyses to perform.',
    choices=list(AnalysisType),
    default=AnalysisType.values(),
    required=False
)
parser.add_argument(
    '-s',
    '--osm_path',
    type=str,
    help="The path to the .osm or .osm.pbf file containing highway data",
    default=None,
    required=False
)

args = parser.parse_args()


if __name__ == "__main__":


    sim_results = load_results(
        args.ids,
        args.results_dir,
        args.locations_dir,
        args.osm_path
    )

    viz = Visualizer(sim_results, args.output_dir)

    if AnalysisType.ANIMATIONS in args.analyses:
        viz.animate_all_trucker_paths()

    if AnalysisType.VIOLS_AGGREGATE in args.analyses:
        viz.plot_aggregate_violations()
