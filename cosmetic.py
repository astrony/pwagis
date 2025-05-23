from qgis.core import QgsProject, QgsRectangle, QgsRasterLayer
from qgis.gui import QgsLayerTreeMapCanvasBridge
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QPixmap
import datetime
import os.path
import os
import json
import requests
import shutil
import configparser
import pandas as pd
from urllib.request import urlopen
from pwagis.utiles import *
from pwagis.search import *
from pwagis.edit import *
from shapely.wkt import loads
import webbrowser


def retrieveCosmetic(self, cosmeticLayerId):
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            url = "https://gisapp.pwa.co.th/api/1.0/cosmetic-layers/" + str(cosmeticLayerId)
            payload = {}
            headers = {
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code == 200:
                data = response.json()
            else:
                data = ""
                message = "ไม่พบข้อมูลที่ต้องการ"
                self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return data
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return "err"
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
        return "err"


def retrieveAllCosmetic(self):
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            url = "https://gisapp.pwa.co.th/api/1.0/cosmetic-layers?limit=10000"
            payload = {}
            headers = {
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code == 200:
                data = response.json()
            else:
                data = ""
                message = "ไม่พบข้อมูลที่ต้องการ"
                self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return data
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return "err"
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
        return "err"


def previewCosmeticLayer(self, cosmeticLayerId):
    url = "https://gisapp.pwa.co.th/p/preview?cosmetic_id=" + cosmeticLayerId + "&access_token=" + self.token_new
    webbrowser.open_new(url)


def zoomToCosmeticLayer(self, data):
    if data == "":
        print("Data not found")
        message = "ไม่พบข้อมูลที่ต้องการ"
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
    else:
        coordinates = []
        geometry_type = str(data['configs'][0]['geometry']['type'])
        coordinates = data['configs'][0]['geometry']['coordinates']
        geo_text = get_geo_string(self, geometry_type, coordinates)
        return geo_text


def showCosmeticLayer(self, data):
    if data == "":
        print("Data not found")
        message = "ไม่พบข้อมูลที่ต้องการ"
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
    else:
        title = str(data['title'])
        description = str(data['description'])


def retrieveData(self, cosmeticId):
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            url = "https://gisapp.pwa.co.th/api/1.0/cosmetic-layers/" + cosmeticId

            payload = {}
            headers = {
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code == 200:
                data = response.json()
            else:
                data = ""
                message = "ไม่พบข้อมูลที่ต้องการ"
                self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return data
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return "err"
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
        return "err"


def updateAcceptStatus(self, data):
    userId = self.userId
    for i in range(len(data['assignUsers'])):
        if data['assignUsers'][i]['id'] == userId:
            print(data['assignUsers'][i]['action'])
            data['assignUsers'][i]['action'] = True
            print(data['assignUsers'][i]['action'])
        # Convert the modified data back to JSON
    modified_json = json.dumps(data)
    data = json.loads(modified_json)
    return data


def acceptJob(self, cosmeticLayerId, modified_json):
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            url = "https://gisapp.pwa.co.th/api/1.0/cosmetic-layers/" + str(cosmeticLayerId)
            payload = json.dumps(modified_json)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("PUT", url, headers=headers, data=payload)
            if response.status_code == 200:
                data = response.json()
                print("Update action status = true complete")
            else:
                data = ""
                message = "ไม่พบข้อมูลที่ต้องการ"
                self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return data
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return "err"
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
        return "err"


def loadLayerToEdit(self, root, group):
    self.geo_col = 0
    self.geo_col_edit = 0
    self.dockwidget.cosmetic_loadataBtn.setEnabled(0)
    self.dockwidget.cosmetic_senddataBtn.setEnabled(0)
    self.dockwidget.cosmeticCombo.setEnabled(0)
    self.dockwidget.cosmetic_senddataBtn.setEnabled(False)
    message = "กำลังดึงข้อมูล"
    self.iface.messageBar().pushMessage("Information", message, level=0, duration=3)
    remove_layer(self)
    extent = self.iface.mapCanvas().extent()
    bbox = str(extent.xMaximum()) + "," + str(extent.yMaximum()) + "," + str(extent.xMinimum()) + "," + str(
        extent.yMinimum())

    data = json.loads(self.collection_json)
    search_id = self.dockwidget.cosmeticCombo.currentText()

    result = list(filter(lambda x: x["itemtype"] == search_id, data['collection'][0]['items']))

    if len(result) > 0:
        collectionid = result[0]['collectionid']
        self.collectionid = collectionid
        db_directory = make_dir(self)
        f_properties = getCollection_item(self, collectionid, bbox, db_directory, root, group)

        self.dockwidget.edit_loadataBtn.setEnabled(1)

        layer = check_layer(self)

        if layer == "error":
            status = "error"
        else:
            # Select edit Form by layer in edit.py type exe: VALE, LEAKPOINT
            if layer.type() == QgsMapLayer.VectorLayer or str(layer.type()) == "LayerType.Vector" or str(layer.type()) == "0":
                # Load symbol from qml file
                qml_file, ui_file, py_file = select_edit_form(self, search_id)
                qml_path = os.path.join(self.plugin_dir, "ui_form", qml_file)
                layer = self.iface.activeLayer()
                layer.loadNamedStyle(qml_path, True)
                layer.triggerRepaint()
                # Load ui form
                ui_path = os.path.join(self.plugin_dir, "ui_form", ui_file)
                py_path = os.path.join(self.plugin_dir, "ui_form", py_file)
                # Set ui form
                config = layer.editFormConfig()
                config.setInitCodeSource(QgsEditFormConfig.CodeSourceFile)
                config.setUiForm(ui_path)
                config.setInitFilePath(py_path)
                config.setInitFunction("close_before")
                # config.setInitFunction("formOpen")
                layer.setEditFormConfig(config)
                googleLayer = QgsProject.instance().mapLayersByName("Google Map")
                self.iface.setActiveLayer(googleLayer[0])
                item = self.dockwidget.cosmeticCombo.currentText()
                if item == "VALVE" or item == "FIREHYDRANT" or item == "METER":
                    googleLayer = QgsProject.instance().mapLayersByName("Google Map")
                    self.iface.setActiveLayer(googleLayer[0])
                    layerPipeName = self.layerPipeName
                    if layerPipeName != "err":
                        layerPipe = QgsProject.instance().mapLayersByName(str(layerPipeName.name()))
                        if layerPipe:
                            layerPipe = layerPipe[0]
                            # Find the layer's current tree node
                            layer_tree_layer = root.findLayer(layerPipe.id())
                            if layer_tree_layer:
                                # Clone the layer to the group and remove from root
                                clone = layer_tree_layer.clone()
                                group.insertChildNode(0, clone)
                                root.removeChildNode(layer_tree_layer)
                    if item == "METER":
                        googleLayer = QgsProject.instance().mapLayersByName("Google Map")
                        self.iface.setActiveLayer(googleLayer[0])
                        layerBldgName = self.layerBldgName
                        layerBldg = QgsProject.instance().mapLayersByName(str(layerBldgName.name()))
                        if layerBldg:
                            layerBldg = layerBldg[0]
                            # Find the layer's current tree node
                            layer_tree_layer = root.findLayer(layerBldg.id())
                            if layer_tree_layer:
                                # Clone the layer to the group and remove from root
                                clone = layer_tree_layer.clone()
                                group.insertChildNode(0, clone)
                                root.removeChildNode(layer_tree_layer)

                googleLayer = QgsProject.instance().mapLayersByName("Google Map")
                self.iface.setActiveLayer(googleLayer[0])
                layer = QgsProject.instance().mapLayersByName(str(layer.name()))
                if layer:
                    layer = layer[0]
                    # Find the layer's current tree node
                    layer_tree_layer = root.findLayer(layer.id())
                    if layer_tree_layer:
                        # Clone the layer to the group and remove from root
                        clone = layer_tree_layer.clone()
                        group.insertChildNode(0, clone)
                        root.removeChildNode(layer_tree_layer)

    self.dockwidget.cosmetic_loadataBtn.setEnabled(1)
    self.dockwidget.cosmetic_senddataBtn.setEnabled(1)
    self.dockwidget.cosmeticCombo.setEnabled(1)


def getCollection_item(self, collectionId, bbox, db_folder, root, group):
    flag = 0
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            self.collectionid = collectionId
            limit = "1"
            url = self.baseUrl + "/api/2.0/resources/features/pwa/collections/" + collectionId + "/items?bbox=" + bbox + "&limit=" + limit
            payload = {}
            headers = {
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            checkContent = response.content
            if response.status_code == 200 and len(checkContent) > 0:
                # numberMatched = response.json()["numberMatched"]
                numberReturned = response.json()["numberReturned"]
                if numberReturned == 0:
                    print("Load Empty Data Layer")
                    flag = 1
                    url = self.baseUrl + "/api/2.0/resources/features/pwa/collections/" + collectionId + "/items?limit=1"
                    payload = {}
                    headers = {
                        'Authorization': 'Bearer ' + self.token_new
                    }
                    response = requests.request("GET", url, headers=headers, data=payload)
                    numberReturned = response.json()["numberReturned"]
                limit = self.maxfeature
                # if (numberMatched > 0) and (numberMatched <= int(limit)):
                if (numberReturned > 0) and (numberReturned <= int(limit)):
                    layerPipeName = ""
                    item = self.dockwidget.cosmeticCombo.currentText()
                    if item == "VALVE" or item == "FIREHYDRANT" or item == "METER":
                        # load symbol pipe for valve firehydrant and meter
                        self.layerPipeName = getCosmeticPipe(self, bbox, limit, db_folder)
                        if self.layerPipeName != "err":
                            qml_file = "symbol_pipe.qml"
                            qml_path = os.path.join(self.plugin_dir, "ui_form", qml_file)
                            layer = self.iface.activeLayer()
                            layer.setReadOnly(True)
                            layer.loadNamedStyle(qml_path, True)
                            layer.triggerRepaint()

                        if item == "METER":
                            self.layerBldgName = getCosmeticBldg(self, bbox, limit, db_folder)
                            # load symbol bldg for meter
                            qml_file = "symbol_bldg.qml"
                            qml_path = os.path.join(self.plugin_dir, "ui_form", qml_file)
                            layer = self.iface.activeLayer()
                            layer.setReadOnly(True)
                            layer.loadNamedStyle(qml_path, True)
                            layer.triggerRepaint()
                    if flag == 0:
                        url = self.baseUrl + "/api/2.0/resources/features/pwa/collections/" + collectionId + "/items?bbox=" + bbox + "&limit=" + limit
                    payload = {}
                    headers = {
                        'Authorization': 'Bearer ' + self.token_new
                    }
                    response = requests.request("GET", url, headers=headers, data=payload)
                    features = response.json()["features"]
                    numberReturned = response.json()["numberReturned"]
                    if len(features) > 0:
                        message = "พบข้อมูล " + str(numberReturned) + " รายการ"
                        # Create JSON file
                        json_file = create_json(self, features)
                        # Create GeoJSON file
                        geojson_file = create_geojson(self, json_file)
                        # Get Item Type from combobox
                        item_type = self.dockwidget.cosmeticCombo.currentText()
                        # Set GeoPackage file name
                        geopackage_file_name = geopackage_name(self, item_type, cosmeticItem=True)

                        db_path_cosmetic = os.path.join(db_folder, geopackage_file_name)
                        self.db_path_cosmetic = db_path_cosmetic
                        self.dockwidget.db_label.setText(str(db_path_cosmetic))

                        # Create GeoPackage file
                        create_geopackage_db(self, db_folder, geopackage_file_name, geojson_file)
                        # Load Geopackage to Map
                        layerName = load_geopackage(self, item_type, db_folder, geopackage_file_name)
                        self.iface.messageBar().pushMessage("Information  ", message, level=0, duration=3)
                        print("getItem : " + str(layerName.name()))
                        return layerName
                    else:
                        message = "Data not found."
                        self.iface.messageBar().pushMessage("Warning  ", message, level=1, duration=3)
                else:
                    if int(numberMatched) > int(limit):
                        message = "Data more than maximize limit 5,000 records."
                        self.iface.messageBar().pushMessage("Warning  ", message, level=1, duration=3)
                    else:
                        message = "Data not found."
                        self.iface.messageBar().pushMessage("Warning  ", message, level=1, duration=3)
            else:
                message = "Data not found."
                self.iface.messageBar().pushMessage("Warning  ", message, level=1, duration=3)
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return "err"
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)


def getCosmeticPipe(self, bbox, limit, db_folder):
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            searchtxt = "B" + self.currentbranch + "_PIPE"
            url = self.baseUrl + "/api/2.0/resources/features/pwa/collections?title=" + searchtxt
            payload = {}
            headers = {
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code == 200:
                numberReturned = response.json()["numberReturned"]
                if numberReturned > 0:
                    collections = response.json()["collections"]
                    pipeCollectionId = collections[0]['id']
                    url = self.baseUrl + "/api/2.0/resources/features/pwa/collections/" + pipeCollectionId + "/items?bbox=" + bbox + "&limit=" + limit
                    payload = {}
                    headers = {
                        'Authorization': 'Bearer ' + self.token_new
                    }
                    response = requests.request("GET", url, headers=headers, data=payload)
                    if response.status_code == 200:
                        features = response.json()["features"]
                        numberReturned = response.json()["numberReturned"]
                        if len(features) > 0:
                            message = "พบข้อมูล " + str(numberReturned) + " รายการ"
                            # Create JSON file
                            json_file = create_json(self, features)
                            # Create GeoJSON file
                            geojson_file = create_geojson(self, json_file)
                            # Get Item Type from combobox
                            item_type = "PIPE"
                            # Set GeoPackage file name
                            geopackage_file_name = geopackage_name(self, item_type, cosmeticItem=True)
                            db_path_cosmetic = os.path.join(db_folder, geopackage_file_name)
                            self.db_path_cosmetic_pipe = os.path.join(self.plugin_dir, "Data", db_path_cosmetic)
                            # Create GeoPackage file
                            create_geopackage_db(self, db_folder, geopackage_file_name, geojson_file)
                            # Load Geopackage to Map
                            layerName = load_geopackage(self, item_type, db_folder, geopackage_file_name)
                            self.iface.messageBar().pushMessage("Information  ", message, level=0, duration=3)
                            return layerName
                        else:
                            message = "Data not found."
                            self.iface.messageBar().pushMessage("Warning  ", message, level=1, duration=3)
                            return "err"
                    else:
                        message = "Data not found."
                        self.iface.messageBar().pushMessage("Warning  ", message, level=1, duration=3)
                        return "err"
                else:
                    message = "ไม่พบข้อมูลที่ต้องการ"
                    self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
                    return "err"
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return "err"

    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
        return "err"


def getCosmeticBldg(self, bbox, limit, db_folder):
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            searchtxt = "B" + self.currentbranch + "_BLDG"
            url = self.baseUrl + "/api/2.0/resources/features/pwa/collections?title=" + searchtxt
            payload = {}
            headers = {
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code == 200:
                numberReturned = response.json()["numberReturned"]
                if numberReturned > 0:
                    collections = response.json()["collections"]
                    bldgCollectionId = collections[0]['id']
                    url = self.baseUrl + "/api/2.0/resources/features/pwa/collections/" + bldgCollectionId + "/items?bbox=" + bbox + "&limit=" + limit
                    payload = {}
                    headers = {
                        'Authorization': 'Bearer ' + self.token_new
                    }
                    response = requests.request("GET", url, headers=headers, data=payload)
                    features = response.json()["features"]
                    numberReturned = response.json()["numberReturned"]
                    if len(features) > 0:
                        message = "พบข้อมูล " + str(numberReturned) + " รายการ"
                        # Create JSON file
                        json_file = create_json(self, features)
                        # Create GeoJSON file
                        geojson_file = create_geojson(self, json_file)
                        # Get Item Type from combobox
                        item_type = "BLDG"
                        # Set GeoPackage file name
                        geopackage_file_name = geopackage_name(self, item_type, cosmeticItem=True)
                        db_path_cosmetic = os.path.join(db_folder, geopackage_file_name)
                        self.db_path_cosmetic_bldg = os.path.join(self.plugin_dir, "Data", db_path_cosmetic)
                        # Create GeoPackage file
                        create_geopackage_db(self, db_folder, geopackage_file_name, geojson_file)
                        # Load Geopackage to Map
                        layerName = load_geopackage(self, item_type, db_folder, geopackage_file_name)
                        self.iface.messageBar().pushMessage("Information  ", message, level=0, duration=3)
                        return layerName
                    else:
                        message = "Data not found."
                        self.iface.messageBar().pushMessage("Warning  ", message, level=1, duration=3)
                else:
                    message = "ไม่พบข้อมูลที่ต้องการ"
                    self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return "err"

    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
        return "err"


def sumCollectionEdit(self):
    item = self.dockwidget.cosmeticCombo.currentText()
    item_id = ""
    if item == "VALVE":
        item_id = "valveId"
    elif item == "FIREHYDRANT":
        item_id = "firehydrantId"
    elif item == "PWA_WATERWORKS":
        item_id = "pwaId"
    elif item == "ROAD":
        item_id = "roadId"
    elif item == "DMA_BOUNDARY":
        item_id = "dmaId"
    elif item == "PIPE":
        item_id = "pipeId"
    elif item == "LEAKPOINT":
        item_id = "leakNo"
    elif item == "METER":
        item_id = "custCode"
    elif item == "BLDG":
        item_id = "bldgId"
    self.item_id = item_id
    self.item = item

    """ """
    if item == "METER":
        add_cmd = "SELECT data_new.meterNo FROM data_new WHERE (data_new.meterNo is NULL) and (data_new.id is NULL)"
    if item == "PWA_WATERWORKS":
        add_cmd = "SELECT data_new.id FROM data_new WHERE (data_new.id  is NULL)"
    if item == "DMA_BOUNDARY":
        add_cmd = "SELECT data_new.id FROM data_new WHERE (data_new.id  is NULL)"
    else:
        add_cmd = "SELECT data_new.id FROM data_new WHERE (data_new.id  is NULL)"

    delete_cmd = "SELECT data_old.id FROM data_old WHERE id NOT IN (SELECT id FROM data_new )"

    print(str(add_cmd))
    rows = execute_data(self, add_cmd)
    add_record = extract_list(rows)
    self.featureid_add = add_record
    print("ADD : " + str(add_record))
    delete_record = []
    edit_record = get_edit_record(self)
    self.featureid_edit = edit_record
    delete_record = get_delete_record(self)
    print(str(delete_record))
    self.featureid_delete = delete_record

    if len(add_record) > 0 or len(edit_record) > 0 or len(delete_record) > 0:
        add_text = "พบรายการใหม่ : " + str(len(add_record)) + " รายการ"
        self.dlg3.label_add.setText(add_text)
        self.dlg3.label_edit.setText("")
        self.dlg3.label_delete.setText("")

        edit_text = "พบรายการแก้ไข : " + str(len(edit_record)) + " รายการ"
        self.dlg3.label_edit.setText(edit_text)

        delete_text = "พบรายการลบ : " + str(len(delete_record)) + " รายการ"
        self.dlg3.label_delete.setText(delete_text)
        self.dlg3.editConfirmBtn.setEnabled(True)

    elif len(add_record) == 0 and len(edit_record) == 0 and len(delete_record) == 0:
        self.dlg3.label_add.setText("ไม่พบรายการข้อมูลนำส่ง")
        self.dlg3.label_edit.setText("")
        self.dlg3.label_delete.setText("")
        self.dlg3.editConfirmBtn.setEnabled(0)

    return add_record, edit_record, delete_record


def exportAddCosmetic(self):
    gpkg_file = os.path.join(self.plugin_dir, "Data", self.db_path_cosmetic)
    print(gpkg_file)
    item_type = self.dockwidget.edit_datalayer_combo.currentText()
    gdf = gpd.read_file(gpkg_file, layer='data_new')

    if item_type == "METER":
        result_df = gdf[gdf['meterNo'].isnull()]
    else:
        if item_type == "PWA_WATERWORKS" or item_type == "DMA_BOUNDARY":
            result_df = gdf
        else:
            result_df = gdf
    next_df = result_df[result_df['id'].isnull()]
    next_df.reset_index(drop=True, inplace=True)
    print(next_df)

    return next_df


def exportEditCosmetic(self):
    gpkg_file = os.path.join(self.plugin_dir, "Data", self.db_path_cosmetic)
    print(gpkg_file)
    item_type = self.dockwidget.edit_datalayer_combo.currentText()
    gdf = gpd.read_file(gpkg_file, layer='data_new')
    next_df = gdf[gdf['id'].isin(self.featureid_edit)]
    next_df.reset_index(drop=True, inplace=True)
    print(next_df)
    return next_df

def exportDeleteCosmetic(self):
    gpkg_file = os.path.join(self.plugin_dir, "Data", self.db_path_cosmetic)
    print(gpkg_file)
    item_type = self.dockwidget.edit_datalayer_combo.currentText()
    gdf = gpd.read_file(gpkg_file, layer='data_old')
    next_df = gdf[gdf['id'].isin(self.featureid_delete)]
    next_df.reset_index(drop=True, inplace=True)
    print(next_df)
    return next_df

def exportJson_addCosmetic(self, next_df):
    result_df = next_df
    db_folder = make_dir(self)
    lastDf = result_df
    # Creating an empty DataFrame with the same columns
    lastDf = lastDf[0:0]
    mode = "add"
    geojson_file = "cosmetic_geo_" + mode + "_" + str(self.item) + ".geojson"
    geojson_file = os.path.join(self.plugin_dir, "Data", db_folder, geojson_file)
    for i in range(len(result_df)):
        tempdf = result_df.loc[[i]]
        # Change data type to int
        # tempdf = change_dataType(self, tempdf)
        tempdf = tempdf.set_crs('epsg:4326')
        # tempdf['id'] = self.featureid_add[i]
        tempdf['id'] = 12345678 + i
        res = pd.concat([lastDf, tempdf])
        lastDf = res
    lastDf.to_file(geojson_file, driver="GeoJSON")
    add_result = str(geojson_file)
    # new_geojson_file = modify_add_geojson(self, geojson_file)
    # gpkg_file = self.noTopGpkg
    # gdf = gpd.read_file(gpkg_file, layer='data_new')

    # add_result = add_featuter(self, new_geojson_file, gpkg_file, result_df, gdf)

    print("No Error --> Export json")

    # self.featureid_add = []
    return add_result, geojson_file


def exportJson_editCosmetic(self, next_df):
    result_df = next_df
    db_folder = make_dir(self)
    print(result_df)
    lastDf = result_df
    # Creating an empty DataFrame with the same columns
    lastDf = lastDf[0:0]
    mode = "edit"
    geojson_file = "cosmetic_geo_" + mode + "_" + str(self.item) + ".geojson"
    geojson_file = os.path.join(self.plugin_dir, "Data", db_folder, geojson_file)
    for i in range(len(result_df)):
        tempdf = result_df.loc[[i]]
        # Change data type to int
        # tempdf = change_dataType(self, tempdf)
        tempdf = tempdf.set_crs('epsg:4326')
        res = pd.concat([lastDf, tempdf])
        lastDf = res
    lastDf.to_file(geojson_file, driver="GeoJSON")
    edit_result = str(geojson_file)
    return edit_result, geojson_file


def exportJson_deleteCosmetic(self, next_df):
    result_df = next_df
    db_folder = make_dir(self)
    print(result_df)
    lastDf = result_df
    # Creating an empty DataFrame with the same columns
    lastDf = lastDf[0:0]
    mode = "delete"
    geojson_file = "cosmetic_geo_" + mode + "_" + str(self.item) + ".geojson"
    geojson_file = os.path.join(self.plugin_dir, "Data", db_folder, geojson_file)
    for i in range(len(result_df)):
        tempdf = result_df.loc[[i]]
        # Change data type to int
        # tempdf = change_dataType(self, tempdf)
        tempdf = tempdf.set_crs('epsg:4326')
        res = pd.concat([lastDf, tempdf])
        lastDf = res
    lastDf.to_file(geojson_file, driver="GeoJSON")
    edit_result = str(geojson_file)
    return edit_result, geojson_file


def modify_add_geojson_cosmetic(self, geojson_file):
    cosmeticJson = retrieveData(self, str(self.cosmeticId))
    cosmeticJson["status"] = "in-review"
    # Set supervisorUser
    cosmeticJson["supervisorUser"] = {"id": str(self.userId)}
    collection = []
    print(cosmeticJson)
    with open(geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
        data = geojson.load(file)  # read JSON data
        del data["crs"]  # remove field crs
        del data["type"]  # remove field type
    i = 0
    while i < len(data["features"]):
        data["features"][i]["properties"]["collectionId"] = str(self.collectionid)
        alias = data["features"][i]["properties"]["globalId"]

        features = data["features"]
        collection.append({"id": str(self.collectionid), "alias": str(alias), "features": features})
        cosmeticJson["collections"] = collection
        i = i + 1
    newData = geojson.dumps(cosmeticJson, indent=4)  # dump jsonfile

    with open(geojson_file, 'w', encoding='utf-8') as file:  # open file in write-mode
        file.write(newData)

    with open(geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
        data = geojson.load(file)  # read JSON data
        data["supervisorUser"]["id"] = str(self.userId)

    print(data)
    return geojson_file


def modify_edit_geojson_cosmetic(self, geojson_file):
    cosmeticJson = retrieveData(self, str(self.cosmeticId))
    cosmeticJson["status"] = "in-review"
    # Set supervisorUser
    cosmeticJson["supervisorUser"] = {"id": str(self.userId)}
    print(cosmeticJson)
    collection = []
    with open(geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
        data = geojson.load(file)  # read JSON data
        del data["crs"]  # remove field crs
        del data["type"]  # remove field type
    i = 0
    while i < len(data["features"]):
        data["features"][i]["properties"]["collectionId"] = str(self.collectionid)
        alias = data["features"][i]["properties"]["globalId"]

        features = data["features"]
        collection.append({"id": str(self.collectionid), "alias": str(alias), "features":  features})
        cosmeticJson["collections"] = collection
        i = i + 1
    newData = geojson.dumps(cosmeticJson, indent=4)  # dump jsonfile

    with open(geojson_file, 'w', encoding='utf-8') as file:  # open file in write-mode
        file.write(newData)

    with open(geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
        data = geojson.load(file)  # read JSON data
        # data["supervisorUser"]["id"] = str(self.userId)

    print(data)
    return geojson_file


def modify_delete_geojson_cosmetic(self, geojson_file):
    cosmeticJson = retrieveData(self, str(self.cosmeticId))
    cosmeticJson["status"] = "in-review"
    # Set supervisorUser
    cosmeticJson["supervisorUser"] = {"id": str(self.userId)}
    collection = []
    with open(geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
        data = geojson.load(file)  # read JSON data
        del data["crs"]  # remove field crs
        del data["type"]  # remove field type
    i = 0
    while i < len(data["features"]):
        # features = data["features"][i]["properties"]["id"]
        data["features"][i]["properties"]["collectionId"] = str(self.collectionid)
        alias = data["features"][i]["properties"]["globalId"]
        features = data["features"]
        # collection.append({"id": str(self.collectionid), "alias": str(alias), "features":  features})
        collection.append({"id": str(self.collectionid), "alias": str(alias), "features": features})
        cosmeticJson["collections"] = collection
        print(str(i))
        i = i + 1

    newData = geojson.dumps(cosmeticJson, indent=4)  # dump jsonfile

    with open(geojson_file, 'w', encoding='utf-8') as file:  # open file in write-mode
        file.write(newData)

    with open(geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
        data = geojson.load(file)  # read JSON data
        # data["supervisorUser"]["id"] = str(self.userId)
    return geojson_file


def updateCosmeticLayer(self, jsonFile):
    status = ""
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            with open(jsonFile, 'r', encoding='utf-8') as file:  # open file in read-mode
                data = geojson.load(file)  # read JSON data
            print(data)
            url = "https://gisapp.pwa.co.th/api/1.0/cosmetic-layers/" + str(self.cosmeticId)
            print(url)
            payload = json.dumps(data)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("PUT", url, headers=headers, data=payload)
            print("respo : " + str(response.status_code))
            if response.status_code == 200:
                message = "Update cosmetic success"
                self.iface.messageBar().pushMessage("Information  ", message, level=3, duration=5)
                status = "update_success"
                print("status = " + status)
            else:
                message = "Update cosmetic not success"
                self.iface.messageBar().pushMessage("Warning ", message, level=2, duration=3)
                print("status = " + status)
            return  status
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
            return "err"
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
        return "err"

