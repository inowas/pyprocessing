#! /usr/env python

import demjson
import flopy.modflow as mf
import flopy.utils as fu
import os
import urllib
import urllib2


class InowasFlopy:
    """The Flopy Class"""

    _input_file = ""
    _api_key = ""
    _api_url = ""
    _data_folder = ""
    _model_id = ""
    _commands = []
    _packages = []
    _packageContent = {}
    _mf = None

    def __init__(self):
        pass

    def from_files(self, input_file):
        self._input_file = input_file
        self._packages = self.read_json_from_file(self._input_file+'.pak')
        self.read_packages(self._packages)
        self.create_model(self._packages, self._packageContent)

    def from_webapi(self, api_url, data_folder, model_id, api_key):
        self._api_url = api_url
        self._data_folder = data_folder
        self._api_key = api_key
        self._model_id = model_id

        print 'Requesting cmd package from: %s' % self.get_packages_url(self._api_url, self._model_id)
        self._commands = self.read_json_from_api(self.get_packages_url(self._api_url, self._model_id), api_key)

        if self._commands['load_from'] == 'api':
            self._packages = self._commands['packages']
            self.read_packages_from_api(self._packages)
            self.create_model(self._packages, self._packageContent)

            if self._commands['write_input']:
                self.write_input_model()

        if self._commands['load_from'] == 'nam':
            self.load_model()

        if self._commands['check']:
            self.check_model()

        if self._commands['run']:
            self.run_model()

        if self._commands['get_data']:
            if 'totim' in self._commands['get_data']:
                totim = self._commands['get_data']['totim']
                heads = self.get_data(totim=totim)
                self.submit_heads(
                    self.get_submit_heads_url(self._api_url, self._model_id),
                    self._api_key,
                    heads=heads,
                    totim=totim
                )

    def read_packages(self, packages):
        for package in packages:
            self._packageContent[package] = self.read_json_from_file(self._input_file+'.'+package)

    def read_packages_from_api(self, packages):
        for package in packages:
            print 'Requesting data of %s-Package from: %s' % (
                package, self.get_package_url(self._api_url, self._model_id, package)
            )

            self._packageContent[package] = self.read_json_from_api(
                self.get_package_url(self._api_url, self._model_id, package),
                self._api_key
            )

    def create_model(self, packages, package_content):
        for package in packages:
            print 'Create Flopy Package: %s' % package
            self.create_package(package, package_content[package])

    def write_input_model(self):
        print 'Write input files'
        self._mf.write_input()

    def run_model(self):
        print 'Run the model'
        self._mf.run_model()

    def load_model(self):
        self.read_packages_from_api(['mf'])

        workspace = os.path.join(
            self._data_folder,
            self._model_id,
            self._packageContent['mf']['model_ws']
        )

        nam_file = os.path.join(
            workspace,
            self._packageContent['mf']['modelname'] + '.nam')

        print 'Load model from %s' % nam_file
        self._mf = mf.Modflow.load(
            nam_file,
            version=self._packageContent['mf']['version'],
            exe_name=self._packageContent['mf']['exe_name'],
            model_ws=workspace
        )

    def check_model(self):
        self._mf.check()

    def get_data(self, totim=0):
        if 'mf' not in self._packageContent:
            self.read_packages_from_api(['mf'])

        head_file = os.path.join(
            self._data_folder,
            self._model_id,
            self._packageContent['mf']['model_ws'],
            self._packageContent['mf']['modelname'] + '.hds')

        times = fu.HeadFile(head_file).get_times()
        i = 0
        while i < len(times):
            if times[i] > totim:
                totim = times[i]
                break
            i += 1

        return fu.HeadFile(head_file).get_data(totim=totim)

    def create_package(self, name, content):
        if name == 'mf':
            model_ws = os.path.realpath(os.path.join(self._data_folder, self._model_id, content['model_ws']))
            if not os.path.exists(model_ws):
                os.makedirs(model_ws)

            self._mf = mf.Modflow(
                modelname=content['modelname'],
                exe_name=content['exe_name'],
                version=content['version'],
                model_ws=model_ws
            )
        if name == 'dis':
            mf.ModflowDis(
                self._mf,
                nlay=content['nlay'],
                nrow=content['nrow'],
                ncol=content['ncol'],
                nper=content['nper'],
                delr=content['delr'],
                delc=content['delc'],
                laycbd=content['laycbd'],
                top=content['top'],
                botm=content['botm'],
                perlen=content['perlen'],
                nstp=content['nstp'],
                tsmult=content['tsmult'],
                steady=content['steady'],
                itmuni=content['itmuni'],
                lenuni=content['lenuni'],
                extension=content['extension'],
                unitnumber=content['unitnumber'],
                xul=content['xul'],
                yul=content['yul'],
                rotation=content['rotation'],
                proj4_str=content['proj4_str'],
                start_datetime=content['start_datetime']
            )
        if name == 'bas':
            mf.ModflowBas(
                self._mf,
                ibound=content['ibound'],
                strt=content['strt'],
                ifrefm=content['ifrefm'],
                ixsec=content['ixsec'],
                ichflg=content['ichflg'],
                stoper=content['stoper'],
                hnoflo=content['hnoflo'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )
        if name == 'lpf':
            mf.ModflowLpf(
                self._mf,
                laytyp=content['laytyp'],
                layavg=content['layavg'],
                chani=content['chani'],
                layvka=content['layvka'],
                laywet=content['laywet'],
                ipakcb=content['ipakcb'],
                hdry=content['hdry'],
                iwdflg=content['iwdflg'],
                wetfct=content['wetfct'],
                iwetit=content['iwetit'],
                ihdwet=content['ihdwet'],
                hk=content['hk'],
                hani=content['hani'],
                vka=content['vka'],
                ss=content['ss'],
                sy=content['sy'],
                vkcb=content['vkcb'],
                wetdry=content['wetdry'],
                storagecoefficient=content['storagecoefficient'],
                constantcv=content['constantcv'],
                thickstrt=content['thickstrt'],
                nocvcorrection=content['nocvcorrection'],
                novfc=content['novfc'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )
        if name == 'pcg':
            mf.ModflowPcg(
                self._mf,
                mxiter=content['mxiter'],
                iter1=content['iter1'],
                npcond=content['npcond'],
                hclose=content['hclose'],
                rclose=content['rclose'],
                relax=content['relax'],
                nbpol=content['nbpol'],
                iprpcg=content['iprpcg'],
                mutpcg=content['mutpcg'],
                damp=content['damp'],
                dampt=content['dampt'],
                ihcofadd=content['ihcofadd'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )
        if name == 'oc':
            mf.ModflowOc(
                self._mf,
                ihedfm=content['ihedfm'],
                iddnfm=content['iddnfm'],
                chedfm=content['chedfm'],
                cddnfm=content['cddnfm'],
                cboufm=content['cboufm'],
                compact=content['compact'],
                stress_period_data=self.get_stress_period_data(content['stress_period_data']),
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )
        if name == 'riv':
            mf.ModflowRiv(
                self._mf,
                ipakcb=content['ipakcb'],
                stress_period_data=content['stress_period_data'],
                dtype=content['dtype'],
                extension=content['extension'],
                unitnumber=content['unitnumber'],
                options=content['options'],
                naux=content['naux']
            )
        if name == 'wel':
            mf.ModflowWel(
                self._mf,
                ipakcb=content['ipakcb'],
                stress_period_data=content['stress_period_data'],
                dtype=content['dtype'],
                extension=content['extension'],
                unitnumber=content['unitnumber'],
                options=content['options']
            )
        if name == 'rch':
            mf.ModflowRch(
                self._mf,
                ipakcb=content['ipakcb'],
                nrchop=content['nrchop'],
                rech=content['rech'],
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )

    @staticmethod
    def read_json_from_file(filename):
        _file = open(filename, 'r')
        return demjson.decode(_file.read())

    @staticmethod
    def read_json_from_api(url, api_key):
        request = urllib2.Request(url)
        request.add_header('X-AUTH-TOKEN', api_key)
        response = urllib2.urlopen(request)
        return demjson.decode(response.read())

    @staticmethod
    def submit_heads(url, api_key, heads, totim):
        print 'Post head-data of totim=%s to %s' % (totim, url)
        request = urllib2.Request(url)
        request.data = urllib.urlencode({'heads': demjson.encode(heads.tolist()), 'totim': totim})
        request.add_header('X-AUTH-TOKEN', api_key)
        response = urllib2.urlopen(request)
        print response.read()

    @staticmethod
    def get_packages_url(api_url, model_id):
        url = '%s/modflowmodels/%s/flopy.json' % (api_url, model_id)
        return url

    @staticmethod
    def get_package_url(api_url, model_id, package):
        url = '%s/modflowmodels/%s/packages/%s.json' % (api_url, model_id, package)
        return url

    @staticmethod
    def get_submit_heads_url(api_url, model_id):
        url = '%s/modflowmodels/%s/heads.json' % (api_url, model_id)
        return url

    @staticmethod
    def get_stress_period_data(stress_periods):
        stress_period_data = {}
        for stress_period in stress_periods:
            stress_period_data[stress_period['stressPeriod'], stress_period['timeStep']] = stress_period['type']

        return stress_period_data
