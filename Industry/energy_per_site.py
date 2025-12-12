###############################################################################                                                                                   
# Chair:            Chair of Renewable and Sustainable Energy Systems (ENS)
# Assistant(s):     Andjelka Kerekes (andelka.kerekes@tum.de)

# Date:             
# Version:          v3.0
# Status:           done/in progress
# Python-Version:   3.7.3 (64-bit)
###############################################################################
import pandas as pd
import os
import numpy as np
import geopandas as gpd
import fiona
import openpyxl
import config
import Industry.specified_energy as specified_energy
# import specified_energy as specified_energy


def load_known_production(file_path, target_year):
    """
    Loads specific mine production data from an external file.
    Expected columns: 'FeatureNam', 'Year', 'Production'
    Returns a dictionary: {'MineName': Production_Value}
    """
    known_map = {}
    try:
        df_add = pd.read_excel(file_path)
        # Filter for the correct year
        df_add = df_add[df_add["Year"] == target_year]
        # Create dictionary
        known_map = dict(zip(df_add["FeatureNam"], df_add["Production (t_Cu)"]))

        print(f"Loaded {len(known_map)} known production values from Additional Info.")
    except Exception as e:
        print(f"Warning: Could not load Additional Info file ({e}). Proceeding without known values.")
    return known_map


def get_usgs_production_targets(file_path, target_year):
    """
    Reads the USGS Excel file and extracts Ore and Metal production targets
    for the specific year.
    """
    targets = {"Ore": 0, "Metal": 0}

    # Helper to clean numbers (e.g., converts "655,500 r" to 655500.0)
    def _clean_val(val):
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            # Remove everything except digits (removes commas, 'r', 'e', etc.)
            clean_str = ''.join(filter(str.isdigit, val))
            return float(clean_str) if clean_str else 0.0
        return 0.0

    try:
        # Load Excel
        df_usgs = pd.read_excel(file_path, sheet_name="Table 1", header=None)

        # Clean whitespace in string columns
        df_usgs = df_usgs.map(lambda x: x.strip() if isinstance(x, str) else x)

        # 1. Find the column index for the target YEAR
        year_col_idx = None
        # Search the first 10 rows and all columns
        found_year = False
        for r in range(min(15, len(df_usgs))): # Scan top 15 rows
            for c in range(len(df_usgs.columns)):
                cell_value = str(df_usgs.iloc[r, c])
                # Check if year is in the cell (e.g. "2019" or "2019 (estimated)")
                if str(target_year) in cell_value:
                    year_col_idx = c
                    found_year = True
                    break
            if found_year:
                break

        if year_col_idx is None:
            print(f"Warning: Year {target_year} not found in USGS file. Using default 0.")
            return targets

        # 2. Locate Data Rows (Assume Commodity Name is in Column 0)
        col_commodity = df_usgs.columns[0]

        # --- A. Get Mine Concentrate (Ore) ---
        mask_ore = df_usgs[col_commodity].astype(str).str.contains("Mine, concentrates, Cu content", case=False, na=False)
        mask_electro = df_usgs[col_commodity].astype(str).str.contains("Electrowon", case=False, na=False)
        val_concentrates = 0
        val_electro = 0

        if mask_ore.any():
            raw_val = df_usgs.loc[mask_ore, year_col_idx].values[0]
            val_concentrates = _clean_val(raw_val)

        if mask_electro.any():
            # Take the first occurrence (Primary)
            raw_val = df_usgs.loc[mask_electro, year_col_idx].values[0]
            val_electro = _clean_val(raw_val)

        targets["Ore"] = val_concentrates + val_electro

        # --- B. Get Smelter and Electrowon (Metal) ---
        mask_smelter = df_usgs[col_commodity].astype(str).str.contains("Smelter, primary", case=False, na=False)

        val_smelter = 0

        if mask_smelter.any():
            raw_val = df_usgs.loc[mask_smelter, year_col_idx].values[0]
            val_smelter = _clean_val(raw_val)

        targets["Metal"] = val_smelter + val_electro

        print(f"USGS Targets for {target_year} -> Ore: {targets['Ore']:,.0f}, Metal: {targets['Metal']:,.0f}")
        return targets

    except Exception as e:
        print(f"Error reading USGS Excel: {e}. Falling back to defaults (0).")
        return targets

