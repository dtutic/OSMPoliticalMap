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

import ogr,sys,urllib2,csv

# Usage: missiong_iso_polygons.py shapefile.shp
# shapefile.shp should contain builded administrative polygons

#create list of ISO codes in second field of data record
iso_list = urllib2.urlopen('https://raw.githubusercontent.com/datasets/country-list/master/data.csv')
reader = csv.reader(iso_list)
data = list(reader)

#add Kosovo even though it is not in ISO3166
data.append(list(['Kosovo','XK']))

del data[0]



driver = ogr.GetDriverByName('ESRI Shapefile')
dataSource = driver.Open(sys.argv[1], 1)

layer = dataSource.GetLayer()

iso = []

for feature in layer:
    if feature.GetField('ISO3166-1_') is not None:
        iso.append(feature.GetField('ISO3166-1_'))
        if feature.GetField('ISO3166-1') is None:
            feature.SetField('ISO3166-1',feature.GetField('ISO3166-1_'))
            layer.SetFeature(feature)
    elif feature.GetField('ISO3166-1') is not None:
        iso.append(feature.GetField('ISO3166-1'))
        if feature.GetField('ISO3166-1_') is None:
            feature.SetField('ISO3166-1_',feature.GetField('ISO3166-1'))
            layer.SetFeature(feature)
    else:
        layer.DeleteFeature(feature.GetFID())

dataSource.Destroy()

missing =  []

for c in data:
    if not (c[1] in iso):
        missing.append(c)
      
for c in missing:
    print c[1]


