""" Classes for reading and unpacking .obj files. """
import numpy as np
from pyqtree import Index
from shapely.geometry import Point, Polygon


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


class River(Object):
    pass


class Terrain(Object):
    def __init__(self, terrain_file, river_file):
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
        #self.simulate()

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
            print(self.mesh)
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