def calc_energy_per_site(app_config):

    #----------------------------------
    # settings
    country = app_config.COUNTRY
    metals = ["Copper", "Cobalt", "Gold", "Nickel", "Manganese"]
    electrowon_names = ["Slag Recovery","Heap Leach","Leach","Solvent Extraction-Electrowinning", "Electrowinning", "Solvent Extraction"]
    ## general
    plant_usage_ore = {"Copper": 0.773, "Cobalt":0, "Gold":0.853, "Nickel":0.285, "Manganese":0.942} # Co from mining not considered
    plant_usage_metal = {"Copper":  0.312, "Cobalt":0.136, "Gold":0.853, "Nickel":0, "Manganese":0.942} # no Ni metal production, no Au metal statistics, Mn ore and fero- or siliconmanganese statistics
    ore_grade = {"Copper":0.0103, "Cobalt":0} # cobalt from mining not considered
    # concentrate_grade = 0.3
    unit_conversion = {"Thousand metric tons":10**3, "Metric tons":1, "Kilograms":10**-3} # into t
    spec_energy = specified_energy.SPEC_ENERGY
    mining_default = specified_energy.MINING_DEFAULT
    smelting_default = specified_energy.SMELTING_DEFAULT

    #----------------------------------

    ## Load USGS data
    input_table = pd.read_csv(app_config.MINES_INPUT_CSV)
    input_table = input_table[input_table["Country"]==country]
    input_table = input_table.loc[input_table["DsgAttr02"].isin(metals)].reset_index()
    output_table = input_table[["Country", "FeatureNam", "DsgAttr02", "DsgAttr03", "DsgAttr06", "MemoOther", "MemoLoc","Latitude", "Longitude", "DsgAttr07", "DsgAttr08"]].copy()

    # Create a list of all possible outputs and allocate Metal or Ore and concentrate to each process
    # clear output type
    output_type_list = []
    for idx, output_name in enumerate(input_table["DsgAttr03"]): # go through all commodity products
        metal = input_table["DsgAttr02"][idx]
        
        if output_name not in ["Metal", "Ore and concentrate"]:
            if " content" in output_name:
                output_name = "Metal in ore"
            elif "Ore." in output_table["MemoOther"][idx]:
                output_name = "Ore and concentrate"
            elif output_name == metal:
                output_name = "Metal" # "Metal" or "Ore and concentrate" - discutable
            else:
                output_name = ""
        output_type_list.append(output_name)
    output_table["Output type (ass.)"] = output_type_list

    # Assess production level for each site

    # a. load usgs total and known production values
    usgs_targets = get_usgs_production_targets(app_config.TOTAL_PROD_USGS_FILE, app_config.YEAR)
    known_production_map = load_known_production(app_config.ADD_INFO_FILE, app_config.YEAR)

    # Map the known values to the table based on FeatureNam
    mapped_values = output_table["FeatureNam"].map(known_production_map)

    # Assign to column ONLY if the commodity is Copper
    # Logic: If DsgAttr02 is 'Copper', take the mapped value. Otherwise, set to NaN.
    output_table["Known_Production_Tonnes"] = np.where(
        output_table["DsgAttr02"] == "Copper",
        mapped_values,
        np.nan
    )
    # -------------------------------------------------------------------------

    # b. clear production_capacity
    production_capacities_2017 = []
    for idx, production_capacity in enumerate(input_table["DsgAttr07"]):
        # metal = input_table["DsgAttr02"][idx]
        unit_orig = input_table["DsgAttr08"][idx]
        
        if production_capacity <0:
            production_capacity = np.nan
            print("Production at a site ", output_table["FeatureNam"][idx], " in ", country, " is missing (negative). Value set to zero. Please, change the input in the input file.")
        elif "Capacity is a combination" in output_table["MemoOther"][idx]:
            number = output_table["MemoOther"].tolist().count(output_table["MemoOther"][idx]) # how many plants are giving the combined capacity
            production_capacity = production_capacity / number
        try:
            production_capacity = production_capacity * unit_conversion[unit_orig]
        except:
            production_capacity = production_capacity # original unit is sometimes nan
        production_capacities_2017.append(production_capacity)
    output_table["production_capacity_modified"] = production_capacities_2017

    # c. Compute Dynamic Plant Usage Factors
    # Factor = Total_USGS_Production / Total_Input_Capacity

    # Calculate Total Input Capacities for Copper
    # Filter for Copper and specific output types
    is_copper = output_table["DsgAttr02"] == "Copper"
    is_ore = output_table["Output type (ass.)"] == "Ore and concentrate"
    is_metal = output_table["Output type (ass.)"] == "Metal"

    # Identify which rows have KNOWN values vs which rely on CAPACITY
    # valid_cap: capacity is not nan
    # is_unknown: we do NOT have a value in Additional_info
    has_known_val = output_table["Known_Production_Tonnes"].notna()
    is_unknown = output_table["Known_Production_Tonnes"].isna()

    # 1. Calculate how much production is already accounted for by "Additional_info"
    # We assume known values in Additional_info match the output type (Ore vs Metal) correctly implicitly
    # (i.e. if a mine is an Ore mine, the value in Excel is Ore)

    known_prod_ore = output_table.loc[is_copper & is_ore & has_known_val, "Known_Production_Tonnes"].sum()
    known_prod_metal = output_table.loc[is_copper & is_metal & has_known_val, "Known_Production_Tonnes"].sum()

    print(f"Known Production (Fixed) -> Ore: {known_prod_ore:,.0f} Metal: {known_prod_metal:,.0f}")

    # 2. Calculate the REMAINING USGS Target
    # If known production exceeds USGS, we floor the remaining target at 0 to avoid negative factors
    target_remaining_ore = max(0, usgs_targets["Ore"] - known_prod_ore)
    target_remaining_metal = max(0, usgs_targets["Metal"] - known_prod_metal)

    print(f"Remaining USGS Target -> Ore: ", f"{target_remaining_ore:,.0f}"," Metal: ", f"{target_remaining_metal:,.0f}")

    # 3. Calculate the Capacity of the UNKNOWN mines only
    cap_remaining_ore = output_table.loc[is_copper & is_ore & is_unknown, "production_capacity_modified"].sum()
    cap_remaining_metal = output_table.loc[is_copper & is_metal & is_unknown, "production_capacity_modified"].sum()

    print(f"Remaining Capacity -> Ore: {cap_remaining_ore:,.0f}, Metal: {cap_remaining_metal:,.0f}")

    # Update the plant_usage dictionary for Copper
    if target_remaining_ore > 0 and cap_remaining_ore > 0:
        plant_usage_ore["Copper"] = target_remaining_ore/ ore_grade["Copper"] / cap_remaining_ore
        print(f"Calculated Copper Ore Usage Factor (Adjusted): {plant_usage_ore['Copper']:.4f}")

    if target_remaining_metal > 0 and cap_remaining_metal > 0:
        plant_usage_metal["Copper"] = target_remaining_metal / cap_remaining_metal
        print(f"Calculated Copper Metal Usage Factor (Adjusted): {plant_usage_metal['Copper']:.4f}")

    # 4. Final Calculation: Apply factors to individual rows
    # Now we apply the (potentially updated) usage factors to the normalized capacity

    final_production = []

    for idx, row in output_table.iterrows():
        metal = row["DsgAttr02"]
        norm_cap = row["production_capacity_modified"]
        output_type = row["Output type (ass.)"]
        known_val = row["Known_Production_Tonnes"]
        # Check if there is a known production value (not NaN)
        if metal == "Copper" and pd.notna(known_val):
            prod = known_val/ore_grade[metal]
        else:# Determine usage factor
            if output_type == "Metal":
                usage = plant_usage_metal.get(metal, 0)
            else:
                usage = plant_usage_ore.get(metal, 0)
            # Calc
            prod = norm_cap * usage

        final_production.append(prod)

    col_name_prod = f"Production_assessed_{app_config.YEAR}_[t]"
    output_table[col_name_prod] = final_production
      
    # Production of copper content in kt
    metal_content_list = []
    for idx, production in enumerate(output_table[col_name_prod]):
        metal = input_table["DsgAttr02"][idx]
        # known_val = row["Known_Production_Tonnes"]
        # # Check if there is a known production value (not NaN)
        # if metal == "Copper" and pd.notna(known_val):
        #     metal_content_list.append(known_val/1000)
        # else:
        if output_table["Output type (ass.)"][idx]=="Ore and concentrate":
            metal_content_list.append(production*ore_grade[metal]/1000) # conversion in kt metal
        else:
            metal_content_list.append(production/1000)
    output_table["Metal content [kt]"] = metal_content_list
    
    # find mine type
    mine_type_list = []
    for name in output_table["FeatureNam"]:
        if "underground" in name.lower():
            mine_type_list.append("Underground")
        elif "pit" in name.lower():
            mine_type_list.append("Open Pit")
        else:
            mine_type_list.append("")
    output_table["Mine type"] = mine_type_list
    
    # find if site is a smelter, refinery or a combination
    metal_proces_list = []
    for idx, name in enumerate(output_table["FeatureNam"]):
        metal = input_table["DsgAttr02"][idx]
        
        if metal == "Copper":
            if "smelter" in name.lower():
                metal_proces_list.append("Smelter")
            elif "refinery" in name.lower():
                metal_proces_list.append("Refinery")
            elif any(x.lower() in name.lower() for x in electrowon_names):
                metal_proces_list.append("Hydrometallurgical")
            elif "plant" in name.lower() or "facility" in name.lower():
                metal_proces_list.append("Smelter+Refinery")
            else:
                metal_proces_list.append("")
        else:
            if output_table["Output type (ass.)"][idx]=="Metal":
                metal_proces_list.append("Smelting/Refining")
            else:
                metal_proces_list.append("")    
    output_table["Metal processing"] = metal_proces_list   
    
    # find the type of a smelter
    smelter_type_list = []
    types = ["Isasmelt","Mitsubishi"] + electrowon_names
    for featureName in output_table["FeatureNam"]:
        element_type = [i for i in types if i.lower() in featureName.lower()]
        element_type = ", ".join(element for element in element_type)
        smelter_type_list.append(element_type)
    output_table["Metal process type"] = smelter_type_list   
    
    # attribute specific energy consumptions
    for en_carrier in spec_energy["Copper"].keys():
        spec_energy_list = []
        for idx, element in enumerate(output_table["Output type (ass.)"]):
            
            metal = input_table["DsgAttr02"][idx]
            if element in ["Ore and concentrate", "Metal in ore"]:
                try:
                    spec_energy_list.append(spec_energy[metal][en_carrier]["Mining"][output_table["Mine type"][idx]]
                                            +spec_energy[metal][en_carrier]["Milling"])
                except:
                    spec_energy_list.append(spec_energy[metal][en_carrier]["Mining"][mining_default]
                                            +spec_energy[metal][en_carrier]["Milling"])
            
            elif element == "Metal":
                if output_table["Metal processing"][idx] in ["Hydrometallurgical","Smelting/Refining"]:
                    spec_energy_list.append(spec_energy[metal][en_carrier][output_table["Metal processing"][idx]])
                elif output_table["Metal processing"][idx] in ["Refinery"]:
                    spec_energy_list.append(spec_energy[metal][en_carrier]["Refining"])
                elif output_table["Metal processing"][idx]=="Smelter+Refinery":
                    spec_energy_list.append(spec_energy[metal][en_carrier]["Refining"]+spec_energy[metal][en_carrier]["Smelting"]["Flash smelting"])
                else:
                    try:
                        spec_energy_list.append(spec_energy[metal][en_carrier]["Smelting"][output_table["Metal process type"][idx]])
                    except:
                        spec_energy_list.append(spec_energy[metal][en_carrier]["Smelting"][smelting_default])
    
            else:
                spec_energy_list.append(0) #""
        output_table["Spec energy "+en_carrier+" [GJ/t]"]= spec_energy_list   
    
    # calculate consumed energy:  multiply production and specific energy consumption
    for en_carrier in spec_energy["Copper"].keys():
        output_table[en_carrier +"_TJ"] = np.array(output_table["Metal content [kt]"])*np.array(output_table["Spec energy "+en_carrier+" [GJ/t]"])
    # Rename the columns
    output_table = output_table.rename(columns={
        "Elec_TJ": app_config.COL_IND_ELEC_TJ,
        "Diesel_TJ": app_config.COL_IND_OIL_TJ
    })

    # =========================================================================
    # ---- SECTION: BREAKDOWN BY PROCESS STEP (ELECTRICITY ONLY) ----
    # =========================================================================

    # Initialize separate columns for each step
    steps = ["Mining", "Milling", "Smelting", "Refining", "Leaching_EW"]
    for step in steps:
        output_table[f"Elec_Step_{step}_TJ"] = 0.0

    # We iterate again to apply step-specific intensities
    # This logic mirrors the aggregation logic above but keeps values separate
    en_carrier = "Elec"

    for idx, row in output_table.iterrows():
        metal = row["DsgAttr02"]
        out_type = row["Output type (ass.)"]
        metal_kt = row["Metal content [kt]"]

        # Skip rows with no production
        if metal_kt == 0:
            continue

        # 1. ORE/CONCENTRATE: Mining + Milling
        if out_type in ["Ore and concentrate", "Metal in ore"]:
            # Mining Step
            mine_t = row["Mine type"]
            try:
                # Try specific mine type (Open Pit/Underground)
                val_mining = spec_energy[metal][en_carrier]["Mining"][mine_t]
            except:
                # Default
                val_mining = spec_energy[metal][en_carrier]["Mining"][mining_default]

            # Milling Step
            val_milling = spec_energy[metal][en_carrier]["Milling"]

            # Assign to columns (TJ = kt * GJ/t)
            output_table.at[idx, "Elec_Step_Mining_TJ"] = metal_kt * val_mining
            output_table.at[idx, "Elec_Step_Milling_TJ"] = metal_kt * val_milling

        # 2. METAL: Smelting, Refining, or Hydrometallurgy
        elif out_type == "Metal":
            proc = row["Metal processing"]
            proc_type = row["Metal process type"]

            if proc == "Hydrometallurgical":
                # Maps to Leaching/EW
                val_hydro = spec_energy[metal][en_carrier]["Hydrometallurgical"]
                output_table.at[idx, "Elec_Step_Leaching_EW_TJ"] = metal_kt * val_hydro

            elif proc == "Smelter":
                # Maps to Smelting
                try:
                    val_smelt = spec_energy[metal][en_carrier]["Smelting"][proc_type]
                except:
                    val_smelt = spec_energy[metal][en_carrier]["Smelting"][smelting_default]
                output_table.at[idx, "Elec_Step_Smelting_TJ"] = metal_kt * val_smelt

            elif proc == "Refinery":
                # Maps to Refining
                # val_ref = spec_energy[metal][en_carrier]["Smelting"][smelting_default]
                val_ref = spec_energy[metal][en_carrier]["Refining"] #[smelting_default]
                output_table.at[idx, "Elec_Step_Refining_TJ"] = metal_kt * val_ref

            elif proc == "Smelter+Refinery":
                # Split: Smelting (assume Flash) + Refining
                val_smelt = spec_energy[metal][en_carrier]["Smelting"]["Flash smelting"]
                val_ref = spec_energy[metal][en_carrier]["Refining"]

                output_table.at[idx, "Elec_Step_Smelting_TJ"] = metal_kt * val_smelt
                output_table.at[idx, "Elec_Step_Refining_TJ"] = metal_kt * val_ref

            elif proc == "Smelting/Refining":
                # For non-copper metals where we have a combined value
                val_combined = spec_energy[metal][en_carrier]["Smelting/Refining"]
                # We allocate this to Smelting for simplicity, or you could create a new 'Other_Process' col
                output_table.at[idx, "Elec_Step_Smelting_TJ"] = metal_kt * val_combined

            elif proc ==  "":
                # Maps to Smelting
                val_ref = spec_energy[metal][en_carrier]["Smelting"][smelting_default]
                output_table.at[idx, "Elec_Step_Smelting_TJ"] = metal_kt * val_ref

    # =========================================================================
    # ---- END SECTION ----
    # =========================================================================


    # ---- ADDITION FOR COPPER-SPECIFIC ELECTRICITY CONSUMPTION ----
    # Initialize the new column with 0
    output_table[app_config.COL_IND_COPPER_ELEC_TJ] = 0.0

    # Create a boolean mask for rows where the metal is Copper
    is_copper_mask = (output_table["DsgAttr02"] == "Copper")

    # For copper rows, calculate electricity consumption.
    output_table[app_config.COL_IND_COPPER_ELEC_TJ] = np.where(
        output_table["DsgAttr02"] == "Copper",  # Condition
        output_table["Metal content [kt]"] * output_table["Spec energy Elec [GJ/t]"], # Value if True
        0.0  # Value if False
    )
     
    ## Adding a uid which is needed afterwards
    output_table["id"] = range(1, len(output_table)+1)
    
    ## Export to csv
    output_table.to_csv(app_config.MINES_OUTPUT_CSV, encoding='utf-8', index=False)
    
    ## Converting df to gdf for further processing & extracting gpkg
    output_table_gdf = gpd.GeoDataFrame(output_table,
                                        geometry=gpd.points_from_xy(output_table.Longitude, output_table.Latitude), crs=app_config.CRS_WGS84)
    if os.path.exists(app_config.MINES_OUTPUT_GPKG):
        print(f"File {app_config.MINES_OUTPUT_GPKG} exists. Deleting it now...")
        os.remove(app_config.MINES_OUTPUT_GPKG)
        print("File deleted.")
    output_table_gdf.to_file(app_config.MINES_OUTPUT_GPKG, layer="mines", driver="GPKG", mode='w')



if __name__ == "__main__":
    calc_energy_per_site(config)