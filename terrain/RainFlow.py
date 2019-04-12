import numpy as np


class RainFlow:
    """ Class for simulating the stepped rain flow process of an Object. """

    def __init__(self, terrain, mesh_size, rainfall_rate, river):
        """
        :param terrain: Object of the terrain.
        :param mesh_size: Width of a cell in the square lattice (mesh) overlaid on the terrain.
        :param rainfall_rate: Numerical amount of rainfall that falls in each cell in each time step.
        :param river: River object needed to accept water from river-adjacent cells in mesh.
        """
        self.terrain = terrain
        self.mesh_size = mesh_size
        self.mesh = None
        self.rainfall_rate = 1  # Placeholder, ideally want to pull this from NOAA data.
        self.river = river
        self.river_state = self.river.initial_state

        self._array_shape = tuple()

        self.setup()
        self.fix_cyclic_flow()

    def __repr__(self):
        """ Prints out a string representation of the water level for each cell in the terrain. """
        bbox = self.terrain.bbox
        offset = self.mesh_size / 2
        str_output = ''

        for y in np.arange(self.precision_round(bbox[1], self.mesh_size / 2) + offset,
                           self.precision_round(bbox[3], self.mesh_size / 2) + offset,
                           self.mesh_size):
            str_output = '\n' + str_output
            for x in np.arange(self.precision_round(bbox[0], self.mesh_size / 2) + offset,
                               self.precision_round(bbox[2], self.mesh_size / 2) + offset,
                               self.mesh_size):
                try:
                    face = self.terrain.get_containing_face([x, y])
                except ValueError:
                    str_output = ' ' + str_output
                    continue

                if face is None:
                    str_output = ' ' + str_output
                else:
                    water_level = str(self.mesh[round(x, 5)][round(y, 5)]['current_water_level'])
                    if water_level == '0':
                        str_output = '.' + str_output
                    else:
                        str_output = water_level + str_output
        return str_output

    @property
    def array_state(self):
        array = np.full(self._array_shape, np.nan)
        for y_hash in self.mesh.values():
            for mesh_point in y_hash.values():
                array[mesh_point['index']] = mesh_point['current_water_level']
        return array

    def setup(self):
        """ Initialize the mesh with constant water level in each cell. """
        mesh = {}
        mesh_precision = 5  # Prevents errors with precision of keys in the mesh
        bbox = self.terrain.bbox  # Stored as (xmin, ymin, xmax, ymax).
        offset = self.mesh_size / 2.0  # Used for shifting reference point from corner to center of cell.

        x_values = np.arange(
            self.precision_round(bbox[0], offset) + offset,
            self.precision_round(bbox[2], offset) + offset,
            self.mesh_size
        )
        y_values = np.arange(
            self.precision_round(bbox[1], offset) + offset,
            self.precision_round(bbox[3], offset) + offset,
            self.mesh_size
        )
        self._array_shape = (len(x_values), len(y_values))

        # Initialize points in mesh overlaid on the terrain.
        for x_index, x in enumerate(x_values):
            y_hash = {}
            for y_index, y in enumerate(y_values):
                # Do not create point if it falls on an edge of the terrain.
                try:
                    face = self.terrain.get_containing_face([x, y])
                except ValueError:
                    print(f"Cannot create point at (x,y) = ({x},{y}), leaving point out of the grid.")
                    continue

                # Only simulate points within the terrain.
                if face is None:
                    continue

                # Normalize (x,y) components of the normal vector.
                norm = np.linalg.norm([face.normal[0], face.normal[1]])

                # Just to prevent divide by zero errors in non-stalgo generated flat terrains.
                if norm == 0:
                    norm = 1
                normal = [-face.normal[0]/norm, -face.normal[1]/norm]

                # Set downhill neighbor as point in mesh nearest to the downhill displaced (x,y) point.
                x_downhill_neighbor = round(x + (self.mesh_size * round(normal[0])), mesh_precision)
                y_downhill_neighbor = round(y + (self.mesh_size * round(normal[1])), mesh_precision)

                # Catches error where a mesh point lies on an edge between faces.
                try:
                    downhill_neighbor_face = self.terrain.get_containing_face([x_downhill_neighbor, y_downhill_neighbor])
                # Error handling doesn't work for flat grids, as the downhill direction is the zero vector.
                except ValueError:
                    print(f"Downhill neighbor cell of ({x},{y}) falls on an edge, marking as sink cell.")
                    downhill_neighbor_face = None

                # Sink cell (associated with a single closest river node to transfer water into)
                if downhill_neighbor_face is None:
                    nearest_river_node_index = self.find_nearest_river_node_index((x, y))
                    y_hash[round(y, mesh_precision)] = {'current_water_level': self.rainfall_rate,
                                                        'next_water_level': 0,
                                                        'index': (x_index, y_index),
                                                        'downhill_neighbor': None,
                                                        'desc_dir': normal,
                                                        'sink_cell': True,
                                                        'nearest_river_node_index': nearest_river_node_index}
                # Interior cell
                else:
                    y_hash[round(y, mesh_precision)] = {'current_water_level': self.rainfall_rate,
                                                        'next_water_level': 0,
                                                        'index': (x_index, y_index),
                                                        'downhill_neighbor': (round(x_downhill_neighbor, mesh_precision),
                                                                              round(y_downhill_neighbor, mesh_precision)),
                                                        'desc_dir': normal,
                                                        'sink_cell': False,
                                                        'nearest_river_node_index': None}
            mesh[round(x, mesh_precision)] = y_hash
        self.mesh = mesh
        return None

    def path_to_river(self, coordinates, path=[]):
        """ Returns an ordered list of the coordinate path to the river for this node.
        :param coordinates: Ordered tuple of xy location of the cell in the grid to start the path at.
        :param path: (1 x n) List of 2-tuples of cell locations leading to a sink node. """
        path += [coordinates]
        path = list(dict.fromkeys(path))

        cell = self.mesh[coordinates[0]][coordinates[1]]
        if cell['sink_cell']:
            return path
        else:
            neighbor = cell['downhill_neighbor']
            return self.path_to_river(neighbor, path)

    def disconnect_cyclic_path_if_exists(self, coordinates, non_cyclic_cells, path=[]):
            """ Disconnects .
            :param coordinates: Tuple of coordinates to add to path of checked.
            :param non_cyclic_cells: List of non-cyclic (eventually terminating) cells in the grid.
            :param path: List of location tuples used to determine if a cycle has been reached. """
            cell = self.mesh[coordinates[0]][coordinates[1]]
            if cell['downhill_neighbor'] is None or coordinates in non_cyclic_cells:
                return
            else:
                if coordinates in path:
                    self.disconnect_cell(coordinates)
                    return
                else:
                    path += [coordinates]
                    neighbor = tuple(cell['downhill_neighbor'])
                    return self.disconnect_cyclic_path_if_exists(neighbor, non_cyclic_cells, path)

    def disconnect_cell(self, coordinates):
        """ Set the cell at the given coordinates to be a terminating river cell.
        :param coordinates: Tuple of location of cell to be marked as a river cell. """
        cell = self.mesh[coordinates[0]][coordinates[1]]
        if cell['downhill_neighbor'] is None:
            return
        else:
            cell['downhill_neighbor'] = None
            cell['nearest_river_node_index'] = self.find_nearest_river_node_index(coordinates)
            cell['sink_cell'] = True

    def fix_cyclic_flow(self):
        """ Disconnect the minimum number of cells to remove any cycles that keep water oscillating in the mesh. """
        visited = []
        for x in self.mesh.keys():
            for y in self.mesh[x].keys():
                # Skip already checked cells
                if (x, y) in visited:
                    continue

                # Disconnect the cell that is causing a cycle, if it exists.
                self.disconnect_cyclic_path_if_exists((x, y), visited)

                # Mark cell as visited
                visited += self.path_to_river((x, y))

                # Remove list duplicates
                visited = list(dict.fromkeys(visited))

    def simulate(self, steps=1):
        """ Simulate the rain flow process for the given number of steps.
        :param steps: Number of steps to iterate the rain flow process.
        """
        # Stop simulation if all water has drained out of the mesh
        for i in range(0, steps):
            if self.total_water_level() <= 0:
                return
            else:
                self.step_cells()

    def total_water_level(self):
        wl = 0
        for y in self.mesh.values():
            for x in y.values():
                wl += x['current_water_level']
        return wl

    @staticmethod
    def precision_round(number, precision):
        """ Round number to nearest value at the given precision. Convenient for mesh operations.
        :param number: Number to be rounded.
        :param precision: Precision to round number up or down toward.
        """
        return round(number / precision) * precision

    """ Simulate the rain flow process on the terrain for the given number of steps. """
    def step_cells(self):
        # Transfer cell's current_water_level to its neighbor's next_water_level
        for x in self.mesh.keys():
            for y in self.mesh[x].keys():
                self.step_cell([x, y])

        # Update cell's current_water_level to be it's next_water_level
        for x in self.mesh.keys():
            for y in self.mesh[x].keys():
                self.update_water_level([x, y])

    def step_cell(self, coordinates):
        """ If interior, transfer the current_water_level of the given cell to its downhill neighbor's next_water_level.
            If sink, transfer the current_water_level of the given cell to its closest river node.
        :param coordinates: (1x2) array of the xy coordinates of the cell to be updated.
        """
        cell = self.mesh[coordinates[0]][coordinates[1]]
        river_node_index = cell['nearest_river_node_index']
        if river_node_index is not None:
            # Transfer this cell's water to its nearest river node.
            self.river_state[river_node_index] += cell['current_water_level']
        else:
            # Transfer this cell's water to its downhill neighbor cell.
            neighbor = cell['downhill_neighbor']
            water_level = cell['current_water_level']
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

    def find_nearest_river_node_index(self, coordinates):
        """ Find the index of the closest river node to the mesh cell with the given coordinates.
        :param coordinates: (1x2) array of the xy coordinates of the mesh cell."""
        closest_river_node_index = 0
        closest_river_node = self.river.vertices[closest_river_node_index]
        closest_dist = np.linalg.norm(np.subtract([closest_river_node[0], closest_river_node[1]], coordinates))

        for river_node_index, river_node in enumerate(self.river.inner_vertices):
            current_dist = np.linalg.norm(np.subtract([river_node[0], river_node[1]], coordinates))
            if current_dist < closest_dist:
                closest_river_node = river_node
                closest_river_node_index = river_node_index
                closest_dist = current_dist

        return closest_river_node_index
