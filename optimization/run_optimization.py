# -*- coding: utf-8 -*-
"""
Created on Wed Aug 03 12:08:10 2016

@author: Notebook
"""
import os
import sys
import flopy
import modflow_optimization

# usage: python run_optimization.py C:\data ed2385c3-06f8-434e-8059-22d893fdcbcb.nam 0 0 15 30


workspace = sys.argv[1]
namFile = sys.argv[2]


try:
    stressPeriod = int(sys.argv[3])
except:
    stressPeriod = 0
    
try:
    pumpingRate = int(sys.argv[4])
except:
    pumpingRate = 0
    
try:
    populationSize = int(sys.argv[5])
except:
    populationSize = 15
    
try:
    numberOfGenerations = int(sys.argv[6])
except:
    numberOfGenerations = 30


model = flopy.modflow.Modflow.load(f=namFile,
                                   model_ws=workspace)
MO = modflow_optimization.Modflow_optimization(model=model,
                                               stress_period=stressPeriod,
                                               rate=pumpingRate)
MO.initialize()
hallOfFame = MO.optimize_model(ngen=numberOfGenerations,
                               pop_size=populationSize)
print hallOfFame