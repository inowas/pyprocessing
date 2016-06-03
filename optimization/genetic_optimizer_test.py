# -*- coding: utf-8 -*-
"""
Test of the Genetic (Evolutionary) Algorithm applied to solve grondwater problem
consisting of finding optimal location and rate of a injection well, that leads 
to maximum efficiency.
Test utilizes Flopy and DEAP libraries.
Parameters of the Genetic Algorithms: individual : [x, y, rate], population: 10 individuals
number of generations: 50, propability for mutation: 0.1, probability to survive: 0.8

@author: aybulat
"""

import matplotlib.pyplot as plt
import sys
import os
import shutil
import numpy as np
from subprocess import check_output

# Import flopy
import flopy

# Set the name of the path to the model working directory
dirname = "P4-4_Hubbertville"
datapath = os.getcwd()
modelpath = os.path.join(datapath, dirname)
# Now let's check if this directory exists.  If not, then we will create it.
if os.path.exists(modelpath):
    pass
else:
    os.mkdir(modelpath)

LX = 4500.
LY = 11000.   # note that there is an added 500m on the top and bottom to represent the boundary conditions,that leaves an aqufier lenght of 10000 m  
ZTOP = 1030.  # the system is unconfined so set the top above land surface so that the water table never > layer top
ZBOT = 980.
NLAY = 1
NROW = 22
NCOL = 9
DELR = LX / NCOL  # recall that MODFLOW convention is DELR is along a row, thus has items = NCOL; see page XXX in AW&H (2015)
DELC = LY / NROW  # recall that MODFLOW convention is DELC is along a column, thus has items = NROW; see page XXX in AW&H (2015)
DELV = (ZTOP - ZBOT) / NLAY
BOTM = np.linspace(ZTOP, ZBOT, NLAY + 1)
HK = 50.
VKA = 1.
RCH = 0.001
WELLQ = -20000. #In P4.4 the proposed well is pumping (Q was set to zero in P4.3)

TOP = ZTOP * np.ones((NROW, NCOL),dtype=np.float)                        
IBOUND = np.ones((NLAY, NROW, NCOL), dtype=np.int32)  # all nodes are active (IBOUND = 1)

# make the top of the profile specified head by setting the IBOUND = -1
IBOUND[:, 0, :] = -1  #don't forget arrays are zero-based!
IBOUND[:, -1, :] = -1  #-1 is Python for last in array

STRT = 1010 * np.ones((NLAY, NROW, NCOL), dtype=np.float32)  # set starting head to 1010 m through out model domain
STRT[:, 0, :] = 1000.       # river stage for setting constant head
STRT[:, -1, :] = 1000. 

def run_ref_model(plot_heads = True):

    dirname = "P4-4_Hubbertville"
    datapath = os.getcwd()
    modelpath = os.path.join(datapath, dirname)     
    modelname = 'P4-4'
    timesteps = [1]
    layer = 0

    MF = flopy.modflow.Modflow(modelname, exe_name='mf2005', version='mf2005', model_ws=modelpath)
    DIS_PACKAGE = flopy.modflow.ModflowDis(MF, NLAY, NROW, NCOL, delr=DELR, delc=DELC, top=TOP, botm=BOTM[1:], laycbd=0) 
    BAS_PACKAGE = flopy.modflow.ModflowBas(MF, ibound=IBOUND, strt=STRT)
    LPF_PACKAGE = flopy.modflow.ModflowLpf(MF, laytyp=1, hk=HK, vka=VKA)
    RCH_PACKAGE = flopy.modflow.ModflowRch(MF, rech=RCH)
    PCG_PACKAGE = flopy.modflow.ModflowPcg(MF, mxiter=900, iter1=900)
    OC_PACKAGE = flopy.modflow.ModflowOc(MF)
    WEL_PACKAGE = flopy.modflow.ModflowWel(MF, stress_period_data=[0,5,4,WELLQ]) 
    
    
    modelfiles = os.listdir(modelpath)
    for filename in modelfiles:
        f = os.path.join(modelpath, filename)
        if modelname in f:
            try:
                os.remove(f)
            except:
                pass
                
    #Now write the model input files
    MF.write_input()
    
    silent = True  #Print model output to screen?
    pause = False   #Require user to hit enter? Doesn't mean much in Ipython notebook
    report = True   #Store the output from the model in buff
    success, buff = MF.run_model(silent=silent, pause=pause, report=report)
    head_file_objects = flopy.utils.HeadFile(os.path.join(modelpath, modelname +'.hds'))
    heads_ts = [head_file_objects.get_data(totim = timestep) for timestep in timesteps]
    heads_ts_array = np.array([heads[layer].tolist() for heads in heads_ts])

    cov = np.mean(heads_ts_array, axis = 0)
    plt.imshow(cov, interpolation = 'nearest')
    plt.colorbar()
    plt.show()
    return np.mean(heads_ts_array)
    
