#

from utils import gdf_concat
from load_agent_results import AgentResultsLoader
from load_locations import load_all_locations, load_highways

class SimulationResults():

    def __init__(self, results_by_agent, all_locations, highways=None):
        self.all_locations = all_locations
        self.highways = highways
        self.results_by_agent = results_by_agent

def load_results(agent_ids, results_parent_dir, locations_dir, osm_path):
    all_locations = load_all_locations(locations_dir)
    highways = load_highways(osm_path)
    all_results = {
        agent_id: AgentResultsLoader.load_agent_results(
            agent_id,
            results_parent_dir,
            all_locations
        )
        for agent_id in agent_ids
    }
    return SimulationResults(all_results, all_locations, highways)
