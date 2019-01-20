""" Classes for plotting xarray data. """
import logging

from matplotlib.animation import FuncAnimation
from mpl_toolkits.basemap import Basemap
from pandas import Timestamp
from pyproj import Geod

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr


class XPlot:
    """ Class to plot and animate xarray datasets. """

    def __init__(self, dataset, parameter, data_selection=None, accumulation=False, vmin=0, vmax=1):
        """
        :param dataset: An xarray.Dataset object with dimensions
                            time, latitude, and longitude.
        :param parameter: The name of the parameter to plot.
        :param data_selection: A dictionary of {dimension: slice}
        """
        self.dataset = dataset
        self.parameter = parameter
        self.selection = {} if data_selection is None else data_selection
        self.accumulation = accumulation
        self.vmin = vmin
        self.vmax = vmax

    def animate(self):
        """ Run the animation. """
        # Set the plot figure.
        figure, axes = plt.subplots(figsize=(8, 5))

        # Subset the dataset.
        animation_dataset = self.dataset.isel(self.selection)

        # Construct the Animator.
        animator = Animator(animation_dataset, self.parameter, figure, axes,
                            self.accumulation, self.vmin, self.vmax)

        # Construct the animation handler.
        _animation = FuncAnimation(figure, animator, init_func=animator.initialize,
                                   frames=len(animation_dataset.time), interval=500,
                                   repeat_delay=1000, blit=False)
        plt.show()


class Animator:
    """ Class to run the animation. """

    def __init__(self, dataset, parameter, figure, axes,
                 accumulation=False, vmin=0, vmax=1):
        """
        :param dataset: An xarray Dataset.
        :param parameter: The name of the parameter to animate.
        :param figure: The matplotlib Figure object.
        :param axes: The matplotlib Axes object corresponding to figure.
        """
        self.dataset = dataset
        self.parameter = parameter
        self.figure = figure
        self.axes = axes
        self.accumulation = accumulation
        self.vmin = vmin
        self.vmax = vmax

        self.array = np.asarray(self.dataset.get(self.parameter))
        self.parameter_name = self.dataset.get(self.parameter).full_name
        self.units = self.dataset.get(self.parameter).units
        self.dates = [Timestamp(date.data).to_pydatetime()
                      for date in self.dataset.time]
        self.lons, self.lats = np.meshgrid(self.dataset.longitude, self.dataset.latitude)
        self.max_frame = len(self.dataset.time)

        self.map = None
        self.quad = None
        self.initialized = False

    def initialize(self):
        """ This function is called first by function. Initializes the plot. """

        if not self.initialized:
            # Set the background map and title.
            self._set_map()
            self._set_title(0)

            # Initialize the mesh object to have zero value everywhere.
            self.quad = self.axes.pcolormesh(
                *self.map(self.lons, self.lats),
                np.zeros((self.lons.shape[0] - 1, self.lons.shape[1] - 1)),
                alpha=0.9, vmin=self.vmin, vmax=self.vmax, cmap='plasma',
            )

            # Add the color bar with label.
            colorbar = self.figure.colorbar(self.quad, ax=self.axes)
            colorbar.set_label(f'{self.units}', rotation=270, labelpad=15)

            # This MUST be called after the mesh object is updated or else the
            #   animation will not update.
            self.quad.changed()
            self.initialized = True

    def __call__(self, frame):
        """
            When FuncAnimation wants to update the animation, it calls this class
                with the current frame. This function updates the quad_mesh object
                with information for the animation's next frame.

        """
        print(f'Frame: {frame + 1} / {self.max_frame}')
        self._set_title(frame)
        if self.accumulation:
            self.quad.set_array(self.array[:frame + 1, :-1, :-1].sum(0).ravel())
        else:
            self.quad.set_array(self.array[frame, :-1, :-1].ravel())
        self.quad.changed()

    def _set_map(self, ellipse='WGS84'):
        """ Set the background map of the plot. """
        # Set the geodesic for geospatial calculations.
        geod = Geod(ellps=ellipse)

        # Calculate the width and height of the dataset (in meters)
        lower_left = self.dataset.latitude[0], self.dataset.longitude[0]
        lower_right = self.dataset.latitude[0], self.dataset.longitude[-1]
        upper_left = self.dataset.latitude[-1], self.dataset.longitude[0]
        _, __, dataweight = geod.inv(*reversed(lower_left), *reversed(lower_right))
        _, __, dataheight = geod.inv(*reversed(lower_left), *reversed(upper_left))

        # Get the center latitude and longitude of the set.
        lat_0 = np.median(self.dataset.latitude)
        lon_0 = np.median(self.dataset.longitude)

        # Construct the Basemap object.
        self.map = Basemap(
            width=dataweight * 1.5, height=dataheight * 1.5, resolution='l',
            projection='laea', lat_0=lat_0, lon_0=lon_0, ax=self.axes)

        # Draw in the superficial features with custom colors.
        self.map.drawlsmask(land_color="#ddaa66", ocean_color="#7777ff", grid=1.25)
        self.map.drawcoastlines(linewidth=0.75, color="#808080")
        self.map.drawrivers(color='#0000ff')
        self.map.drawcountries(linewidth=1.5)
        self.map.drawstates(linewidth=0.75)

    def _set_title(self, frame):
        """ Set the title depending on the frame. """
        if frame == 0:
            # Color the title green to indicate the first time step.
            color = 'g'
        else:
            # Otherwise color the title black.
            color = 'k'

        # Write the title.
        self.axes.set_title(f'{self.parameter_name}: {self.dates[frame]:%c}',
                            color=color, fontname='monospace',
                            fontsize='large', fontweight='demi')


def quiet_open_mfdataset(files):
    """ Quietly open gribs into an xarray Dataset. """
    logging.disable(logging.ERROR)
    dataset = xr.open_mfdataset(files, concat_dim='time', engine='cfgrib',
                                backend_kwargs={'indexpath': '', 'errors': 'ignore'})
    logging.disable(logging.NOTSET)
    return dataset
