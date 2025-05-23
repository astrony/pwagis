from qgis.core import QgsVectorLayer, QgsDataSourceUri, QgsProject, QgsJsonExporter, QgsPoint, QgsMapLayerStyle, QgsRectangle, QgsMapLayerStyleManager, QgsCoordinateReferenceSystem, \
    QgsRasterLayer, QgsEditorWidgetSetup, QgsEditFormConfig, QgsPageSizeRegistry, QgsVectorFileWriter, QgsLayoutItemPage, \
    QgsCoordinateTransform, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemMapGrid, QgsLayoutItemLabel, \
    QgsLayoutPoint, QgsUnitTypes, QgsLayoutSize, QgsLayoutExporter, QgsLayoutItemPage, QgsRectangle, QgsPoint, \
    QgsReadWriteContext, QgsMapLayer
from qgis.PyQt.QtWidgets import *

import os.path
import os
import json
import requests
import pandas as pd
from pwagis.utiles import *
import geopandas as gpd
import datetime
import sqlite3
from ulid import ULID
import geojson
from pwagis.datalayer import *
from pwagis.creatform import *
from pwagis.search import *
from pwagis.pipe_project import *
from pwagis.topology_check.lib.read_file import *
from pwagis.topology_check.lib.topology import topo_bldg, topo_pipe, topo_valve, topo_firehydrant, topo_leakpoint, topo_meter, topo_pwa_waterworks, topo_dma_boundary
from datetime import datetime
from datetime import date
from osgeo import ogr


""" Get Collection For Support Layer"""
def getCollectionSupport(self, bbox, limit, db_folder, support_layer):
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        elif t_status == "0":
            searchtxt = "B" + self.currentbranch + "_" + str(support_layer)
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
                    supportCollectionId = collections[0]['id']
                    url = self.baseUrl + "/api/2.0/resources/features/pwa/collections/" + supportCollectionId + "/items?bbox=" + bbox + "&limit=" + limit
                    payload = {}
                    headers = {
                        'Authorization': 'Bearer ' + self.token_new
                    }
                    response = requests.request("GET", url, headers=headers, data=payload)
                    if response.status_code == 200:
                        features = response.json()["features"]
                        numberReturned = response.json()["numberReturned"]
                        if len(features) > 0:
                            # Create JSON file
                            json_file = create_json(self, features)
                            # Create GeoJSON file
                            geojson_file = create_geojson(self, json_file)
                            # Get Item Type from combobox
                            item_type = str(support_layer)
                            # Set GeoPackage file name
                            geopackage_file_name = geopackage_name(self, item_type, cosmeticItem=False)
                            # os.path.join(self.plugin_dir, "Data",
                            db_path = os.path.join(db_folder, geopackage_file_name)
                            if support_layer == "PIPE":
                                self.db_path_pipe = os.path.join(self.plugin_dir, "Data", db_path)
                            # Create GeoPackage file
                            create_geopackage_db(self, db_folder, geopackage_file_name, geojson_file)
                            # Load Geopackage to Map
                            layerName = load_geopackage(self, item_type, db_folder, geopackage_file_name)
                            message = "พบข้อมูล " + str(numberReturned) + " รายการ"
                            self.iface.messageBar().pushMessage("Information  ", message, level=0, duration=3)
                            return layerName
                        else:
                            message = "ไม่พบข้อมูลที่ต้องการ " + str(support_layer)
                            self.iface.messageBar().pushMessage("Warning  ", message, level=1, duration=3)
                            return "err"
                    else:
                        message = "ไม่พบข้อมูลที่ต้องการ " + str(support_layer)
                        self.iface.messageBar().pushMessage("Warning  ", message, level=1, duration=3)
                        return "err"
                else:
                    message = "ไม่พบข้อมูลที่ต้องการ " + str(support_layer)
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


def getCollection_New(self, dataLayer):
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            searchtxt = "B" + self.currentbranch + "_" + dataLayer
            collection = []
            items = []
            branchid = ''
            url = self.baseUrl + "/api/2.0/resources/features/pwa/collections?limit=200&offset=0&title=" + searchtxt
            payload = {}
            headers = {
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code == 200:
                numberReturned = response.json()["numberReturned"]
                if numberReturned > 0:
                    collections = response.json()["collections"]
                    for index, coll_id in enumerate(collections):
                        title = str(coll_id["title"])
                        title = title.split('_')
                        branchid = title[0]
                        if title[1] == 'PWA' or title[1] == 'DMA' or title[1] == 'FLOW' or title[1] == 'STEP':
                            itemtype = str(title[1]) + "_" + str(title[2])
                        elif title[1] == 'PIPE' and len(title) > 2:
                            itemtype = str(title[1]) + "_" + str(title[2])
                        else:
                            itemtype = title[1]
                        if itemtype != "LEAKPOINT" and itemtype != "ROAD":  # Hide LEAKPOINT
                        # if itemtype != "ROAD":  # Hide ROAD
                            items.append({'itemtype': str(itemtype), 'collectionid': str(coll_id["id"])})

                    collection.append({'branchid': branchid, 'items': items})
                    data = {}
                    self.collection_json = json.dumps(data)
                    data = {'collection': collection}
                    self.collection_json = json.dumps(data)
                    return "success"
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


def getItem_new(self, collectionId, bbox, db_folder, root, group):
    print("get item new")
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
            # if response.status_code == 200 and len(checkContent) > 0:
            if response.status_code == 200 and len(checkContent) > 0:
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
                if (numberReturned > 0) and (numberReturned <= int(limit)):
                    layerPipeName = ""
                    item = self.dockwidget.edit_datalayer_combo.currentText()
                    if item == "VALVE":
                        print("Load VALVE Layer")
                        self.layerPipeName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="PIPE")
                        if self.layerPipeName != "err":
                            supportLayer(self, qml_file="symbol_pipe.qml")
                        else:
                            print("No PIPE Layer")
                        self.layerMeterName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="METER")
                        if self.layerMeterName != "err":
                            supportLayer(self, qml_file="symbol_meter.qml")
                        else:
                            print("No METER Layer")
                        self.layerFireName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="FIREHYDRANT")
                        if self.layerFireName != "err":
                            supportLayer(self, qml_file="symbol_fire.qml")
                        else:
                            print("No FIREHYDRANT Layer")
                    elif item == "FIREHYDRANT":
                        print("Load FIREHYDRANT Layer")
                        self.layerPipeName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="PIPE")
                        if self.layerPipeName != "err":
                            supportLayer(self, qml_file="symbol_pipe.qml")
                        else:
                            print("No PIPE Layer")
                        self.layerMeterName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="METER")
                        if self.layerMeterName != "err":
                            supportLayer(self, qml_file="symbol_meter.qml")
                        else:
                            print("No METER Layer")
                        self.layerValveName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="VALVE")
                        if self.layerValveName != "err":
                            supportLayer(self, qml_file="symbol_valve.qml")
                        else:
                            print("No VALVE Layer")
                    elif item == "BLDG":
                        print("Load BLDG Layer")
                        self.layerPipeName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="PIPE")
                        if self.layerPipeName != "err":
                            supportLayer(self, qml_file="symbol_pipe.qml")
                        self.layerMeterName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="METER")
                        if self.layerMeterName != "err":
                            supportLayer(self, qml_file="symbol_meter.qml")
                        else:
                            print("No METER Layer")
                    elif item == "METER":
                        print("Load METER Layer")
                        self.layerPipeName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="PIPE")
                        if self.layerPipeName != "err":
                            supportLayer(self, qml_file="symbol_pipe.qml")
                        self.layerBldgName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="BLDG")
                        if self.layerBldgName != "err":
                            supportLayer(self, qml_file="symbol_bldg.qml")
                        else:
                            print("No BLDG Layer")
                    elif item == "PIPE":
                        print("Load PIPE Layer")
                        self.layerBldgName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="BLDG")
                        if self.layerBldgName != "err":
                            supportLayer(self, qml_file="symbol_bldg.qml")
                        else:
                            print("No BLDG Layer")
                        self.layerMeterName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="METER")
                        if self.layerMeterName != "err":
                            supportLayer(self, qml_file="symbol_meter.qml")
                        else:
                            print("No METER Layer")
                        self.layerValveName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="VALVE")
                        if self.layerValveName != "err":
                            supportLayer(self, qml_file="symbol_valve.qml")
                        else:
                            print("No VALVE Layer")
                        self.layerFireName = getCollectionSupport(self, bbox, limit, db_folder, support_layer="FIREHYDRANT")
                        if self.layerFireName != "err":
                            supportLayer(self, qml_file="symbol_fire.qml")
                        else:
                            print("No FIREHYDRANT Layer")
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
                        if flag == 0:
                            message = "พบข้อมูล " + str(numberReturned) + " รายการ"
                        else:
                            message = "ไม่พบข้อมูล"
                        # Create JSON file
                        json_file = create_json(self, features)
                        # Create GeoJSON file
                        geojson_file = create_geojson(self, json_file)
                        # Get Item Type from combobox
                        item_type = self.dockwidget.edit_datalayer_combo.currentText()
                        # Set GeoPackage file name
                        geopackage_file_name = geopackage_name(self, item_type, cosmeticItem=False)

                        db_path = os.path.join(db_folder, geopackage_file_name)
                        self.dockwidget.db_label.setText(str(db_path))

                        # Create GeoPackage file
                        if flag == 0:
                            create_geopackage_db(self, db_folder, geopackage_file_name, geojson_file)
                            # Load Geopackage to Map
                            layerName = load_geopackage(self, item_type, db_folder, geopackage_file_name)
                        else:
                            create_geopackage_temp(self, db_folder, geopackage_file_name, geojson_file)
                            # Load Geopackage to Map
                            layerName = load_geopackage2(self, item_type, db_folder, geopackage_file_name)

                        self.iface.messageBar().pushMessage("Information  ", message, level=0, duration=3)
                        print("getItem : " + str(layerName.name()))
                        return layerName
                    else:
                        message = "Data not found"
                        self.iface.messageBar().pushMessage("Warning  ", message, level=1, duration=3)
                else:
                    if int(numberMatched) > int(limit):
                        message = "Data more than maximize limit 5,000 records."
                        self.iface.messageBar().pushMessage("Warning  ", message, level=1, duration=3)
                    else:
                        message = "No Active layer"
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


