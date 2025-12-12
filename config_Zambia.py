from pyproj import CRS
from pathlib import Path
import numpy as np

ROOT_DIR = Path( __file__ ).parent.absolute()

# -----------------------------------------------------------------------------
# AREA OF INTEREST CHOICE -- to update with the country
# -----------------------------------------------------------------------------
COUNTRY = "Zambia"
ISO_CODE = "ZMB"
# Define area of interest
AREA_OF_INTEREST = "COUNTRY"  # Can be "COUNTRY" or a specific region like "Copperbelt"

YEAR = 2019 # year of analysis

# -----------------------------------------------------------------------------
# COORDINATE REFERENCE SYSTEMS
# -----------------------------------------------------------------------------
CRS_WGS84 = CRS("EPSG:4326") # Original WGS84 coordinate system
CRS_PROJ = CRS("EPSG:32736") # Projection system for the selected country - see http://epsg.io/ for more info
TARGET_CRS_METERS = "EPSG:32735" # Used for grid line buffering (UTM Zone 35S)

# -----------------------------------------------------------------------------
# PARAMETERS - HEXAGONS
# -----------------------------------------------------------------------------

# hexagon size
HEX_SIZE = 7 ## resolution info here https://h3geo.org/docs/core-library/restable

# BUFFER DISTANCE in meters.
buffer_distance_meters = 1000 # This should be larger than half the diagonal of a hexagon


# -----------------------------------------------------------------------------
# INDUSTRY FILES
# -----------------------------------------------------------------------------

USGS_TABLE = "myb3-20-21-Zambia-advrel.xlsx"

# -----------------------------------------------------------------------------
# RESIDENTIAL FILES
# -----------------------------------------------------------------------------

# WorldPop files
# Link: https://apps.worldpop.org/peanutButter/
WP_BUILDINGS_COUNT_TIF = f"{ISO_CODE}_buildings_v2_0_count.tif"
WP_BUILDINGS_URBAN_TIF = f"{ISO_CODE}_buildings_v2_0_urban.tif"
WP_POPULATION_TIF =f"{ISO_CODE}_population_2022_v2_0_gridded_total.tif"
USE_POP_FILE = False

# Lighting file
# # set_lightscore_sy_xxxx.tif: Predicted likelihood that a settlement is electrified (0 to 1)
# Link: http://www-personal.umich.edu/~brianmin/HREA/data.html
HREA_LIGHTING_TIF = f"{ISO_CODE}_set_lightscore_sy_2019.tif"

# RWI file
# Link: https://gee-community-catalog.org/projects/rwi/
# run the notebook Rasterize RWI.ipynb to generate rwi_map.tif
RWI_MAP_TIF = f"rwi_map_{COUNTRY}.tif"
RWI_FILE_CSV = f"{ISO_CODE.lower()}_relative_wealth_index.csv"

# Falchetta Tiers file
# run the script transform-nc_to_tiff.py to generate .tif file
FALCHETTA_TIERS_TIF = f"tiersofaccess_SSA_2018_band1_{COUNTRY}.tif"

# GDP file Kummu dataset
# Link https://www.nature.com/articles/sdata20184#Sec9
# GDP_PPP_TIF = "GDP_PPP_30arcsec_v3_band3_{COUNTRY}.tif"

# UN Energy Balance file
# https://data.un.org/SdmxBrowser/start
UN_ENERGY_BALANCE_CSV = f"UNSD+DF_UNData_EnergyBalance+1.0_{ISO_CODE}.csv"

# Grid line files
# Data available at https://datacatalog.worldbank.org/search/dataset/0040190/Zambia---Electricity-Transmission-Network
# or https://energydata.info/dataset/zambia-electrical-lines
MV_LINES_SHP = "Zambia - MVLines/Zambia - MVLines.shp"
HV_LINES_SHP = "Zambia - HVLines/HVLines.shp"

