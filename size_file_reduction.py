"""File reduction for website"""

import geopandas as gpd
# Check if we are running the notebook directly, if so move workspace to parent dir
import sys
import os
current_dir = os.path.abspath(os.getcwd())
if os.path.basename(current_dir) != 'EDeMOS':
  sys.path.insert(0, os.path.dirname(current_dir))
  os.chdir('..')
  print(f'Move to {os.getcwd()}')

## Define directories and dataset names
ROOT_DIR = os.path.abspath(os.curdir)
in_path = ROOT_DIR
out_path = ROOT_DIR + "/Outputs"

file = gpd.read_file(out_path + "\\" + f'total_electricity_consumption_Zambia.gpkg')  # , driver='GeoJSON', index=False)
print(file.columns)

list_columns_tokeep = ['h3_index', 'geometry',
                     'n0', 'n1', 'n2', 'n3', 'n4', 'n5',
                     'NAME_1',
                     'locationWP',
                     'HH_total',
                     'pop_total',
                     'HHwithAccess',
                     #'res_Bui',
                     'total_employee',
                     'res_elec_kWh_meth2',
                     'res_elec_kWh_meth2_scaled',
                     'ser_elec_kWh_final',
                     'ind_elec_GWh',
                     # add mining output?
                     ]

file_website = file[list_columns_tokeep]
# rename column?
# file_website.head(3)
file_website.to_file(out_path + "\\" + f'total_elec_consumption_web.gpkg', driver='GPKG') #, index=False)