# -*- coding: utf-8 -*-
"""
Created on Fri May 20 16:20:24 2016

@author: aybulat
"""

"""
Modflow CHD line boundary module. Modflow CHD
"""

import intersector

def give_SPD(points, point_vals, line, stress_period_list, interract_layers, xmax, xmin, ymax, ymin, nx, ny, layers_botm = None):
    """
    Function interpolating given point values along on a grid along given line 
    and returning Stress Period Data dictionary object
    """
    # Definition of the cells intersected by a line boundary and by observation points
    line_cols, line_rows = intersector.line_area_intersect(line, xmax, xmin, ymax, ymin, nx, ny)
    point_cols, point_rows = [],[]

    # Columns and rows of the observation points
    for point in points:
        point_cols.append(int((point[0] - xmin)/(xmax - xmin) * nx)  if point[0] < xmax else nx - 1)
        point_rows.append(int((point[1] - ymin)/(ymax - ymin) * ny)  if point[1] < ymax else ny - 1)

    # Create a list of line cell values in which cells under points inherit their values and others beckome None
    list_of_values = []
    for period in stress_period_list:
        list_of_values_single_timestep = []
        for line_idx in range(len(line_cols)):
            for point_idx in range(len(point_cols)):
                if line_cols[line_idx] == point_cols[point_idx] and line_rows[line_idx] == point_rows[point_idx]:
                    list_of_values_single_timestep.append(point_vals[period][point_idx])
                else:
                    list_of_values_single_timestep.append(None)
        
        # Fill the None values with distance - weighted average of closest not-None cells
        for i in range(len(list_of_values_single_timestep)):
            if list_of_values_single_timestep[i] is None:
                j = 1
                l = 1
                k = list_of_values_single_timestep[i] # Backward value
                m = list_of_values_single_timestep[i] # Forward value
                while m is None:
                    m = list_of_values_single_timestep[i - l] 
                    l += 1
                while k is None:
                    k = list_of_values_single_timestep[i + j] if (i + j) < len(list_of_values_single_timestep) else list_of_values_single_timestep[(i + j - len(list_of_values_single_timestep))]
                    j += 1
                # Interpolating values using IDW method
                list_of_values_single_timestep[i] = (m * 1./(l-1) + k * 1./(j-1))/(1./(j-1) + 1./(l-1))
        # Write resulting values lists for every time step
        list_of_values.append(list_of_values_single_timestep)
    
    # Reversing rows upside down due to flopy error
    line_rows_reversed = [(ny-1) - i for i in line_rows]

    # Checking if the boundary cells will become dry due to low specified head. If so, layer removed from the interracted layers list
    for idx, layer in enumerate(layers_botm):
        for period in stress_period_list:
            for i in range(len(line_cols)):
                cell_botm_elevation = layer[line_rows[i], line_cols[i]] if type(layer) == list else layer
                if list_of_values[period][i] <= cell_botm_elevation:
                    del interract_layers[idx]
                    break
            break

    
    # Writing CHD Stress Period Data dictionary    
    CHD_stress_period_data = {}
    for period in stress_period_list:
        SPD_single = []
        for lay in interract_layers:
            for i in range(len(line_cols)):
                # For periods except the last one head at begining and end vary
                if period != stress_period_list[-1]:
                    SPD_single.append([lay, line_rows_reversed[i], line_cols[i], list_of_values[period][i], list_of_values[period + 1][i]])
                else:
                    SPD_single.append([lay, line_rows_reversed[i], line_cols[i], list_of_values[period][i], list_of_values[period][i]])
                CHD_stress_period_data[period] = SPD_single
    
    return CHD_stress_period_data
