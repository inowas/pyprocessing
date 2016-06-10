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
        self.request_data = request_data
        self.base_url = request_data["base_url"]
        responce = urlopen(self.base_url + '/api/models/' +
                           request_data['model_id'] + '.json').read()
        self.jsonData = json.loads(responce)
        self.id = str(self.jsonData['id'])
        self.owner_id = str(self.jsonData['owner']['id'])
        self.name = str(self.jsonData['name'])
        self.area = Area(self.jsonData['area'])
        self.soil_model = Soil_model(self.jsonData['soil_model'], self.base_url)
        self.calculation_properties = Calculation_properties(self.jsonData['calculation_properties'])
        self.boundaries = [Boundary(i, self.base_url)
                           for i in self.jsonData['boundaries']]

        if 'strt_head_mode' in request_data:
            self.strt_head_mode = request_data['strt_head_mode']

    def set_properties(self):
        """
        Calculating properties of the model objects into Flopy input format
        """
        self.IBOUND = ibound.give_ibound(line=self.area.boundary_line,
                                         number_of_layers=len(self.soil_model.geological_layers),
                                         nx=self.jsonData['grid_size']['n_x'],
                                         ny=self.jsonData['grid_size']['n_y'],
                                         xmin=self.area.xmin,
                                         xmax=self.area.xmax,
                                         ymin=self.area.ymin,
                                         ymax=self.area.ymax)
        print 'IBOUND array is created'
        self.layers_properties = {}
        for i, prop in enumerate(self.soil_model.geological_layers[1].properties):
            self.layers_properties[prop.property_type_abr] = [layer.properties[i].values[0].data
                                                              for layer
                                                              in self.soil_model.geological_layers]
        self.botm = [layer.botm[0] for layer in self.soil_model.geological_layers]
        self.top = self.soil_model.geological_layers[0].top[0]
        print self.top
        print self.botm
        print 'Layers properties are written'
        self.GHB_SPD = [boundary.give_spd(area_xmin=self.area.xmin,
                                           area_xmax=self.area.xmax,
                                           area_ymin=self.area.ymin,
                                           area_ymax=self.area.ymax,
                                           grid_nx=self.jsonData['grid_size']['n_x'],
                                           grid_ny=self.jsonData['grid_size']['n_y'],
                                           layers=[i for i in range(len(self.soil_model.geological_layers)) if self.soil_model.geological_layers[i].id in boundary.interracted_layers_ids],
                                           layers_bot=self.layers_properties['eb'],
                                           strt=self.strt_head_mode,
                                           stress_periods=range(len(self.calculation_properties.stress_periods))) for boundary in self.boundaries if boundary.type == 'GHB']
        if len(self.GHB_SPD) > 0:
            dic = {}
            for i in range(len(self.GHB_SPD) - 1):
                for j in self.GHB_SPD[i]:
                    dic[j] = self.GHB_SPD[0][j] + self.GHB_SPD[i + 1][j]
            self.GHB_SPD = dic

        self.CHD_SPD = [boundary.give_spd(area_xmin=self.area.xmin,
                                           area_xmax=self.area.xmax,
                                           area_ymin=self.area.ymin,
                                           area_ymax=self.area.ymax,
                                           grid_nx=self.jsonData['grid_size']['n_x'],
                                           grid_ny=self.jsonData['grid_size']['n_y'],
                                           layers=[i for i in range(len(self.soil_model.geological_layers)) if self.soil_model.geological_layers[i].id in boundary.interracted_layers_ids],
                                           layers_bot=self.layers_properties['eb'],
                                           strt=self.strt_head_mode,
                                           stress_periods=range(len(self.calculation_properties.stress_periods))) for boundary in self.boundaries if boundary.type == 'CHB']


        if len(self.CHD_SPD) > 0:
            dic = {}
            for i in range(len(self.CHD_SPD) - 1):
                for j in self.CHD_SPD[i]:
                    dic[j] = self.CHD_SPD[0][j] + self.CHD_SPD[i + 1][j]
            self.CHD_SPD = dic


        self.WEL_SPD = well_spd.give_well_spd(xmin=self.area.xmin,
                                               xmax=self.area.xmax,
                                               ymin=self.area.ymin,
                                               ymax=self.area.ymax,
                                               nx=self.jsonData['grid_size']['n_x'],
                                               ny=self.jsonData['grid_size']['n_y'],
                                               x=[boundary.x for boundary in self.boundaries if boundary.type == 'WEL'],
                                               y=[boundary.y for boundary in self.boundaries if boundary.type == 'WEL'],
                                               rates=[boundary.rates for boundary in self.boundaries if boundary.type == 'WEL'],
                                               layers=[boundary.find_interracted_layer(self.soil_model)[0] for boundary in self.boundaries if boundary.type == 'WEL'],
                                               strt_mode='warmed_up',
                                               stress_periods=range(len(self.calculation_properties.stress_periods)))


        print 'Stress period data objects are created'

        self.NSTP = [i.nstp for i in self.calculation_properties.stress_periods]
        self.PERLEN = [i.length for i in self.calculation_properties.stress_periods]
        self.STEADY = [i.steady for i in self.calculation_properties.stress_periods]
        if self.strt_head_mode == 'warmed_up':
            self.STEADY = [True] + self.STEADY
            self.PERLEN = [100] + self.PERLEN
            self.NSTP = [1] + self.NSTP
        print 'PERLEN: ' + str(self.PERLEN)
        print 'STEADY: ' + str(self.STEADY)
        print 'NSTP: ' + str(self.NSTP)

    def run_model(self, workspace):
        MF = flopy.modflow.Modflow(self.id, exe_name='mf2005',
                                   version='mf2005', model_ws=workspace)
        DIS_PACKAGE = flopy.modflow.ModflowDis(MF,
                                               nlay=np.shape(self.IBOUND)[0],
                                               nrow=np.shape(self.IBOUND)[1],
                                               ncol=np.shape(self.IBOUND)[2],
                                               delr=(self.area.ymax-self.area.ymin)/np.shape(self.IBOUND)[1],
                                               delc=(self.area.xmax-self.area.xmin)/np.shape(self.IBOUND)[2],
                                               botm=self.botm,
                                               top=self.top,
                                               laycbd=0,
                                               steady=self.STEADY,
                                               nper=len(self.NSTP),
                                               nstp=self.NSTP,
                                               perlen=self.PERLEN)
        BAS_PACKAGE = flopy.modflow.ModflowBas(MF,
                                               ibound=self.IBOUND,
                                               strt=np.mean(np.array(self.layers_properties['et'][0] if 'et' in self.layers_properties else 100)),
                                               hnoflo=-9999,
                                               stoper=1.)
        OC_PACKAGE = flopy.modflow.ModflowOc(MF)
        LPF_PACKAGE = flopy.modflow.ModflowLpf(MF,
                                               hk=self.layers_properties['hc'] if 'hc' in self.layers_properties else 1.0,
                                               hani=self.layers_properties['ha'] if 'ha' in self.layers_properties else 1.0,
                                               vka=self.layers_properties['va'] if 'va' in self.layers_properties else 1.0)
        PCG_PACKAGE = flopy.modflow.ModflowPcg(MF,
                                               mxiter=900,
                                               iter1=900)

        if len(self.CHD_SPD) > 0:
            CHD = flopy.modflow.ModflowChd(MF,
                                           stress_period_data=self.CHD_SPD)
        if len(self.GHB_SPD) > 0:
            CHD = flopy.modflow.ModflowChd(MF,
                                           stress_period_data=self.GHB_SPD)
        if len(self.WEL_SPD) > 0:
            WEL = flopy.modflow.ModflowWel(MF,
                                           stress_period_data=self.WEL_SPD)
        # Write Modflow input files and run the model
        MF.write_input()
        print 'Modflow files are written'
