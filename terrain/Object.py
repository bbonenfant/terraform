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
        self._initial_state = None
        self._center_adjacency = None
        self._directed_graph = None
        self._distance_matrix = None
        self._flow_matrix = None
        super().__init__(obj_file)

    def unpack(self):
        """ Unpack the information from the .obj file. """
        super().unpack()
        self.construct_directed_graph()
        self.construct_flow_matrix()

    @property
    def center_adjacency(self):
        return self._center_adjacency

    @property
    def directed_graph(self):
        return self._directed_graph

    @property
    def distance_matrix(self):
        return self._distance_matrix

    @property
    def flow_matrix(self):
        """ The flow matrix is the private _flow_matrix scaled by the velocity. """
        id_matrix = np.identity(self._flow_matrix.shape[0])
        scaled_flow = id_matrix - (self.velocity * (id_matrix - self._flow_matrix))
        if (not np.all(scaled_flow >= 0)) or (not np.all(scaled_flow <= 1)):
            raise ValueError("The flow matrix has either elements greater than 1 or less than zero. "
                             "This indicates that the velocity value was not valid.")
        return scaled_flow

    @property
    def initial_state(self):
        if (self._initial_state is None) and (self.distance_matrix is not None):
            self._initial_state = np.sum(self.distance_matrix, axis=1)
        return self._initial_state

    @property
    def offset_vector(self):
        """ The offset vector needed to "fill up" this source nodes. """
        return (self.flow_matrix @ self.initial_state) - self.initial_state

    @property
    def velocity(self):
        """ This is a placeholder. This sets the velocity within the threshold to produce a valid flow matrix. """
        return 1 / abs(10 * np.min(self._flow_matrix))

    def _construct_center_adjacency(self):
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
        self._center_adjacency = np.zeros((vertices_count, vertices_count), dtype=bool)
        self._distance_matrix = np.zeros((vertices_count, vertices_count), dtype=float)

        # Iterate over the vertices to populate the adjacency matrix.
        for vertex_index, vertex in enumerate(self.inner_vertices):
            for face in self.get_member_faces(vertex):
                for face_vertex in get_adjacent_vertices(vertex, face):
                    if (face_vertex[2] > 1e-6) and (not np.array_equal(face_vertex, vertex)):
                        face_vertex_index = np.where((self.inner_vertices == face_vertex).all(axis=1))[0][0]
                        self._center_adjacency[vertex_index, face_vertex_index] = True
                        self._distance_matrix[vertex_index, face_vertex_index] = np.linalg.norm(vertex - face_vertex)

    def construct_directed_graph(self):
        """ Construct the directed graph of the river. """
        # Construct the adjacency matrix of the interior river points.
        self._construct_center_adjacency()

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
            adjacency_vector = self.center_adjacency[vertex]
            upstream_vertices = [vertex for vertex in np.where(adjacency_vector != 0)[0] if not visited[vertex]]

            # Indicate the current vertex as "downstream" of the "upstream" vertices and pop them on the queue.
            for upstream_vertex in upstream_vertices:
                self._directed_graph[upstream_vertex, vertex] = 1
                vertex_queue.put(upstream_vertex)

        if len([row for row in self.directed_graph if np.array_equal(row, np.zeros(vertices_count))]) != 1:
            # If any rows besides the sink row are zero vectors, then this indicates that the algorithm did not
            #   reach the corresponding node, so raise RuntimeError.
            raise RuntimeError(f'A connected graph was not constructed.')

    def construct_flow_matrix(self):
        """ Construct the flow matrix. """

        def complete_cross(row_index_, column_index_):
            """ Complete the row and column of the Flow Matrix associated with row_index_, column_index_"""
            # We remove the np.nan value to obtain a valid dot product.
            self._flow_matrix[row_index_, column_index_] = 0
            dot_product = self._flow_matrix[row_index_] @ self.initial_state
            if dot_product == 0:
                # If the dot product is zero, we assume that this row corresponds to a source node.
                percent_flow = 1 / self.initial_state[row_index_]
            else:
                # Else we calculate the percent flow as usual.
                percent_flow = dot_product / self.initial_state[row_index_]
            # Fill in the (zeroed) undetermined value with (1 - {percent flow}) [The percent that did not flow]
            self._flow_matrix[row_index_, column_index_] = 1 - percent_flow

            # Now we fill the np.nan element in the column with the percent flow value.
            undetermined_column_elements = np.where(np.isnan(self._flow_matrix[:, column_index_]))[0]
            if undetermined_column_elements.size == 1:
                # assert len(undetermined_column_elements) == 1, \
                #     f"Expected only one undetermined element in the row. Found: {len(undetermined_column_elements)}"
                new_row_index = undetermined_column_elements[0]
                self._flow_matrix[new_row_index, column_index_] = percent_flow

        # The nonzero values of the flow matrix will be the same as those of the directed graph, so we copy this
        #   matrix, replacing the nonzero values with np.nan values to indicate an unfilled value.
        self._flow_matrix = self._directed_graph.astype(float).transpose() + np.identity(self._directed_graph.shape[0])
        self._flow_matrix[np.nonzero(self._flow_matrix)] = np.nan

        # Get a list of rows all rows. These will be removed from the list once they are filled.
        undetermined_rows = list(range(self._flow_matrix.shape[0]))

        # Loop over all the rows until they are all filled. Note, this is not the fastest way to do this,
        #   Most likely a recursive strategy would be faster, but this is the simplest to implement.
        while undetermined_rows:
            rows_to_delete = []
            for row_index in undetermined_rows:
                undetermined_row_elements = np.where(np.isnan(self._flow_matrix[row_index]))[0]
                # If a row has only one element with np.nan, then there is enough information for this row to be filled.
                if len(undetermined_row_elements) == 1:
                    column_index = undetermined_row_elements[0]
                    complete_cross(row_index, column_index)
                    rows_to_delete.append(row_index)
            for row in rows_to_delete:
                undetermined_rows.remove(row)

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
