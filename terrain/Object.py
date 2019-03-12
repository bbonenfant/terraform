""" Classes for reading and unpacking .obj files. """
import queue
import numpy as np
from pyqtree import Index
from shapely.geometry import Point, Polygon
from matplotlib import pylab as pl
from matplotlib import collections as mc


class Face:
    __slots__ = ['vertices', 'normal', 'polygon', '_index']

    def __init__(self, vertices, normal, polygon, index):
        """
        :param vertices: (Nx3) ndarray of floats representing the vertices of the face.
        :param normal: A 3D ndarray representing the normal vector to the face.
        :param polygon: The shapely.geometry.Polygon instance of the face.
        """
        self.vertices = vertices
        self.normal = normal
        self.polygon = polygon
        self._index = index

    def __repr__(self):
        return (f'Face(\n\tvertices=\\'
                f'\n{self.vertices},'
                f'\n\tnormal={self.normal}'
                f'\n\tpolygon={self.polygon}'
                f'\n\tindex={self.index}'
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
        return self.polygon.bounds


class Object:
    """ Class for reading and unpacking .obj files. """

    def __init__(self, obj_file):
        """
        :param obj_file: Path to a .obj file.
        """
        self.file = obj_file
        self.name = None
        self.vertices = None
        self.normal_vectors = None
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

    @property
    def bbox(self):
        xmin = self._quadtree.center[0] - (self._quadtree.width / 2)
        ymin = self._quadtree.center[1] - (self._quadtree.height / 2)
        xmax = xmin + self._quadtree.width
        ymax = ymin + self._quadtree.height
        return (xmin, ymin, xmax, ymax)


    def unpack(self):
        """ Unpack the information from the .obj file. """
        self._parse_file()
        self._construct_quadtree()
        self._construct_adjacency()

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
        self.normal_vectors = np.array([[float(num) for num in normal.split()[1:]] for normal in normal_strings])

        self.faces = []
        for face in face_strings:
            # Split up the face string into the components
            #  The components are "<vertex>/<vertex-texture>/<normal-vector>"
            components = face.split()[1:]

            # Get the normal vector.
            normal_index = int(components[0].split('/')[-1]) - 1
            normal = self.normal_vectors[normal_index]

            # Get the vertices.
            vertex_indices = [int(component.split('/')[0]) - 1 for component in components]
            vertices = np.array([self.vertices[index] for index in vertex_indices])

            # Construct the faces.
            self.faces.append(Face(vertices=vertices, normal=normal, polygon=Polygon(vertices), index=len(self.faces)))

    def _construct_quadtree(self):
        """ Construct the quadtree instance. Useful for searching the terrain. """
        # Create the total bounding box.
        self._quadtree = Index((*self.vertices.min(0)[:2], *self.vertices.max(0)[:2]))

        # Insert the bounding boxes of the faces into the quadtree.
        for face in self.faces:
            self._quadtree.insert(face, face.bbox)

    def _construct_adjacency(self):
        """ Construct the adjacency matrix for the faces of the terrain. """

        def numpy_vector_intersect(vector_array1, vector_array2):
            """ Computes the intersection of two numpy arrays of vectors. """
            return set(map(tuple, vector_array1)).intersection(map(tuple, vector_array2))

        # Initialize an empty adjacency matrix.
        faces_count = len(self.faces)
        self._adjacency_matrix = np.zeros((faces_count, faces_count), dtype=bool)

        # Efficiently loop over the faces using the quadtree search.
        for face in self.faces:
            # Get all the proper neighbors of the face.
            neighbors = filter(face.__ne__, self.quadtree.intersect(face.bbox))

            # Loop over the neighbors. Neighbor is deemed adjacent if they share more than two vertices (an edge).
            for neighbor in neighbors:
                vertex_intersection = numpy_vector_intersect(face.vertices, neighbor.vertices)
                self._adjacency_matrix[face.index, neighbor.index] = len(vertex_intersection) > 1

    def get_containing_face(self, point):
        """
            Return the face of the terrain which contains "point".
            Note: By contains this means that the 2D projection of the point lies within
                    the 2D projection of the face.
        :param point: An iterable of floats.
        :return: Face
        """
        target = Point(point)
        for face in self.quadtree.intersect(point):
            if target.within(face.polygon.exterior):
                raise ValueError(f'Point {point} is either a vertex or on the edge of polygon(s).')
            elif target.within(face.polygon):
                return face
        return None

    def get_member_faces(self, vertex):
        """
            Return a list of faces of which the vertex argument is a defining member of.
        :param vertex: The vertex. (1x3 ndarray
        :return: List of faces.
        """
        return [face for face in self.quadtree.intersect(vertex[:2]) if vertex in face.vertices]


class River(Object):
    """ Class for reading and unpacking .obj files, specifically those describing a river. """

    def __init__(self, obj_file):
        """
        :param obj_file: Path to a .obj file.
        """
        self.inner_vertices = None
        self.river_head = None
        self._adjacency_matrix_inner_vertices = None
        self._directed_graph = None
        super().__init__(obj_file)

    def unpack(self):
        """ Unpack the information from the .obj file. """
        super().unpack()
        self.construct_directed_graph()

    @property
    def adjacency_matrix_inner_vertices(self):
        return self._adjacency_matrix_inner_vertices

    @property
    def directed_graph(self):
        return self._directed_graph

    def _construct_adjacency_inner_vertices(self):
        """ Construct the adjacency matrix for the inner vertices of the terrain. """
        def get_adjacent_vertices(vertex_, face_):
            """ Return the adjacent vertices to vertex_ in face_ """
            try:
                index = np.where((face_.vertices == vertex_).all(axis=1))[0][0]
            except IndexError:
                # If the vertex is not found in the face (possibility due to bounding box) return empty list.
                return []
            try:
                return face_.vertices[index - 1], face_.vertices[index + 1]
            except IndexError:
                # If the vertex is the last of the list of vertices, then the first vertex is also adjacent.
                return face_.vertices[index - 1], face_.vertices[0]

        # Subset the inner vertices (these are the vertices with nonzero z-coordinates).
        inner_vertices_indexes = np.nonzero(self.vertices[:, 2] > 1e-6)
        self.inner_vertices = np.unique(self.vertices[inner_vertices_indexes], axis=0)

        # Construct an empty adjacency matrix for the inner vertices.
        vertices_count = self.inner_vertices.shape[0]
        self._adjacency_matrix_inner_vertices = np.zeros((vertices_count, vertices_count), dtype=bool)

        # Iterate over the vertices to populate the adjacency matrix.
        for vertex_index, vertex in enumerate(self.inner_vertices):
            for face in self.get_member_faces(vertex):
                for face_vertex in get_adjacent_vertices(vertex, face):
                    if (face_vertex[2] > 1e-6) and (not np.array_equal(face_vertex, vertex)):
                        face_vertex_index = np.where((self.inner_vertices == face_vertex).all(axis=1))[0][0]
                        self._adjacency_matrix_inner_vertices[vertex_index, face_vertex_index] = True

    def construct_directed_graph(self):
        """ Construct the directed graph of the river. """
        # Construct the adjacency matrix of the interior river points.
        self._construct_adjacency_inner_vertices()

        # Construct an empty matrix to serve as the directed graph.
        vertices_count = self.inner_vertices.shape[0]
        self._directed_graph = np.zeros((vertices_count, vertices_count), dtype=bool)

        # Initialize looping
        #   We assume the vertex of the head of the river is the vertex with maximum z-coordinate.
        head_vertex = self.inner_vertices[:, 2].argmax()
        self.river_head = self.inner_vertices[head_vertex]
        #   We create a LiFo queue for dealing with branches in the river.
        vertex_queue = queue.LifoQueue()
        vertex_queue.put(head_vertex)
        #   We create a visitation boolean array to avoid cycles.
        visited = np.zeros(vertices_count)

        # Loop over the vertices until the vertex queue is empty.
        while not vertex_queue.empty():
            # Pop a vertex out of the queue and mark it as visited.
            vertex = vertex_queue.get()
            visited[vertex] = 1

            # Gather all "upstream" vertices using the adjacency matrix and visitation boolean array.
            adjacency_vector = self.adjacency_matrix_inner_vertices[vertex]
            upstream_vertices = [vertex for vertex in np.where(adjacency_vector != 0)[0] if not visited[vertex]]

            # Indicate the current vertex as "downstream" of the "upstream" vertices and pop them on the queue.
            for upstream_vertex in upstream_vertices:
                self._directed_graph[upstream_vertex, vertex] = 1
                vertex_queue.put(upstream_vertex)

    def plot_river(self):
        """ Plot the directed graph. """
        lines = []
        for upstream_index, upstream_vertex in enumerate(self.inner_vertices):
            for downstream_index in np.where(self.directed_graph[upstream_index] != 0)[0]:
                lines.append([tuple(upstream_vertex[:2]), tuple(self.inner_vertices[downstream_index][:2])])

        fig, ax = pl.subplots()
        pl.scatter(self.river_head[0], self.river_head[1], c='y', s=50, marker='*', zorder=10)
        ax.add_collection(mc.LineCollection(lines, colors=[(0, 0, 1, 1)] * len(lines)))
        ax.autoscale()
        ax.margins(0.1)


class Terrain(Object):
    """ Class to hold all terrain information. """

    def __init__(self, terrain_file, river_file):
        """
        :param terrain_file: Path to the output terrain .obj file.
        :param river_file: Path to the output river .obj file.
        """
        self.river = River(river_file)
        super().__init__(terrain_file)


class RainFlow:
    """ Class for simulating the stepped rain flow process of an Object. """

    def __init__(self, obj_file, mesh_size, rainfall_rate):
        """
        :param obj_file: Path to a .obj file.
        :param mesh_size: Width of a cell in the square lattice (mesh) overlaid on the terrain.
        :param rainfall_rate: Numerical amount of rainfall that falls in each cell in each time step.
        """
        self.terrain = Object(obj_file)
        self.mesh_size = mesh_size
        self.mesh = None
        self.rainfall_rate = 1  # Placeholder, ideally want to pull this from NOAA data.

        self.setup()

    def __repr__(self):
        """ Prints out a string representation of the water level for each cell in the terrain. """
        bbox = self.terrain.bbox
        offset = self.mesh_size / 2
        str_output = ''

        for y in np.arange(bbox[1] + offset, bbox[3] + offset,self.mesh_size):
            str_output = '\n' + str_output
            for x in np.arange(bbox[0] + offset, bbox[2] + offset,self.mesh_size):
                face = self.terrain.get_containing_face([x,y])
                if face is None:
                    str_output = '-' + str_output
                else:
                    water_level = str(self.mesh[x][y]['current_water_level'])
                    str_output = water_level + str_output
        return str_output

    def setup(self):
        """ Initialize the mesh with constant water level in each cell. """
        mesh = {}
        bbox = self.terrain.bbox # Stored as (xmin,ymin,xmax,ymax).
        offset = self.mesh_size / 2  # Used for shifting reference point from corner to center of cell.

        for x in np.arange(bbox[0] + offset, bbox[2] + offset, self.mesh_size):
            y_hash = {}
            for y in np.arange(bbox[1] + offset, bbox[3] + offset, self.mesh_size):
                face = self.terrain.get_containing_face([x,y])

                # Only simulate points within the terrain.
                if face is None:
                    next

                x_downhill_neighbor = self.precision_round(x + (self.mesh_size * face.normal[0]), self.mesh_size / 2)
                y_downhill_neighbor = self.precision_round(y + (self.mesh_size * face.normal[1]), self.mesh_size / 2)
                downhill_neighbor_face = self.terrain.get_containing_face([x_downhill_neighbor, y_downhill_neighbor])

                if downhill_neighbor_face is None:  # Sink cell, likely next to a river.
                    y_hash[y] = {'current_water_level' : self.rainfall_rate,
                                  'next_water_level' : 0,
                                  'downhill_neighbor' : [x,y],
                                  'desc_dir' : face.normal}
                else:  # Interior cell
                    y_hash[y] = {'current_water_level' : self.rainfall_rate,
                                  'next_water_level' : 0,
                                  'downhill_neighbor' : [x_downhill_neighbor, y_downhill_neighbor],
                                  'desc_dir' : face.normal}
            mesh[x] = y_hash
        self.mesh = mesh
        return None

    def simulate(self, steps=5):
        """ Simulate the rain flow process for the given number of steps.
        :param steps: Number of steps to iterate the rain flow process.
        """
        for i in range(0, steps):
            for x in self.mesh.keys():
                for y in self.mesh[x].keys():
                    self.step_cell([x,y])

            for x in self.mesh.keys():
                for y in self.mesh[x].keys():
                    self.update_water_level([x,y])

    def precision_round(self, number, precision):
        """ Round number to nearest value at the given precision.
        :param number: Number to be rounded.
        :param precision: Precision to round number up or down toward.
        """
        return round(number / precision) * precision

    def step_cell(self, coordinates):
        """ Transfer the current water level of the given cell to its downhill neighbor's next water level.
        :param coordinates: (1x2) array of the xy coordinates of the cell to be updated.
        """
        neighbor = self.mesh[coordinates[0]][coordinates[1]]['downhill_neighbor']
        water_level = self.mesh[coordinates[0]][coordinates[1]]['current_water_level']
        self.mesh[neighbor[0]][neighbor[1]]['next_water_level'] += water_level

    def update_water_level(self, coordinates, rainfall=False):
        """ Move water from the given cell's next water level to its current water level.
        :param coordinates: (1x2) array of the xy coordinates of the cell to be updated.
        :param rainfall: A boolean that determines if all water levels are increased by a constant amount each step.
        """
        next_water_level = self.mesh[coordinates[0]][coordinates[1]]['next_water_level']
        self.mesh[coordinates[0]][coordinates[1]]['current_water_level'] = next_water_level
        self.mesh[coordinates[0]][coordinates[1]]['next_water_level'] = 0

        if rainfall:
            self.mesh[coordinates[0]][coordinates[1]]['current_water_level'] += next_water_level
