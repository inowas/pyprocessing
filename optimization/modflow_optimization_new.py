import flopy
import random
import numpy as np
import os
from deap import base
from deap import creator
from deap import tools
from deap import algorithms
import spd_conversion
from ghost_well import GhostWell


"""
This code is an implementation of a Genetic optimization algorithm
(https://en.wikipedia.org/wiki/Genetic_algorithm).
Python DEAP library is used (https://github.com/DEAP).
Position of an injection well (lay, row, col) is beeing optimized.
Objecive function - maximize storage increase with respect to reference situation.
"""


class ModflowOptimization(object):
    """
    Modflow optimization class
    """
    def __init__(self, data):
        self.request_data = data
        self.model = flopy.modflow.Modflow.load(f=data['model_name'],
                                                model_ws=data['workspace'])
        self.stress_periods = data['time']['stress_periods']
        self.steady = data['time']['steady']
        self.ngen = data['ngen']
        self.popsize = data['popsize']
        self.control_layer = data['control_layer']
        self.ghost_wells = [GhostWell(idx, i) for idx, i in enumerate(data['wells'])]
        self.variables_map = []

    def initialize(self):
        self.model = spd_conversion.prepare_packages_steady(self.model,
                                                            self.stress_periods)
        self.model.write_input()
        head_file_name = os.path.join(self.model.model_ws, self.model.name)
        head_file_object = flopy.utils.HeadFile(head_file_name + '.hds')
        self.reference_head = head_file_object.get_alldata(mflay=self.control_layer,
                                                           nodata=-9999)
        self.reference_head = np.mean(self.reference_head, axis=0)
        head_file_object.close()

    def generate_candidate(self, ranges):
        candidate = []
        for well in self.ghost_wells:
            if 'lay' in well.well_variables:
                candidate.append(random.randint(well.bbox['layer_min'],
                                                well.bbox['layer_max']))
                self.variables_map.append('lay' + str(well.id))
            if 'row' in well.well_variables:
                candidate.append(random.randint(well.bbox['row_min'],
                                                well.bbox['row_max']))
                self.variables_map.append('row' + str(well.id))
            if 'col' in well.well_variables:
                candidate.append(random.randint(well.bbox['col_min'],
                                                well.bbox['col_max']))
                self.variables_map.append('col' + str(well.id))
            if 'rates' in well.well_variables:
                for i in range(len(self.stress_periods)):
                    candidate.append(random.random())
                    self.variables_map.append('rate' + str(well.id))

        print(' '.join(['FIRST CANDIDATE WELL:', str(candidate)]))
        return candidate

    def evaluate(self, individual):

        if 'WEL' in self.model.get_package_list():
            wel = self.model.get_package('WEL')
            spd = wel.stress_period_data.data

            for idx, well_data in enumerate(self.ghost_wells):
                spd = well.append_to_spd(data=well_data,
                                         spd=spd, idx=idx)

            wel_new = flopy.modflow.ModflowWel(self.model,
                                               stress_period_data=spd)
            wel_new.write_file()
        else:
            wel_new = flopy.modflow.ModflowWel(self.model,
                                               stress_period_data={0: [individual]})
            wel_new.write_file()

        silent = True
        pause = False
        report = False

        success, buff = self.model.run_model(silent, pause, report)

        try:
            head_file_objects = flopy.utils.HeadFile(os.path.join(self.model.model_ws,
                                                                  self.model.name + '.hds'))
            heads_timestep = head_file_objects.get_data(kstpkper=(0, 0))[-1]
            fitness = np.mean(heads_timestep - self.reference_head),
        except:
            fitness = -9999,

        return fitness

