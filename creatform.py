from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QAbstractItemView, QFileDialog
from qgis.core import QgsVectorLayer, QgsProject, QgsPoint, QgsRectangle, QgsCoordinateReferenceSystem, QgsRasterLayer, QgsMapLayer
from qgis.utils import *
from qgis.PyQt import uic
import qgis


# Get the active layer (using Python syntax)
def check_layer(self):
    canvas = self.iface.mapCanvas()
    # canvas = qgis.gui.QgsMapCanvas()
    layer = canvas.currentLayer()

    if not layer:
            message = "No active layer found. Please select a layer."
            self.iface.messageBar().pushMessage("Information  ", message, level=3, duration=3)
            return "error"
    else:
        if layer.type() == QgsMapLayer.RasterLayer or str(layer.type()) == "LayerType.Raster" or str(layer.type()) == "1":
            message = "No active Vector layer found. Please select a layer."
            self.iface.messageBar().pushMessage("Information  ", message, level=3, duration=3)
            return "error"
        elif layer.type() == QgsMapLayer.VectorLayer or str(layer.type()) == "LayerType.Vector" or str(layer.type()) == "0":
            # Rest of the code (same as before, starting from field properties)
            # fields = layer.fields()
            field_names = list(layer.attributeAliases().keys())
            self.dockwidget.plainTextEdit_3.insertPlainText("")
            self.dockwidget.plainTextEdit_3.insertPlainText(str(field_names))
            return layer
        elif layer.type() == QgsMapLayer.VectorTileLayer or str(layer.type()) == "LayerType.VectorTile" or str(layer.type()) == "4":
            return layer


"""
0: Vector layer (QgsMapLayer.VectorLayer)
1: Raster layer (QgsMapLayer.RasterLayer)
2: Plugin layer (QgsMapLayer.PluginLayer)
3: Mesh layer (QgsMapLayer.MeshLayer)
4: Vector tile layer (QgsMapLayer.VectorTileLayer)
"""