#        MF.plot()
        print 'Model calculation started'
        MF.run_model()
        print 'Model calculation finished'
    def create_phantomes(self, phantome_wells):
        # Stuff for optimization comes here
        self.phantom_wells = [Phantome_well[i] for i in phantome_wells]
        self.phantome_SPD = {}



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
        self.initial_values = Initial_values(jsonDataCalculation['initial_values'])
        self.stress_periods = [Stress_period(i)
                               for i in jsonDataCalculation['stress_periods']]


class Area(object):
    """
    Area class. ---> Model.area
    """
    def __init__(self, jsonDataArea):
        self.id = str(jsonDataArea['id'])
        print 'Getting data for the area id ' + self.id
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
        if 'head_from_top_elevation' in jsonDataCalculationInitial:
            self.head_from_top_elevation = jsonDataCalculationInitial['head_from_top_elevation']
        if 'interpolation' in jsonDataCalculationInitial:
            self.interpolation = jsonDataCalculationInitial['interpolation']
        if 'steady_state_calculation' in jsonDataCalculationInitial:
            self.steady_state_calculation = jsonDataCalculationInitial['steady_state_calculation']


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
        self.nstp = jsonDataStress['numberOfTimeSteps']
        self.steady = jsonDataStress['steady']


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
        print 'Getting data for the Layer id ' + self.id
        # Set data
        url = base_url + '/api/geologicallayers/' + self.id + '.json'
        responce = urlopen(url).read()
        jsonData = json.loads(responce)
        self.properties = [Property(i, base_url)
                           for i
                           in jsonData['properties']]
        self.hc = [i.values[0].data
                    for i
                    in self.properties
                    if i.property_type_abr == 'hc']
