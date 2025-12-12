# Main configuration dispatcher
# This file is responsible for loading the correct country-specific configuration.
import importlib

# Select the active country by changing the string value below.
ACTIVE_COUNTRY = "Zambia"  # Or "Kenya" "Zambia":

if ACTIVE_COUNTRY == "Kenya":
    import config_Kenya
    importlib.reload(config_Kenya)
    from config_Kenya import *
    print(f"INFO: Successfully loaded configuration for Kenya from config.py.")
elif ACTIVE_COUNTRY == "Zambia":
    import config_Zambia
    importlib.reload(config_Zambia)
    from config_Zambia import *
    print(f"INFO: Successfully loaded configuration for Zambia from config.py.")
else:
    raise ValueError(
        f"Unsupported country: '{ACTIVE_COUNTRY}'. "
        f"Please check the ACTIVE_COUNTRY variable in config.py "
        f"and ensure a corresponding config_{ACTIVE_COUNTRY}.py file exists."
    )


# -----------------------------------------------------------------------------
# PATHS
# -----------------------------------------------------------------------------

DATA_FOLDER = ROOT_DIR / "Data"
# Input paths
ADMIN_PATH = DATA_FOLDER / "admin"
ADMIN_GPKG = f"gadm41_{ISO_CODE}.gpkg"

# Output paths
OUTPUT_DIR = ROOT_DIR / "Outputs"
# Ensure all folders for output files exist
OUTPUT_DIR.mkdir(exist_ok=True)

# -----------------------------------------------------------------------------
# RESIDENTIAL PATHS
# -----------------------------------------------------------------------------

# File paths

# Input paths
GRID_PATH = DATA_FOLDER / "Grid" / COUNTRY # For MV/HV lines
ENERGY_BALANCE_PATH = DATA_FOLDER / "EnergyBalance"
WORLDPOP_PATH = RESIDENTIAL_DATA_PATH / "WorldPop"
LIGHTING_PATH = RESIDENTIAL_DATA_PATH / "Lighting"
RWI_PATH = RESIDENTIAL_DATA_PATH / "WealthIndex"
POP_PATH = RESIDENTIAL_DATA_PATH / "HRSL"
FALCHETTA_PATH = RESIDENTIAL_DATA_PATH / "Falchetta_ElecAccess"
# GDP_PATH = RESIDENTIAL_DATA_PATH / "GDP")
DHS_FOLDER = RESIDENTIAL_DATA_PATH / "DHS" / COUNTRY

# Output paths
RESIDENTIAL_OUTPUT_DIR = ROOT_DIR / "Buildings" / "Outputs" # As used in building_demand.py for dataHH_region.csv
FIGURES_DHS_FOLDER = ROOT_DIR / "Buildings" / "Figures" # As used in estimate_energy_rwi_link_national_new.py

# Ensure all folders for output files exist
RESIDENTIAL_OUTPUT_DIR.mkdir(exist_ok=True)
FIGURES_DHS_FOLDER.mkdir(exist_ok=True)

# -----------------------------------------------------------------------------
# PARAMETERS ENERGY BALANCE
# -----------------------------------------------------------------------------

# UN Energy Balance codes
UN_ELEC_CODE = "B07_EL"
UN_OIL_CODE = "B03_OP"
UN_HH_TRANSACTION_CODE = "B50_1231"
UN_SERVICES_TRANSACTION_CODE = "B49_1235"
UN_OTHER_TRANSACTION_CODE = "B51_1234" # Other consumption not elsewhere specified
UN_INDUSTRY_NFM = "B29_1214a"
UN_INDUSTRY_MINING = "B33_1214e"

# -----------------------------------------------------------------------------
# PARAMETERS - ADMIN
# -----------------------------------------------------------------------------

# HEXAGON FILE NAME
H3_GRID_HEX_SHP = f"h3_grid_at_hex_{COUNTRY}_size{HEX_SIZE}.shp" # Located in current OUTPUT_DIR

