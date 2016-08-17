#! /usr/env python

import demjson
import flopy.modflow as mf
import os
import urllib2


class InowasFlopy:
    """The Flopy Class"""

    _input_file = ""
    _api_key = ""
    _api_url = ""
    _data_folder = ""
    _model_id = ""
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

        self._packages = self.read_json_from_api(api_url+'/modflowmodel/'+model_id+'/packages.json', api_key)
        self.read_packages_from_api(self._packages)
        self.create_model(self._packages, self._packageContent)

    def read_packages(self, packages):
        for package in packages:
            self._packageContent[package] = self.read_json_from_file(self._input_file+'.'+package)

    def read_packages_from_api(self, packages):
        for package in packages:
            self._packageContent[package] = self.read_json_from_api(
                self._api_url+'/modflowmodel/'+self._model_id+'/packages/'+package+'.json',
                self._api_key
            )

    def create_model(self, packages, package_content):
        for package in packages:
            self.create_package(package, package_content[package])

        self._mf.write_input()
        self._mf.run_model()

    def create_package(self, name, content):
        if name == 'mf':

            model_ws = os.path.realpath(os.path.join(self._data_folder, self._model_id, content['model_ws']))
            if not os.path.exists(model_ws):
                os.makedirs(model_ws)

            self._mf = mf.Modflow(
                modelname=content['modelname'].replace(" ", "_"),
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
                extension=content['extension'],
                unitnumber=content['unitnumber']
            )

    @staticmethod
    def read_json_from_file(filename):
        _file = open(filename, 'r')
        return demjson.decode(_file.read())

    @staticmethod
    def read_json_from_api(url, api_key):
        print url
        request = urllib2.Request(url)
        request.add_header('X-AUTH-TOKEN', api_key)
        response = urllib2.urlopen(request)
        return demjson.decode(response.read())
