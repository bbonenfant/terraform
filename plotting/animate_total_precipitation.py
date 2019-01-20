#! /usr/bin/env python3
from os import path
import sys

# Hack in the path to sys.path to ensure the imports will work.
root_dir = path.dirname(path.dirname(__file__))
sys.path = [root_dir] + sys.path

from plotting.XPlot import *

weather_dir = path.join(root_dir, 'data', 'weather_data')
units_conversion = 0.0393701  # millimeters -> inches


def animate():
    """ Animate the total precipitation. """
    # Open and prepare the weather data.
    dataset = quiet_open_mfdataset(path.join(weather_dir, 'houston_precipitation', 'gfs*'))
    dataset.tp.data *= units_conversion
    dataset.tp.attrs['full_name'] = 'Total Precipitation'
    dataset.tp.attrs['units'] = 'precipitation in inches'

    # Animate
    XPlot(dataset, 'tp', accumulation=True, vmax=25).animate()


if __name__ == '__main__':
    animate()
