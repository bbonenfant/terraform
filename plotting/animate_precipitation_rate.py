#! /usr/bin/env python3
from os import path
import sys

# Hack in the path to sys.path to ensure the imports will work.
root_dir = path.dirname(path.dirname(__file__))
sys.path = [root_dir] + sys.path

from plotting.XPlot import *

weather_dir = path.join(root_dir, 'data', 'weather_data')
units_conversion = 141.732  # millimeters per second -> inches per hour


def animate():
    """ Animate the precipitation rate. """
    # Open and prepare the weather data.
    dataset = quiet_open_mfdataset(path.join(weather_dir, 'houston_rate', 'gfs*'))
    dataset.prate.data *= units_conversion
    dataset.prate.attrs['full_name'] = 'Precipitation Rate'
    dataset.prate.attrs['units'] = 'inches per hour'

    # Animate
    XPlot(dataset, 'prate').animate()


if __name__ == '__main__':
    animate()
