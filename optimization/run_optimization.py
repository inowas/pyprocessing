# -*- coding: utf-8 -*-
"""
Created on Wed Aug 03 12:08:10 2016

@author: Notebook
"""

import sys
import flopy
import modflow_optimization

# usage: python run_optimization.py .\test_model tutorial2.nam 0 10000 1 1

#workspace = sys.argv[1]
#namFile = sys.argv[2]
#
#try:
#    stressPeriod = int(sys.argv[3])
#except:
#    stressPeriod = 0
#
#try:
#    pumpingRate = int(sys.argv[4])
#except:
#    pumpingRate = 1000
#
#try:
#    populationSize = int(sys.argv[5])
#except:
#    populationSize = 15
#
#try:
#    numberOfGenerations = int(sys.argv[6])
#except:
#    numberOfGenerations = 30

workspace = 'C:\\Users\\Notebook\\Documents\\GitHub\\pyprocessing\\optimization\\test_model'
namFile = 'tutorial2.nam'
stressPeriod = 0
pumpingRate = 1000
populationSize = 1
numberOfGenerations = 1

data = {
    'model_name': 'tutorial2',
    'workspace': 'C:\\Users\\Notebook\\Documents\\GitHub\\pyprocessing\\optimization\\test_model',
    'ngen': 1,
    'popsize': 1,
    'wells': [
        {
            'location': {
                'lay': 0,
                'row': 0,
                'col': 0
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
        'stress_periods':[0, 1, 2],
        'steady': [True, False, False]
    }
}

model = flopy.modflow.Modflow.load(f=namFile,
                                   model_ws=workspace)
MO = modflow_optimization.ModflowOptimization(model=model,
                                              stress_period=stressPeriod,
                                              rate=pumpingRate,
                                              stress_period_start=0,
                                              stress_period_end=2,
                                              mode='transient',
                                              control_layer=0)
MO.initialize()
hall_of_fame = MO.optimize_model(ngen=numberOfGenerations,
                                 pop_size=populationSize)
# print(hall_of_fame)

import matplotlib.pyplot as plt
import flopy.utils.binaryfile as bf

headobj = bf.HeadFile('test_model\\tutorial2'+'.hds')
times = headobj.get_times()
head = headobj.get_data(totim=150)
# print(head)
plt.imshow(head[0])
plt.show()
