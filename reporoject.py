#Copyright (C) 2016, 2017 Drazen Tutic, Tomislav Jogun, Ana Kuvezdic Divjak
#This file is part of OSMPoliticalMap software.
#
#OSMPoliticalMap is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#OSMPoliticalMap is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with OSMPoliticalMap.  If not, see <http://www.gnu.org/licenses/>.

from osgeo import ogr, osr
import os,sys
from pyproj import Proj
import numpy as np

map_proj=Proj(os.getenv('OSM_PROJ'))

driver = ogr.GetDriverByName('ESRI Shapefile')

def Reproject_Ring(g):
    p_len = g.GetPointCount()
    points = np.zeros((p_len,2))
    for i in range(0, p_len):
        p = g.GetPoint(i)
        points[i,0],points[i,1] = map_proj(p[0],p[1])   
    ring = ogr.Geometry(ogr.wkbLinearRing)    
    for i in range (0,p_len):
        ring.AddPoint(points[i,0], points[i,1])
    return ring

def Reproject_Line(g):
    p_len = g.GetPointCount()
    points = np.zeros((p_len,2))
    for i in range(0, p_len):
        p = g.GetPoint(i)
        points[i,0],points[i,1] = map_proj(p[0],p[1])       
    line = ogr.Geometry(ogr.wkbLineString)    
    for i in range (0,p_len):
        line.AddPoint(points[i,0], points[i,1])
    return line

def Reproject_Point(g):
    points = np.zeros((1,2)) 
    for i in range(0,1):
        p = g.GetPoint(i)
        points[i,0],points[i,1] = map_proj(p[0],p[1])       
    point = ogr.Geometry(ogr.wkbPoint)
    for i in range(0,1):
        point.AddPoint(points[i,0], points[i,1])
    return point

# get the input layer
inDataSet = driver.Open(sys.argv[1])
inLayer = inDataSet.GetLayer()

# create the output layer
outputShapefile = sys.argv[2]
if os.path.exists(outputShapefile):
    driver.DeleteDataSource(outputShapefile)
outDataSet = driver.CreateDataSource(outputShapefile)
outLayer = outDataSet.CreateLayer(inLayer.GetName(), geom_type=inLayer.GetGeomType(),options=['ENCODING=UTF8'])

# add fields
inLayerDefn = inLayer.GetLayerDefn()
for i in range(0, inLayerDefn.GetFieldCount()):
    fieldDefn = inLayerDefn.GetFieldDefn(i)
    outLayer.CreateField(fieldDefn)

# get the output layer's feature definition
outLayerDefn = outLayer.GetLayerDefn()

# loop through the input features
feature = inLayer.GetNextFeature()
while feature:
    geom = feature.GetGeometryRef()
    if geom.GetGeometryName() == 'MULTIPOLYGON':
        geom_proj = ogr.Geometry(ogr.wkbMultiPolygon)
        for i in range(0, geom.GetGeometryCount()): #iterate over polygons
            poly = ogr.Geometry(ogr.wkbPolygon) 
            g = geom.GetGeometryRef(i) #polygon can have multiple rings
            for j in range(0, g.GetGeometryCount()): #iterate over rings
                ring = g.GetGeometryRef(j) #access to a ring (closed polyline)
                ring_proj = Reproject_Ring(ring) 
                poly.AddGeometry(ring_proj)
            geom_proj.AddGeometry(poly)                      
    elif geom.GetGeometryName() == 'POLYGON':
        geom_proj = ogr.Geometry(ogr.wkbPolygon) 
        for i in range(0, geom.GetGeometryCount()): #iterate over rings
            g = geom.GetGeometryRef(i) #access to a ring (closed polyline)
            ring_proj = Reproject_Ring(g)
            geom_proj.AddGeometry(ring_proj)
    elif geom.GetGeometryName() == 'MULTILINESTRING':
        geom_proj = ogr.Geometry(ogr.wkbMultiLineString)
        for i in range(0, geom.GetGeometryCount()): #iterate over lines
            g = geom.GetGeometryRef(i) 
            line_proj = Reproject_Line(g) 
            geom_proj.AddGeometry(line_proj)
    elif geom.GetGeometryName() == 'LINESTRING':
        geom_proj = Reproject_Line(geom)
    elif geom.GetGeometryName() == 'POINT':
        geom_proj = Reproject_Point(geom)
    # create a new feature
    outFeature = ogr.Feature(outLayerDefn)
    # set the geometry and attribute
    outFeature.SetGeometry(geom_proj)
    for i in range(0, outLayerDefn.GetFieldCount()):
        outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), feature.GetField(i))
    # add the feature to the shapefile
    outLayer.CreateFeature(outFeature)
    # destroy the features and get the next input feature
    outFeature.Destroy()
    feature.Destroy()
    feature = inLayer.GetNextFeature()


#create .prj file with fake projection (Plate Caree) instead of given one to avoid geographic CRS in QGIS
srs = osr.SpatialReference()
srs.ImportFromProj4('+proj=eqc +ellps=WGS84')
if srs is not None:
    srs.MorphToESRI()
    file = open(os.path.splitext(sys.argv[2])[0]+'.prj', 'w')
    file.write(srs.ExportToWkt())
    file.close()


# close the shapefiles
inDataSet.Destroy()
outDataSet.Destroy()
