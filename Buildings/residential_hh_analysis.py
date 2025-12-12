import geopandas as gpd
import pandas as pd
import numpy as np


def determine_location_status(grid_gdf, app_config):
    """
    Determines urban/rural status for each grid cell based on WorldPop urban extent data.

    Args:
        grid_gdf: GeoDataFrame of the hexagonal grid with WorldPop data.
        app_config: The configuration module.

    Returns:
        GeoDataFrame: grid_gdf with an added column for location status.
    """
    print("Determining location status (urban/rural)...")
    if app_config.COL_LOCATION_WP not in grid_gdf.columns:
        raise KeyError(f"Required column '{app_config.COL_LOCATION_WP}' not found in grid. Available: {grid_gdf.columns.tolist()}")

    grid_gdf[app_config.COL_LOC_ASSESSED] = grid_gdf.apply(
        lambda row: "urban" if row[app_config.COL_LOCATION_WP] == 1 else "rural",
        axis=1
    )
    # Other methods
    # grid["locGHSL"] = grid.apply (lambda row: ("urban" if ((row['SMOD'] == 30) or (row['SMOD'] == 21) or (row['SMOD'] == 22) or (row['SMOD' ] == 23))
#                                              else "rural"), axis=1)
    # grid["locAssessed"] = grid.apply(lambda row: ("urban" if ((row['buildingssum'] > 1000)) # number chosen to get 1 for nb of HH per rural building
#                                              else "rural"), axis=1)
    print(f"'{app_config.COL_LOC_ASSESSED}' column created. Counts: {grid_gdf[app_config.COL_LOC_ASSESSED].value_counts().to_dict()}")
    return grid_gdf