# Create JSON file
def create_json(self, features):
    json_file = "temp_in.json"
    json_in = os.path.join(self.plugin_dir, "Data", json_file)
    # Open a file for writing
    with open(json_in, 'w', encoding='utf-8') as f:
        # Serialize the data and write it to the file
        json.dump(features, f, ensure_ascii=False)
    return json_in


# Create GeoJSON file
def create_geojson(self, json_file):
    # Load your JSON data
    with open(json_file, 'r', encoding='utf8') as f:
        data = json.load(f)
    # Create a GeoJSON object
    geojson_data = geojson.FeatureCollection(data)
    geojson_file = "geojson_temp.geojson"
    geojson_temp = os.path.join(self.plugin_dir, "Data", geojson_file)
    # Dump GeoJSON to a file
    with open(geojson_temp, 'w', encoding='utf8') as f:
        geojson.dump(geojson_data, f, ensure_ascii=False)
    return geojson_file


# Create file name
def geopackage_name(self, item_type, cosmeticItem):
    file_name = ""
    now = datetime.now()
    file_name = self.currentbranch + "_" + item_type + "_" + str(now.strftime("%Y%m%d%H%M")) + ".gpkg"
    if cosmeticItem is True:
        file_name = "cosmetic_" + item_type + "_" + str(now.strftime("%Y%m%d%H%M")) + ".gpkg"
    return file_name


def geojson_name(self, item_type, mode):
    file_name = ""
    # now = datetime.datetime.today()
    now = datetime.now()
    file_name = self.currentbranch + "_" + item_type + "_" + mode + ".geojson"
    return file_name


# Create geopackage file
def create_geopackage_db(self, db_folder, db_file, geojson_file):
    db_file = db_folder + "/" + db_file
    input_geojson_file = os.path.join(self.plugin_dir, "Data", geojson_file)
    output_gpkg_file = os.path.join(self.plugin_dir, "Data", db_file)
    # Load GeoJSON file
    gdf = gpd.read_file(input_geojson_file)
    # Write the GeoDataFrame to a gpkg file
    gdf.to_file(output_gpkg_file, encoding='utf-8', driver='GPKG', layer='data_old')
    # Duplicate data to Data_new
    new_gdf = gdf
    gdf["_temp_id"] = None
    gdf.to_file(output_gpkg_file, encoding='utf-8', driver='GPKG', layer='data_new')


# Create geopackage file
def create_geopackage_temp(self, db_folder, db_file, geojson_file):
    db_file = db_folder + "/" + db_file
    input_geojson_file = os.path.join(self.plugin_dir, "Data", geojson_file)
    output_gpkg_file = os.path.join(self.plugin_dir, "Data", db_file)
    # Load GeoJSON file
    gdf = gpd.read_file(input_geojson_file)
    # gdf = gdf.drop(gdf.index)
    # Write the GeoDataFrame to a gpkg file
    gdf.to_file(output_gpkg_file, encoding='utf-8', driver='GPKG', layer='data_old')
    # Duplicate data to Data_new
    new_gdf = gdf
    gdf["_temp_id"] = None
    gdf.to_file(output_gpkg_file, encoding='utf-8', driver='GPKG', layer='data_new')


# Load s to map
def load_geopackage(self, item_type, db_folder, db_file):
    db_file = db_folder + "/" + db_file
    self.db_path = os.path.join(self.plugin_dir, "Data", db_file)
    display_name = self.currentbranch + '_' + item_type
    geopackage_layer = self.db_path + "|layername=data_new"
    """ """

    vector_layer = self.iface.addVectorLayer(geopackage_layer, display_name, "ogr")
    googleLayer = QgsProject.instance().mapLayersByName(vector_layer.name())
    self.iface.setActiveLayer(googleLayer[0])

    # print(str(vector_layer))
    return vector_layer


def load_geopackage2(self, item_type, db_folder, db_file):
    print("load 2 ")
    db_file = db_folder + "/" + db_file
    self.db_path = os.path.join(self.plugin_dir, "Data", db_file)
    display_name = self.currentbranch + '_' + item_type
    geopackage_layer = self.db_path + "|layername=data_new"
    vector_layer = self.iface.addVectorLayer(geopackage_layer, display_name, "ogr")
    googleLayer = QgsProject.instance().mapLayersByName(vector_layer.name())
    self.iface.setActiveLayer(googleLayer[0])

    """ Update Data """
    """
    query_cmd = "UPDATE data_new SET id = NULL"
    updateData(self, query_cmd)
    query_cmd = "UPDATE data_new SET _id = NULL"
    updateData(self, query_cmd)
    """

    """ Delete temp data  """
    query_cmd = "DELETE FROM data_new"
    deleteData(self, query_cmd)

    query_cmd = "DELETE FROM data_old"
    deleteData(self, query_cmd)

    # print(str(vector_layer))
    return vector_layer


def updateData(self, query_cmd):
    geopackage_file = self.db_path
    conn = ogr.Open(geopackage_file, 1)  # open in update mode
    conn.ExecuteSQL(query_cmd)


def deleteData(self, query_cmd):
    geopackage_file = self.db_path
    conn = sqlite3.connect(geopackage_file)
    cursor = conn.cursor()
    cursor.execute(query_cmd)
    conn.commit()
    conn.close()


def checkDuplicate_data(self):
    # query_cmd = "SELECT data_new.id, COUNT(*) as Count FROM data_new GROUP BY data_new.id HAVING COUNT(*) > 1"
    # query_cmd = "SELECT *, COUNT(*) as Count FROM data_new GROUP BY data_new.id HAVING COUNT(*) > 1"
    query_cmd = "SELECT * FROM data_new WHERE id IN (SELECT id FROM data_new GROUP BY id HAVING COUNT(*) > 1)"
    geopackage_file = self.db_path
    conn = sqlite3.connect(geopackage_file)
    cursor = conn.cursor()
    cursor.execute(query_cmd)
    rows = cursor.fetchall()
    conn.close()
    return rows


def execute_data(self, query_cmd):
    geopackage_file = self.db_path
    conn = sqlite3.connect(geopackage_file)
    cursor = conn.cursor()
    cursor.execute(query_cmd)
    rows = cursor.fetchall()
    conn.close()
    return rows


def execute_delete(self, query_cmd):
    geopackage_file = self.db_path
    conn = sqlite3.connect(geopackage_file)
    cursor = conn.cursor()
    cursor.execute(query_cmd)
    rows = cursor.rowcount
    conn.close()
    return rows


def extract_list(record):
    rows = []
    if len(record) > 0:
        for row in record:
            rows.append(row[0])
    return rows


def create_edit_cmd(self, col_name):
    search_col = ""
    for name in col_name:
        if search_col == "":
            search_col = "A." + str(name) + "!= B." + str(name)
        else:
            search_col = search_col + " or " + "A." + str(name) + "!= B." + str(name)
    edit_cmd = "SELECT A.id FROM data_old A, data_new B WHERE A.id = B.id AND (" + search_col + ")"
    return edit_cmd


