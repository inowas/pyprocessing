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
import demjson

from imports import model

# Sample input data ###########################################################
sample_data = {"model_id": "94c48987-7d4f-46ac-9eb8-22e2d4a12d18",
               "calculate": True,
               "nx": 50,
               "ny": 50,
               "give_raster": True,
               "time_steps_of_interest": [10, 20],
               "layer_of_interest": 1,
               "operation": "mean",
               "base_url": "http://app.dev.inowas.com",
               "strt_head_mode": "warmed_up",
               "prior_steady_period_lenght" : 1,
               "nstp": [30, 27, 30],
               "packages": ["CHD", "WEL"]}
request_data = sample_data

working_directory = '../data/modflow/'
#request_data = demjson.decode(str(sys.argv[1]))
###############################################################################


class Modflow:

    _base_url = ""
    _executable = ""
    _input_file = ""
    _output_file = ""
    _workspace = ""

    def __init__(self, workspace):
        self._workspace = workspace

    def set_input_file(self, input_file):
        self._input_file = input_file

    def set_output_file(self, output_file):
        self._output_file = output_file

    def set_base_url(self, base_url):
        self._base_url = base_url

    def set_executable(self, executable):
        self._executable = executable

    @staticmethod
    def read_from_file(input_file):
        print "Open and read input file %s", input_file
        _file = open(input_file, 'r')
        json_input = _file.read()
        print "The content of the input file is %s", json_input
        return demjson.decode(json_input)

    def self_check_calculation(self):
        if self._base_url == "":
            raise ValueError('Base Url is not given')
        if self._executable == "":
            raise ValueError('Executable is not given')
        if self._input_file == "":
            raise ValueError('InputFileName is not given')
        if self._workspace == "":
            raise ValueError('Workspace ist not given')

    def self_check_result(self):
        if self._input_file == "":
            raise ValueError('InputFileName is not given')
        if self._output_file == "":
            raise ValueError('OutputFileName is not given')
        if self._workspace == "":
            raise ValueError('Workspace is not given')
        if not os.path.exists(self._workspace):
            raise ValueError('Workspace path does not exists')

    def create_and_run(self):
        try:
            self.self_check_calculation()
            data = self.read_from_file(self._input_file)

            if not os.path.exists(self._workspace):
                print "Creating output folder %s", self._workspace
                os.makedirs(self._workspace)

            m = model.Model()
            m.setFromJson(data)  # here is injected and treated an bject or array
            m.set_properties(data['nx'], data['ny'])  # this could be loaded from model
            m.run_model(self._workspace)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise
        else:
            print 'model created, calculated and saved'

    def get_result(self):
        try:
            self.self_check_result()
            data = self.read_from_file(self._input_file)
            Modflow.read_output(self._workspace, data)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise
        else:
            print 'model created, calculated and saved'

    @staticmethod
    def read_output(workspace, data):

        try:
            output_type = data['output_type']
        except KeyError:
            # Key is not present
            return

        try:
            model_id = data['model_id']
        except KeyError:
            # Key is not present
            return

        try:
            layer = data['layer']
        except KeyError:
            # Key is not present
            return

        if output_type == 'raster':

            try:
                operation = data['operation']
            except KeyError:
                # Key is not present
                return

            try:
                timesteps = data['time_steps']
            except KeyError:
                # Key is not present
                return

            return Modflow.read_output_raster(workspace, model_id, timesteps, layer, operation)

        elif output_type == 'time_series':

            try:
                cell_x = data['cell_x']
                cell_y = data['cell_y']
            except KeyError:
                # Key is not present
                return

            return Modflow.read_output_time_series(workspace, model_id, layer, cell_x, cell_y)

    @staticmethod
    def read_output_raster(workspace, name, timesteps, layer, operation):
        try:
            possible_operations = ['mean', 'raw', 'delta', 'max', 'min', 'standard_deviation']
            if operation not in possible_operations:
                print 'requested operation is not available'
                return

            head_file_objects = flopy.utils.HeadFile(os.path.join(workspace, name + '.hds'))
            heads_ts = [head_file_objects.get_data(totim=timestep) for timestep in timesteps]
            heads_ts_array = np.array([heads[layer].tolist() for heads in heads_ts])

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
            print "Unexpected error:", sys.exc_info()[0]
            raise
        else:
            print 'raster produced'

    @staticmethod
    def read_output_time_series(workspace, name, layer, cell_x, cell_y):
        hds = flopy.utils.HeadFile(os.path.join(workspace, name + '.hds'))
        return hds.get_ts((layer - 1, cell_x - 1, cell_y - 1))