# Admin boundaries
ADMIN_LAYER_REGION = "ADM_ADM_1"
ADMIN_LAYER_COUNTRY = "ADM_ADM_0"
ADMIN_REGION_COLUMN_NAME = "NAME_1"

# -----------------------------------------------------------------------------
# COLUMN NAMES FOR GRID
# -----------------------------------------------------------------------------
# Input columns from H3 grid
COL_H3_ID = 'h3_index' # the ID column in h3_grid_at_hex.shp
COL_ADMIN_NAME = ADMIN_REGION_COLUMN_NAME

# Processed column names
COL_BUILDINGS_SUM = 'buildingssum'
COL_POPULATION_WP = 'populationWP'
COL_LOCATION_WP = 'locationWP' # after processing_raster
COL_HREA_MEAN = 'HREA' # after processing_raster and rename
PROB_ELEC_COL = COL_HREA_MEAN # residential analysis parameters
COL_RWI_MEAN = 'rwi_mean'
COL_TIERS_FALCHETTA_MAJ = 'tiers_falchetta_maj'
COL_TIERS_FALCHETTA_MEAN = 'tiers_falchetta_mean'
COL_GDP_PPP_MEAN = 'GDP_PPP'

COL_LOC_ASSESSED = 'location' # Final urban/rural column
COL_STATUS_ELECTRIFIED = 'status_electrified'
COL_IS_NEAR_ANY_LINE = 'is_near_any_line'

COL_RES_URBAN_BUI = 'res_urbanBui'
COL_RES_RURAL_BUI = 'res_ruralBui'
COL_RES_BUI = 'res_totalBui'
COL_HH_URBAN = 'HH_urban'
COL_HH_RURAL = 'HH_rural'
COL_HH_TOTAL = 'HH_total'
COL_POP_URBAN = 'pop_urban'
COL_POP_RURAL = 'pop_rural'
COL_POPULATION = 'pop_total'

COL_POP_WITH_ACCESS_URB = 'pop_withAccess_urb'
COL_POP_WITH_ACCESS_RUR = 'pop_withAccess_rur'
COL_POP_WITH_ACCESS = 'pop_withAccess'
COL_HH_WITH_ACCESS_URB = 'HHwithAccess_urb'
COL_HH_WITH_ACCESS_RUR = 'HHwithAccess_rur'
COL_HH_WITH_ACCESS = 'HHwithAccess'
COL_HH_WO_ACCESS_URB = 'HHwoAccess_urb'
COL_HH_WO_ACCESS_RUR = 'HHwoAccess_rur'
COL_HH_WO_ACCESS = 'HHwoAccess'

COL_RWI_NORM = 'rwi_norm'
COL_RWI_MODIFIED = 'rwi_modified'
COL_RWI_REGION_MODIFIED  = 'rwi_region_modified'
COL_RWI_ANALYSIS = 'rwi_analysis'
COL_RES_ELEC_PER_HH_LOG = 'elec_perHH_kWh_log'
COL_RES_ELEC_PER_HH_KWH_DHS = 'elec_perHH_kWh_DHS'
COL_RES_ELEC_KWH_METH1 = 'res_elec_kWh_meth1'
COL_RES_ELEC_KWH_METH2 = 'res_elec_kWh_meth2'
COL_RES_TOTAL_ELEC_KWH_DHS = 'res_elec_kWh_dhs'
COL_RES_ELEC_KWH_METH1_SCALED = 'res_elec_kWh_meth1_scaled'
COL_RES_ELEC_KWH_METH2_SCALED = 'res_elec_kWh_meth2_scaled'
COL_RES_ELEC_KWH_FINAL = 'res_elec_kWh_final'

