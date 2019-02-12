import os
import pytest
import numpy as np
from itertools import count

from terrain.Object import Face, Object


class TestObject:
    """ Class for testing Object functionality. """
    test_data_directory = os.path.join(os.path.dirname(__file__), 'test_data')
    grid_mesh_file = os.path.join(test_data_directory, 'mesh_grid.obj')
    rotated_grid_mesh_file = os.path.join(test_data_directory, 'mesh_rotated_grid.obj')

    @staticmethod
    def teardown_method():
        """ Method to tear down the test environment after testing. """
        Face.indexer = count()

    def test_parse_file(self, snapshot):
        """ Test that parse_file parses the .obj file as expected. """
        # Arrange
        test_object = Object(self.grid_mesh_file)
        expected_vertices = np.array([[row, column] for row in range(-2, 3) for column in range(-2, 3)])
        expected_normals = np.array([[0, 1]])

        # Act
        test_object._parse_file()

        # Assert
        np.array_equal(expected_vertices, test_object.vertices)
        np.array_equal(expected_normals, test_object.normal_vectors)
        snapshot.assert_match(list(map(str, test_object.faces)))

    def test_construct_adjacency_grid(self):
        """
            Test that the expected adjacency matrix is constructed when
                the mesh is provided by `mesh_grid.obj`.
        """
        # Arrange
        expected_adjacency_matrix = np.array([
            [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],
        ], dtype=bool)

        # Act
        result_adjacency_matrix = Object(self.grid_mesh_file).adjacency_matrix

        # Assert
        assert np.array_equal(expected_adjacency_matrix, result_adjacency_matrix)

    def test_construct_adjacency_rotated_grid(self):
        """
            Test that the expected adjacency matrix is constructed when
                the mesh is provided by `mesh_rotated_grid.obj`.
        """
        # Arrange
        expected_adjacency_matrix = np.array([
            [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
            [1, 1, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 1, 1, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 1, 1],
            [0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
        ], dtype=bool)

        # Act
        result_adjacency_matrix = Object(self.rotated_grid_mesh_file).adjacency_matrix

        # Assert
        assert np.array_equal(expected_adjacency_matrix, result_adjacency_matrix)

    @pytest.mark.parametrize(
        'query_bbox,expected_indices',
        [
            [(-2, -2, 2, 2), set(range(16))],
            [(0, 0), {5, 6, 9, 10}],
            [(-1.5, -1.5, 0.5, -0.5), {0, 1, 4, 5, 8, 9}],
        ])
    def test_construct_quadtree_grid(self, query_bbox, expected_indices):
        """ Test that query the quadtree of Object(mesh_grid.obj) returns expected results. """
        # Arrange
        test_quadtree = Object(self.grid_mesh_file).quadtree

        # Act
        faces = test_quadtree.intersect(query_bbox)
        indices = {face.index for face in faces}

        # Assert
        assert expected_indices == indices

    @pytest.mark.parametrize(
        'query_bbox,expected_indices',
        [
            [(-2.5, -2, 2.5, 2), set(range(10))],
            [(-0.5, 0), {1, 3, 4, 6}],
            [(-1, -2, 1, 0.5), {0, 1, 3, 4, 5, 6, 8, 9}],
        ])
    def test_construct_quadtree_rotated_grid(self, query_bbox, expected_indices):
        """ Test that query the quadtree of Object(mesh_rotated_grid.obj) returns expected results. """
        # Arrange
        test_quadtree = Object(self.rotated_grid_mesh_file).quadtree

        # Act
        faces = test_quadtree.intersect(query_bbox)
        indices = {face.index for face in faces}

        # Assert
        assert expected_indices == indices

    @pytest.mark.parametrize(
        'point,expected_index',
        [
            [(0.2, 1.75), 11],
            [(-5 / 3, -0.5), 1],
            [(-0.444, np.sqrt(2)), 7],
        ]
    )
    def test_get_containing_face(self, point, expected_index):
        """ Test that get_containing_face returns expected results for valid arguments. """
        # Arrange
        test_object = Object(self.grid_mesh_file)

        # Act
        face = test_object.get_containing_face(point)

        # Assert
        assert expected_index == face.index

    @pytest.mark.parametrize('point', [(0, 0), (0, 0.5), (1, -np.sqrt(3))])
    def test_get_containing_face_error(self, point):
        # Arrange
        test_object = Object(self.grid_mesh_file)

        # Act & Raise
        with pytest.raises(ValueError):
            test_object.get_containing_face(point)
