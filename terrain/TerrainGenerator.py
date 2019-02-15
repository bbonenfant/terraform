import cv2
import pymesh
import imutils
import subprocess
import numpy as np
from lxml import etree
from os import path, sep
from matplotlib.path import Path
from datetime import datetime
from shapely.geometry import Polygon

from terrain.Object import Terrain
from utilities.timing import TimingDict


class TerrainGenerator:
    """ Class for generating terrain from a ipe file with the outline of a river. """

    _blender_script = path.join(path.dirname(__file__), 'blender_script.py')
    _data_directory = path.join(path.dirname(__file__), 'data')

    _contour_image = path.join(_data_directory, 'contour.png')
    _river_file = path.join(_data_directory, 'river.ipe')
    _river_out_file = path.join(_data_directory, 'river_out.ipe')
    _terrain_file = path.join(_data_directory, 'terrain.off')
    _subset_river_file = path.join(_data_directory, 'river_subset.obj')
    _subset_terrain_file = path.join(_data_directory, 'terrain_subset.obj')
    _simplified_river_file = path.join(_data_directory, 'simplified_river_subset.obj')
    _simplified_terrain_file = path.join(_data_directory, 'simplified_terrain_subset.obj')

    _timing_data = TimingDict()

    def __init__(self, river_trace_image=None, ipe_file=None, terrain_maximum_height=0.015, terrain_slope=0.200,
                 stalgo_executable=None, blender_executable=None):
        """
        :param river_trace_image: Path to a image from the USGS Streamer web app which traces a river.
        :param ipe_file: Path to a .ipe file to be used as the input to STALGO.
                            Can be used in place of a "river trace image".
        :param terrain_maximum_height: Maximum terrain height generated by STALGO.
        :param terrain_slope: Slope used by STALGO.
        :param stalgo_executable: Path to the STALGO executable.
        :param blender_executable: Path to blender executable.
        """
        # Some basic safety checks.
        assert river_trace_image is not None or ipe_file is not None, \
            'Must supply one of "river_trace_image" or "ipe_file"'
        if river_trace_image is not None:
            if not path.isfile(river_trace_image):
                raise FileNotFoundError(river_trace_image)
        else:
            if not path.isfile(ipe_file):
                raise FileNotFoundError(ipe_file)

        self.trace_image = river_trace_image
        self.ipe_file = ipe_file
        self.max_height = terrain_maximum_height
        self.slope = terrain_slope

        # Default locations of the STALGO and Blender executables.
        self.stalgo = stalgo_executable if stalgo_executable is not None else 'stalgo'
        self.blender = blender_executable if blender_executable is not None else \
            path.join(sep, 'Applications', 'Blender', 'blender.app', 'Contents', 'MacOS', 'blender')

        self.river_vertices = None
        self.terrain = None

    def run(self):
        """ Generate the terrain file and construct the terrain object. """
        self._timing_data.put('total_time')

        # Generate an .ipe file from the river trace file.
        if self.trace_image is not None:
            self.river_vertices = self.draw_polygon(self.trace_image)
            self.write_ipe()

            # Run Stalgo and simplify the output.
            self.execute_stalgo(self.stalgo, self._river_file, self.max_height, self.slope)
        else:
            self.execute_stalgo(self.stalgo, self.ipe_file, self.max_height, self.slope)

        self._subset_mesh()
        self._simplify_mesh(self._subset_terrain_file, self._simplified_terrain_file)
        self._simplify_mesh(self._subset_river_file, self._simplified_river_file)

        # Construct the terrain object.
        self.terrain = self._timing_data.time('terrain_creation', Terrain,
                                              self._simplified_terrain_file, self._simplified_river_file)

        # Print the timing data.
        self._timing_data.total_time.time()

        print('\nTiming Data:\n\t{}'.format("\n\t".join(str(self._timing_data).split('\n'))))

    @classmethod
    @_timing_data.time('contour_river')
    def draw_polygon(cls, river_trace_image):
        """
            Using the input 1D river trace from USGS Streamer web-app: https://txpub.usgs.gov/DSS/streamer/web/
        :param river_trace_image: Path to an image of the river trace.
        :return: Return an (Nx2) ndarray defining a polygon.
        """

        # noinspection PyUnusedLocal
        def show(image, image_name):
            """ Small function useful for debugging. Used to show an image using CV. """
            cv2.namedWindow(image_name, cv2.WINDOW_NORMAL)      # Create a window.
            cv2.imshow(image_name, image)                       # Show the image in that window.
            key = cv2.waitKey(0)                                # Create a callback for exiting the window.
            if key == 27:                                       # Set the escape key as the exit window key.
                cv2.destroyAllWindows()

        # Read the image into OpenCV.
        river = cv2.imread(river_trace_image)

        # Cast to gray-scale and get a bit mask of the trace (collect all the pixels that are red).
        river_gray = cv2.cvtColor(river, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(river_gray, 127, 255, 0)

        # Use OpenCV to find the contours and then use the imutils library to unpack the OpenCV results.
        contour_package = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contour_package)

        # The contours will be an array. We assume that the river is the last contour
        #   (the rectangular outline of the entire image will also be included in this array).
        #   The contour will be an array of points which are a "sampling" of an outline.
        river_contour = contours[-1]

        # Get the perimeter of the contour and then approximate a polygon of the contour.
        #   epsilon: This is an tolerance value for how far the polygon edge can deviate from the contour points.
        perimeter = cv2.arcLength(river_contour, True)
        polygon = cv2.approxPolyDP(river_contour, epsilon=(1e-4 * perimeter), closed=True)

        # Draw the contours and polygon onto the original image and save to file.
        cv2.drawContours(river, [river_contour], -1, (0, 255, 0), 3)
        cv2.drawContours(river, [polygon], -1, (255, 0, 0), 3)
        cv2.imwrite(cls._contour_image, river)

        # The polygon array that OpenCV returns has shape (<number-of-vertices>, 1, 2).
        #   We flatten the inner dimension to get an array of shape (<number-of-vertices>, 2)
        flattened_polygon = polygon.reshape(polygon.shape[0:3:2])

        return flattened_polygon

    def write_ipe(self):
        """ Write the polygon to a .ipe file. """
        # Create the root of the .ipe (xml) file.
        river = etree.Element('ipe', version="70206", creator="Ipe 7.2.9")

        # We copy the general structure of the .ipe files that STALGO outputs.
        _info = etree.SubElement(
            river, 'info', created=f"D:{datetime.now():%Y%m%d%H%M%S}", modified=f"D:{datetime.now():%Y%m%d%H%M%S}")
        style = etree.SubElement(river, 'ipestyle', name="stalgo")
        _pen = etree.SubElement(style, 'pen', name="heavier", value="0.8")
        page = etree.SubElement(river, 'page')
        _polychains_layer = etree.SubElement(page, 'layer', name='polychains')
        group = etree.SubElement(page, 'group', layer='polychains')
        group_path = etree.SubElement(group, 'path', stroke="black", pen="heavier")

        # We construct the text list vertices which define the polygon.
        #   The first vertices is appended by 'm' and the rest are appended by 'l'.
        #   The first vertex is the same as the last vertex.
        first_vertex = self.river_vertices[0]
        path_text = f'\n{first_vertex[0]} {first_vertex[1]} m\n'
        for vertex in self.river_vertices[1:]:
            path_text += f'{vertex[0]} {vertex[1]} l\n'
        path_text += f'{first_vertex[0]} {first_vertex[1]} l\n'
        group_path.text = path_text

        # We need to use lxml here to pretty-print the xml. STALGO requires this formatting for parsing the .ipe file.
        with open(self._river_file, 'wb') as fout:
            fout.write(etree.tostring(river, encoding='UTF-8', xml_declaration=True, pretty_print=True))

    @staticmethod
    @_timing_data.time('run_stalgo')
    def execute_stalgo(stalgo_executable, ipe_file, terrain_maximum_height, terrain_slope,
                       terrain_out_file=_terrain_file, ipe_out_file=_river_out_file):
        """
            Run STALGO.
        :param stalgo_executable: Path to the STALGO executable.
        :param ipe_file: Path to the ipe file with the outline of a river.
        :param terrain_maximum_height: Maximum terrain height generated by STALGO.
        :param terrain_slope: Slope used by STALGO.
        :param terrain_out_file: Path to the output the terrain (.off) file.
        :param ipe_out_file: Path to output the .ipe file after being rescaled by STALGO.
        """
        subprocess.run((f'{stalgo_executable} --sk '
                        f'--input {ipe_file} --output-ipe7 {ipe_out_file} '
                        f'--output-terrain {terrain_out_file} '
                        f'--output-terrain-maxheight {terrain_maximum_height} '
                        f'--output-terrain-slope {terrain_slope}').split())

    @_timing_data.time('simplify_mesh')
    def _simplify_mesh(self, input_file, output_file):
        """ Run a blender script to simplify and merge the polygons of the mesh. """
        subprocess.run((f'{self.blender} -b -P {self._blender_script} -- '
                        f'--input {input_file} --output {output_file}').split())

    def _subset_mesh(self):
        """ Subset the STALGO output mesh by removing the river and points outside of the offset. """
        # Get the total mesh and the river polygon.
        mesh = self._timing_data.time('load_mesh', pymesh.load_mesh, self._terrain_file)
        river = self.get_river_polygon()

        # Collect all the vertices whose projection onto the XY plane are *strictly* within the river polygon.
        #   The buffer of 0.001 gives the vertices some thickness which is needed due to floating point error
        #     i.e. collect all vertices such that a ball of radius 0.001 centered at the vertex is entirely contained
        #     within the polygon.
        self._timing_data.put('matplotlib_river')
        river_path = Path(list(river.exterior.coords)[:-1])
        terrain_vertices = np.logical_not(river_path.contains_points(mesh.vertices[:, :2], radius=-0.0001))
        self._timing_data.matplotlib_river.time()

        terrain_faces = np.all(terrain_vertices[mesh.faces], axis=1)
        mesh_terrain_faces = np.arange(mesh.num_faces, dtype=int)[terrain_faces]
        mesh_river_faces = np.array([n for n in np.arange(mesh.num_faces, dtype=int) if n not in mesh_terrain_faces])

        # Subset the original mesh, only keeping the selected faces.
        subset_terrain = self._timing_data.time('subset_terrain', pymesh.submesh, mesh, mesh_terrain_faces, 0)
        subset_river = self._timing_data.time('subset_river', pymesh.submesh, mesh, mesh_river_faces, 0)

        # Save to file.
        pymesh.save_mesh(filename=self._subset_terrain_file, mesh=subset_terrain)
        pymesh.save_mesh(filename=self._subset_river_file, mesh=subset_river)

    @_timing_data.time('construct_river_polygon')
    def get_river_polygon(self):
        """ Construct a Polygon from the vertices of the river that are extracted from the ipe file. """
        # Extract the river layer from the ipe file.
        river = self._extract_layer('polychains').find('path')

        # Scape the xml text for the points and construct a (Nx2) numpy array.
        point_list = river.text.replace('m', '').replace('l', '').split()
        vertices = np.array([[float(start), float(end)] for start, end in zip(*[iter(point_list)] * 2)])

        # Translate and scale the coordinates to their original state.
        vertices = self.rescale_from_ipe(vertices)

        return Polygon(vertices)

    def _extract_layer(self, layer_name):
        """
            Extract the layer corresponding with layer_name from ipe_file.
        :param layer_name: The name of the layer to be extracted.
        :return: Xml Element instance.
        """
        tree = etree.parse(self._river_out_file)
        page = tree.getroot().find('page')
        return next(group for group in page.findall('group') if group.attrib['layer'] == layer_name)

    @staticmethod
    def rescale_from_ipe(points, translation_vector=(300, 450), scale_factor=200):
        """
            Rescale and translate points from the ipe file.
            STALGO translates and scales the points by (300, 450) and 200 respectively so that
              the image can be seen in the IPE app. We need undo this to line up with the terrain mesh.
        :param points: Array of points from an ipe file.
        :param translation_vector: The vector that was used to spatially translate the ipe points.
        :param scale_factor: The fact that was used to scale up the ipe points.
        :return: Scaled and translated ndarray of points.
        """
        return (np.asarray(points) - np.asarray(translation_vector)) / scale_factor