def sum_cud(self):
    item = self.dockwidget.edit_datalayer_combo.currentText()
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
        # item_id = "meterNo"
        item_id = "custCode"
    elif item == "BLDG":
        item_id = "bldgId"
    elif item == "FLOW_METER":
        item_id = ""
    elif item == "STEP_TEST":
        item_id = "stepNo"

    self.item_id = item_id
    self.item = item

    """ Check Copy Item """
    rows = checkDuplicate_data(self)
    duplicate_record = extract_list(rows)

    """ Update Data """
    if len(duplicate_record) > 0:
        for i in range(len(duplicate_record)):
            tempGlobalId = str(ULID())
            print("Dup = " + str(duplicate_record))
            # query_cmd = "UPDATE data_new SET id = NULL,_id = NULL WHERE id = '" + str(duplicate_record[i]) + "'"
            query_cmd = "UPDATE data_new SET id = NULL,_id = NULL, globalId = '" + str(tempGlobalId) + "' WHERE fid = '" + str(duplicate_record[i]) + "'"
            updateData(self, query_cmd)

    if item == "METER":
        add_cmd = "SELECT data_new.meterNo FROM data_new WHERE (data_new.meterNo is NULL) and (data_new.id is NULL)"
    if item == "PWA_WATERWORKS":
        add_cmd = "SELECT data_new.id FROM data_new WHERE (data_new.id  is NULL)"
    if item == "DMA_BOUNDARY":
        add_cmd = "SELECT data_new.id FROM data_new WHERE (data_new.id  is NULL)"
    else:
        # add_cmd = "SELECT data_new." + item_id + " FROM data_new WHERE (data_new." + item_id + " is NULL) and (data_new.id is NULL)"
        add_cmd = "SELECT data_new.id FROM data_new WHERE (data_new.id  is NULL)"

    delete_cmd = "SELECT data_old.id FROM data_old WHERE id NOT IN (SELECT id FROM data_new )"

    print(str(add_cmd))
    rows = execute_data(self, add_cmd)
    add_record = extract_list(rows)
    self.featureid_add = add_record
    print("ADD : " + str(add_record))
    self.dockwidget.LogTextEdit.insertPlainText(add_cmd)
    delete_record = []

    edit_record = get_edit_record(self)
    self.dockwidget.LogTextEdit.insertPlainText(str(edit_record))
    self.featureid_edit = edit_record

    # rows = execute_data(self, delete_cmd)
    delete_record = get_delete_record(self)
    # delete_record = extract_list(rows)
    print(str(delete_record))
    self.featureid_delete = delete_record
    self.dockwidget.LogTextEdit.insertPlainText(str(delete_record))

    if len(add_record) > 0 or len(edit_record) > 0 or len(delete_record) > 0:
        print("1")
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
        print("0")
        self.dlg3.label_add.setText("ไม่พบรายการข้อมูลนำส่ง")
        self.dlg3.label_edit.setText("")
        self.dlg3.label_delete.setText("")
        self.dlg3.editConfirmBtn.setEnabled(0)

    self.dockwidget.add_Btn.setEnabled(1)
    self.dockwidget.edit_Btn.setEnabled(0)
    self.dockwidget.delete_Btn.setEnabled(0)

    return add_record, edit_record, delete_record


def export_geojson(self):
    gpkg_file = self.db_path
    gdf = gpd.read_file(gpkg_file, layer='data_new')


def get_delete_record(self):
    get_id_old_cmd = "SELECT id FROM data_old"
    temp_db = execute_data(self, get_id_old_cmd)
    list_old_id = extract_list(temp_db)
    list_id = []
    for i in range(len(list_old_id)):
        sql_cmd = "SELECT id FROM data_new where id = '" + str(list_old_id[i]) + "'"
        temp_db = execute_data(self, sql_cmd)
        if len(temp_db) == 0:
            list_id.append(list_old_id[i])
    return list_id


def get_edit_record(self):
    get_col_name_cmd = "SELECT name FROM PRAGMA_TABLE_INFO('data_old')"
    col_name = execute_data(self, get_col_name_cmd)
    list_col_name = extract_list(col_name)
    edit_cmd = create_edit_cmd(self, list_col_name)
    rows = execute_data(self, edit_cmd)
    edit_record = extract_list(rows)
    print("EDIT = " + str(edit_record))

    # if self.item_id == 'pwaId' and len(edit_record) == 0:
    if self.item == 'PWA_WATERWORKS' and len(edit_record) == 0:
        edit_cmd = "SELECT A.id FROM data_old A, data_new B WHERE A.id = B.id AND not exists(select A.remark intersect select B.remark)"
        rows = execute_data(self, edit_cmd)
        edit_record = extract_list(rows)
        if len(edit_record) == 0:
            edit_cmd = "SELECT A.id FROM data_old A, data_new B WHERE A.id = B.id AND not exists(select A.waterResource intersect select B.waterResource)"
            rows = execute_data(self, edit_cmd)
            edit_record = extract_list(rows)
            """
            if len(edit_record) == 0:
                edit_cmd = "SELECT A.id FROM data_old A, data_new B WHERE A.id = B.id AND not exists(select A.pictureResource intersect select B.pictureResource)"
                rows = execute_data(self, edit_cmd)
                edit_record = extract_list(rows)
            """

    return edit_record


def goto_error(self, unsuccessful_geo, unsuccessful_text, errType):
    # unsuccessful_text = ""
    list_not_edit = unsuccessful_text
    print(list_not_edit)
    feature_geo = unsuccessful_geo
    geo_text = str(feature_geo)

    zoomToPoint(self, geo_text)
    print(str(unsuccessful_geo))
    layer = self.iface.activeLayer()
    if layer and layer.type() == QgsMapLayer.VectorLayer:
        if self.dockwidget.radio_add.isChecked() is True:
            colum = self.dockwidget.tableUnsuccessful.columnCount()
            i = 0
            while i < colum:
                id_col = self.dockwidget.tableUnsuccessful.horizontalHeaderItem(i).text()
                if errType == "topo":
                    layer.selectByExpression("\"_temp_id\" = '{}'".format(list_not_edit))
                elif errType == "attribute":
                    layer.selectByExpression("\"globalId\" = '{}'".format(list_not_edit))

                i = i + 1
        else:
            print("edit")
            colum = self.dockwidget.tableUnsuccessful_edit.columnCount()
            i = 0
            while i < colum:
                id_col = self.dockwidget.tableUnsuccessful_edit.horizontalHeaderItem(i).text()
                if id_col == "id":
                    layer.selectByExpression("\"globalId\" = '{}'".format(list_not_edit))
                i = i + 1


def export_add(self):
    self.dockwidget.tableUnsuccessful.horizontalHeader().setVisible(True)
    db_folder = make_dir(self)
    gpkg_file = self.db_path
    item_type = self.dockwidget.edit_datalayer_combo.currentText()
    gdf = gpd.read_file(gpkg_file, layer='data_new')

    if self.item_id == "custCode":
        result_df = gdf[gdf['meterNo'].isnull()]
    else:
        if self.item_id == "pwaId" or self.item_id == "dmaId":
            result_df = gdf
        else:
            result_df = gdf

    next_df = result_df[result_df['id'].isnull()]
    next_df.reset_index(drop=True, inplace=True)

    mode = "1"
    input_f = gdf
    input_bbox = os.path.join(self.plugin_dir, "topology_check", "data", "province_bbox.geojson")
    bbox_df = gpd.read_file(input_bbox)
    # if self.item == ""
    df_check = ""

    if self.item == "BLDG":
        df_check = topo_bldg(mode, input_pwa_layer=input_f, input_bbox=bbox_df, logfile=None)
    elif self.item == "PIPE":
        df_check = topo_pipe(mode, input_pwa_layer=input_f, pipe_id='globalId', function_id='functionId', input_bbox=bbox_df, logfile=None)
    elif self.item == "PWA_WATERWORKS":
        df_check = topo_pwa_waterworks(mode, input_pwa_layer=input_f, pwa_id='globalId', input_bbox=bbox_df, logfile=None)
    elif self.item == "METER":  # Meter
        df_check = topo_meter(mode, input_pwa_layer=input_f, meter_id='custCode', input_bbox=bbox_df, logfile=None)
    elif self.item == "DMA_BOUNDARY":
        df_check = topo_dma_boundary(mode, input_pwa_layer=input_f, input_bbox=bbox_df, logfile=None)
    elif self.item == "VALVE":
        pipe_file = self.db_path_pipe
        input_p = gpd.read_file(pipe_file, layer='data_new')
        df_check = topo_valve(mode, input_pwa_layer=input_f, input_pipe=input_p, valve_id='globalId', function_id='functionId', input_bbox=bbox_df, logfile=None)
    elif self.item == "FIREHYDRANT":
        pipe_file = self.db_path_pipe
        input_p = gpd.read_file(pipe_file, layer='data_new')
        df_check = topo_firehydrant(mode, input_pwa_layer=input_f, input_pipe=input_p, fire_id='globalId', function_id='functionId', input_bbox=bbox_df, logfile=None)
    elif self.item == "STEP_TEST":
        df_check = input_f
    elif self.item == "FLOW_METER":
        df_check = input_f

    df_check = df_check.drop(columns=['geometry'])

    if self.item == "DMA_BOUNDARY":
        extracted_column = input_f[['_temp_id', 'geometry']]
        result3 = pd.merge(df_check, extracted_column, on=['_temp_id'], how='outer')
    elif self.item == "PWA_WATERWORKS":
        extracted_column = input_f[['_temp_id', 'geometry']]
        result4 = pd.merge(df_check, extracted_column, on=['_temp_id'], how='outer')
        result3 = result4[result4['_id'].isnull()]
    else:
        extracted_column = input_f[['_temp_id', 'geometry']]
        result4 = pd.merge(df_check, extracted_column, on=['_temp_id'], how='outer')
        result3 = result4[result4['_id'].isnull()]

    result4 = result3[result3['_temp_id'].notnull()]
    result4.reset_index(drop=True, inplace=True)

    data_col = []
    data_col.append('_temp_id')
    for col in result4.columns:
        temp_col = col.split('_')
        if temp_col[0] == 'topo':
            data_col.append(col)

    data_col.append('geometry')
    result3 = result4[data_col]
    result3.reset_index(drop=True, inplace=True)
    self.dockwidget.tableUnsuccessful.setColumnCount(len(result3.columns))
    self.dockwidget.tableUnsuccessful.setRowCount(0)
    e_header = data_col
    self.dockwidget.tableUnsuccessful.setHorizontalHeaderLabels(e_header)
    print(e_header)
    for row in range(len(result3)):
        row_count = self.dockwidget.tableUnsuccessful.rowCount()
        self.dockwidget.tableUnsuccessful.insertRow(row_count)
        col_err = 0
        for col in range(len(data_col)):
            err_content = str(result3.loc[row][data_col[col]])
            if err_content == "true":
                self.dockwidget.tableUnsuccessful.setItem(row_count, col, QTableWidgetItem("ผิดเงื่อนไข"))
                col_err = col_err + 1
            elif err_content == "false":
                self.dockwidget.tableUnsuccessful.setItem(row_count, col, QTableWidgetItem("ผ่าน"))
            elif err_content == "error":
                self.dockwidget.tableUnsuccessful_edit.setItem(row_count, col, QTableWidgetItem("ผ่าน"))
            else:
                self.dockwidget.tableUnsuccessful.setItem(row_count, col,
                                                              QTableWidgetItem(str(result3.loc[row][data_col[col]])))
        if col_err == 0:
            self.dockwidget.tableUnsuccessful.removeRow(row_count)
    row_count = self.dockwidget.tableUnsuccessful.rowCount()
    col_count = self.dockwidget.tableUnsuccessful.columnCount()

    if self.geo_col == 0:
        # Hide Geo col
        self.dockwidget.tableUnsuccessful.setColumnHidden(len(data_col)-1, True)
        # Hide _temp_id col
        self.geo_col = len(data_col) - 1
    else:
        # Show Geo col
        self.dockwidget.tableUnsuccessful.setColumnHidden(len(data_col) - 1, False)
        # Show _temp_id col
        self.geo_col = len(data_col) - 1

    add_message = ""
    if row_count == 0:
        self.dockwidget.tableUnsuccessful.horizontalHeader().setVisible(False)
        print("No Topo error")
        # self.addDf = result_df
        self.addDf = next_df
        # self.addDf = result3
        self.noTopGpkg = gpkg_file
    else:
        add_message = "พบความผิดพลาดการเพิ่ม " + str(row_count) + " รายการ"
        # self.dockwidget.unsuccess_group.setEnabled(1)

    return row_count, add_message


