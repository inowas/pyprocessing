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

        if 'min_percentile' in json_dict:
            self._min_percentile = json_dict['min_percentile']
        else:
            self._min_percentile = 5.

        if 'max_percentile' in json_dict:
            self._max_percentile = json_dict['max_percentile']
        else:
            self._max_percentile = 95.

        if 'color_scheme' in json_dict:
            self._color_scheme = json_dict['color_scheme']
        else:
            self._color_scheme = 'jet'
    
    def setOutputFileName(self, name):
        self._name = name

    def makeImage(self):
        self.fileName = self.writeRaster(self._data, self._nodata,
                                         self._workspace,
                                         self._name, self._color_scheme,
                                         self._min_percentile,
                                         self._max_percentile)
        return self.fileName

    @staticmethod
    def writeRaster(data, nodata, workspace, name, color_scheme='jet',
                    min_percentile=5, max_percentile=95):

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

        valid_color_schemes = ['jet', 'gist_earth', 'rainbow', 'terrain']
        if color_scheme not in valid_color_schemes:
            print 'Not valid color scheme name'
            return

        alfa = np.ones((np.shape(data)[0], np.shape(data)[1]))
        for i in nodata:
            alfa[data == i] = 0
            no_nodata[data == i] = np.nan

        norm = plt.Normalize(vmin=np.nanpercentile(no_nodata, min_percentile),
                             vmax=np.nanpercentile(no_nodata, max_percentile))
        if color_scheme == 'jet':
            colors = plt.cm.jet(norm(data))
        elif color_scheme == 'gist_earth':
            colors = plt.cm.gist_earth(norm(data))
        elif color_scheme == 'rainbow':
            colors = plt.cm.rainbow(norm(data))
        elif color_scheme == 'terrain':
            colors = plt.cm.terrain(norm(data))

        rgb_uint8 = (np.dstack((colors[:, :, 0],
                                colors[:, :, 1],
                                colors[:, :, 2],
                                alfa)) * 255.999) .astype(np.uint8)

        img = Image.fromarray(rgb_uint8)
        fileName = os.path.join(workspace, name + '.png')
        img.save(fileName)

        return 'Raster image is created ' + fileName
