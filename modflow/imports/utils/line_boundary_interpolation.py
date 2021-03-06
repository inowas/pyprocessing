# -*- coding: utf-8 -*-
"""
Created on Fri May 20 16:20:24 2016

@author: aybulat
"""

"""
Modflow CHD line boundary module. Modflow CHD
"""

import intersector

def give_SPD(points, point_vals, line, stress_period_list, interract_layers, xmax, xmin, ymax, ymin, nx, ny, boundary_type, layers_botm = None, strt_head_mode = 'simple'):
    """
    Function interpolating given point values along on a grid along given line
    and returning Stress Period Data dictionary object
    """
    strt_head_mode_options = ['warmed_up', 'simple']
    if strt_head_mode not in strt_head_mode_options:
        print 'given stress period data write mode option is not supported, should be either "warmed_up" or "simple"'
        return
        
    xmin = float(xmin)
    xmax = float(xmax)
    ymin = float(ymin)
    ymax = float(ymax)
    
    # Definition of the cells intersected by a line boundary and by observation points
    line_cols, line_rows = intersector.line_area_intersect(line, xmax, xmin, ymax, ymin, nx, ny)
    point_cols, point_rows = [],[]
    # Reversing rows upside down due to flopy error
    line_rows_reversed = [(ny-1) - i for i in line_rows]

    # Columns and rows of the observation points
    for point in points:
        point_cols.append(int((point[0] - xmin)/(xmax - xmin) * nx)  if point[0] < xmax else nx - 1)
        point_rows.append(int((point[1] - ymin)/(ymax - ymin) * ny)  if point[1] < ymax else ny - 1)

    # Create a list of line cell values in which cells under points inherit their values and others beckome None
    def interpolate_property(stress_period_list,line_cols,line_rows,point_cols,point_rows,point_vals):        
        list_of_values = []
        for period in stress_period_list:
            list_of_values_single_timestep = []
            for line_idx in range(len(line_cols)):
                for point_idx in range(len(point_cols)):
                    if line_cols[line_idx] == point_cols[point_idx] and line_rows[line_idx] == point_rows[point_idx]:
                        list_of_values_single_timestep.append(point_vals[point_idx][period])
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
        return list_of_values
    
    if 'hh' in point_vals:
        point_head_vals = point_vals['hh']
        list_of_head_values = interpolate_property(stress_period_list,
                                                   line_cols,line_rows,
                                                   point_cols,point_rows,
                                                   point_head_vals)
        # Checking if the boundary head cells will become dry due to low specified head.
        # If so, layer removed from the interracted layers list
        n_removed_layers = 0                                      
        for idx, layer in enumerate(layers_botm):
            for period in stress_period_list:
                for i in range(len(line_cols)):
                    cell_botm_elevation = layer[line_rows_reversed[i]][line_cols[i]] if type(layer) == list else layer
                    if list_of_head_values[period][i] <= cell_botm_elevation:
                        del interract_layers[idx - n_removed_layers]
                        n_removed_layers += 1
                        break
                break

    if 'rs' in point_vals:
        point_stage_vals = point_vals['rs']
        list_of_stage_values = interpolate_property(stress_period_list,
                                                    line_cols,line_rows,
                                                    point_cols,point_rows,
                                                    point_stage_vals)
    if 'rbc' in point_vals:
        point_conductance_vals = point_vals['rbc']
        list_of_conductance_values = interpolate_property(stress_period_list,
                                                          line_cols,line_rows,
                                                          point_cols,point_rows,
                                                          point_conductance_vals)
    if 'eb' in point_vals:
        point_elevation_vals = point_vals['eb']
        list_of_elevation_values = interpolate_property(stress_period_list,
                                                        line_cols,line_rows,
                                                        point_cols,point_rows,
                                                        point_elevation_vals)


    if boundary_type == 'CHB':
        # Writing CHD Stress Period Data dictionary
        if strt_head_mode == 'simple':
            CHD_stress_period_data = {}
            for period in stress_period_list:
                SPD_single = []
                for lay in interract_layers:
                    for i in range(len(line_cols)):
                        # For periods except the last one head at begining and end vary
                        if period != stress_period_list[-1]:
                            SPD_single.append([lay, line_rows_reversed[i], line_cols[i],
                                               list_of_head_values[period][i],
                                               list_of_head_values[period + 1][i]])
                        else:
                            SPD_single.append([lay, line_rows_reversed[i],
                                               line_cols[i], list_of_head_values[period][i],
                                               list_of_head_values[period][i]])
                        CHD_stress_period_data[period] = SPD_single

        elif strt_head_mode == 'warmed_up':
            CHD_stress_period_data = {}
            for period in stress_period_list:
                SPD_single = []
                for lay in interract_layers:
                    for i in range(len(line_cols)):
                        # For periods except the last one head at begining and end vary
                        if period != stress_period_list[-1]:
                            SPD_single.append([lay, line_rows_reversed[i], line_cols[i],
                                               list_of_head_values[period][i],
                                               list_of_head_values[period + 1][i]])
                        else:
                            SPD_single.append([lay, line_rows_reversed[i], line_cols[i],
                                               list_of_head_values[period][i],
                                               list_of_head_values[period][i]])
                        if len(CHD_stress_period_data) == 0:
                            CHD_stress_period_data[period] = SPD_single
                        CHD_stress_period_data[period + 1] = SPD_single
        else:
            print 'given strt_mode is not supported'
            return
            
    elif boundary_type == 'RIV':
        if strt_head_mode == 'simple':
            CHD_stress_period_data = {}
            for period in stress_period_list:
                SPD_single = []
                for i in range(len(line_cols)):
                        # For periods except the last one head at begining and end vary
                        SPD_single.append([0, line_rows_reversed[i], line_cols[i],
                                           list_of_stage_values[period][i],
                                           list_of_conductance_values[period][i],
                                           list_of_elevation_values[period][i]])
                        CHD_stress_period_data[period] = SPD_single

        elif strt_head_mode == 'warmed_up':
            CHD_stress_period_data = {}
            for period in stress_period_list:
                SPD_single = []
                for i in range(len(line_cols)):
                    # For periods except the last one head at begining and end vary
                    SPD_single.append([0, line_rows_reversed[i], line_cols[i],
                                       list_of_stage_values[period][i],
                                       list_of_conductance_values[period][i],
                                       list_of_elevation_values[period][i]])
                    if len(CHD_stress_period_data) == 0:
                        CHD_stress_period_data[period] = SPD_single
                    CHD_stress_period_data[period + 1] = SPD_single
       
        else:
            print 'given strt_mode is not supported'
            return
#    for i in CHD_stress_period_data:
#        print len(CHD_stress_period_data[i])

    return CHD_stress_period_data
