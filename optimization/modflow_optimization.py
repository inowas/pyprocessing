import flopy
import random
import numpy as np
import os
from deap import base
from deap import creator
from deap import tools
from deap import algorithms
import spd_conversion


"""
This code is an implementation of a Genetic optimization algorithm (https://en.wikipedia.org/wiki/Genetic_algorithm).
Python DEAP library is used (https://github.com/DEAP).
Position of an injection well (lay, row, col) is beeing optimized.
Objecive function - maximize storage increase with respect to reference situation.
"""

class Modflow_optimization(object):
    """
    Modflow optimization class
    """

    valid_optimization_packages = ['WEL', 'LAK']
    valid_optimization_parameters = ['row', 'column', 'layer', 'rate', 'stage']

    def __init__(self, model, package='WEL', stress_period=None,
                 stress_period_start=None, stress_period_end=None,
                 parameters=['row', 'column', 'layer'], rate=None, mode=None,
                 control_layer=None):

        try:
            name = model.name
        except:
            print('Given model is not a valid Flopy model object')
            return

        if package not in self.valid_optimization_packages:
            print('Given gackage name is incorrect')
            return

        for parameter in parameters:
            if parameter not in self.valid_optimization_parameters:
                print('Given parameters list is invalid')
                return
            if package == 'wel' and parameter == 'stage':
                print('Given parameters list does not fit the specified package')
                return
            if package == 'lak' and parameter == 'rate':
                print('Given parameters list does not fit the specified package')
                return

        if not isinstance(stress_period, int):
            print('Given stress period index is invalid')
            return

        if stress_period < 0 or stress_period > model.nper - 1:
            print('Given stress period index is not within the Models nstp range')
            return

        self.model = model #  Flopy model object.
        self.package = package #  Name of the package to be optimized.
        self.stress_period = stress_period #  Index of a stress period
        self.stress_period_start = stress_period_start
        self.stress_period_end = stress_period_end
        self.parameters = parameters #  List of parameters names that will be optimized
        self.rate = rate
        self.mode = mode
        self.nlay = model.get_package('DIS').nlay
        self.nrow = model.get_package('DIS').nrow
        self.ncol = model.get_package('DIS').ncol
        self.control_layer = control_layer
        self.reference_head = None

    def initialize(self, reference_method='mean'):
        """
        Initial model run. Reference situation.The lxyq tuple of lay,row,col,rate.
        """

        if self.mode == 'steady':
            self.model = spd_conversion.prepare_packages_steady(self.model, self.stress_period)
        elif self.mode == 'transient':
            self.model = spd_conversion.prepare_packages_transient(self.model,
                                                                   self.stress_period_start,
                                                                   self.stress_period_end)
        else:
            print('Invalid stress period mode. Exit simulation')


        print('Writing new model input files...')
        self.model.write_input()

        silent = False
        pause = False
        report = True

        print('Running model...')
        self.model.run_model(silent, pause, report)
        head_file_name = os.path.join(self.model.model_ws, self.model.name)
        head_file_objects = flopy.utils.HeadFile(head_file_name +'.hds')

        if self.mode == 'steady':
            heads_timestep = head_file_objects.get_data(kstpkper=(0, 0))[self.control_layer]
        else:
            heads_timestep = head_file_objects.get_alldata(mflay=self.control_layer, nodata=-9999)
            heads_timestep = np.mean(heads_timestep, axis=0)

        head_file_objects.close()

        self.reference_head = heads_timestep

    def optimize_model(self, ngen=30, cxpb=0.5, mutpb=0.1, pop_size=15):
        """
        DEAP Optimization
        """
        print('OPTIMIZATION STARTED')
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
        self.result, self.log = algorithms.eaSimple(
            pop, toolbox,
            cxpb=cxpb, mutpb=mutpb,
            ngen=ngen, stats=stats,
            halloffame=self.hallOfFame, verbose=False
            )
        return self.hallOfFame


    def generate_candidate(self, ranges):
        """
        Generate initial individual
        """
        candidate = [random.randint(0, ranges[0]-1),
                     random.randint(0, ranges[1]-1),
                     random.randint(0, ranges[2]-1),
                     self.rate]
        print(' '.join(['FIRST CANDIDATE WELL: ', str(candidate)]))

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
            if 'WEL' in self.model.get_package_list():
                wel = self.model.get_package('WEL')
                spd = wel.stress_period_data.data[0][:-1]
                print(spd)
                spd = np.append(spd, np.array([tuple_ind],
                                              dtype=spd.dtype)).view(np.recarray)

                wel_new = flopy.modflow.ModflowWel(self.model, stress_period_data={0:spd})
                wel_new.write_file()
            else:
                wel_new = flopy.modflow.ModflowWel(self.model, stress_period_data={0:[individual]})
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

# if __name__ == __main__:
#   m = flopy.modflow.Modflow.load(model_ws='C:\\Users\\Notebook\\Documents\\GitHub\\pyprocessing\\modflow\\Modflow_exercise',
#                               f='Modflow_exercise.nam')
#   MO=Modflow_optimization(m)
#   MO.optimize_model()
#        import matplotlib.pyplot as plt
#        gen, mean, min_, max_ = self.log.select("gen", "mean", "min", "max")
#
#        min_ = np.hstack(min_)
#        min_[min_ < 0] = None
#
#        mean = np.hstack(mean)
#        mean[mean < 0] = None
#
#        plt.plot(gen, mean, label="average")
#        plt.plot(gen, min_, label="minimum")
#        plt.plot(gen, max_, label="maximum")
#        plt.xlabel("Generation")
#        plt.ylabel("Fitness")
#        plt.legend(loc="lower right")