import numpy as np

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
        self.river_state = self.river.initial_state
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
        return RainFlow(self.terrain, 0.005, 1, self.river)

    def rainfall(self):
        """ Increment the volume of all river nodes by some amount pulled from NOAA. """
        rainfall_const = 1
        self.river_state = [v + rainfall_const for v in self.river_state]

    def flow_into_river(self):
        """ Step the terrain rain flow including updating the river nodes. """
        # Update the river levels used in RainFlow.
        self.rain_flow.river_state = self.river_state
        # Step terrain cells, adding water levels from river-adjacent cells into river state.
        self.rain_flow.simulate()
        # Update the river levels used in Model.
        self.river_state = self.rain_flow.river_state

    def update_river_state(self, iterations=1):
        """
            Update the river state for a single step. This involves three parts:
                1) Add the rain that has fallen directly onto the river.
                2) Add the rain that has flowed from the terrain to the river.
                3) Simulate the river flowing down the river.
        """
        for i in range(0, iterations):
            self.rainfall()
            self.flow_into_river()
            self.river_state = (self.river.flow_matrix @ self.river_state) + self.river.offset_vector