def exportJson_add(self):
    result_df = self.addDf
    db_folder = make_dir(self)
    lastDf = result_df
    # Creating an empty DataFrame with the same columns
    lastDf = lastDf[0:0]
    mode = "add"
    geojson_file = "geo_" + mode + "_" + str(self.item) + ".geojson"
    geojson_file = os.path.join(self.plugin_dir, "Data", db_folder, geojson_file)
    for i in range(len(result_df)):
        tempdf = result_df.loc[[i]]
        # Change data type to int
        # tempdf = change_dataType(self, tempdf)
        tempdf = tempdf.set_crs('epsg:4326')
        # tempdf['id'] = self.featureid_add[i]
        tempdf['id'] = 12345678 + i
        res = pd.concat([lastDf, tempdf])
        # res = lastDf.append(tempdf, ignore_index=True)
        lastDf = res
    lastDf.to_file(geojson_file, driver="GeoJSON")

    new_geojson_file = modify_add_geojson(self, geojson_file)
    gpkg_file = self.noTopGpkg
    gdf = gpd.read_file(gpkg_file, layer='data_new')

    add_result = add_featuter(self, new_geojson_file, gpkg_file, result_df, gdf)

    print("No Error --> Export json")

    self.featureid_add = []
    return add_result


def exportJson_edit(self):
    result_df = self.editDf
    db_folder = make_dir(self)
    lastDf = result_df
    # Creating an empty DataFrame with the same columns
    lastDf = lastDf[0:0]
    mode = "edit"
    geojson_file = "geo_" + mode + "_" + str(self.item) + ".geojson"
    geojson_file = os.path.join(self.plugin_dir, "Data", db_folder, geojson_file)
    print("Export JSON -->")
    for i in range(len(result_df)):
        tempdf = result_df.loc[[i]]
        # Change data type to int
        tempdf = change_dataType(self, tempdf)
        tempdf = tempdf.set_crs('epsg:4326')
        # tempdf['id'] = self.featureid_edit[i]
        res = pd.concat([lastDf, tempdf])
        # res = lastDf.append(tempdf, ignore_index=True)
        lastDf = res
    lastDf.to_file(geojson_file, driver="GeoJSON")
    print("Mo JSON -->")
    new_geojson_file = modify_edit_geojson(self, geojson_file)
    gpkg_file = self.noTopGpkg
    gdf = gpd.read_file(gpkg_file, layer='data_new')

    # edit_featuter(self, new_geojson_file, gpkg_file, result_df, gdf)
    update_result = update_featuter(self, new_geojson_file, gpkg_file)

    print("No Error --> Export json")
    self.featureid_edit = []
    return update_result


def exportJson_delete(self):
    result_df = self.deleteDf
    db_folder = make_dir(self)
    lastDf = result_df
    # Creating an empty DataFrame with the same columns
    lastDf = lastDf[0:0]
    mode = "delete"
    # geojson_file = "geo_" + mode + "_" + str(i) + ".geojson"
    geojson_file = "geo_" + mode + "_" + str(self.item_id) + ".geojson"
    geojson_file = os.path.join(self.plugin_dir, "Data", db_folder, geojson_file)
    print("Export JSON Delete-->")
    for i in range(len(result_df)):
        tempdf = result_df.loc[[i]]
        # Change data type to int
        tempdf = change_dataType(self, tempdf)
        tempdf = tempdf.set_crs('epsg:4326')
        tempdf['id'] = self.featureid_delete[i]
        res = pd.concat([lastDf, tempdf])
        lastDf = res
    lastDf.to_file(geojson_file, driver="GeoJSON")
    print("Mo JSON -->")
    new_geojson_file = modify_delete_geojson(self, geojson_file)
    gpkg_file = self.noTopGpkg
    gdf = gpd.read_file(gpkg_file, layer='data_new')

    delete_result = delete_featuter(self, new_geojson_file, gpkg_file)

    # delete_featuter(self, new_geojson_file, gpkg_file, result_df, gdf)

    print("No Error --> Export json")
    self.featureid_delete = []
    return delete_result