def determine_electrification_status(grid_gdf, app_config, admin_gdf, prox_line=True):
    """
    Determines electrification status of grid cells based on proximity to MV/HV lines
    and HREA (High Resolution Electricity Access) likelihood scores.

    Args:
        prox_line: Include the proximity of hv and mv lines.
        grid_gdf: GeoDataFrame of the hexagonal grid.
        app_config: The configuration module.
        admin_gdf: GeoDataFrame of admin boundaries

    Returns:
        GeoDataFrame: grid_gdf with added columns for line proximity and electrification status.
    """
    print("Determining electrification status...")

    # Load MV and HV lines
    mv_lines_gdf = gpd.read_file(app_config.GRID_PATH / app_config.MV_LINES_SHP)
    hv_lines_gdf = gpd.read_file(app_config.GRID_PATH /app_config.HV_LINES_SHP)
    # print(f"MV lines loaded: {mv_lines_gdf.shape}, HV lines loaded: {hv_lines_gdf.shape}")

    print("--- Initial Data Sanity Check ---")
    target_crs = app_config.TARGET_CRS_METERS
    print(f"Grid CRS: {grid_gdf.crs} | Shape: {grid_gdf.shape}")
    print(f"Admin Boundary CRS: {admin_gdf.crs} | Shape: {admin_gdf.shape}")
    print(f"MV Lines CRS: {mv_lines_gdf.crs} | Shape: {mv_lines_gdf.shape}")
    print(f"HV Lines CRS: {hv_lines_gdf.crs} | Shape: {hv_lines_gdf.shape}")
    print(f"Target CRS for all operations: {target_crs}\n")

    if prox_line:
        # --- STEP 1: PROJECT ALL DATA TO THE TARGET CRS ---
        # This ensures all subsequent operations (clip, buffer, sjoin) are in the same
        # projected, meter-based coordinate system.

        print("--- Projecting all data to target CRS ---")
        grid_projected = grid_gdf.to_crs(target_crs)
        admin_projected = admin_gdf.to_crs(target_crs)
        # mv_lines_projected = mv_lines_gdf.to_crs(target_crs)
        # hv_lines_projected = hv_lines_gdf.to_crs(target_crs)

        # Initialize the proximity column to False
        grid_gdf[app_config.COL_IS_NEAR_ANY_LINE] = False

        # Define line types and their specific buffer distances
        lines_to_process = [
            {'name': 'HV Lines', 'gdf': hv_lines_gdf, 'buffer_dist': app_config.HV_LINES_BUFFER_DIST},
            {'name': 'MV Lines', 'gdf': mv_lines_gdf, 'buffer_dist': app_config.MV_LINES_BUFFER_DIST}
        ]

        for line_info in lines_to_process:
            current_lines_gdf = line_info['gdf']
            line_name = line_info['name']
            buffer_dist = line_info['buffer_dist']
            print(f"Processing proximity for {line_name} with buffer {buffer_dist}m...")

            if current_lines_gdf.crs != target_crs:
                lines_for_clip_and_buffer = current_lines_gdf.to_crs(target_crs)
            else:
                lines_for_clip_and_buffer = current_lines_gdf.copy()

            # 1. Clip lines
            clipped_lines_gdf = gpd.clip(lines_for_clip_and_buffer, admin_projected)
            if clipped_lines_gdf.empty:
                print(f"No {line_name} found within the admin boundaries after clipping.")
                continue

            # 2. Buffer
            buffered_lines = clipped_lines_gdf.buffer(buffer_dist)
            if buffered_lines.is_empty.all():
                print(f"Buffer for {line_name} is empty. Skipping spatial join.")
                continue

            # 3. Create a GeoDataFrame of the individual buffers
            buffered_areas_gdf = gpd.GeoDataFrame(geometry=buffered_lines, crs=target_crs)

            # 4. Perform the spatial join.
            # Use an 'inner' join to get only the grid cells that intersect.
            intersecting_grid = gpd.sjoin(grid_projected, buffered_areas_gdf, how='inner', predicate='intersects')

            # Get the unique indices of the original grid cells that are near the lines
            indices_to_update = intersecting_grid.index.unique()

            # 5. Update the 'is_near_any_line' column in the ORIGINAL grid.
            grid_gdf.loc[indices_to_update, app_config.COL_IS_NEAR_ANY_LINE] = True

        print(f"Updated 'is_near_any_line' column. Current counts:")
        print(grid_gdf['is_near_any_line'].value_counts())

    if app_config.PROB_ELEC_COL not in grid_gdf.columns:
        raise KeyError(f"Required column '{app_config.PROB_ELEC_COL}' not found in grid.")
    if app_config.COL_LOC_ASSESSED not in grid_gdf.columns:
        raise KeyError(f"Required column '{app_config.COL_LOC_ASSESSED}' not found in grid.")

    # electrified or non-electrified status with thresholds depending on the location
    threshold_map = {'urban': app_config.THRESHOLD_ELEC_ACCESS_URBAN, 'rural': app_config.THRESHOLD_ELEC_ACCESS_RURAL}
    if prox_line:
        grid_gdf[app_config.COL_STATUS_ELECTRIFIED] = grid_gdf.apply(
            lambda row: "elec" if (
                row[app_config.PROB_ELEC_COL] > threshold_map[row[app_config.COL_LOC_ASSESSED]] and
                row[app_config.COL_IS_NEAR_ANY_LINE]
            ) else "nonelec",
            axis=1
        )
    else:
        grid_gdf[app_config.COL_STATUS_ELECTRIFIED] = grid_gdf.apply(
            lambda row: "elec" if (
                row[app_config.PROB_ELEC_COL] > threshold_map[row[app_config.COL_LOC_ASSESSED]]
            ) else "nonelec",
            axis=1
        )
    print(f"'{app_config.COL_STATUS_ELECTRIFIED}' column created. Counts: {grid_gdf[app_config.COL_STATUS_ELECTRIFIED].value_counts().to_dict()}")

    return grid_gdf


