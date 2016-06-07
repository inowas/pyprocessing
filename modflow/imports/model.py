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
from imports.utils import well_spd


class Model(object):
    """
    Model class
    """
    strt_head_mode = 'warmed_up'

    def __init__(self):
        pass

    def setFromJson(self, request_data):
        """
        Function to get model's data and create respective model objects
        """
        self.base_url = request_data["base_url"]
        responce = urlopen(self.base_url + '/api/models/' +
                           request_data['model_id'] + '.json').read()
        self.jsonData = json.loads(responce)
        self.id = str(self.jsonData['id'])
        self.owner_id = str(self.jsonData['owner']['id'])
        self.describtion = str(self.jsonData['description'])
        self.name = str(self.jsonData['name'])
        self.area = Area(self.jsonData['area'])
        self.soil_model = Soil_model(self.jsonData['soil_model'], self.base_url)
        self.calculation_properties = Calculation_properties(self.jsonData['calculation_properties'])
        self.boundaries = [Boundary(i, self.base_url)
                           for i in self.jsonData['boundaries']]
        self.wells = [Well(i, self.base_url)
                      for i in self.jsonData['wells']]

        if 'strt_head_mode' in request_data:
            self.strt_head_mode = request_data['strt_head_mode']

    def set_properties(self, nx, ny):
        """
        Calculating properties of the model objects into Flopy input format
        """
        self.IBOUND = ibound.give_ibound(line=self.area.boundary_line,
                                         number_of_layers=len(self.soil_model.geological_layers),
                                         nx=nx,
                                         ny=ny,
                                         xmin=self.area.xmin,
                                         xmax=self.area.xmax,
                                         ymin=self.area.ymin,
                                         ymax=self.area.ymax)

        self.layers_properties = {}
        for i, prop in enumerate(self.soil_model.geological_layers[0].properties):
            self.layers_properties[prop.property_type_abr] = [layer.properties[i].values[0].data
                                                              for layer
                                                              in self.soil_model.geological_layers]

        self.SPD_list = [line_boundary_interpolation.give_SPD(points=boundary.points_xy,
                                                              point_vals=boundary.points_values,
                                                              line=boundary.boundary_line,
                                                              stress_period_list=range(len(self.calculation_properties.stress_periods)),
                                                              interract_layers=[i for i
                                                                                in range(len(self.soil_model.geological_layers))
                                                                                if self.soil_model.geological_layers[i].id in boundary.interracted_layers_ids],
                                                              xmin=self.area.xmin,
                                                              xmax=self.area.xmax,
                                                              ymin=self.area.ymin,
                                                              ymax=self.area.ymax,
                                                              nx = nx,
                                                              ny = ny,
                                                              layers_botm=self.layers_properties['eb'],
                                                              strt_head_mode=self.strt_head_mode)
                                                              for boundary in self.boundaries]
        self.WELL_SPD = well_spd.give_well_spd(xmin=self.area.xmin,
                                               xmax=self.area.xmax,
                                               ymin=self.area.ymin,
                                               ymax=self.area.ymax,
                                               nx=nx, ny=ny,
                                               x=[i.x for i in self.wells],
                                               y=[i.y for i in self.wells],
                                               rates=[i.rates for i in self.wells],
                                               layers=[i.find_interracted_layer(self.soil_model)[0] for i in self.wells],
                                               strt_mode='warmed_up',
                                               stress_periods=range(len(self.calculation_properties.stress_periods)))

        self.NPER = len(self.SPD_list[0])
        if self.strt_head_mode == 'simple':
            self.PERLEN = [i.length for i in self.calculation_properties.stress_periods]
            self.STEADY = False
        elif self.strt_head_mode == 'warmed_up':
            self.STEADY = [True] + [False for i in range(self.NPER - 1)]
            self.PERLEN = [100] + [i.length for i in self.calculation_properties.stress_periods]

    def run_model(self, workspace):

        MF = flopy.modflow.Modflow(self.id, exe_name='mf2005',
                                   version='mf2005', model_ws=workspace)
        DIS_PACKAGE = flopy.modflow.ModflowDis(MF,
                                               nlay=np.shape(self.IBOUND)[0],
                                               nrow=np.shape(self.IBOUND)[1],
                                               ncol=np.shape(self.IBOUND)[2],
                                               delr=(self.area.ymax-self.area.ymin)/np.shape(self.IBOUND)[1],
                                               delc=(self.area.xmax-self.area.xmin)/np.shape(self.IBOUND)[2],
                                               botm=self.layers_properties['eb'] if 'eb' in self.layers_properties else None,
                                               top=self.layers_properties['et'][0] if 'et' in self.layers_properties else None,
                                               laycbd=0,
                                               steady=self.STEADY,
                                               nper=self.NPER,
                                               nstp=self.PERLEN,
                                               perlen=self.PERLEN)
        BAS_PACKAGE = flopy.modflow.ModflowBas(MF,
                                               ibound=self.IBOUND,
                                               strt=np.mean(np.array(self.layers_properties['et'][0])),
                                               hnoflo=-9999,
                                               stoper=1.)
        OC_PACKAGE = flopy.modflow.ModflowOc(MF)
        LPF_PACKAGE = flopy.modflow.ModflowLpf(MF,
                                               hk=self.layers_properties['hc'] if 'hc' in self.layers_properties else None,
                                               laytyp=1,
                                               hani=self.layers_properties['ha'] if 'ha' in self.layers_properties else None,
                                               vka=self.layers_properties['va'] if 'va' in self.layers_properties else None)
        PCG_PACKAGE = flopy.modflow.ModflowPcg(MF,
                                               mxiter=900,
                                               iter1=900)
        CHD = flopy.modflow.ModflowChd(MF, stress_period_data=self.SPD_list[0])
        WEL = flopy.modflow.ModflowWel(MF, stress_period_data=self.WELL_SPD)
        # Write Modflow input files and run the model
        MF.write_input()
        MF.plot()
        MF.run_model()

    def create_phantomes(self, phantome_wells):
        # Stuff for optimization comes here
        self.phantom_wells = [Phantome_well[i] for i in phantome_wells]
        self.phantome_SPD = {}


