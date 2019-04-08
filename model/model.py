import os
from shutil import rmtree
from tqdm import tqdm
import numpy as np
import seaborn as sbn
import networkx as nx
import matplotlib.pyplot as plt

from terrain import TerrainGenerator
from terrain.RainFlow import RainFlow


class Model:
    """
        The class for running the model and holding the model states.

    How the model works:
        There are three steps:

    """

    def __init__(self, terrain_file):
        """
        :param terrain_file: The path to the input file to the TerrainGenerator. (*.ipe or *.png expected)
        """
        self.terrain_file = terrain_file
        self.terrain = self._get_terrain()
        self.river = self.terrain.river
        self.river_state = np.copy(self.river.initial_state)
        self.rain_flow = self._get_rain_flow()

    def _get_terrain(self):
        """ Run the TerrainGeneration and return the terrain object. """
        if self.terrain_file.endswith('.ipe'):
            terr_gen = TerrainGenerator(ipe_file=self.terrain_file)
        elif self.terrain_file.endswith('.png'):
            terr_gen = TerrainGenerator(river_trace_image=self.terrain_file)
        else:
            raise TypeError(f'Invalid file type. Expected *.ipe or *.png - Found {self.terrain_file}')

        terr_gen.run()
        return terr_gen.terrain

    def _get_rain_flow(self):
        """ Initialize RainFlow and return the RainFlow object. """
        if self.terrain is None:
            raise ValueError('Terrain object never initialized.')
        return RainFlow(self.terrain, 0.007, 1, self.river)

    def rainfall(self, scale_factor=1):
        """ Increment the volume of all river nodes by some amount pulled from NOAA. """
        # rainfall = np.full(self.river_state.shape, fill_value=0.003)
        rainfall = scale_factor * 0.001 * self.river.initial_state
        self.river_state += rainfall

    def flow_into_river(self):
        """ Step the terrain rain flow including updating the river nodes. """
        # Update the river levels used in RainFlow.
        self.rain_flow.river_state = self.river_state
        # Step terrain cells, adding water levels from river-adjacent cells into river state.
        self.rain_flow.simulate()
        # Update the river levels used in Model.
        self.river_state = self.rain_flow.river_state

    def update_river_state(self, iterations=1, no_rainfall=False, scale_factor=1):
        """
            Update the river state for a single step. This involves three parts:
                1) Add the rain that has fallen directly onto the river.
                2) Add the rain that has flowed from the terrain to the river.
                3) Simulate the river flowing down the river.
        """
        for _ in range(iterations):  # tqdm(range(iterations), unit='iteration'):
            if not no_rainfall:
                self.rainfall(scale_factor)
            self.flow_into_river()
            self.river_state = self.river.flow_matrix @ self.river_state + self.river.offset_vector

            # The river shouldn't drain, so we set a lower bound for each node as the initial state.
            self.river_state = np.where(self.river_state < self.river.initial_state,
                                        self.river.initial_state, self.river_state)

    def test_run(self):
        self.test_data = np.empty((51, len(self.river_state)))
        self.test_data[0] = self.river_state / self.river.initial_state
        rainfall_steps = 20

        def scale_function(n):
            return n * (rainfall_steps - n) / (((rainfall_steps / 2) ** 2) * .8)

        for rf in tqdm(range(rainfall_steps + 1)):
            self.update_river_state(1000, scale_factor=scale_function(rf))
            self.test_data[rf] = self.river_state / self.river.initial_state

        for r in tqdm(range(rainfall_steps + 1, 51)):
            self.update_river_state(1000, no_rainfall=True)
            self.test_data[r] = self.river_state / self.river.initial_state

        iterations = list(range(0, 50001, 1000))
        for node in range(25, len(self.river_state), 50):
            plt.plot(iterations, self.test_data[:, node], label=f'Node {node:03d}')
        plt.axvline(rainfall_steps * 1000, color='r', linestyle='--', label='Rainfall Cutoff')
        plt.xlabel('Iterations')
        plt.ylabel('Percent of initial state')
        plt.title('Gauge level vs time')  # with initial dump of 0.1 across all nodes.')
        plt.legend()
        plt.show()

        # im_dir = 'gif_images'
        # if os.path.isdir(im_dir):
        #     rmtree(im_dir)
        # os.mkdir(im_dir)
        #
        # for index, state in tqdm(enumerate(self.test_data)):
        #     plt.clf()
        #     plt.title(f'River Flow - Iteration {index * 1000}')
        #     plt.axis('off')
        #     graph = nx.from_numpy_array(self.river.center_adjacency)
        #     _edges = nx.draw_networkx_edges(graph, self.river.inner_vertices[:, :2])
        #     nodes = nx.draw_networkx_nodes(graph, self.river.inner_vertices[:, :2],
        #                                    node_color=(state * self.river.initial_state),
        #                                    node_size=13, cmap='magma', vmin=0, vmax=0.40)
        #     plt.colorbar(nodes, label='Amount of Water')
        #     plt.savefig(os.path.join(im_dir, f'image_{index:02d}.png'), dpi=200, bbox_inches='tight')

    def plot(self):
        """ Plot river. """
        plt.clf()
        graph = nx.from_numpy_array(self.river.center_adjacency)
        _edges = nx.draw_networkx_edges(graph, self.river.inner_vertices[:, :2])
        nodes = nx.draw_networkx_nodes(graph, self.river.inner_vertices[:, :2], node_color=self.river_state,
                                       node_size=13, cmap='magma')
        plt.colorbar(nodes)
        plt.title('River Directed Graph')
        plt.show()

    def plot_terrain(self):
        """ Plot terrain. """
        plt.axis('off')
        sbn.heatmap(self.rain_flow.array_state, vmin=0, vmax=20, cmap='inferno')