def calculate_household_numbers_popinput(grid_gdf, app_config, data_HH, df_censusdata):
    """
    Calculates household numbers per grid cell direclty from the population input file.

    Args:
        grid_gdf: GeoDataFrame of the hexagonal grid.
        app_config: The configuration module.
        data_HH: DataFrame with census data.

    Returns:
               - grid_gdf: Updated grid GeoDataFrame with new household columns.
    """
    if app_config.PROVINCE_DATA_AVAILABLE:
        # --- Step 1: Create the mapping Series from data_HH ---
        # This creates a Series where the index is the province ('region')
        # and the values are the urban household sizes.
        urban_hh_size_map = data_HH['size_HH_urban']

        # This does the same for rural household sizes.
        rural_hh_size_map = data_HH['size_HH_rural']
        # --- Step 2: Map these sizes to your grid geodataframe ---
        # This creates a new column in 'grid' by looking up each province (app_config.COL_ADMIN_NAME)
        # in the corresponding map.
        grid_gdf['temp_urban_hh_size'] = grid_gdf[app_config.COL_ADMIN_NAME].map(urban_hh_size_map)
        grid_gdf['temp_rural_hh_size'] = grid_gdf[app_config.COL_ADMIN_NAME].map(rural_hh_size_map)

        # --- Step 3: Select the correct household size for each grid cell ---
        # Use np.where for a fast conditional selection.
        # If grid['locationWP'] is 'urban', use the value from 'temp_urban_hh_size',
        # otherwise, use the value from 'temp_rural_hh_size'.
        grid_gdf['hh_size'] = np.where(grid_gdf[app_config.COL_LOC_ASSESSED] == 'urban',
                                   grid_gdf['temp_urban_hh_size'],
                                   grid_gdf['temp_rural_hh_size'])
        # --- Step 4: Compute the number of households ---
        grid_gdf[app_config.COL_HH_TOTAL] = grid_gdf[app_config.COL_POPULATION_WP] / grid_gdf['hh_size']

        # --- Step 5: Clean up the temporary columns ---
        grid_gdf.drop(columns=['temp_urban_hh_size', 'temp_rural_hh_size', 'hh_size'], inplace=True)
    else:
        grid_gdf['hh_size'] = np.where(grid_gdf[app_config.COL_LOC_ASSESSED] == 'urban',
                                   df_censusdata['size_HH_urban'],
                                   df_censusdata['size_HH_rural'])
        grid_gdf[app_config.COL_HH_TOTAL] = grid_gdf[app_config.COL_POPULATION_WP] / grid_gdf['hh_size']
    grid_gdf[app_config.COL_HH_URBAN] = np.where(grid_gdf[app_config.COL_LOC_ASSESSED] == 'urban',
                                   grid_gdf[app_config.COL_HH_TOTAL],
                                   0)
    grid_gdf[app_config.COL_HH_RURAL] = np.where(grid_gdf[app_config.COL_LOC_ASSESSED] == 'rural',
                               grid_gdf[app_config.COL_HH_TOTAL],
                               0)
    return grid_gdf