# Census data files
# The file should contain the following data: 'region', 'HH_urban', 'HH_rural','size_HH_urban', 'size_HH_rural'
PROVINCE_DATA_AVAILABLE = True
CENSUS_PROVINCE_CSV = Path("Census") / COUNTRY / "Census_Zambia.csv"
CENSUS_NATIONAL_CSV = Path("Census") / COUNTRY / "Census_Zambia_National.csv"

# DHS Survey related files (used by estimate_energy_rwi_link_national_new.py)
# 1. Run read_DHS_hh_to_df.py in HouseholdEnergyUse folder to generate the household_data.csv
# 2. Run estimate_energy_perhh_DHS.py in HouseholdEnergyUse folder
# For services:
# 1 Download the Individual Recode  XXXXDT.ZIP to generate employee_survey_(men/women).csv
# 2 Run: read_DHS_services_to_df.py in HouseholdEnergyUse folder
# 3 Download or add the 'pop15-49_share_{COUNTRY}.csv' file in the DHS folder

RESIDENTIAL_DATA_PATH = ROOT_DIR / "Buildings" / "Data"
DHS_FOLDER = RESIDENTIAL_DATA_PATH / "DHS" / COUNTRY
DHS_HOUSEHOLD_DATA_CSV = DHS_FOLDER / f'household_data_{COUNTRY}.csv'
DHS_EMPLOYEE_WOMEN_CSV = DHS_FOLDER / f'employee_survey_women_{COUNTRY}.csv'
DHS_EMPLOYEE_MEN_CSV = DHS_FOLDER / f'employee_survey_men_{COUNTRY}.csv'
# Extract relevant information from Household population by age, sex and residence from DHS report
DHS_WORKING_POP_SHARE_CSV = DHS_FOLDER / f'pop15-49_share_{COUNTRY}.csv'

# -----------------------------------------------------------------------------
# DHS FILES PARAMETERS
# -----------------------------------------------------------------------------
DHS_HH_SURVEY_FILE = 'ZMHR71DT/ZMHR71FL'
DHS_SERVICES_SURVEY_FILE = 'ZMIR71DT/ZMIR71FL'

# Households labels
# Choose the labels to be selected from the .do file
# label variable hv001    "Cluster number"
#label variable hv005       "Household sample weight (6 decimals)"
#label variable hv009       "Number of household members",
#label variable hv022       "Sample strata for sampling errors"
#label variable hv023       "Stratification used in sample design"
#label variable hv024       "Province"
#label variable hv025       "Type of place of residence"
#label variable hv206       "Has electricity",
#label variable hv207       "Has radio"
#label variable hv208       "Has television"
#label variable hv209       "Has refrigerator"
#label variable hv243a      "Has mobile telephone"
#label variable hv243e      "Has a computer"
# label variable sh121f   "Access to Internet"
# label variable sh121j   "Washing machine"
# label variable sh121k   "Air conditioner"
# label variable sh121l   "Generator"
# label variable sh121m   "Microwave"
#label variable hv270       "Wealth index combined"
#label variable hv270a      "Wealth index for urban/rural"
#label variable hv271       "Wealth index factor score combined (5 decimals)"
#label variable hv271a      "Wealth index factor score for urban/rural (5 decimals)"
# label variable hv201    "Source of drinking water"
# label variable hv205    "Type of toilet facility"
# label variable hv211    "Has motorcycle/scooter"
# label variable hv212    "Has car/truck"
# label variable hv226    "Type of cooking fuel"
labels_hh = ['hv001', 'hv005','hv009', 'hv022', 'hv023', 'hv024', 'hv025', 'hv206', 'hv207', 'hv208', 'hv209', 'hv243a',
             'hv243e', 'sh121f', 'sh121j', 'sh121k', 'sh121l', 'sh121m',
             'hv270', 'hv270a', 'hv271', 'hv271a',
             'hv201', 'hv205', 'hv211', 'hv212', 'hv226',
             ]

