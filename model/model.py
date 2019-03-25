import numpy as np

from terrain import TerrainGenerator


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

    def _get_terrain(self):
        """ Run the TerrainGeneration and return the terrain object. """
        if self.terrain_file.ends_with('.ipe'):
            terr_gen = TerrainGenerator(ipe_file=self.terrain_file)
        elif self.terrain_file.ends_with('.png'):
            terr_gen = TerrainGenerator(river_trace_image=self.terrain_file)
        else:
            raise TypeError(f'Invalid file type. Expected *.ipe or *.png - Found {self.terrain_file}')

        terr_gen.run()
        return terr_gen.terrain

    def update_river_state(self):
        """
            Update the river state. This involves two steps:
                1) Add the rain that has fallen directly onto the river.
                2) Add the rain that has flowed from the terrain to the river.
                3) Simulate the river flowing down the river.
        """

        # self.rain_flow()
        # self.flow_into_river()
        self.river_state = (self.river.flow_matrix @ self.river_state) + self.river.offset_vector
