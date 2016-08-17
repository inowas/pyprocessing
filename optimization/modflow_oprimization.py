import flopy
import random
import numpy as np
import os
from copy import deepcopy
from deap import base
from deap import creator
from deap import tools
from deap import algorithms


class Modflow_optimization(object):
    """
    Modflow optimization class
    """
    valid_packages = ['WEL', 'LAK']
    valid_parameters = ['row', 'column', 'layer', 'rate', 'stage']
    
    def __init__(self, model, package='WEL', stress_period=0,
                 parameters=['row', 'column', 'layer']):
        
        try:
            name = model.name
        except:
            print 'Given model is not a valid Flopy model object'
            return
            
        if package not in self.valid_packages:
            print 'Given gackage name is incorrect'
            return
         
        for parameter in parameters:
            if parameter not in self.valid_parameters:
                print 'Given parameters list is invalid'
                return
            if package == 'wel' and parameter == 'stage':
                print 'Given parameters list does not fit the specified package'
                return
            if package == 'lak' and parameter == 'rate':
                print 'Given parameters list does not fit the specified package'
                return
                
        if type(stress_period) != int:
            print 'Given stress period index is invalid'
            return
        
        if stress_period < 0 or stress_period > model.nper - 1:
            print 'Given stress period index is not within the Models nstp range'
            return
            
        self.model = model #  Flopy model object.
        self.package = package #  Name of the package to be optimized.
        self.stress_period = stress_period #  Index of a stress period for which steady state simulation will take place.
        self.parameters = parameters #  List of parameters names that will be optimized
        self.rate= 10000
        
    def initialize(self):
        """
        Initial model run. Reference situation.The lxyq tuple of lay,row,col,rate.
        """
        print 'Reading stress-period-data of the given model object...'
        
        for package_name in self.model.get_package_list():
            
            if package_name == 'WEL':
                wel = self.model.get_package(package_name)
                spd = wel.stress_period_data.data[self.stress_period]
                wel_new = flopy.modflow.ModflowWel(self.model, stress_period_data = {0:spd})

            if package_name == 'RIV':
                riv = self.model.get_package(package_name)
                spd = riv.stress_period_data.data[self.stress_period]
                riv_new = flopy.modflow.ModflowRiv(self.model, stress_period_data = {0:spd})
            
            if package_name == 'CHD':
                chd = self.model.get_package(package_name)
                spd = chd.stress_period_data.data[self.stress_period]
                chd_new = flopy.modflow.ModflowChd(self.model, stress_period_data = {0:spd})
            
            if package_name == 'GHB':
                ghb = self.model.get_package(package_name)
                spd = ghb.stress_period_data.data[self.stress_period]
                ghb_new = flopy.modflow.ModflowGhb(self.model, stress_period_data = {0:spd})

            if package_name == 'LAK':
                lak = self.model.get_package(package_name)
                spd = lak.stress_period_data.data[self.stress_period]
                lak_new = flopy.modflow.ModflowLak(self.model, stress_period_data = {0:spd})

            if package_name == 'DIS':
                dis = self.model.get_package(package_name)
                perlen = [dis.perlen.array[self.stress_period]]
                delc = dis.delc.array
                delr = dis.delr.array
                self.nlay = dis.nlay
                self.nrow = dis.nrow
                self.ncol = dis.ncol
                steady = [True]
                top = dis.top.array
                botm = dis.botm.array
                laycbd = dis.laycbd.array 
                dis_new = flopy.modflow.ModflowDis(self.model, nlay=self.nlay, nrow=self.nrow, ncol=self.ncol,
                                                   delr=delr, delc=delc, top=top, steady=steady,
                                                   botm=botm, laycbd=laycbd, perlen=perlen)

        self.model.write_input()
        
        silent = False
        pause = False
        report = True
        
        success, buff = self.model.run_model(silent, pause, report)

        head_file_objects = flopy.utils.HeadFile(os.path.join(self.model.model_ws,
                                                              self.model.name +'.hds'))

        heads_timestep = head_file_objects.get_data(kstpkper=(0, 0))[-1]
        self.reference_head = heads_timestep
        
    def optimize_model(self, ngen=20, cxpb=0.5, mutpb=0.1, pop_size=20):
        """
        
        """
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        
        toolbox = base.Toolbox()
        
        toolbox.register("candidate", self.generate_candidate,
                         [self.nlay, self.nrow, self.ncol])
                         
        toolbox.register("individual", tools.initIterate,
                         creator.Individual, toolbox.candidate)
                         
        toolbox.register("population", tools.initRepeat,
                         list, toolbox.individual)
                         
        toolbox.register("mate", tools.cxOnePoint)
        
        toolbox.register("evaluate", self.evaluate)
        
        toolbox.register("mutate", self.mutate)
        
        toolbox.register("select", tools.selTournament, tournsize=3)
        
        pop = toolbox.population(n=pop_size)
        
        self.hallOfFame = tools.HallOfFame(maxsize=100)
        
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("mean", np.mean, axis=0)
        stats.register("std", np.std, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)
        self.result, self.log = algorithms.eaSimple(pop, toolbox,
                                          cxpb=cxpb, mutpb=mutpb,
                                          ngen=ngen, stats=stats,
                                          halloffame=self.hallOfFame, verbose=False)
                                          
        import matplotlib.pyplot as plt                               
        gen, mean, min_, max_ = self.log.select("gen", "mean", "min", "max")
        
        min_ = np.hstack(min_)
        min_[min_ < 0] = None
        
        mean = np.hstack(mean)
        mean[mean < 0] = None
        
        plt.plot(gen, mean, label="average")
        plt.plot(gen, min_, label="minimum")
        plt.plot(gen, max_, label="maximum")
        plt.xlabel("Generation")
        plt.ylabel("Fitness")
        plt.legend(loc="lower right")
        
    def generate_candidate(self, ranges):
        """
        
        """
        candidate = [random.randint(0,ranges[0]-1),
                     random.randint(0,ranges[1]-1),
                     random.randint(0,ranges[2]-1),
                     self.rate]
                     
        return candidate
        
    def mutate(self, individual):
        """
        
        """
        random_num = random.randint(-1,1)
        nxtLay = individual[0] + random_num if individual[0] + random_num <= self.nlay-1 else 0
        individual[0] = nxtLay
        
        random_num = random.randint(-1,1)
        nxtRow = individual[1] + random_num if individual[1] + random_num <= self.nrow-1 else 0
        individual[1] = nxtRow
        
        random_num = random.randint(-1,1)
        nxtCol = individual[2] + random_num if individual[2] + random_num <= self.ncol-1 else 0
        individual[2] = nxtCol
        
        return individual,
        
    def evaluate(self, individual):

        tuple_ind = tuple(individual)

        if self.package == 'WEL':
            wel = self.model.get_package('WEL')
            spd = wel.stress_period_data.data[0][:-1]
            spd = np.append(spd, np.array([tuple_ind],
                                          dtype=spd.dtype)).view(np.recarray)

            wel_new = flopy.modflow.ModflowWel(self.model, stress_period_data = {0:spd})
            wel_new.write_file()
        
        silent = True
        pause = False
        report = False
        
        success, buff = self.model.run_model(silent, pause, report)
        
        

        try:
            head_file_objects = flopy.utils.HeadFile(os.path.join(self.model.model_ws,
                                                                  self.model.name +'.hds'))

            heads_timestep = head_file_objects.get_data(kstpkper=(0, 0))[-1]
            fitness = np.mean(heads_timestep - self.reference_head),
        except:
            fitness = -9999,

        return fitness
        
m = flopy.modflow.Modflow.load('C:\Users\Notebook\Documents\GitHub\pyprocessing\modflow\data\ed2385c3-06f8-434e-8059-22d893fdcbcb.nam')
MO=Modflow_optimization(m)
MO.initialize()
MO.optimize_model()