# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 14:27:31 2016

@author: aybulat
"""
from urllib import urlopen
import json
import numpy as np
from operator import methodcaller
import datetime
import flopy

from imports.utils import ibound
from imports.utils import line_boundary_interpolation

class Model(object):
    """
    Model class
    """
    def __init__(self):
        pass
    def setFromJson(self, jsonData):
        """
        Function to get model's data and create respective model objects
        """
        self.id = str(jsonData['id'])
        self.owner_id = str(jsonData['owner']['id'])
        self.describtion = str(jsonData['description'])
        self.name = str(jsonData['name'])
        self.area = Area(jsonData['area'])
        self.soil_model = Soil_model(jsonData['soil_model'])
        self.calculation_properties = Calculation_properties(jsonData['calculation_properties'])        
        self.boundaries = [Boundary(i) for i in jsonData['boundaries']] if len(jsonData['boundaries']) > 0 else None

    def set_properties(self, nx, ny):
        """
        Calculating properties of the model objects into Flopy input format
        """
        
        self.IBOUND = ibound.give_ibound(line = self.area.boundary_line,
                                         number_of_layers = len(self.soil_model.geological_layers),
                                         nx = nx, 
                                         ny = ny, 
                                         xmin = self.area.xmin, 
                                         xmax = self.area.xmax, 
                                         ymin = self.area.ymin, 
                                         ymax = self.area.ymax)
                                         
        self.layers_properties = {}
        for i, prop in enumerate(self.soil_model.geological_layers[0].properties):
            self.layers_properties[prop.property_type_abr] = [layer.properties[i].values[0].value 
                                                    for layer in self.soil_model.geological_layers]

        self.PERLEN = [i.length for i in self.calculation_properties.stress_periods]
        
    
        self.SPD_list = [line_boundary_interpolation.give_SPD(points = boundary.points_xy,
                                                              point_vals = boundary.points_values,
                                                              line = boundary.boundary_line,
                                                              stress_period_list = range(len(self.calculation_properties.stress_periods)),
                                                              interract_layers = [i for i in range(len(self.soil_model.geological_layers))
                                                                                  if self.soil_model.geological_layers[i].id in boundary.interracted_layers_ids],
                                                              xmin = self.area.xmin, 
                                                              xmax = self.area.xmax, 
                                                              ymin = self.area.ymin, 
                                                              ymax = self.area.ymax,
                                                              nx = nx,
                                                              ny = ny,
                                                              layers_botm = self.layers_properties['eb']) 
                                                              for boundary in self.boundaries]
        
    def run_model(self, workspace):

        # Write flopy input datasets
        NLAY = np.shape(self.IBOUND)[0]
        NROW = np.shape(self.IBOUND)[1]
        NCOL = np.shape(self.IBOUND)[2]
        CHD_SPD = self.SPD_list[0]
        TOP = self.layers_properties['et'][0]
        BOT = self.layers_properties['eb']
        HK = self.layers_properties['hc']
        HANI = self.layers_properties['ha']
        VANI = self.layers_properties['va']
        DELR = (self.area.ymax - self.area.ymin) / np.shape(self.IBOUND)[1]
        DELC = (self.area.xmax - self.area.xmin) / np.shape(self.IBOUND)[2]
        NPER = len(self.SPD_list[0])
        NSTP = PERLEN = self.PERLEN
    #    STRT = m.initial_head
        
        MF = flopy.modflow.Modflow(self.id, exe_name='mf2005', version='mf2005', model_ws=workspace)
        DIS_PACKAGE = flopy.modflow.ModflowDis(MF, nlay=NLAY, nrow=NROW, ncol=NCOL, 
                                               delr=DELR, botm=BOT, delc=DELC,top=TOP, 
                                               laycbd=0, steady=False, nper = NPER, 
                                               nstp = NSTP, perlen = PERLEN)
        BAS_PACKAGE = flopy.modflow.ModflowBas(MF, ibound=self.IBOUND, strt=TOP, hnoflo = -9999, stoper = 1.)
        OC_PACKAGE = flopy.modflow.ModflowOc(MF)
        LPF_PACKAGE = flopy.modflow.ModflowLpf(MF, hk=HK, laytyp = 1)
        PCG_PACKAGE = flopy.modflow.ModflowPcg(MF, mxiter=900, iter1=900)
        CHD = flopy.modflow.ModflowChd(MF, stress_period_data = CHD_SPD)
        
        # Write Modflow input files and run the model    
        MF.write_input()
        MF.run_model()
            

class Calculation_properties(object):
    """
    Calculation properties class. ---> Model.calculation_properties
    """
    def __init__(self, jsonDataCalculation):
        self.calculation_type = str(jsonDataCalculation['calculation_type'])
        self.recalculation = jsonDataCalculation['recalculation']
        self.initial_values = Initial_values(jsonDataCalculation['initial_values'])
        self.stress_periods = [Stress_period(i) for i in jsonDataCalculation['stress_periods']] if len(jsonDataCalculation['stress_periods']) > 0 else None

            
class Area(object):
    """
    Area class. ---> Model.area
    """
    def __init__(self, jsonDataArea):
        self.id = str(jsonDataArea['id'])
        self.geometry = jsonDataArea['geometry']
        points_id = []
        
        for point in self.geometry[0]:
            try:
                points_id.append(int(point))
            except:
                pass

        self.boundary_line = [self.geometry[0][str(i)] for i in sorted(points_id)]

        x = [i[0] for i in self.boundary_line]
        y = [i[1] for i in self.boundary_line]        
        self.xmin = min(x)
        self.xmax = max(x)
        self.ymin = min(y)
        self.ymax = max(y)
 

class Initial_values(object):
    """
    Initial values class. ---> Calculation properties.initial_values
    """
    def __init__(self, jsonDataCalculationInitial):
        self.head_from_top_elevation = jsonDataCalculationInitial['head_from_top_elevation']
        self.interpolation = jsonDataCalculationInitial['interpolation']
        
class Stress_period(object):
    """
    Stress period class. ---> Calculation properties.stress_periods
    """
    def __init__(self, jsonDataStress):
        begin_raw = str(jsonDataStress['dateTimeBegin']['date'])
        end_raw = str(jsonDataStress['dateTimeEnd']['date'])
        self.dateTimeBegin = datetime.datetime.strptime(begin_raw,"%Y-%m-%d %H:%M:%S.%f")
        self.dateTimeEnd = datetime.datetime.strptime(end_raw,"%Y-%m-%d %H:%M:%S.%f")
        self.length = (self.dateTimeEnd - self.dateTimeBegin).days


        
class Soil_model(object):
    """
    Soil model class. ---> Model.soil_model
    """
    def __init__(self, jsonDataSoil):
        self.id = str(jsonDataSoil['id'])
        layers_unsorted = [Geological_layer(i) for i in jsonDataSoil['geological_layers']] if len(jsonDataSoil['geological_layers']) > 0 else None
        self.geological_layers = sorted(layers_unsorted, key = methodcaller('avg_top_elev'), reverse = True)
        
class Geological_layer(object):
    """
    Geological layer class. ---> Soil_model.geological_layers
    """
    def __init__(self, jsonDataLayer):
        self.id = str(jsonDataLayer['id'])
        # Set data
        url = 'http://app.dev.inowas.com/api/geologicallayers/'+self.id+'.json'
        responce = urlopen(url).read()
        jsonData = json.loads(responce)
        self.properties = [Property(i) for i in jsonData['properties']] if len(jsonData['properties']) > 0 else None
        self.top = [i.values[0].value for i in self.properties if i.property_type_abr == 'et']
        self.botm = [i.values[0].value for i in self.properties if i.property_type_abr == 'eb']
    def avg_top_elev(self):
        """
        Function returning mean layer elevation used to define order of the layers
        """
        return np.mean(np.array(self.top))
        
class Boundary(object):
    """
    Boundary class. ---> Model.boundaries
    """
    def __init__(self, jsonDataBoundary):
        self.id = str(jsonDataBoundary['id'])
        # Set data
        url = 'http://app.dev.inowas.com/api/boundaries/'+self.id+'.json'
        responce = urlopen(url).read()
        jsonData = json.loads(responce)
        
        self.geometry = jsonData['geometry']
        self.observation_points = [Observation_points(i) for i in jsonData['observation_points']] if len(jsonData['observation_points']) > 0 else None
        points_id = []
        for point in self.geometry:
            try:
                points_id.append(int(point))
            except:
                pass
        self.boundary_line = [self.geometry[str(i)] for i in range(len(points_id))]

        self.points_xy = []
        self.points_values = []
        for point in range(len(self.observation_points)):
            self.points_values.append([i.value for i in self.observation_points[point].properties[0].values])
            self.points_xy.append([self.observation_points[point].x, self.observation_points[point].y])

        self.interracted_layers_ids = [str(i['id']) for i in jsonData['geological_layers']]

class Observation_points(object):
    """
    Observation point class. ---> Boundary.observation_points
    """ 
    def __init__(self, jsonDataObservationPoints):

        self.id = str(jsonDataObservationPoints['id'])
        self.properties = [Property(i) for i in jsonDataObservationPoints['properties']] if len(jsonDataObservationPoints['properties']) > 0 else None
        self.x = float(jsonDataObservationPoints['point']['x'])
        self.y = float(jsonDataObservationPoints['point']['y'])

class Property(object):
    """
    
    """
    def __init__(self, jsonDataProperty):
        self.id = str(jsonDataProperty['id'])
        self.name = str(jsonDataProperty['name'])
        self.property_type_abr = str(jsonDataProperty['property_type']['abbreviation'])
        self.values = [Value(i) for i in jsonDataProperty['values']] if len(jsonDataProperty['values']) > 0 else None
        
        
class Value(object):
    """
    
    """
    def __init__(self, jsonDataValue):
        if 'value' in jsonDataValue:
            self.value = float(jsonDataValue['value'])
        elif 'raster' in jsonDataValue:
            self.value = str(jsonDataValue['value'])
        else:
            self.value = None

        self.datetime = str(jsonDataValue['datetime']) if 'datetime' in jsonDataValue else None


#class Date_time_end(object):
#    """
#    
#    """
#    def __init__(self, jsonDataTimeEnd):
#        self.date = str(jsonDataTimeEnd['date'])
#        self.timezone = str(jsonDataTimeEnd['timezone'])
#        self.timezone_type = str(jsonDataTimeEnd['timezone_type'])
#        
#class Date_time_begin(object):
#    """
#    
#    """
#    def __init__(self, jsonDataTimeBegin):
#        self.date = str(jsonDataTimeBegin['date'])
#        self.timezone = str(jsonDataTimeBegin['timezone'])
#        self.timezone_type = str(jsonDataTimeBegin['timezone_type'])