COL_SER_BUI = 'serBui'
COL_SER_BUI_ACC = 'serBUi_access'
COL_SER_ELEC_KWH_BUI = 'ser_elec_kWh_bui'
# COL_SER_ELEC_KWH_GDP = 'Ser_elec_kWh_GDP' # If GDP method is used
COL_TOTAL_EMPLOYEE = 'total_employee'
COL_TOTAL_EMPLOYEE_WITH_ACCESS = 'total_employee_withaccess'
COL_SER_ELEC_KWH_EMP = 'ser_elec_kWh_emp'
COL_SER_ELEC_KWH_WEIGHTED = 'ser_elec_kWh_weighted'
COL_SER_ELEC_KWH_FINAL = 'ser_elec_kWh_final' # Final services result

COL_BUI_ELEC_KWH_FINAL = 'bui_elec_kWh_final'

# -----------------------------------------------------------------------------
# INDUSTRY PARAMETERS
# -----------------------------------------------------------------------------
MINES_DATA_PATH = ROOT_DIR / "Industry/Data/mines"
USGS_DATA_PATH = MINES_DATA_PATH / "Africa_GIS.gdb"
USGS_DATA_OUTPUT_PATH = MINES_DATA_PATH / "Africa_GIS"
# Ensure folder for USGS output files exist
USGS_DATA_OUTPUT_PATH.mkdir(exist_ok=True)
MINES_INPUT_CSV = USGS_DATA_OUTPUT_PATH / "AFR_Mineral_Facilities.csv"
# MINES_INPUT_CSV = MINES_DATA_PATH / "Mineral_Facilities_correctedInput.csv"
TOTAL_PROD_USGS_FILE = MINES_DATA_PATH / USGS_TABLE
ADD_INFO_FILE = MINES_DATA_PATH / "Additional_info.xlsx"
COL_IND_ELEC_TJ = "ind_elec_TJ"
COL_IND_ELEC_GWH = "ind_elec_GWh"
COL_IND_ELEC_KWH = "ind_elec_kWh"
COL_IND_OIL_TJ = "ind_diesel_TJ"
COL_IND_TOTAL_TJ = "ind_total_energy_TJ"
COL_IND_COPPER_ELEC_TJ = "copper_elec_TJ"
COL_IND_ELEC_SCALED_TJ = "ind_elec_scaled_TJ"

INDUSTRY_OUTPUT_DIR = ROOT_DIR / "Industry/Outputs"
INDUSTRY_OUTPUT_DIR.mkdir(exist_ok=True)
MINES_OUTPUT_GPKG = INDUSTRY_OUTPUT_DIR / f"mineral_facilities_{COUNTRY.lower()}.gpkg"
MINES_OUTPUT_CSV = INDUSTRY_OUTPUT_DIR / f"mineral_facilities_{COUNTRY.lower()}.csv"


# -----------------------------------------------------------------------------
# TOTAL PARAMETERS
# -----------------------------------------------------------------------------

COL_TOTAL_ELEC_KWH = 'total_elec_kWh'

# -----------------------------------------------------------------------------
# RESULTS FILES NAME
# -----------------------------------------------------------------------------
RESIDENTIAL_TEMP_FILE = RESIDENTIAL_OUTPUT_DIR / f'data_res_{COUNTRY}_hexsize{HEX_SIZE}.gpkg'
RESIDENTIAL_GRID_FILE = RESIDENTIAL_OUTPUT_DIR / f'data_res_{ACTIVE_COUNTRY}.csv'
SERVICES_GRID_FILE = RESIDENTIAL_OUTPUT_DIR / f'data_ser_{ACTIVE_COUNTRY}.csv'
BUILDINGS_GPKG_FILE = RESIDENTIAL_OUTPUT_DIR / f'buildings_map_{ACTIVE_COUNTRY}.gpkg'
INDUSTRY_GPKG_FILE = INDUSTRY_OUTPUT_DIR / f'ind_energy_map_{ACTIVE_COUNTRY}.gpkg'
TOTAL_ELECTRICITY_GPKG_FILE = OUTPUT_DIR / f'total_electricity_consumption_{ACTIVE_COUNTRY}.gpkg'