reference_heads = run_ref_model()

def run_model(xyq, plot_heads = False):
    x = xyq[0]
    y = xyq[1]
    q = xyq[2]
    dirname = "P4-4_Hubbertville"
    datapath = os.getcwd()
    modelpath = os.path.join(datapath, dirname)     
    modelname = 'P4-4'
    timesteps = [1]
    layer = 0

    MF = flopy.modflow.Modflow(modelname, exe_name='mf2005', version='mf2005', model_ws=modelpath)
    DIS_PACKAGE = flopy.modflow.ModflowDis(MF, NLAY, NROW, NCOL, delr=DELR, delc=DELC, top=TOP, botm=BOTM[1:], laycbd=0) 
    BAS_PACKAGE = flopy.modflow.ModflowBas(MF, ibound=IBOUND, strt=STRT)
    LPF_PACKAGE = flopy.modflow.ModflowLpf(MF, laytyp=1, hk=HK, vka=VKA)
    RCH_PACKAGE = flopy.modflow.ModflowRch(MF, rech=RCH)
    PCG_PACKAGE = flopy.modflow.ModflowPcg(MF, mxiter=900, iter1=900)
    OC_PACKAGE = flopy.modflow.ModflowOc(MF)
    WEL_PACKAGE = flopy.modflow.ModflowWel(MF, stress_period_data=[[0,y,x,q],[0,5,4,WELLQ]]) 
    
    
    modelfiles = os.listdir(modelpath)
    for filename in modelfiles:
        f = os.path.join(modelpath, filename)
        if modelname in f:
            try:
                os.remove(f)
            except:
                pass
                
    #Now write the model input files
    MF.write_input()
    
    silent = True  #Print model output to screen?
    pause = False   #Require user to hit enter? Doesn't mean much in Ipython notebook
    report = True   #Store the output from the model in buff
    success, buff = MF.run_model(silent=silent, pause=pause, report=report)
    head_file_objects = flopy.utils.HeadFile(os.path.join(modelpath, modelname +'.hds'))
    heads_ts = [head_file_objects.get_data(totim = timestep) for timestep in timesteps]
    heads_ts_array = np.array([heads[layer].tolist() for heads in heads_ts])
    if plot_heads:
        cov = np.mean(heads_ts_array, axis = 0)
        plt.imshow(cov, interpolation = 'nearest')
        plt.colorbar()
        plt.show()
    else:
        return ((np.mean(heads_ts_array) - reference_heads)/q,)

injection_min, injection_max = 5000, 50000
injection_step = 100


import random
from deap import base
from deap import creator
from deap import tools
from deap import algorithms
import numpy as np

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)
IND_SIZE=10

def generate_xyq(ranges):
    xyq= [random.randint(0,ranges[0]), random.randint(0,ranges[1]), random.randint(ranges[2]/injection_step,ranges[3]/injection_step) * injection_step]
    return xyq
def mutate(individual):
    num = random.randint(-1,1)
    nxtCol = individual[0] + num if individual[0] + num <= NCOL-1 else 0
    individual[0] = range(NCOL-1)[nxtCol]
    num = random.randint(-1,1)    
    nxtRow = individual[1] + num if individual[1] + num <= NROW-1 else 0
    individual[1] = range(NROW-1)[nxtRow]
    mutQ = individual[2] + random.randint(-3,3) * injection_step
    individual[2] = mutQ
    return individual,
    
toolbox = base.Toolbox()
toolbox.register("x_y_coord", generate_xyq, [NCOL-1,NROW-1, injection_min, injection_max])
toolbox.register("individual", tools.initIterate, creator.Individual,
                 toolbox.x_y_coord)
toolbox.register("population", tools.initRepeat, list, 
                 toolbox.individual)
toolbox.register("mate", tools.cxOnePoint)
toolbox.register("evaluate", run_model)
toolbox.register("mutate", mutate)
toolbox.register("select", tools.selTournament, tournsize=3)
pop = toolbox.population(n = 10)

stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("mean", np.mean, axis=0)
stats.register("std", np.std, axis=0)
stats.register("min", np.min, axis=0)
stats.register("max", np.max, axis=0)
result, log = algorithms.eaSimple(pop, toolbox,
                             cxpb=0.8, mutpb=0.1,
                             ngen=50, stats = stats, verbose=False)

plt.figure(1, figsize=(11, 4), dpi=500)
plots = plt.plot(log.select('max'),'c-', log.select('mean'), 'b-', antialiased=True)
plt.legend(plots, ('Minimum fitness', 'Mean fitness'))
plt.ylabel('Fitness')
plt.xlabel('Iterations')
plt.show()
from scipy.stats import mode
run_model(xyq=mode(result)[0][0], plot_heads = True)
                 