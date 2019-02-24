import os
import pytest
from terrain.Object import RainFlow

class TestRainFlow:
    """ Class for testing RainFlow functionality. """
    test_data_directory = os.path.join(os.path.dirname(__file__), 'test_data')
    sloped_mesh_grid_file = os.path.join(test_data_directory, 'mesh_grid_sloped.obj')

    def test_initialize_rainflow (self):
        """ Test that a rainflow mesh can be initialized over a terrain. """
        # Arrange
        expected_mesh = '1111\n1111\n1111\n1111\n'

        # Act
        mesh = RainFlow(self.sloped_mesh_grid_file, 1, 1)

        # Assert
        assert expected_mesh == mesh.__repr__()

    def test_simulate (self):
        """ Test that stepping the rainflow process on a sloped plane drains the water to the lowest cells. """
        # Arrange
        expected_mesh = '0000\n0000\n0000\n4444\n'

        # Act
        mesh = RainFlow(self.sloped_mesh_grid_file, 1, 1)
        mesh.simulate(10)

        # Assert
        assert expected_mesh == mesh.__repr__()
