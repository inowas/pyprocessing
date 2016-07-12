from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import os
import demjson
import sys


class RasterImage(object):

    def __init__(self):
        pass

    def from_file(self, input_file):
        try:
            _file = open(input_file, 'r')
            json_input = _file.read()
        except IOError as exc:
            self._error = True
            self._error_message = str(exc)
            return
        except Exception as exc:
            self._error = True
            self._error_message = str(exc)
            return
        self.decode_json(json_input)

    def from_string(self, json_input):
        self.decode_json(json_input)

    def decode_json(self, json_input):
        try:
            json_dict = demjson.decode(json_input)
        except:
            print "Something went wrong with the json decoding"
            return

        if 'data' in json_dict:
            self._data = json_dict['data']
        else:
            print 'Data not provided'
            sys.exit()

        if 'nodata' in json_dict:
            self._nodata = json_dict['nodata']
        else:
            print 'Default nodata value is used'
            self._nodata = -9999.

        if 'workspace' in json_dict:
            self._workspace = json_dict['workspace']
        else:
            print 'Default workspace is used'
            self._workspace = os.path.join('images')

        if 'name' in json_dict:
            self._name = json_dict['name']
        else:
            print 'Default name is used'
            self._name = 'image'
    
        self.min_val = 5
        self.min_real_value = False
        self.max_val = 95
        self.max_real_value = False
        
        if 'min' in json_dict:
            if type(json_dict['min']) is float or type(json_dict['min']) is int:
                self.min_val = json_dict['min']
                self.min_real_value = True
            elif json_dict['min'][-1] == '%':
                self.min_val = float(json_dict['min'][:-1])
                self.min_real_value = False
            else:
                print 'Default 5 percentile is used for min boundary'
        else:
            print 'Default 5 percentile is used for min boundary'

        if 'max' in json_dict:
            if type(json_dict['max']) is float or type(json_dict['max']) is int:
                self.max_val = json_dict['max']
                self.max_real_value = True
            elif json_dict['max'][-1] == '%':
                self.max_val = float(json_dict['max'][:-1])
                self.max_real_value = False
            else:
                print 'Default 95 percentile is used for max boundary'
        else:
            print 'Default 95 percentile is used for max boundary'


        if 'color_scheme' in json_dict:
            self._color_scheme = json_dict['color_scheme']
        else:
            self._color_scheme = 'jet'

    def setOutputFileName(self, name):
        self._name = name

    def makeImage(self):
        self.fileName = self.writeRaster(self._data, self._nodata,
                                         self._workspace,
                                         self._name, self.min_val,
                                         self.max_val, self.min_real_value,
                                         self.max_real_value, self._color_scheme,)
        return self.fileName

    @staticmethod
    def writeRaster(data, nodata, workspace, name, min_val, max_val,
                    min_real_value, max_real_value, color_scheme='jet'):

        try:
            data = np.array(data)
            no_nodata = data.astype(float)
        except:
            print 'Data array format is not correct'
            return

        # Checking if nodata is iterable
        try:
            iterator = iter(nodata)
        except TypeError:
            nodata = [nodata]
        else:
            pass

        valid_color_schemes = ['jet', 'gist_earth', 'rainbow', 'terrain', 'gist_rainbow']
        if color_scheme not in valid_color_schemes:
            print 'Not valid color scheme name'
            return

        alfa = np.ones((np.shape(data)[0], np.shape(data)[1]))
        for i in nodata:
            alfa[data == i] = 0
            no_nodata[data == i] = np.nan
            
        max_bound = max_val if max_real_value else np.nanpercentile(no_nodata, max_val)
        min_bound = min_val if min_real_value else np.nanpercentile(no_nodata, min_val)
        print max_bound, min_bound
        norm = plt.Normalize(vmin=min_bound, vmax=max_bound)
        if color_scheme == 'jet':
            colors = plt.cm.jet(norm(data))
        elif color_scheme == 'gist_earth':
            colors = plt.cm.gist_earth(norm(data))
        elif color_scheme == 'rainbow':
            colors = plt.cm.rainbow(norm(data))
        elif color_scheme == 'terrain':
            colors = plt.cm.terrain(norm(data))
        elif color_scheme == 'gist_rainbow':
            colors = plt.cm.gist_rainbow(norm(data))

        rgb_uint8 = (np.dstack((colors[:, :, 0],
                                colors[:, :, 1],
                                colors[:, :, 2],
                                alfa)) * 255.999) .astype(np.uint8)
        print rgb_uint8
        
        img = Image.fromarray(rgb_uint8)
        fileName = os.path.join(workspace, name)
        img.save(fileName)
        print 'Raster image is created ' + fileName
        return 'Raster image is created ' + fileName