class Well(object):
    """
    Wells class
    """
    def __init__(self, jsonDataWell, base_url):
        self.id = str(jsonDataWell['id'])
        url = base_url + '/api/wells/' + self.id + '.json'
        responce = urlopen(url).read()
        jsonData = json.loads(responce)
#        print jsonData
        self.x = float(jsonData['point']['x'])
        self.y = float(jsonData['point']['y'])
        self.interracted_layer_id = str(jsonData['layer'])

        rate_property = [Property(i, base_url)
                         for i
                         in jsonData['properties']
                         if i['property_type']['abbreviation'] == 'pur']
        top_property = [Property(i, base_url)
                        for i
                        in jsonData['properties']
                        if i['property_type']['abbreviation'] == 'pur']
        botm_property = [Property(i, base_url)
                         for i
                         in jsonData['properties']
                         if i['property_type']['abbreviation'] == 'pur']

        self.rates = [i.data for i in rate_property[0].values]
        self.top = [i.data for i in top_property[0].values]
        self.botm = [i.data for i in botm_property[0].values]

    def find_interracted_layer(self, soil_model):
        return [i for i in range(len(soil_model.geological_layers))
                if soil_model.geological_layers[i].id == self.interracted_layer_id]


class Phantome_well(object):
    def __init__(self):
        self.x
        self.y
        self.row
        self.column
        self.layer
        self.rate

    def give_SPD_singe(self):
        return [self.layer, self.row, self.column, self.rate]


class Calculation_properties(object):
    """
    Calculation properties class. ---> Model.calculation_properties
    """
    def __init__(self, jsonDataCalculation):
        self.calculation_type = str(jsonDataCalculation['calculation_type'])
        self.recalculation = jsonDataCalculation['recalculation']
        self.initial_values = Initial_values(jsonDataCalculation['initial_values'])
        self.stress_periods = [Stress_period(i)
                               for i in jsonDataCalculation['stress_periods']]


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

        self.boundary_line = [self.geometry[0][str(i)]
                              for i in sorted(points_id)]

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
        self.dateTimeBegin = datetime.datetime.strptime(begin_raw,
                                                        "%Y-%m-%d %H:%M:%S.%f")
        self.dateTimeEnd = datetime.datetime.strptime(end_raw,
                                                      "%Y-%m-%d %H:%M:%S.%f")
        self.length = (self.dateTimeEnd - self.dateTimeBegin).days


