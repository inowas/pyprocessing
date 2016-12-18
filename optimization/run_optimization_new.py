# -*- coding: utf-8 -*-
"""
Created on Wed Oct 19 14:24:58 2016

@author: Notebook
"""
import sys
import flopy
import modflow_optimization

data = {
    'model_name': 'tutorial2',
    'workspace': 'C:\\Users\\Notebook\\Documents\\GitHub\\pyprocessing\\optimization\\test_model',
    'ngen': 1,
    'popsize': 1,
    'control_layer': 0
    'wells': [
        {
            'location': {
                'lay': 0,
                'row': 0,
                'col': 0
            },
            'bbox': {
                'xmin': 0,
                'xmax' 10,
                'ymin' 0,
                'ymax' 10
            },
            'pumping': {
                'rates': {
                    0: 100,
                    1: 100,
                    2: 100
                },
                'total_volume': 300
            }
        },
        {
            'location': {
                'lay': 0,
                'row': 1,
                'col': 1
            },
            'bbox': {
                'xmin': 0,
                'xmax' 10,
                'ymin' 0,
                'ymax' 10
            },
            'pumping': {
                'rates': {
                    0: -100,
                    1: -100,
                    2: -100
                },
                'total_volume': -300
            }
        }
    ],
    'time': {
        'stress_periods': [0, 1, 2],
        'steady': [True, False, False]
    }
}

MO = modflow_optimization.ModflowOptimization(data)





