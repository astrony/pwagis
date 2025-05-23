from qgis.core import QgsProject, QgsRectangle, QgsRasterLayer
from qgis.gui import QgsLayerTreeMapCanvasBridge
from qgis.PyQt.QtCore import Qt
import requests
import json
import os.path
import os
from pwagis.utiles import *


def loadReference(self):
    # Pipe
    self.pipeSizes = allReference(self, referenceType='self.pipeSizes')
    self.pipeClasses = allReference(self, referenceType='pipe-classes')
    self.pipeGrades = allReference(self, referenceType='pipe-grades')
    self.pipeLayings = allReference(self, referenceType='pipe-layings')
    self.pipeProducts = allReference(self, referenceType='pipe-products')
    self.pipeTypes = allReference(self, referenceType='pipe-types')
    self.pipeFunctions = allReference(self, referenceType='pipe-functions')

    # Valve
    self.valveSizes = allReference(self, referenceType='valve-sizes')
    self.valveStatus = allReference(self, referenceType='valve-status')
    self.valveTypes = allReference(self, referenceType='valve-types')
    self.valveFunctions = allReference(self, referenceType='valve-functions')

    # Firehydrant
    self.firehydrantStatus = allReference(self, referenceType='fire-hydrant-status')
    self.firehydrantSizes = allReference(self, referenceType='fire-hydrant-sizes')

    # PWA_Waterwork
    self.costcenters = allReference(self, referenceType='pwa-waterwork-costcenters')
    self.pwaStations = allReference(self, referenceType='pwa-waterwork-stations')

    # Road
    self.roadFunctions = allReference(self, referenceType='road-functions')
    self.roadTypes = allReference(self, referenceType='road-types')

    # Struct
    self.structTypes = allReference(self, referenceType='struct-type')

    # Building
    self.buildingTypes = allReference(self, referenceType='building-types')
    self.useStatus = allReference(self, referenceType='building-use-status')


""" Start Data Dic """


def allReference(self, referenceType):
    data = []
    if checkAllConnection(self) is True:
        url = self.baseurl + "/api/2.0/resources/references/" + referenceType
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + self.token_new
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        data = response.json()["items"]
    else:
        pass
    return data


""" End Data Dic """


def checkAllConnection(self):
    status = False
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            status = True
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
    return status
