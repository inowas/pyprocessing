#! /usr/env python


from sklearn.gaussian_process import GaussianProcess
import demjson
import numpy as np


class Interpolation:
    """The interpolation class"""

    _method = ""
    _xMin = 0.0
    _xMax = 0.0
    _yMin = 0.0
    _yMax = 0.0
    _nX = 0
    _nY = 0
    _dX = 0.0
    _dY = 0.0
    _X = []
    _Y = []
    _points = []
    _output = ""
    _json_output = ""
    _error = False
    _error_message = ""

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
        except Exception as exc:
            self._error = True
            self._error_message = "Something went wrong with the json decoding"
            return

        if 'type' in json_dict:
            self._method = json_dict['type']

        if 'bounding_box' in json_dict:
            bounding_box = json_dict['bounding_box']

            if 'x_min' in bounding_box:
                self._xMin = float(bounding_box['x_min'])

            if 'x_max' in bounding_box:
                self._xMax = float(bounding_box['x_max'])

            if 'y_min' in bounding_box:
                self._yMin = float(bounding_box['y_min'])

            if 'y_max' in bounding_box:
                self._yMax = float(bounding_box['y_max'])

        if 'grid_size' in json_dict:
            grid_size = json_dict['grid_size']

            if 'n_x' in grid_size:
                self._nX = grid_size['n_x']

            if 'n_y' in grid_size:
                self._nY = grid_size['n_y']

        self._dX = (self._xMax - self._xMin) / self._nX
        self._dY = (self._yMax - self._yMin) / self._nY

        if 'point_values' in json_dict:
            self._points = json_dict['point_values']

        for point in self._points:
            if 'x' in point and 'y' in point:
                self._X.append([point['x'], point['y']])

            if 'value' in point:
                self._Y.append(point['value'])

    def calculate(self):
        if not self._error:
            try:
                if self._method == 'kriging':
                    self._output = self.kriging(self._nX, self._nY, self._X, self._Y, self._xMin, self._yMin, self._dX, self._dY)
                elif self._method == 'mean':
                    self._output = self.mean(self._nX, self._nY, self._Y)
                elif self._method == 'gaussian':
                    self._output = self.gaussian_process(self._nX, self._nY, self._X, self._Y, self._xMin, self._yMin, self._dX, self._dY)
                elif self._method == 'idw':
                    self._output = self.inverse_distance_weighting(self._nX, self._nY, self._X, self._Y, self._xMin, self._yMin, self._dX, self._dY)
                else:
                    self._error = True
                    self._error_message = 'Method %s is not supported' % self._method
            except:
                self._error = True
                self._error_message = 'Exception raised in calculation of method %s' % self._method

    def render_output(self, output_file=''):
        if self._error:
            self.render_error()
            return

        output = self.render(self._method, self._output)
        if output_file == '':
            print output
        else:
            try:
                output_file = open(output_file, 'w')
                output_file.truncate()
                output_file.write(output)
                output_file.close()
            except IOError as exc:
                self._error = True
                self._error_message = str(exc)
                self.render_error()
                return

            self.render_success()

    def render_success(self):
        result = {"success": self._method}
        print demjson.encode(result)

    def render_error(self):
        result = {"error": self._error_message}
        print demjson.encode(result)

    @staticmethod
    def render(method, output):
        if (method == 'kriging') or (method == 'mean') or (method == 'gaussian') or (method == 'idw'):
            result = {"raster": output, "method": method}
            return demjson.encode(result)

    @staticmethod
    def kriging(nx, ny, x, y, x_min, y_min, dx, dy):
        grid = np.zeros((ny, nx))

        k = kriging(np.array(x), np.array(y))
        k.train()
        for i in range(ny):
            for j in range(nx):
                cell = np.array([y_min + dy * j + .5 * dy, x_min + dx * i + .5 * dx])
                grid[i][j] = k.predict(cell)
        return grid

    @staticmethod
    def mean(nx, ny, values):
        mean_value = np.mean(values)
        grid = mean_value * np.ones((ny, nx))
        return grid
        
    @staticmethod
    def gaussian_process(nx, ny, X, y, x_min, y_min, dx, dy):
        """
        Gausian process method. To replace kriging.
        Description:
        http://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.GaussianProcess.html#sklearn.gaussian_process.GaussianProcess.predict
        The scikit learn python library should be installed
        Should be tested
        """

        # Prediction is very sensetive to the parameters below, method to be used carefully!
        gp = GaussianProcess(regr='quadratic', corr='cubic', theta0=0.1, thetaL=.001, thetaU=1., nugget=0.01)
        gp.fit(X, y)
        X_grid_x = np.linspace(x_min, x_min+dx*nx, nx)
        X_grid_y = np.linspace(y_min, y_min+dy*ny, ny)
        xv, yv = np.meshgrid(X_grid_x, X_grid_y)
        
        X_grid = np.dstack(( xv.flatten(), yv.flatten()))[0]
        grid = np.reshape(gp.predict(X_grid, eval_MSE=False, batch_size=None), (ny, nx))
        return grid

    @staticmethod
    def inverse_distance_weighting(nx, ny, X, y, x_min, y_min, dx, dy):
        """
        Inverse-distance weighting interpolation method
        """

        def pointValue(x, y, power, smoothing, xv, yv, values):
            """ This function is used inside the inverse_distance_weighting method. """
            from math import pow  
            from math import sqrt
            
            nominator=0  
            denominator=0  
            for i in range(0,len(values)):  
                dist = sqrt((x-xv[i])*(x-xv[i])+(y-yv[i])*(y-yv[i])+smoothing*smoothing)
                #If the point is really close to one of the data points, return the data point value to avoid singularities  
                if(dist<0.0000000001):  
                    return values[i]
                nominator=nominator+(values[i]/pow(dist,power))  
                denominator=denominator+(1/pow(dist,power))  
            #Return NODATA if the denominator is zero  
            if denominator > 0:  
                value = nominator/denominator  
            else: 
                value = -9999
            return value
            
        power, smoothing = 5, 0
        xv = [i[0] for i in X]
        yv = [i[1] for i in X]    
        grid = np.zeros((ny, nx))

        for i in range(nx):
            for j in range(ny):  
                grid[j][i] = pointValue((x_min + dx/2)+dx*i, (y_min + dy/2)+dy*j, power, smoothing, xv, yv, y)
        return grid