def export_edit(self):
    self.dockwidget.tableUnsuccessful_edit.horizontalHeader().setVisible(True)
    db_folder = make_dir(self)
    gpkg_file = self.db_path
    item_type = self.dockwidget.edit_datalayer_combo.currentText()
    gdf = gpd.read_file(gpkg_file, layer='data_new')
    result_df = gdf[gdf['id'].isin(self.featureid_edit)]
    result_df.reset_index(drop=True, inplace=True)
    mode = "1"
    input_f = gdf
    input_bbox = os.path.join(self.plugin_dir, "topology_check", "data", "province_bbox.geojson")
    bbox_df = gpd.read_file(input_bbox)
    df_check = ""
    if self.item == "BLDG":
        df_check = topo_bldg(mode, input_pwa_layer=input_f, input_bbox=bbox_df, logfile=None)
    elif self.item == "PIPE":
        df_check = topo_pipe(mode, input_pwa_layer=input_f, pipe_id='globalId', function_id='functionId', input_bbox=bbox_df, logfile=None)
    elif self.item == "PWA_WATERWORKS":
        df_check = topo_pwa_waterworks(mode, input_pwa_layer=input_f, pwa_id='globalId', input_bbox=bbox_df, logfile=None)
    elif self.item == "METER":  # Meter
        df_check = topo_meter(mode, input_pwa_layer=input_f, meter_id='custCode', input_bbox=bbox_df, logfile=None)
    elif self.item == "DMA_BOUNDARY":
        df_check = topo_dma_boundary(mode, input_pwa_layer=input_f, input_bbox=bbox_df, logfile=None)
    elif self.item == "VALVE":
        pipe_file = self.db_path_pipe
        input_p = gpd.read_file(pipe_file, layer='data_new')
        df_check = topo_valve(mode, input_pwa_layer=input_f, input_pipe=input_p, valve_id='globalId', function_id='functionId', input_bbox=bbox_df, logfile=None)
    elif self.item == "FIREHYDRANT":
        pipe_file = self.db_path_pipe
        input_p = gpd.read_file(pipe_file, layer='data_new')
        df_check = topo_firehydrant(mode, input_pwa_layer=input_f, input_pipe=input_p, fire_id='globalId', function_id='functionId', input_bbox=bbox_df, logfile=None)
    elif self.item == "STEP_TEST":
        df_check = input_f
    elif self.item == "FLOW_METER":
        df_check = input_f

    df_check = df_check.drop(columns=['geometry'])
    result2 = df_check.query('~index.duplicated()')

    if self.item == "DMA_BOUNDARY" or self.item == "PWA_WATERWORKS":
        extracted_column = gdf[['id', 'geometry']]
        result4 = pd.merge(result2, extracted_column, on=['id'], how='outer')

    else:
        # extracted_column = gdf[['id', 'geometry', str(self.item_id)]]
        extracted_column = gdf[['id', 'geometry']]
        # result4 = pd.merge(result2, extracted_column, on=[str(self.item_id)], how='outer')
        result4 = pd.merge(result2, extracted_column, on=['id'], how='outer')

    result3 = result4[result4['id'].isin(self.featureid_edit)]
    result3.reset_index(drop=True, inplace=True)
    if self.item == "DMA_BOUNDARY" or self.item == "PWA_WATERWORKS":
        result5 = result3
    else:
        # result5 = result3.drop(columns=[self.item_id])
        result5 = result3
    result3 = result5.drop(columns=['_temp_id'])
    result6 = result3.drop_duplicates(subset=['id'])
    data_col = []
    data_col.append('id')
    for col in result6.columns:
        temp_col = col.split('_')
        if temp_col[0] == 'topo':
            data_col.append(col)

    data_col.append('geometry')
    result3 = result6[data_col]
    result3.reset_index(drop=True, inplace=True)

    self.dockwidget.tableUnsuccessful_edit.setColumnCount(len(result3.columns))

    self.dockwidget.tableUnsuccessful_edit.setRowCount(0)
    e_header = data_col
    self.dockwidget.tableUnsuccessful_edit.setHorizontalHeaderLabels(e_header)
    print("len " + str(len(result3)))
    for row in range(len(result3)):
        row_count = self.dockwidget.tableUnsuccessful_edit.rowCount()
        self.dockwidget.tableUnsuccessful_edit.insertRow(row_count)
        col_err = 0
        for col in range(len(data_col)):
            err_content = str(result3.loc[row][data_col[col]])
            if err_content == "true":
                self.dockwidget.tableUnsuccessful_edit.setItem(row_count, col, QTableWidgetItem("ผิดเงื่อนไข"))
                col_err = col_err + 1
            elif err_content == "false":
                self.dockwidget.tableUnsuccessful_edit.setItem(row_count, col, QTableWidgetItem("ผ่าน"))
            elif err_content == "error":
                self.dockwidget.tableUnsuccessful_edit.setItem(row_count, col, QTableWidgetItem("ผ่าน"))
            else:
                self.dockwidget.tableUnsuccessful_edit.setItem(row_count, col,
                                                          QTableWidgetItem(str(result3.loc[row][data_col[col]])))
        if col_err == 0:
            self.dockwidget.tableUnsuccessful_edit.removeRow(row_count)
    row_count = self.dockwidget.tableUnsuccessful_edit.rowCount()
    col_count = self.dockwidget.tableUnsuccessful_edit.columnCount()

    if self.geo_col_edit == 0:
        # Hide Geo col
        self.dockwidget.tableUnsuccessful_edit.setColumnHidden(len(data_col)-1, True)
        # Hide _temp_id col
        self.geo_col_edit = len(data_col) - 1
    else:
        # Show Geo col
        self.dockwidget.tableUnsuccessful_edit.setColumnHidden(len(data_col) - 1, False)
        # Show _temp_id col
        self.geo_col_edit = len(data_col) - 1

    print("row :" + str(row_count))
    edit_message = ""
    if row_count == 0:
        self.dockwidget.tableUnsuccessful_edit.horizontalHeader().setVisible(False)
        print("Edit No Topo error")
        self.editDf = result_df
        print("result 834 : " + str(result_df))
        self.noTopGpkg = gpkg_file
    else:
        edit_message = "พบความผิดพลาดการแก้ไข " + str(row_count) + " รายการ"
        # self.dockwidget.unsuccess_group.setEnabled(1)

    return row_count, edit_message


def export_delete(self):
    db_folder = make_dir(self)
    gpkg_file = self.db_path
    gdf = gpd.read_file(gpkg_file, layer='data_old')
    result_df = gdf[gdf['id'].isin(self.featureid_delete)]
    result_df.reset_index(drop=True, inplace=True)

    self.noTopGpkg = gpkg_file
    # delete_featuter(self, new_geojson_file, gpkg_file)
    # if os.path.exists(new_geojson_file):
    #   message = "Create File GeoJSON Finish"
    #   self.iface.messageBar().pushMessage("Information  ", message, level=3, duration=3)
    self.deleteDf = result_df


def remove_layer(self):
    root = QgsProject.instance().layerTreeRoot()
    layers = root.findLayers()
    for layer in layers:
        name = layer.name()
        tile_type = name.split('_')
        if tile_type[0] == self.currentbranch:
            layer = QgsProject.instance().mapLayersByName(name)[0]
            QgsProject.instance().removeMapLayer(layer.id())
    canvas = self.iface.mapCanvas()
    canvas.refresh()


