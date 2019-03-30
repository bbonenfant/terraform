import os
import pytest
from terrain.RainFlow import RainFlow
from terrain.Object import Object
from terrain.Object import River


class TestRainFlow:
    """ Class for testing RainFlow functionality. """
    test_data_directory = os.path.join(os.path.dirname(__file__), 'test_data')
    sloped_mesh_grid_file = os.path.join(test_data_directory, 'mesh_grid_sloped.obj')
    rotated_mesh_grid_file = os.path.join(test_data_directory, 'mesh_rotated_grid.obj')
    terrain = Object(sloped_mesh_grid_file)
    rotated_terrain = Object(rotated_mesh_grid_file)
    river_file = os.path.join(test_data_directory, 'river.obj')
    river = River(river_file)

    def test_initialize_rainflow (self):
        """ Test that a rainflow mesh can be initialized over a terrain. """
        # Arrange
        expected_mesh = '1111\n1111\n1111\n1111\n'

        # Act

        mesh = RainFlow(self.terrain, 1, 1, self.river)

        # Assert
        assert expected_mesh == mesh.__repr__()

    def test_simulate (self):
        """ Test that stepping the rainflow process on a sloped plane drains the water to the lowest cells and then into
        the river. """
        # Arrange
        expected_mesh = '....\n....\n....\n....\n'

        # Act
        mesh = RainFlow(self.terrain, 1, 1, self.river)
        mesh.simulate(10)

        # Assert
        assert expected_mesh == mesh.__repr__()