def calculate_household_numbers(grid_gdf, app_config, data_HH, regions_list):
    """
    Calculates residential building counts and household numbers per grid cell.

    It distinguishes between urban and rural areas and uses either provincial or
    national level census data based on `app_config.PROVINCE_DATA_AVAILABLE`.
    Calculates total population if provincial data (with household sizes) is used.

    Args:
        grid_gdf: GeoDataFrame of the hexagonal grid.
        app_config: The configuration module.
        data_HH: DataFrame with census data.
        regions_list: List of region names being processed.

    Returns:
        tuple: (grid_gdf, df_HH_buildings)
               - grid_gdf: Updated grid GeoDataFrame with new household/population columns.
               - df_HH_buildings: DataFrame summarizing household data by region (if provincial).
                                  Returns None if national data is used.
    """
    print("Calculating household numbers...")
    df_HH_buildings = None # Initialize for optional return

    if app_config.PROVINCE_DATA_AVAILABLE:
        data_buildings_list = []
        for region_name in regions_list:
            if app_config.COL_ADMIN_NAME not in grid_gdf.columns:
                 raise KeyError(f"Admin name column '{app_config.COL_ADMIN_NAME}' not found in grid for region filtering.")

            totalBuildings = grid_gdf[grid_gdf[app_config.COL_ADMIN_NAME] == region_name][app_config.COL_BUILDINGS_SUM].sum()
            urbanBuildings = grid_gdf[(grid_gdf[app_config.COL_LOC_ASSESSED] == "urban") & (grid_gdf[app_config.COL_ADMIN_NAME] == region_name)][app_config.COL_BUILDINGS_SUM].sum()
            ruralBuildings = grid_gdf[(grid_gdf[app_config.COL_LOC_ASSESSED] == "rural") & (grid_gdf[app_config.COL_ADMIN_NAME] == region_name)][app_config.COL_BUILDINGS_SUM].sum()

            data_region = {
                'region': region_name,
                'totalBuildings': totalBuildings,
                'urbanBuildings': urbanBuildings if totalBuildings > 0 else 0,
                'ruralBuildings': ruralBuildings if totalBuildings > 0 else 0,
                'shareRuralBuild': ruralBuildings / totalBuildings if totalBuildings > 0 else 0,
                'shareUrbanBuild': urbanBuildings / totalBuildings if totalBuildings > 0 else 0,
            }
            data_buildings_list.append(data_region)

        df_buildings = pd.DataFrame(data_buildings_list)
        df_buildings.set_index('region', inplace=True)
        df_HH_buildings = data_HH.merge(df_buildings, left_on='region', right_on='region', how='left')

        #Reallocate HH if no buildings linked to the location
        # Create masks for the conditions
        cond_no_urban_buildings = (df_HH_buildings['urbanBuildings'] == 0) & (df_HH_buildings['HH_urban'] > 0)
        cond_no_rural_buildings = (df_HH_buildings['ruralBuildings'] == 0) & (df_HH_buildings['HH_rural'] > 0)
        # Reallocate HH_urban to HH_rural if urbanBuildings is 0
        df_HH_buildings.loc[cond_no_urban_buildings, 'HH_rural'] = df_HH_buildings.loc[cond_no_urban_buildings, 'HH_rural'] + df_HH_buildings.loc[cond_no_urban_buildings, 'HH_urban']
        df_HH_buildings.loc[cond_no_urban_buildings, 'HH_urban'] = 0
        # Reallocate HH_rural to HH_urban if ruralBuildings is 0
        df_HH_buildings.loc[cond_no_rural_buildings, 'HH_urban'] = \
            df_HH_buildings.loc[cond_no_rural_buildings, 'HH_urban'] + \
            df_HH_buildings.loc[cond_no_rural_buildings, 'HH_rural']
        df_HH_buildings.loc[cond_no_rural_buildings, 'HH_rural'] = 0


        # Warning if mismatch happen
        # To avoid division by zero, we calculate the denominator first
        denominator_urban = app_config.NB_OF_HH_PER_RES_BUILDING_URBAN * df_HH_buildings['urbanBuildings']
        # Initialize the column with zeros
        df_HH_buildings['shareUrbanResBui'] = 0.0
        # Identify rows where the denominator is non-zero
        valid_mask_urban = denominator_urban != 0
        # Calculate the share only for valid rows
        df_HH_buildings.loc[valid_mask_urban, 'shareUrbanResBui'] = df_HH_buildings.loc[valid_mask_urban, 'HH_urban'] / denominator_urban[valid_mask_urban]

        # --- Print data inconsistencies ---
        invalid_mask = ~valid_mask_urban & (df_HH_buildings['HH_urban'] > 0)
        if invalid_mask.any():
            lost_hh = df_HH_buildings.loc[invalid_mask, 'HH_urban'].sum()
            regions_affected = df_HH_buildings.loc[invalid_mask].index.tolist()
            print(
                f"Data Inconsistency: {lost_hh:,.0f} urban households could not be allocated "
                f"because no urban buildings were found in region(s): {regions_affected}. "
                f"Their share is set to 0."
            )

        df_HH_buildings['shareUrbanResBui'] = df_HH_buildings['HH_urban'] / (app_config.NB_OF_HH_PER_RES_BUILDING_URBAN * df_HH_buildings['urbanBuildings'])
        df_HH_buildings['shareRuralResBui'] = df_HH_buildings['HH_rural'] / (app_config.NB_OF_HH_PER_RES_BUILDING_RURAL * df_HH_buildings['ruralBuildings'])

        df_HH_buildings.fillna(0, inplace=True)

        df_HH_buildings['resUrbanBui'] = df_HH_buildings['urbanBuildings'] * df_HH_buildings['shareUrbanResBui']
        df_HH_buildings['resRuralBui'] = df_HH_buildings['ruralBuildings'] * df_HH_buildings['shareRuralResBui']
        df_HH_buildings['resTotalBui'] = df_HH_buildings['resUrbanBui'] + df_HH_buildings['resRuralBui']

        # if not app_config.COL_ADMIN_NAME in df_HH_buildings.index:
        #     raise KeyError(f"Required column '{app_config.COL_ADMIN_NAME}' not found in census data.")

        grid_gdf[app_config.COL_RES_URBAN_BUI] = grid_gdf.apply(
            lambda row: row[app_config.COL_BUILDINGS_SUM] * df_HH_buildings.loc[row[app_config.COL_ADMIN_NAME], 'shareUrbanResBui']
                        if row[app_config.COL_LOC_ASSESSED] == 'urban' else 0, axis=1
        )
        grid_gdf[app_config.COL_RES_RURAL_BUI] = grid_gdf.apply(
            lambda row: row[app_config.COL_BUILDINGS_SUM] * df_HH_buildings.loc[row[app_config.COL_ADMIN_NAME], 'shareRuralResBui']
                        if row[app_config.COL_LOC_ASSESSED] == 'rural' else 0, axis=1
        )
    else:
        totalBuildings = grid_gdf[app_config.COL_BUILDINGS_SUM].sum()
        urbanBuildings = grid_gdf[grid_gdf[app_config.COL_LOC_ASSESSED] == "urban"][app_config.COL_BUILDINGS_SUM].sum()
        ruralBuildings = grid_gdf[grid_gdf[app_config.COL_LOC_ASSESSED] == "rural"][app_config.COL_BUILDINGS_SUM].sum()

        nat_HH_urban = data_HH['Urban'].iloc[0]
        nat_HH_rural = data_HH['Rural'].iloc[0]

        shareResBui_urban = nat_HH_urban / (app_config.NB_OF_HH_PER_RES_BUILDING_URBAN * urbanBuildings) if urbanBuildings > 0 else 0
        shareResBui_rural = nat_HH_rural / (app_config.NB_OF_HH_PER_RES_BUILDING_RURAL * ruralBuildings) if ruralBuildings > 0 else 0

        grid_gdf[app_config.COL_RES_URBAN_BUI] = grid_gdf.apply(
            lambda row: row[app_config.COL_BUILDINGS_SUM] * shareResBui_urban if row[app_config.COL_LOC_ASSESSED] == 'urban' else 0, axis=1
        )
        grid_gdf[app_config.COL_RES_RURAL_BUI] = grid_gdf.apply(
            lambda row: row[app_config.COL_BUILDINGS_SUM] * shareResBui_rural if row[app_config.COL_LOC_ASSESSED] == 'rural' else 0, axis=1
        )

    grid_gdf[app_config.COL_RES_BUI] = grid_gdf[app_config.COL_RES_URBAN_BUI] + grid_gdf[app_config.COL_RES_RURAL_BUI]
    grid_gdf[app_config.COL_HH_URBAN] = (grid_gdf[app_config.COL_RES_URBAN_BUI] * app_config.NB_OF_HH_PER_RES_BUILDING_URBAN).fillna(0)
    grid_gdf[app_config.COL_HH_RURAL] = (grid_gdf[app_config.COL_RES_RURAL_BUI] * app_config.NB_OF_HH_PER_RES_BUILDING_RURAL).fillna(0)
    grid_gdf[app_config.COL_HH_TOTAL] = grid_gdf[app_config.COL_HH_URBAN] + grid_gdf[app_config.COL_HH_RURAL]

    if app_config.PROVINCE_DATA_AVAILABLE:
        if not all(f"size_HH_{loc}" in data_HH.columns for loc in ["urban", "rural"]):
            raise KeyError("Missing 'size_HH_urban' or 'size_HH_rural' in census data for population calculation.")

        get_size_HH = lambda row: data_HH.loc[row[app_config.COL_ADMIN_NAME], f"size_HH_{row[app_config.COL_LOC_ASSESSED]}"] \
                                  if row[app_config.COL_ADMIN_NAME] in data_HH.index else np.nan
        grid_gdf[app_config.COL_POP_URBAN] = grid_gdf[app_config.COL_HH_URBAN] * grid_gdf.apply(get_size_HH, axis=1)
        grid_gdf[app_config.COL_POP_RURAL] = grid_gdf[app_config.COL_HH_RURAL] * grid_gdf.apply(get_size_HH, axis=1)
        grid_gdf[app_config.COL_POPULATION] = grid_gdf[app_config.COL_POP_URBAN] + grid_gdf[app_config.COL_POP_RURAL]
        total_population = grid_gdf[app_config.COL_POPULATION].sum()
        print(f"Total population calculated: {total_population:,.0f}")

    print("Finished calculating household numbers.")
    return grid_gdf, df_HH_buildings

