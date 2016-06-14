# -*- coding: utf-8 -*-
"""
Created on Thu May 19 14:24:38 2016

@author: aybulat

This is script for running a service for preprocessing input data, execution
of a Modflow model and postprocessing results.
Service's module structure: main.py/imports/model.py
                                           /utils/intersector.py
                                                 /ibound.py
                                                 /line_boundary.py

Features so far include: variable resolution, number of layers, layers
properties, stress periods
CHD boundary condition with line-point interpolation tool.

Layer properties given with rasters have to be finished and tested

Things to add: well and river BC type, initial head definition (in this version
is taken from top elevation).

Postprocessing include calculation of ['mean', 'raw', 'delta', 'max', 'min',
'standard_deviation'] property arrays
for the given time steps of interest, result saved in 'responce_raster'

Modflow working directory have to be changed

This file's structure will be changed depending on requirements of the
implemented web serving technology

"""

import numpy as np
import os
import sys
import flopy

from imports import model

# Sample input data ###########################################################
sample_data = {"model_id": "74f8ece4-a427-4bca-b426-42d7413cf874",
               "calculate": True,
               "give_result": False,
               "output_type": "raster",
               "time_steps_of_interest": [1],
               "layer_of_interest": 9,
               "operation": "raw",
               "base_url": "http://app.dev.inowas.com",
               "incluede_packages": ["CHD"]}
request_data = sample_data

working_directory = '../data/modflow/'
#request_data = demjson.decode(str(sys.argv[1]))
###############################################################################


def create_and_run(workspace, data):
    try:
        m = model.Model()
        m.setFromJson(data)
    except:
        print "Error while getting model data occured: ", sys.exc_info()[0]
        raise
        sys.exit()
    try:
        m.set_properties()
    except:
        print "Error while producing model input occured: ", sys.exc_info()[0]
        raise
        sys.exit()
    try:
        m.run_model(workspace)
    except:
        print "Error while model execution occured:", sys.exc_info()[0]
        raise
        sys.exit()
    else:
        print 'model created, calculated and saved'


def read_output(workspace, name, timesteps, layer, operation):

    possible_operations = ['mean', 'raw', 'delta',
                           'max', 'min', 'standard_deviation']
    if operation not in possible_operations:
        print 'requested operation is not available'
        return
    try:
        head_file_objects = flopy.utils.HeadFile(os.path.join(workspace,
                                                              name+'.hds'))
        heads_ts = [head_file_objects.get_data(totim=timestep) for timestep
                    in timesteps]
        heads_ts_array = np.array([heads[layer].tolist() for heads in heads_ts])
    except:
        print "Error while reading 'hds' file occured: ", sys.exc_info()[0]
        raise
        return
    try:
        if operation == 'mean':
            return np.mean(heads_ts_array, axis=0)
        elif operation == 'raw':
            return heads_ts_array
        elif operation == 'delta':
            return heads_ts_array[-1] - heads_ts_array[0]
        elif operation == 'max':
            return np.max(heads_ts_array, axis=0)
        elif operation == 'min':
            return np.min(heads_ts_array, axis=0)
        elif operation == 'standard_deviation':
            return np.std(heads_ts_array, axis=0)
    except:
        print "Error while postprocessing rasters occured:", sys.exc_info()[0]
        raise
        return
    else:
        print 'raster produced'


###############################################################################

response_raster = ""

# modflow workspace
workspace = working_directory + request_data['model_id']

if not os.path.exists(workspace):
    if request_data['calculate']:
        os.makedirs(workspace)
    else:
        print 'model does not exist, first calculate'
        quit()

if request_data['calculate']:
    create_and_run(workspace, request_data)

if request_data['give_result']:
    response_raster = read_output(workspace, request_data['model_id'],
                                  request_data['time_steps_of_interest'],
                                  request_data['layer_of_interest'],
                                  request_data['operation'])

#print demjson.encode({"head": responce_raster})
import matplotlib.pyplot as plt
ras = np.array(response_raster)
#ras[ras==-9999]=np.nan
plt.imshow(ras[0])
plt.colorbar()

###############################################################################