class Soil_model(object):
    """
    Soil model class. ---> Model.soil_model
    """
    def __init__(self, jsonDataSoil, base_url):
        self.id = str(jsonDataSoil['id'])
        layers_unsorted = [Geological_layer(i, base_url)
                           for i
                           in jsonDataSoil['geological_layers']]
        self.geological_layers = sorted(layers_unsorted,
                                        key=methodcaller('avg_top_elev'),
                                        reverse=True)

class Geological_layer(object):
    """
    Geological layer class. ---> Soil_model.geological_layers
    """
    def __init__(self, jsonDataLayer, base_url):
        self.id = str(jsonDataLayer['id'])
        # Set data
        url = base_url + '/api/geologicallayers/' + self.id + '.json'
        responce = urlopen(url).read()
        jsonData = json.loads(responce)
        self.properties = [Property(i, base_url)
                           for i
                           in jsonData['properties']]
        self.top = [i.values[0].data
                    for i
                    in self.properties
                    if i.property_type_abr == 'et']
        self.botm = [i.values[0].data
                     for i
                     in self.properties
                     if i.property_type_abr == 'eb']

    def avg_top_elev(self):
        """
        Function returning mean layer elevation used to define
        order of the layers
        """
        return np.mean(np.array(self.top))

class Boundary(object):
    """
    Boundary class. ---> Model.boundaries
    """
    def __init__(self, jsonDataBoundary, base_url):
        self.id = str(jsonDataBoundary['id'])
        # Set data
        url = base_url + '/api/boundaries/'+self.id+'.json'
        responce = urlopen(url).read()
        jsonData = json.loads(responce)

        self.geometry = jsonData['geometry']
        self.observation_points = [Observation_points(i, base_url) for i in jsonData['observation_points']] if len(jsonData['observation_points']) > 0 else None
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
            self.points_values.append([i.data for i in self.observation_points[point].properties[0].values])
            self.points_xy.append([self.observation_points[point].x, self.observation_points[point].y])

        self.interracted_layers_ids = [str(i['id']) for i in jsonData['geological_layers']]

class Observation_points(object):
    """
    Observation point class. ---> Boundary.observation_points
    """
    def __init__(self, jsonDataObservationPoints, base_url):

        self.id = str(jsonDataObservationPoints['id'])
        self.properties = [Property(i, base_url) for i in jsonDataObservationPoints['properties']] if len(jsonDataObservationPoints['properties']) > 0 else None
        self.x = float(jsonDataObservationPoints['point']['x'])
        self.y = float(jsonDataObservationPoints['point']['y'])

class Property(object):
    """

    """
    def __init__(self, jsonDataProperty, base_url):
        self.id = str(jsonDataProperty['id'])
        self.property_type_abr = str(jsonDataProperty['property_type']['abbreviation'])
        self.values = [Value(i, base_url) for i in jsonDataProperty['values']] if len(jsonDataProperty['values']) > 0 else None


class Value(object):
    """

    """
    def __init__(self, jsonDataValue, base_url):
        if 'value' in jsonDataValue:
            self.dataType = 'singleValue'
            self.data = float(jsonDataValue['value'])
        elif 'raster' in jsonDataValue:
            self.dataType = 'raster'
            rasterID = str(jsonDataValue['raster']['id'])
            url = base_url + '/api/rasters/' + rasterID + '.json'
            responce = urlopen(url).read()
            rasterInfo = json.loads(responce)
            self.raster_nx = int(rasterInfo['grid_size']['n_x'])
            self.raster_ny = int(rasterInfo['grid_size']['n_y'])
            self.raster_xmin = float(rasterInfo['bounding_box']['x_min'])
            self.raster_xmax = float(rasterInfo['bounding_box']['x_max'])
            self.raster_ymin = float(rasterInfo['bounding_box']['y_min'])
            self.raster_ymax = float(rasterInfo['bounding_box']['y_max'])
            self.raster_srid = float(rasterInfo['bounding_box']['srid'])
            self.raster_nodata = float(rasterInfo['no_data_val'])
            self.data = rasterInfo['data']
        else:
            self.data = None

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