#        self.vka = [i.values[0].data
#                    for i
#                    in self.properties
#                    if i.property_type_abr == 'et']
#        self.hani = [i.values[0].data
#                    for i
#                    in self.properties
#                    if i.property_type_abr == 'et']
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
        self.type = str(jsonData['type'])
        print 'Preparing data for the '+self.type+' boundary id ' + self.id
        self.data_given_at = None
        # Properies
        if 'properties' in jsonData and len(jsonData['properties']) > 0:
            self.data_given_at = 'geometry'
            self.properties = [Property(i, base_url)
                               for i
                               in jsonData['properties']]
            self.value = []
            self.value.append([i.data for i in self.properties[0].values])
        if 'observation_points' in jsonData and len(jsonData['observation_points']) > 0:
            # Observation points
            self.data_given_at = 'points'
            self.observation_points = []
            self.observation_points = [Observation_points(i, base_url)
                                       for i in jsonData['observation_points']]
            self.points_xy = []
            self.points_values = []
            for point in range(len(self.observation_points)):
                print [i for i in self.observation_points[point].properties]
                self.points_values.append([i.data for i
                                          in self.observation_points[point].properties[0].values])
                self.points_xy.append([self.observation_points[point].x,
                                       self.observation_points[point].y])

        if self.type == 'WEL':
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
        else:
            self.geometry = jsonData['geometry']
            points_id = []
            for point in self.geometry:
                try:
                    points_id.append(int(point))
                except:
                    pass
            self.boundary_line = [self.geometry[str(i)] for i in range(len(points_id))]
            # Layers
            self.interracted_layers_ids = [str(i['id']) for i in jsonData['geological_layers']]

    def find_interracted_layer(self, soil_model):
        return [i for i in range(len(soil_model.geological_layers))
                if soil_model.geological_layers[i].id == self.interracted_layer_id]

    def give_spd(self, area_xmin, area_xmax, area_ymin, area_ymax, grid_nx, grid_ny, layers, layers_bot, strt, stress_periods):
        self.spd = line_boundary_interpolation.give_SPD(points=self.points_xy if self.data_given_at == 'points' else [self.boundary_line[0]],
                                                        point_vals=self.points_values if self.data_given_at == 'points' else self.value,
                                                        line=self.boundary_line,
                                                        stress_period_list=stress_periods,
                                                        interract_layers=layers if len(layers)>0 else range(len(layers_bot)),
                                                        xmin=area_xmin,
                                                        xmax=area_xmax,
                                                        ymin=area_ymin,
                                                        ymax=area_ymax,
                                                        nx=grid_nx,
                                                        ny=grid_ny,
                                                        layers_botm=layers_bot,
                                                        strt_head_mode=strt)
        return self.spd



class Observation_points(object):
    """
    Observation point class. ---> Boundary.observation_points
    """
    def __init__(self, jsonDataObservationPoints, base_url):
        self.id = str(jsonDataObservationPoints['id'])
        print 'Getting data for the observation point id ' + self.id
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
