""" Classes for reading and unpacking .obj files. """
import numpy as np
from pyqtree import Index
from itertools import count
from shapely.geometry import Point, Polygon


class Face:

    __slots__ = ['vertices', 'normal', 'polygon', '_index']
    indexer = count()

    def __init__(self, vertices, normal, polygon):
        """
        :param vertices: (Nx3) ndarray of floats representing the vertices of the face.
        :param normal: A 3D ndarray representing the normal vector to the face.
        :param polygon: The shapely.geometry.Polygon instance of the face.
        """
        self.vertices = vertices
        self.normal = normal
        self.polygon = polygon
        self._index = next(self.indexer)

    def __repr__(self):
        return (f'Face(\n\tvertices=\ '
                f'\n{self.vertices},'
                f'\n\tnormal={self.normal}'
                f'\n\tpolygon={self.polygon}'
                f'\n)')

    def __eq__(self, other):
        return np.array_equal(self.vertices, other.vertices)

    @property
    def index(self):
        """ Return the face's index in the terrains list of faces. """
        return self._index

    @property
    def bbox(self):
        """ Return a tuple indicating a bounding box for the polygon. """
        return np.array([*self.vertices.min(0)[:2], *self.vertices.max(0)[:2]])

    @property
    def neighborhood(self):
        """ Return a tuple indicating a bounding box for the polygon with 5% extra width on all sides. """
        lower = self.vertices.min(0)[:2]
        lower -= abs(lower) * 0.1
        upper = self.vertices.max(0)[:2]
        upper += abs(upper) * 0.1

        return np.array([*lower, *upper])

    # @property
    # def neighborhood2(self):
    #     """ Return a tuple indicating a bounding box for the polygon with 5% extra width on all sides. """
    #     lower = self.vertices.min(0)[:2]
    #     lower -= abs(lower) * 0.2
    #     upper = self.vertices.max(0)[:2]
    #     upper += abs(upper) * 0.2
    #
    #     return np.array([*lower, *upper])


class Object:
    """ Class for reading and unpacking .obj files. """

    def __init__(self, obj_file):
        """
        :param obj_file: Path to a .obj file.
        """
        self.file = obj_file
        self.name = None
        self.vertices = None
        self.faces = None

        self._adjacency_matrix = None
        self._quadtree = None

        self.unpack()

    def __repr__(self):
        return f'{self.name} :: NumberOfVertices = {len(self.vertices)}, NumberOfFaces = {len(self.faces)}'

    @property
    def adjacency_matrix(self):
        return self._adjacency_matrix

    @property
    def quadtree(self):
        return self._quadtree

    def unpack(self):
        """ Unpack the information from the .obj file. """
        self._parse_file()
        self._construct_quadtree()
        self._construct_adjacency()
        self._construct_adjacency2()

    def _parse_file(self):
        """ Extract the vertex and face information from the .obj file. """
        vertex_strings = []
        normal_strings = []
        face_strings = []
        with open(self.file) as fin:
            for line in fin:
                if line.startswith('vn'):  # normal vectors
                    normal_strings.append(line.strip())
                elif line.startswith('v'):  # vertices
                    vertex_strings.append(line.strip())
                elif line.startswith('f'):  # faces
                    face_strings.append(line.strip())
                elif line.startswith('o'):  # object name
                    self.name = line.strip()[2:]

        self.vertices = np.array([[float(num) for num in vertex.split()[1:]] for vertex in vertex_strings])
        normal_vectors = np.array([[float(num) for num in normal.split()[1:]] for normal in normal_strings])

        self.faces = []
        for face in face_strings:
            # Split up the face string into the components
            #  The components are "<vertex>/<vertex-texture>/<normal-vector>"
            components = face.split()[1:]

            # Get the normal vector.
            normal_index = int(components[0].split('/')[-1]) - 1
            normal = normal_vectors[normal_index]

            # Get the vertices.
            vertex_indices = [int(component.split('/')[0]) - 1 for component in components]
            vertices = np.array([self.vertices[index] for index in vertex_indices])

            # Construct the faces.
            self.faces.append(Face(vertices=vertices, normal=normal, polygon=Polygon(vertices)))

    def _construct_quadtree(self):
        """ Construct the quadtree instance. Useful for searching the terrain. """
        # Create the total bounding box.
        self._quadtree = Index((*self.vertices.min(0)[:2], *self.vertices.max(0)[:2]))

        # Insert the bounding boxes of the faces into the quadtree.
        for face in self.faces:
            self._quadtree.insert(face, face.bbox)

    def _construct_adjacency(self):
        """ Construct the adjacency matrix for the faces of the terrain. """
        # Initialize an empty adjacency matrix.
        faces_count = len(self.faces)
        self._adjacency_matrix = np.zeros((faces_count, faces_count), dtype=bool)

        # Efficiently loop over the faces using the quadtree search.
        for face in self.faces:
            # Get all the proper neighbors of the face.
            neighbors = [neighbor for neighbor in self.quadtree.intersect(face.neighborhood) if neighbor != face]

            # Loop over the neighbors. Neighbor is deemed adjacent if they share more than two vertices (an edge).
            for neighbor in neighbors:
                vertex_intersection = np.intersect1d(face.vertices, neighbor.vertices)
                if len(vertex_intersection) > 1:
                    self._adjacency_matrix[face.index, neighbor.index] = True
                    self._adjacency_matrix[neighbor.index, face.index] = True

    def _construct_adjacency2(self):
        # Initialize an empty adjacency matrix.
        faces_count = len(self.faces)
        adjacency_matrix = np.zeros((faces_count, faces_count), dtype=bool)

        # Efficiently loop over the faces using the quadtree search.
        for face in self.faces:
            # Get all the proper neighbors of the face.
            neighbors = [neighbor for neighbor in self.quadtree.intersect(face.bbox) if neighbor != face]

            # Loop over the neighbors. Neighbor is deemed adjacent if they share more than two vertices (an edge).
            for neighbor in neighbors:
                vertex_intersection = np.intersect1d(face.vertices, neighbor.vertices)
                if len(vertex_intersection) > 1:
                    adjacency_matrix[face.index, neighbor.index] = True
                    adjacency_matrix[neighbor.index, face.index] = True
        print(f'Does construct_adjacency == construct_adjacency2 : '
              f'{np.array_equal(adjacency_matrix, self.adjacency_matrix)}')

    def get_containing_face(self, point):
        """
            Return the face of the terrain which contains "point".
            Note: By contains this means that the 2D projection of the point lies within
                    the 2D projection of the face.
        :param point: An iterable of floats.
        :return: Face
        """
        for face in self.quadtree.intersect(point):
            if Point(point).within(face.polygon):
                return face
        return None