def modify_edit_geojson(self, geojson_file):
    with open(geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
        data = json.load(file)  # read JSON data
        del data["crs"]  # remove field crs  and type
        i = 0
        last_a_ref = ""
        while i < len(data["features"]):
            a_ref = str(ULID())
            field = data["features"][i]["properties"]["id"]
            data["features"][i]["id"] = field
            data["features"][i]["alias"] = a_ref
            """ Change Type """
            if str(self.item) == "VALVE":
                typeId = data["features"][i]["properties"]["typeId"]
                sizeId = data["features"][i]["properties"]["sizeId"]
                statusId = data["features"][i]["properties"]["statusId"]
                functionId = data["features"][i]["properties"]["functionId"]

                if typeId is not None:
                    del data["features"][i]["properties"]["typeId"]
                    data["features"][i]["properties"]["typeId"] = int(typeId)
                if sizeId is not None:
                    del data["features"][i]["properties"]["sizeId"]
                    data["features"][i]["properties"]["sizeId"] = int(sizeId)
                if statusId is not None:
                    del data["features"][i]["properties"]["statusId"]
                    data["features"][i]["properties"]["statusId"] = int(statusId)
                if functionId is not None:
                    del data["features"][i]["properties"]["functionId"]
                    data["features"][i]["properties"]["functionId"] = int(functionId)

            elif str(self.item) == "BLDG":
                # del data["features"][i]["properties"]["addressNo"]
                # del data["features"][i]["properties"]["custFullName"]

                useStatusId = data["features"][i]["properties"]["useStatusId"]
                if useStatusId is not None:
                    del data["features"][i]["properties"]["useStatusId"]
                    data["features"][i]["properties"]["useStatusId"] = int(useStatusId)
                useTypeId = data["features"][i]["properties"]["useTypeId"]
                if useTypeId is not None:
                    del data["features"][i]["properties"]["useTypeId"]
                    data["features"][i]["properties"]["useTypeId"] = int(useTypeId)
                buildingTypeId = data["features"][i]["properties"]["buildingTypeId"]
                if buildingTypeId is not None:
                    del data["features"][i]["properties"]["buildingTypeId"]
                    data["features"][i]["properties"]["buildingTypeId"] = int(buildingTypeId)

            elif str(self.item) == "FIREHYDRANT":
                sizeId = data["features"][i]["properties"]["sizeId"]
                statusId = data["features"][i]["properties"]["statusId"]
                if sizeId is not None:
                    del data["features"][i]["properties"]["sizeId"]
                    data["features"][i]["properties"]["sizeId"] = int(sizeId)
                if statusId is not None:
                    del data["features"][i]["properties"]["statusId"]
                    data["features"][i]["properties"]["statusId"] = int(statusId)
            elif str(self.item) == "PIPE":
                productId = data["features"][i]["properties"]["productId"]
                if productId is not None:
                    del data["features"][i]["properties"]["productId"]
                    data["features"][i]["properties"]["productId"] = int(productId)
                functionId = data["features"][i]["properties"]["functionId"]
                if functionId is not None:
                    del data["features"][i]["properties"]["functionId"]
                    data["features"][i]["properties"]["functionId"] = int(functionId)
                layingId = data["features"][i]["properties"]["layingId"]
                if layingId is not None:
                    del data["features"][i]["properties"]["layingId"]
                    data["features"][i]["properties"]["layingId"] = int(layingId)
                sizeId = data["features"][i]["properties"]["sizeId"]
                if sizeId is not None:
                    del data["features"][i]["properties"]["sizeId"]
                    data["features"][i]["properties"]["sizeId"] = sizeId
                classId = data["features"][i]["properties"]["classId"]
                if classId is not None:
                    del data["features"][i]["properties"]["classId"]
                    data["features"][i]["properties"]["classId"] = int(classId)
                    for iPipeClass in range(len(self.pipeClasses)):
                        if self.pipeClasses[iPipeClass]["classId"] == classId:
                            pipeClass = self.pipeClasses[iPipeClass]["description"]
                            data["features"][i]["properties"]["class"] = str(pipeClass)

            del data["features"][i]["properties"]["id"]
            i = i + 1
        newData = geojson.dumps(data, indent=4)  # dump jsonfile

    with open(geojson_file, 'w', encoding='utf-8') as file:  # open file in write-mode
        file.write(newData)
    return geojson_file


def modify_add_geojson(self, geojson_file):
    with open(geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
        data = json.load(file)  # read JSON data
        del data["crs"]  # remove field crs  and type
        i = 0
        last_a_ref = ""
        while i < len(data["features"]):
            a_ref = data["features"][i]["properties"]["globalId"]
            data["features"][i]["alias"] = a_ref
            feature_type = data["features"][i]["type"]
            del data["features"][i]["type"]
            data["features"][i]["type"] = feature_type
            geometry = data["features"][i]["geometry"]
            del data["features"][i]["geometry"]
            data["features"][i]["geometry"] = geometry
            # Set PWA Code
            data["features"][i]["properties"]["pwaCode"] = str(self.currentbranch)

            del data["features"][i]["properties"]["id"]
            if str(self.item) == "VALVE":
                typeId = data["features"][i]["properties"]["typeId"]
                sizeId = data["features"][i]["properties"]["sizeId"]
                statusId = data["features"][i]["properties"]["statusId"]
                functionId = data["features"][i]["properties"]["functionId"]

                if typeId is not None:
                    del data["features"][i]["properties"]["typeId"]
                    data["features"][i]["properties"]["typeId"] = int(typeId)
                if sizeId is not None:
                    del data["features"][i]["properties"]["sizeId"]
                    data["features"][i]["properties"]["sizeId"] = int(sizeId)
                if statusId is not None:
                    del data["features"][i]["properties"]["statusId"]
                    data["features"][i]["properties"]["statusId"] = int(statusId)
                if functionId is not None:
                    del data["features"][i]["properties"]["functionId"]
                    data["features"][i]["properties"]["functionId"] = int(functionId)

            elif str(self.item) == "BLDG":
                # del data["features"][i]["properties"]["addressNo"]
                # del data["features"][i]["properties"]["custFullName"]

                useStatusId = data["features"][i]["properties"]["useStatusId"]
                if useStatusId is not None:
                    del data["features"][i]["properties"]["useStatusId"]
                    data["features"][i]["properties"]["useStatusId"] = int(useStatusId)
                useTypeId = data["features"][i]["properties"]["useTypeId"]
                if useTypeId is not None:
                    del data["features"][i]["properties"]["useTypeId"]
                    data["features"][i]["properties"]["useTypeId"] = int(useTypeId)
                buildingTypeId = data["features"][i]["properties"]["buildingTypeId"]
                if buildingTypeId is not None:
                    del data["features"][i]["properties"]["buildingTypeId"]
                    data["features"][i]["properties"]["buildingTypeId"] = int(buildingTypeId)

            elif str(self.item) == "FIREHYDRANT":
                sizeId = data["features"][i]["properties"]["sizeId"]
                statusId = data["features"][i]["properties"]["statusId"]
                if sizeId is not None:
                    del data["features"][i]["properties"]["sizeId"]
                    data["features"][i]["properties"]["sizeId"] = int(sizeId)
                if statusId is not None:
                    del data["features"][i]["properties"]["statusId"]
                    data["features"][i]["properties"]["statusId"] = int(statusId)

            elif str(self.item) == "PIPE":
                productId = data["features"][i]["properties"]["productId"]
                print(type(productId))
                if productId is not None:
                    del data["features"][i]["properties"]["productId"]
                    data["features"][i]["properties"]["productId"] = int(productId)
                functionId = data["features"][i]["properties"]["functionId"]
                if functionId is not None:
                    del data["features"][i]["properties"]["functionId"]
                    data["features"][i]["properties"]["functionId"] = int(functionId)
                layingId = data["features"][i]["properties"]["layingId"]
                if layingId is not None:
                    del data["features"][i]["properties"]["layingId"]
                    data["features"][i]["properties"]["layingId"] = int(layingId)
                sizeId = data["features"][i]["properties"]["sizeId"]
                if sizeId is not None:
                    del data["features"][i]["properties"]["sizeId"]
                    data["features"][i]["properties"]["sizeId"] = int(sizeId)

                classId = data["features"][i]["properties"]["classId"]

                if classId is not None:
                    del data["features"][i]["properties"]["classId"]
                    data["features"][i]["properties"]["classId"] = int(classId)

                    for iPipeClass in range(len(self.pipeClasses)):
                        if self.pipeClasses[iPipeClass]["classId"] == classId:
                            pipeClass = self.pipeClasses[iPipeClass]["description"]
                            data["features"][i]["properties"]["class"] = str(pipeClass)

            if "_id" in data["features"][i]["properties"]:
                del data["features"][i]["properties"]["_id"]
            # data["features"][i]["properties"]["globalId"] = a_ref

            f_properties = data["features"][i]["properties"]
            del data["features"][i]["properties"]
            data["features"][i]["properties"] = f_properties

            i = i + 1
        newData = geojson.dumps(data, indent=4)  # dump jsonfile
    with open(geojson_file, 'w', encoding='utf-8') as file:  # open file in write-mode
        file.write(newData)
    return geojson_file


def modify_delete_geojson(self, geojson_file):
    with open(geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
        data = geojson.load(file)  # read JSON data
        del data["crs"]  # remove field crs  and type
        del data["type"]
        i = 0
        while i < len(data["features"]):
            field = data["features"][i]["properties"]["id"]
            data["features"][i]["id"] = field
            del data["features"][i]["properties"]
            del data["features"][i]["geometry"]
            del data["features"][i]["type"]

            i = i + 1
        newData = geojson.dumps(data, indent=4)  # dump jsonfile
    with open(geojson_file, 'w', encoding='utf-8') as file:  # open file in write-mode
        file.write(newData)
    return geojson_file


def delete_featuter(self, new_geojson_file, gpk_file):
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            with open(new_geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
                data = geojson.load(file)  # read JSON data
            url = self.baseUrl + "/api/2.0/resources/features/pwa/collections/" + str(self.collectionid) + "/items"
            payload = json.dumps(data)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("DELETE", url, headers=headers, data=payload)
            if response.status_code == 204:
                message = "Delete feature success"
                self.iface.messageBar().pushMessage("Information  ", message, level=3, duration=5)
                return "delete_success"
            else:
                message = "Delete feature not success"
                self.iface.messageBar().pushMessage("Warning ", message, level=2, duration=3)
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)


def delete_featuter_old(self, new_geojson_file, gpkg_file):
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            with open(new_geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
                data = geojson.load(file)  # read JSON data
            url = self.host + "/features/1.1-beta/collections/" + str(self.collectionid) + "/items/" + str(featureid)
            payload = json.dumps(data)
            headers = {
                'Authorization': 'Bearer ' + self.token
            }
            response = requests.request("DELETE", url, headers=headers, data=payload)
            if response.status_code == 204:
                # Load GeoPackage to GeoDataFrame
                gdf_old = gpd.read_file(gpkg_file, layer='data_old')
                gdf_new = gpd.read_file(gpkg_file, layer='data_new')
                # Search featureid before delete from data_old and get index
                delete_index = gdf_old.index[gdf_old['id'] == str(featureid)].tolist()
                gdf_old = gdf_old.drop(gdf_old.index[delete_index])
                # Export GeoDataFrame to GeoPackage
                gdf_old.to_file(gpkg_file, encoding='utf-8', driver='GPKG', layer='data_old')
                gdf_new.to_file(gpkg_file, encoding='utf-8', driver='GPKG', layer='data_new')
                message = "Delete feature " + str(featureid) + "success"
                self.iface.messageBar().pushMessage("Information  ", message, level=3, duration=5)
            else:
                message = "Delete feature " + str(featureid) + "not success"
                self.iface.messageBar().pushMessage("Warning ", message, level=2, duration=3)
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)


def add_featuter(self, new_geojson_file, gpkg_file, result_df, gdf):
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            with open(new_geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
                data = geojson.load(file)  # read JSON data
            url = self.baseUrl + "/api/2.0/resources/features/pwa/collections/" + str(self.collectionid) + "/items?validate=attribute"
            payload = json.dumps(data)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code == 200:    # 201 Created
               # self.dockwidget.unsuccess_group.setEnabled(0)
               self.dockwidget.tableUnsuccessful.setRowCount(0)
               # Show _temp_id and geo column
               self.dockwidget.tableUnsuccessful.setColumnHidden(1, False)
               self.dockwidget.tableUnsuccessful.setColumnHidden(3, False)
               self.dockwidget.tableUnsuccessful.horizontalHeader().setVisible(False)
               self.dockwidget.send_dataBtn.setEnabled(0)
               add_result = "add_success"
               message = "Add feature success "
               self.iface.messageBar().pushMessage("Information ", message, level=3, duration=5)
               return add_result
            elif response.status_code == 403:  # 403 no permission to access service
                message = "No permission to access service"
                self.iface.messageBar().pushMessage("Warning ", message, level=2, duration=3)
            elif response.status_code == 400:  # 400 Bad Request (attribute error)
                data = json.loads(response.text)
                attributeError = data['attribute']
                err_data = data["features"]

                if len(attributeError) > 0:
                    self.dockwidget.tableUnsuccessful.horizontalHeader().setVisible(True)
                    self.dockwidget.tableUnsuccessful.setColumnHidden(2, False)
                    self.dockwidget.tableUnsuccessful.setColumnCount(0)
                    print_message("พบ attribute error การเพิ่ม " + str(len(attributeError)) + " รายการ")
                    self.dockwidget.tableUnsuccessful.setColumnCount(4)
                    e_header = ['alias', "globalId", "attributeError", "GEO"]
                    self.dockwidget.radio_add.setChecked(True)
                    self.dockwidget.tableUnsuccessful.setHorizontalHeaderLabels(e_header)

                    self.dockwidget.tableUnsuccessful.setRowCount(0)
                    for j in range(len(attributeError)):
                        new_str = ""
                        attributeError_id = attributeError[j]["globalId"]
                        listKey = list(attributeError[j].keys())
                        for i in range(len(listKey)):
                            #if i > 0:
                            if attributeError[j][listKey[i]] != "":
                                if listKey[i] != "globalId":
                                    new_str = new_str + str(listKey[i]) + " : " + attributeError[j][listKey[i]]

                                    new_str = new_str + ", "
                        for z in range(len(err_data)):
                            err_alias = err_data[z]['alias']
                            # err_alias = err_data[z]['globalId']
                            err_id = err_data[z]['alias']
                            # err_id = err_data[z]['globalId']
                            eer_geo = err_data[z]["geometry"]["coordinates"]
                            geometry_type = err_data[z]["geometry"]["type"]
                            # _temp_id = err_data[z]['properties']['_temp_id']
                            globalId = err_data[z]['properties']['globalId']

                            if err_alias == attributeError_id:
                                err_feature = err_id
                                err_content = new_str
                                coordinates = eer_geo
                                geometry_type = geometry_type
                                geo_text = get_geo_string(self, geometry_type, coordinates)

                                row_count = self.dockwidget.tableUnsuccessful.rowCount()
                                self.dockwidget.tableUnsuccessful.insertRow(row_count)

                                self.dockwidget.tableUnsuccessful.setItem(row_count, 0, QTableWidgetItem(str(err_feature)))
                                self.dockwidget.tableUnsuccessful.setItem(row_count, 1, QTableWidgetItem(str(globalId)))
                                self.dockwidget.tableUnsuccessful.setItem(row_count, 2, QTableWidgetItem(str(err_content)))
                                self.dockwidget.tableUnsuccessful.setItem(row_count, 3, QTableWidgetItem(str(geo_text)))

                            # Hide _temp_id and geo column
                    self.dockwidget.tableUnsuccessful.setColumnHidden(1, True)
                    self.dockwidget.tableUnsuccessful.setColumnHidden(3, True)
                    message = "Add feature not success"
                    self.iface.messageBar().pushMessage("Warning ", message, level=2, duration=3)
            else:
                message = "Add feature not success"
                self.iface.messageBar().pushMessage("Warning ", message, level=2, duration=3)
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)


def update_featuter(self, new_geojson_file, gpkg_file):
    print("Update Fea - 0")
    if checkNetConnection() is True:
        t_status = check_token_expired(self)
        if t_status == "1":
            t_status = load_new_token(self)
        if t_status == "0":
            with open(new_geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
                data = geojson.load(file)  # read JSON data
            url = self.baseUrl + "/api/2.0/resources/features/pwa/collections/" + str(self.collectionid) + "/items?validate=attribute"
            payload = json.dumps(data)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + self.token_new
            }
            response = requests.request("PUT", url, headers=headers, data=payload)
            if response.status_code == 400:
                print("Update Fea - 1")
                data = json.loads(response.text)
                attributeError = data['attribute']
                err_data = data["features"]
                if len(attributeError) > 0:
                    self.dockwidget.tableUnsuccessful_edit.horizontalHeader().setVisible(True)
                    self.dockwidget.tableUnsuccessful_edit.setColumnHidden(2, False)
                    self.dockwidget.tableUnsuccessful_edit.setColumnCount(0)
                    print_message("พบ attribute error การแก้ไข" + str(len(attributeError)) + " รายการ")
                    self.dockwidget.tableUnsuccessful_edit.setColumnCount(4)
                    e_header = ['alias', "globalId", "attributeError", "GEO"]
                    self.dockwidget.radio_edit.setChecked(True)
                    self.dockwidget.tableUnsuccessful_edit.setHorizontalHeaderLabels(e_header)

                    self.dockwidget.tableUnsuccessful_edit.setRowCount(0)
                    attributeError = response.json()["attribute"]
                    print(attributeError)
                    for j in range(len(attributeError)):
                        new_str = ""
                        attributeError_id = attributeError[j]["globalId"]
                        listKey = list(attributeError[j].keys())
                        for i in range(len(listKey)):
                            # if i > 0:
                            if attributeError[j][listKey[i]] != "":
                                if listKey[i] != "globalId":
                                    new_str = new_str + str(listKey[i]) + " : " + attributeError[j][listKey[i]]
                                    print("i = " + str(i) + ", att = " + str(len(listKey)))
                                    # if len(listKey) > 1 and i < (len(listKey)-1):
                                    new_str = new_str + ", "
                        for z in range(len(err_data)):
                            err_alias = err_data[z]['alias']
                            # err_alias = err_data[z]['globalId']
                            err_id = err_data[z]['alias']
                            # err_id = err_data[z]['globalId']
                            eer_geo = err_data[z]["geometry"]["coordinates"]
                            geometry_type = err_data[z]["geometry"]["type"]
                            # _temp_id = err_data[z]['properties']['_temp_id']
                            globalId = err_data[z]['properties']['globalId']

                            if err_alias == attributeError_id:
                                err_feature = err_id
                                err_content = new_str
                                coordinates = eer_geo
                                geometry_type = geometry_type
                                geo_text = get_geo_string(self, geometry_type, coordinates)

                                row_count = self.dockwidget.tableUnsuccessful_edit.rowCount()
                                self.dockwidget.tableUnsuccessful_edit.insertRow(row_count)

                                self.dockwidget.tableUnsuccessful_edit.setItem(row_count, 0, QTableWidgetItem(str(err_feature)))
                                self.dockwidget.tableUnsuccessful_edit.setItem(row_count, 1, QTableWidgetItem(str(globalId)))
                                self.dockwidget.tableUnsuccessful_edit.setItem(row_count, 2, QTableWidgetItem(str(err_content)))
                                self.dockwidget.tableUnsuccessful_edit.setItem(row_count, 3, QTableWidgetItem(str(geo_text)))

                            print(str(new_str))
                            # Hide _temp_id and geo column
                    self.dockwidget.tableUnsuccessful_edit.setColumnHidden(1, True)
                    self.dockwidget.tableUnsuccessful_edit.setColumnHidden(3, True)
                    # self.dockwidget.unsuccess_group.setEnabled(1)
            elif response.status_code == 200:
                print("Update Fea - 3")
                # self.dockwidget.unsuccess_group.setEnabled(0)
                self.dockwidget.tableUnsuccessful.setRowCount(0)
                # Show _temp_id and geo column
                # self.dockwidget.tableUnsuccessful_edit.setColumnHidden(1, False)
                self.dockwidget.tableUnsuccessful_edit.setColumnHidden(2, False)
                self.dockwidget.tableUnsuccessful_edit.horizontalHeader().setVisible(False)

                self.dockwidget.send_dataBtn.setEnabled(0)

                message = "Edit feature success"
                self.iface.messageBar().pushMessage("Information ", message, level=3, duration=5)
                return "edit_success"
            else:
                print("Update feature not success error code : " + str(response.status_code))
                message = "Edit feature not success"
                self.iface.messageBar().pushMessage("Information ", message, level=3, duration=3)
        else:
            message = "Can not get token from server"
            self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)


def update_featuter_old(self, new_geojson_file, gpkg_file):
    if checkNetConnection() is True:
        o_status = check_oldToken_expired(self)
        if o_status == "1":
            o_status = refresh_token(self)
        if o_status == "0":
            with open(new_geojson_file, 'r', encoding='utf-8') as file:  # open file in read-mode
                data = geojson.load(file)  # read JSON data
            url = self.host + "/features/1.1-beta/collections/" + str(self.collectionid) + "/items/" + str(self.featureid_edit[0])
            payload = json.dumps(data)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + self.token
            }
            response = requests.request("PUT", url, headers=headers, data=payload)
            if response.status_code == 200:
                # features_id = response.json()["features"][0]["id"]
                # Load GeoPackage to GeoDataFrame
                gdf_old = gpd.read_file(gpkg_file, layer='data_old')
                gdf_new = gpd.read_file(gpkg_file, layer='data_new')
                # Update data_new to data_old
                gdf_old.set_index('id', inplace=True)
                gdf_new.set_index('id', inplace=True)
                gdf_old.update(gdf_new)
                # Export GeoDataFrame to GeoPackage
                gdf_old.to_file(gpkg_file, encoding='utf-8', driver='GPKG', layer='data_old')
                gdf_new.to_file(gpkg_file, encoding='utf-8', driver='GPKG', layer='data_new')
                message = "Edit feature success"
                self.iface.messageBar().pushMessage("Information ", message, level=3, duration=5)
            else:
                message = "Edit feature not success"
                self.iface.messageBar().pushMessage("Information ", message, level=3, duration=3)
    else:
        message = "No internet connection."
        self.iface.messageBar().pushMessage("Warning  ", message, level=2, duration=3)


def change_dataType(self, result_df):
    new_df = result_df
    active_layer = self.iface.activeLayer().name()
    active_layer_name = active_layer.split('_')
    if active_layer_name[1] == 'FIREHYDRANT':
        new_df['sizeId'] = new_df['sizeId'].astype(int)
        new_df['statusId'] = new_df['statusId'].astype(int)
    elif active_layer_name[1] == 'VALVE':
        new_df['typeId'] = new_df['typeId'].astype(int)
        new_df['sizeId'] = new_df['sizeId'].astype(int)
        new_df['statusId'] = new_df['statusId'].astype(int)
        if new_df['functionId'] is not None:
            new_df['functionId'] = new_df['functionId'].astype(int)
    elif active_layer_name[1] == 'PIPE':
        new_df['productId'] = new_df['productId'].astype(int)
        new_df['functionId'] = new_df['functionId'].astype(int)
        new_df['layingId'] = new_df['layingId'].astype(int)
        # new_df['classId'] = new_df['classId'].astype(int)
        # new_df['gradeId'] = new_df['gradeId'].astype(int)
        # print(str(new_df['sizeId']))
        # new_df['sizeId'] = new_df['sizeId'].astype(int)
    # elif active_layer_name[1] == 'BLDG':
    #    new_df['useStatusId'] = new_df['useStatusId'].astype(int)
    return new_df


def select_edit_form(self, search_id):
    qml_file = ""
    ui_file = ""
    py_file = ""
    if search_id == "VALVE":
        qml_file = "symbol_valve.qml"
        ui_file = "form_valve.ui"
        py_file = "form_valve.py"
    elif search_id == "FIREHYDRANT":
        qml_file = "symbol_fire.qml"
        ui_file = "form_fire.ui"
        py_file = "form_fire.py"
    elif search_id == "PWA_WATERWORKS":
        qml_file = "symbol_pwawaterworks.qml"
        ui_file = "form_pwawaterworks.ui"
        py_file = "form_pwawaterworks.py"
    elif search_id == "ROAD":
        qml_file = "symbol_road.qml"
        ui_file = "form_road.ui"
        py_file = "form_road.py"
    elif search_id == "DMA_BOUNDARY":
        qml_file = "symbol_dmaboundaries.qml"
        ui_file = "form_dmaboundaries.ui"
        py_file = "form_dmaboundaries.py"
    elif search_id == "PIPE":
        qml_file = "symbol_pipe.qml"
        ui_file = "form_pipe.ui"
        py_file = "form_pipe.py"
    elif search_id == "LEAKPOINT":
        qml_file = "symbol_leakpoint.qml"
        ui_file = "form_leak.ui"
        py_file = "form_leak.py"
    elif search_id == "METER":
        qml_file = "symbol_meter.qml"
        ui_file = "form_meter.ui"
        py_file = "form_meter.py"
    elif search_id == "BLDG":
        qml_file = "symbol_bldg.qml"
        ui_file = "form_bldg.ui"
        py_file = "form_bldg.py"
    elif search_id == "STEP_TEST":
        qml_file = "symbol_step_test.qml"
        ui_file = "form_steptest.ui"
        py_file = "form_steptest.py"
    elif search_id == "FLOW_METER":
        qml_file = "symbol_flow.qml"
        ui_file = "form_flowmeter.ui"
        py_file = "form_flowmeter.py"
    elif search_id == "STRUCT":
        qml_file = "symbol_struct.qml"
        ui_file = "form_struct.ui"
        py_file = "form_struct.py"
    elif search_id == "PIPE_SERV":
        qml_file = "symbol_pipeserv.qml"
        ui_file = "form_pipeserve.ui"
        py_file = "form_pipeserve.py"

    return qml_file, ui_file, py_file


def print_message(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText(message)
    msg.setWindowTitle("PWA Message")
    # msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msg.setStandardButtons(QMessageBox.Ok)
    retval = msg.exec_()


def print_message_select(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText(message)
    msg.setWindowTitle("PWA Message")
    # msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    retval = msg.exec_()
    if retval == QMessageBox.Ok:
        return "ok"


def stop_edit(self):
   msgBox = QMessageBox()
   msgBox.setIcon(QMessageBox.Information)
   msgBox.setText("Do you want to save the changes to layer")
   msgBox.setWindowTitle("Stop Edit")
   msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
   returnValue = msgBox.exec()
   if returnValue == QMessageBox.Ok:
       layer = self.iface.activeLayer()
       layer.commitChanges()
       m_action = "save"
   else:
       layer = self.iface.activeLayer()
       layer.rollBack()
       m_action = "discards"

   return m_action


def refresh_data(self, root, group):
    self.geo_col = 0
    self.geo_col_edit = 0
    self.dockwidget.edit_loadataBtn.setEnabled(0)
    self.dockwidget.send_dataBtn.setEnabled(0)
    self.dockwidget.edit_datalayer_combo.setEnabled(0)
    message = "กำลังดึงข้อมูล"
    self.iface.messageBar().pushMessage("Information", message, level=0, duration=3)
    self.dockwidget.add_Btn.setEnabled(0)
    self.dockwidget.edit_Btn.setEnabled(0)
    self.dockwidget.delete_Btn.setEnabled(0)
    remove_layer(self)
    # Clear Table unsuccessful
    self.dockwidget.tableUnsuccessful.setRowCount(0)

    extent = self.iface.mapCanvas().extent()
    bbox = str(extent.xMaximum()) + "," + str(extent.yMaximum()) + "," + str(extent.xMinimum()) + "," + str(
        extent.yMinimum())

    data = json.loads(self.collection_json)
    search_id = self.dockwidget.edit_datalayer_combo.currentText()

    result = list(filter(lambda x: x["itemtype"] == search_id, data['collection'][0]['items']))

    if len(result) > 0:
        collectionid = result[0]['collectionid']
        self.collectionid = collectionid
        db_directory = make_dir(self)
        f_properties = getItem_new(self, collectionid, bbox, db_directory, root, group)

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
                item = self.dockwidget.edit_datalayer_combo.currentText()

                if item == "VALVE" or item == "FIREHYDRANT" or item == "METER" or item == "BLDG":
                    if self.layerPipeName != "err":
                        setSupportLayer(self, root, group, supportLayerName=self.layerPipeName.name())
                    if item == "VALVE":
                        if self.layerMeterName != "err":
                            setSupportLayer(self, root, group, supportLayerName=self.layerMeterName.name())
                        if self.layerFireName != "err":
                            setSupportLayer(self, root, group, supportLayerName=self.layerFireName.name())
                    elif item == "FIREHYDRANT":
                        if self.layerMeterName != "err":
                            setSupportLayer(self, root, group, supportLayerName=self.layerMeterName.name())
                        if self.layerValveName != "err":
                            setSupportLayer(self, root, group, supportLayerName=self.layerValveName.name())
                    elif item == "METER":
                        if self.layerBldgName != "err":
                            setSupportLayer(self, root, group, supportLayerName=self.layerBldgName.name())
                    elif item == "BLDG":
                        if self.layerMeterName != "err":
                            setSupportLayer(self, root, group, supportLayerName=self.layerMeterName.name())
                elif item == "PIPE":
                    if self.layerBldgName != "err":
                        setSupportLayer(self, root, group, supportLayerName=self.layerBldgName.name())
                    if self.layerMeterName != "err":
                        setSupportLayer(self, root, group, supportLayerName=self.layerMeterName.name())
                    if self.layerValveName != "err":
                        setSupportLayer(self, root, group, supportLayerName=self.layerValveName.name())
                    if self.layerFireName != "err":
                        setSupportLayer(self, root, group, supportLayerName=self.layerFireName.name())
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
    self.dockwidget.edit_datalayer_combo.setEnabled(1)
    self.dockwidget.edit_loadataBtn.setEnabled(1)
    self.dockwidget.send_dataBtn.setEnabled(1)


def after_edit(self):
    self.geo_col = 0
    self.geo_col_edit = 0
    self.dockwidget.radio_add.setChecked(False)
    self.dockwidget.radio_edit.setChecked(False)
    self.dockwidget.send_dataBtn.setEnabled(True)

def setSupportLayer(self, root, group, supportLayerName):
    googleLayer = QgsProject.instance().mapLayersByName("Google Map")
    self.iface.setActiveLayer(googleLayer[0])
    layerSupport = QgsProject.instance().mapLayersByName(str(supportLayerName))
    if layerSupport:
        layerSupport = layerSupport[0]
        # Find the layer's current tree node
        layer_tree_layer = root.findLayer(layerSupport.id())
        if layer_tree_layer:
            # Clone the layer to the group and remove from root
            clone = layer_tree_layer.clone()
            group.insertChildNode(0, clone)
            root.removeChildNode(layer_tree_layer)


""" Load Qml For Support Layer"""
def supportLayer(self, qml_file):
    qml_path = os.path.join(self.plugin_dir, "ui_form", qml_file)
    layer = self.iface.activeLayer()
    layer.setReadOnly(True)
    layer.loadNamedStyle(qml_path, True)
    layer.triggerRepaint()