def estimate_hh_with_access(grid_gdf, app_config, data_HH, df_HH_buildings=None):
    """
    Estimates the number of households and population with electricity access and calculates access rates.

    Updates grid_gdf with columns for households with and without access.
    If provincial data is available,
    this DataFrame is updated with regional access summaries and saved to a CSV.

    Args:
        grid_gdf: GeoDataFrame of the hexagonal grid.
        app_config: The configuration module.
        df_HH_buildings: DataFrame for regional household summaries.
        data_HH: DataFrame with household size data by region.

    Returns:
        tuple: (grid_gdf, df_HH_buildings)
               - grid_gdf: Updated grid GeoDataFrame.
               - df_HH_buildings: Updated regional summary DataFrame (or None).
    """
    print("Estimating households with access...")

    # Ensure required columns exist
    required_cols = [app_config.COL_HH_URBAN, app_config.COL_HH_RURAL,
                     app_config.PROB_ELEC_COL, app_config.COL_STATUS_ELECTRIFIED]
    for col in required_cols:
        if col not in grid_gdf.columns:
            raise KeyError(f"Required column '{col}' not found in grid_gdf for HH access calculation.")

    # Calculate households with access
    grid_gdf[app_config.COL_HH_WITH_ACCESS_URB] = (
        grid_gdf[app_config.COL_HH_URBAN] *
        grid_gdf[app_config.PROB_ELEC_COL] *
        (grid_gdf[app_config.COL_STATUS_ELECTRIFIED] == 'elec') *
        app_config.CORRECTION_FACTOR_URBAN_HH_ACCESS
    )
    grid_gdf[app_config.COL_HH_WITH_ACCESS_RUR] = (
        grid_gdf[app_config.COL_HH_RURAL] *
        grid_gdf[app_config.PROB_ELEC_COL] *
        (grid_gdf[app_config.COL_STATUS_ELECTRIFIED] == 'elec')
    )
    grid_gdf[app_config.COL_HH_WITH_ACCESS] = grid_gdf[app_config.COL_HH_WITH_ACCESS_URB] + grid_gdf[app_config.COL_HH_WITH_ACCESS_RUR]

    # Calculate households without access
    grid_gdf[app_config.COL_HH_WO_ACCESS_URB] = grid_gdf[app_config.COL_HH_URBAN] - grid_gdf[app_config.COL_HH_WITH_ACCESS_URB]
    grid_gdf[app_config.COL_HH_WO_ACCESS_RUR] = grid_gdf[app_config.COL_HH_RURAL] - grid_gdf[app_config.COL_HH_WITH_ACCESS_RUR]
    grid_gdf[app_config.COL_HH_WO_ACCESS] = grid_gdf[app_config.COL_HH_WO_ACCESS_URB] + grid_gdf[app_config.COL_HH_WO_ACCESS_RUR]

    if app_config.PROVINCE_DATA_AVAILABLE and df_HH_buildings is not None:
        print("Aggregating HH and population access data by region...")
        # Compute population with access
        get_size_HH = lambda row: data_HH.loc[row[app_config.COL_ADMIN_NAME], f"size_HH_{row[app_config.COL_LOC_ASSESSED]}"] \
                              if row[app_config.COL_ADMIN_NAME] in data_HH.index else np.nan

        grid_gdf[app_config.COL_POP_WITH_ACCESS_URB] = grid_gdf[app_config.COL_HH_WITH_ACCESS_URB] * grid_gdf.apply(get_size_HH, axis=1).replace([np.inf, -np.inf, np.nan], 0)
        grid_gdf[app_config.COL_POP_WITH_ACCESS_RUR] = grid_gdf[app_config.COL_HH_WITH_ACCESS_RUR] * grid_gdf.apply(get_size_HH, axis=1).replace([np.inf, -np.inf, np.nan], 0)
        grid_gdf[app_config.COL_POP_WITH_ACCESS] = grid_gdf[app_config.COL_POP_WITH_ACCESS_URB] + grid_gdf[app_config.COL_POP_WITH_ACCESS_RUR]
        total_population_with_access = grid_gdf[app_config.COL_POP_WITH_ACCESS].sum()
        print(f"Total population with access (estimated): {total_population_with_access:,.0f}")

        # Aggregate all access metrics by region
        df_access_summary = grid_gdf.groupby(app_config.COL_ADMIN_NAME)[[
            app_config.COL_HH_WITH_ACCESS_URB, app_config.COL_HH_WITH_ACCESS_RUR, app_config.COL_HH_WITH_ACCESS,
            app_config.COL_POP_WITH_ACCESS_URB, app_config.COL_POP_WITH_ACCESS_RUR, app_config.COL_POP_WITH_ACCESS,
            app_config.COL_POPULATION, app_config.COL_POP_URBAN, app_config.COL_POP_RURAL
        ]].sum()
        df_access_summary.rename_axis('region', inplace=True)
        # Merge access summary with the main regional dataframe
        df_HH_buildings = df_HH_buildings.drop('Total', errors='ignore')
        df_HH_buildings = df_HH_buildings.merge(df_access_summary, left_index=True, right_index=True, how='left')
        df_HH_buildings.fillna(0, inplace=True)

        def safe_divide(numerator, denominator):
            """Performs division and returns 0 where the denominator is zero."""
            if np.isscalar(denominator):
                return numerator / denominator if denominator != 0 else np.nan
            else: # It's an array/Series
                return np.where(denominator == 0, np.nan, numerator / denominator)


        # Calculate access rates for each region
        df_HH_buildings['accessRateHH'] = safe_divide(df_HH_buildings[app_config.COL_HH_WITH_ACCESS], df_HH_buildings['HH_total'])
        df_HH_buildings['accessRateHH_urban'] = safe_divide(df_HH_buildings[app_config.COL_HH_WITH_ACCESS_URB], df_HH_buildings['HH_urban'])
        df_HH_buildings['accessRateHH_rural'] = safe_divide(df_HH_buildings[app_config.COL_HH_WITH_ACCESS_RUR], df_HH_buildings['HH_rural'])
        df_HH_buildings['accessRatePop'] = safe_divide(df_HH_buildings[app_config.COL_POP_WITH_ACCESS], df_HH_buildings[app_config.COL_POPULATION])
        df_HH_buildings['accessRatePop_urban'] = safe_divide(df_HH_buildings[app_config.COL_POP_WITH_ACCESS_URB], df_HH_buildings[app_config.COL_POP_URBAN])
        df_HH_buildings['accessRatePop_rural'] = safe_divide(df_HH_buildings[app_config.COL_POP_WITH_ACCESS_RUR], df_HH_buildings[app_config.COL_POP_RURAL])

        # Add national summary row
        df_sum = df_HH_buildings.sum(numeric_only=True)
        df_sum[app_config.COL_ADMIN_NAME] = 'National'
        # Recalculate rates for National summary
        df_sum['accessRateHH'] = safe_divide(df_sum[app_config.COL_HH_WITH_ACCESS], df_sum['HH_total'])
        df_sum['accessRateHH_urban'] = safe_divide(df_sum[app_config.COL_HH_WITH_ACCESS_URB], df_sum['HH_urban'])
        df_sum['accessRateHH_rural'] = safe_divide(df_sum[app_config.COL_HH_WITH_ACCESS_RUR], df_sum['HH_rural'])

        # Calculate population access rates for National summary
        df_sum['accessRatePop'] = safe_divide(df_sum[app_config.COL_POP_WITH_ACCESS], df_sum[app_config.COL_POPULATION])
        df_sum['accessRatePop_urban'] = safe_divide(df_sum[app_config.COL_POP_WITH_ACCESS_URB], df_sum[app_config.COL_POP_URBAN])
        df_sum['accessRatePop_rural'] = safe_divide(df_sum[app_config.COL_POP_WITH_ACCESS_RUR], df_sum[app_config.COL_POP_RURAL])

        df_sum = pd.DataFrame(df_sum).T.set_index(app_config.COL_ADMIN_NAME)
        df_HH_buildings = pd.concat([df_HH_buildings, df_sum])

        output_csv_path = app_config.RESIDENTIAL_OUTPUT_DIR / "dataHH_region.csv"
        df_HH_buildings.to_csv(output_csv_path, index=True)
        print(f"Regional HH summary saved to {output_csv_path}")
        print(df_HH_buildings[['accessRateHH','accessRateHH_urban','accessRateHH_rural']].tail())
        print("National Summary Access Rates:")
        print(df_HH_buildings.loc['National', ['accessRateHH', 'accessRateHH_urban', 'accessRateHH_rural', 'accessRatePop', 'accessRatePop_urban', 'accessRatePop_rural']])

    print("Finished estimating households with access.")
    return grid_gdf, df_HH_buildings