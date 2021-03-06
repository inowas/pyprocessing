# -*- coding: utf-8 -*-
"""
Created on Fri May 20 11:43:26 2016

@author: aybulat
"""

import numpy as np
import matplotlib.path as mplPath
import intersector
#import matplotlib.pyplot as plt


def give_ibound(line, number_of_layers, nx, ny, xmin, xmax, ymin, ymax, boundary_value=1):
    """
    Function that finds if cells of a given grid are inside a given polygon.
    Returns an IBOUND - 2D array object, in which inner cells have values of '1' and outer have values of '0'
    Inner points defined using the matplotlib's mplPath function
    """
    # Convert input to floats
#    print line
    xmin = float(xmin)
    xmax = float(xmax)
    ymin = float(ymin)
    ymax = float(ymax)
    # Application of the 'line_area_intersect function to define cells intersected by the polygon
    area_line_cols, area_line_rows = intersector.line_area_intersect(line = line, xmax = xmax, xmin = xmin, ymax = ymax, ymin = ymin, nx = nx, ny = ny)
    # Domain definition
    ibound = np.zeros((int(number_of_layers), ny, nx), dtype=np.int32)
    x = np.linspace(xmin, xmax, nx)
    y = np.linspace(ymin, ymax, ny)

    bbPath = mplPath.Path(np.array(line[:-1]))

    for i in range(ny):
        for j in range(nx):
            cell_is_inside = bbPath.contains_point((x[j], y[i]))
            if cell_is_inside:
                ibound[:, i, j] = 1
#    print len(area_line_rows)
    for i in range(len(area_line_rows)):
        ibound[:, area_line_rows[i], area_line_cols[i]] = boundary_value
    # Rotete the array to 180 degrees to fit flopy IBOUND convention
    return np.rot90(ibound, 2)

#import matplotlib.pyplot as plt
snrow = 11
sncol = 11
snx, sny = sncol, snrow
sxmin, sxmax, symin, symax = 0., 400., 0., 400.
sline = [[0.,0.],[0.,300.],[400.,300.],[400.,0.],[0.,0.]]
snumber_of_layers = 1
i = give_ibound(sline, snumber_of_layers, snx, sny, sxmin, sxmax, symin, symax)
#plt.imshow(i[0], interpolation = 'nearest')
