# -*- coding: utf-8 -*-
"""
Created on Fri May 20 15:02:33 2016

@author: aybulat
"""

import numpy as np

def line_area_intersect(line, xmax, xmin, ymax, ymin, nx, ny):
    """
    Function returning lists of rows and columns of a given grid intersected by a given line
    Is a modification of a Bresenham's algorithm https://en.wikipedia.org/wiki/Bresenham's_line_algorithm 
    """
    line_cols = []
    line_rows = []
    dx = (xmax - xmin)/nx
    dy = (ymax - ymin)/ny
    #Converting line values to floats
    for i, point in enumerate(line):
        for j, xy in enumerate(point):
            line[i][j] = float(xy)
    # Line is divided into segments operation is repeated for each. 
    for segment in range(len(line) - 1):
        strt_x = line[segment][0]
        end_x = line[segment + 1][0]
        strt_y = line[segment][1]
        end_y = line[segment + 1][1]

        strt_col = int((strt_x - xmin)/(xmax - xmin) * (nx)) if strt_x < xmax else nx - 1
        end_col = int((end_x - xmin)/(xmax - xmin) * (nx)) if end_x < xmax else nx - 1
        strt_row = int((strt_y - ymin)/(ymax - ymin) * (ny)) if strt_y < ymax else ny - 1 
        end_row = int((end_y - ymin)/(ymax - ymin) * (ny)) if end_y < ymax else ny - 1

        steep = abs(strt_y - end_y) >= abs(strt_x - end_x)
        # If segment is steep turn the domain to 90 degrees
        if steep:
            strt_y, strt_x = strt_x, strt_y
            end_y, end_x = end_x, end_y
            strt_col, strt_row = strt_row, strt_col
            end_col, end_row = end_row, end_col
            dy, dx = dx, dy
            xmin, ymin = ymin, xmin
        # Calculate the segments function parameters
        slope = (end_y - strt_y)/(end_x - strt_x)  
        upwards = abs(strt_y) <= abs(end_y)
        forward = abs(strt_x) <= abs(end_x)
        # Find first border coordinates (bx, by) of the grid
        strt_bx = xmin + (strt_col + 1) * dx if forward else xmin + (strt_col) * dx
        strt_by = ymin + (strt_row + 1) * dy if upwards else ymin + (strt_row) * dy
        segment_rows = [strt_row]
        segment_cols = [strt_col]
        j = 0
        # Appending cells intersected by the segment to segment_rows, cols 
        for i in range(abs(end_col - strt_col)):
            y = strt_y + slope * (strt_bx + dx * i - strt_x) if forward else strt_y + slope * (strt_bx - dx * i - strt_x)
            crossed = y >= strt_by + dy * j if upwards else y <= strt_by - dy * j
            if crossed:
                col = strt_col + i if forward else strt_col - i
                segment_cols.append(col)
                col = strt_col + (i + 1) if forward else strt_col - (i + 1) 
                segment_cols.append(col)
                row = strt_row + (j + 1) if upwards else strt_row - (j + 1)
                segment_rows.append(row)
                segment_rows.append(row)
                j += 1
            else:
                col = strt_col + (i + 1) if forward else strt_col - (i + 1)
                segment_cols.append(col)
                row = strt_row + j if upwards else strt_row - j
                segment_rows.append(row)
        # Check if the ending cell is in the list, otherwise append it
        if segment_rows[-1] != end_row or segment_cols[-1] != end_col:
            segment_cols.append(end_col)
            segment_rows.append(end_row)
        # Transformation of the domain back
        if steep:
            segment_cols, segment_rows = segment_rows, segment_cols
            xmin, ymin = ymin, xmin
            dx, dy = dy, dx
        # Append segment's cells to the line's cells lists
        if segment == 0:
            line_cols += segment_cols
            line_rows += segment_rows
        else:
            line_cols += segment_cols[1:]
            line_rows += segment_rows[1:]

    return np.array(line_cols), np.array(line_rows)