# Define the columns we want to change in the DHS data and what their new names will be.
DHS_SURVEY_HH_old_to_new_names = {
    "Has electricity": "Electricity",
    "Has radio": "Radio",
    "Has mobile telephone": "Mobile telephone",
    "Has television": "Television",
    "Has refrigerator": "Refrigerator",
    "Has a computer": "Computer",
    "Access to Internet": "Internet",
    "Washing machine": "Washing machine",
    "Air conditioner": "Air conditioner",
    "Generator": "Generator",
    "Microwave": "Microwave",
}

# DHS Input Columns
DHS_CLUSTER = "Cluster number"
DHS_WEALTH_INDEX = "Wealth index factor score combined (5 decimals)"
DHS_WEIGHT = "Household sample weight (6 decimals)"
DHS_ELEC_ACCESS = "Electricity"
DHS_URBAN_RURAL = "Type of place of residence"
DHS_PROVINCE = "Province"


APPLIANCE_ELECTRICITY_CONS = 'appliance_energy_use.csv'
TIER = np.array([0, 0, 0, 1, 2, 2, 3, 4])

# -----------------------------------------------------------------------------
# PARAMETERS ENERGY BALANCE
# -----------------------------------------------------------------------------

# UN Energy Balance year
UN_ENERGY_YEAR = YEAR

# -----------------------------------------------------------------------------
# ANALYSIS PARAMETERS
# -----------------------------------------------------------------------------

# Residential demand parameters
THRESHOLD_ELEC_ACCESS_URBAN = 0.9
THRESHOLD_ELEC_ACCESS_RURAL = 0.3
MV_LINES_BUFFER_DIST = 500 # meters
HV_LINES_BUFFER_DIST = 500 # meters
CORRECTION_FACTOR_URBAN_HH_ACCESS = 0.75 #0.75 # For HHwithAccess_urb calculation
# Parameters below used to determine residential buildings but doesn't affect households numbers
NB_OF_HH_PER_RES_BUILDING_URBAN = 1.1 # to update depending on the country
NB_OF_HH_PER_RES_BUILDING_RURAL = 1.0

# Residential energy per HH - Method 1 (Logistic RWI)
LOGISTIC_E_THRESHOLD = 4656 # kWh, adjust to country
LOGISTIC_ALPHA_DERIVATION_THRESHOLD = 0.1 # set so that E_HH = 7kWh for lowest tier
# alpha = E_threshold / 0.1 - 1. This implies a specific low energy value.
# To get E_HH = 7kWh when rwi_norm is low (exp term ~1), E_threshold / (1+alpha) = 7.
# For now, will keep E_threshold and how alpha is derived from it.
LOGISTIC_K_INITIAL_GUESS = 10

# DHS Data parameters
DHS_ELEC_KWH_ASSESSED_SURVEY = 'electricity_cons_kWh'
DHS_RECALCULATE_ENERGY_PERHH = True
DHS_ELAS = 0.4
DHS_HH_SIZE = 4
DHS_EMPLOYMENT_CATEGORIES = ['professional/technical/managerial', 'clerical', 'sales', 'services', 'skilled manual']
DHS_WORKING_AGE_GROUP_KEY = '15-49'

# Tiers for comparison
BINS_TIERS_ENERGY = [0, 7, 72.9-0.1, 364.9-0.1, 1250.4-0.1, 3012.2-0.1, float('inf')]

# Services demand parameters
# Weights for weighted average of services energy (alpha: GDP, beta: buildings, gamma: employees)
SERVICES_WEIGHT_GDP = 0.0 # alpha
SERVICES_WEIGHT_BUILDINGS = 0.0 # beta
SERVICES_WEIGHT_EMPLOYEES = 1.0 # gamma
# THRESHOLD_ACCESS_SERVICES = 0.1 # from original script, check if used with new structure
