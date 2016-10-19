# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 11:56:01 2016

@author: Notebook
"""
import numpy as np


class GhostWell(object):
    """Well used in optimization process"""
    def __init__(self, idx, data):
        self.id = idx
        self.data = data
        # Area bounding box
        self.bbox = data['bbox']

        # Variables to be optimized
        self.wel_variables = []
        if 'lay' not in data['location'] or data['location']['lay'] is None:
            self.wel_variables.append('lay')
        if 'row' not in data['location'] or data['location']['row'] is None:
            self.wel_variables.append('row')
        if 'col' not in data['location'] or data['location']['col'] is None:
            self.wel_variables.append('col')
        if 'rates' not in data['pumping'] or data['pumping']['rates'] is None:
            self.wel_variables.append('rates')
        if 'total_volume' not in data['pumping'] or data['pumping']['total_volume'] is None:
            self.wel_variables.append('toltal_volume')

        self._once_appended = False

    def append_to_spd(self, data, spd, idx):
        # Replace previousely appended ghost well with a new one
        self.data = data
        if self._once_appended:
            for period in self.data:
                np.put(spd[period], idx, (self.data[period]))

        else:
            # Initially append a ghost well
            for period in self.data:
                spd[period] = np.append(
                                spd,
                                np.array([self.data[period]], dtype=spd.dtype)
                                ).view(np.recarray)

            return spd
