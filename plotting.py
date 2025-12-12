# Mapping / Plotting
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
from matplotlib.colors import LogNorm
from matplotlib_scalebar.scalebar import ScaleBar
import matplotlib.colors as colors
from shapely.geometry.point import Point
import pandas as pd

import geopandas as gpd
import numpy as np


def plot_sector_consumption_map(grid_gdf, col_to_plot, app_config, admin_gdf_param, region_gdf_param, sector_name,
                           lines_gdf=None, fig_size=(25, 15), title = True,
                                plot_as_dots=False, dot_markersize=50):
    print(f"Plotting {sector_name} Consumption map...")

    if col_to_plot not in grid_gdf.columns:
        print(f"Warning: Column '{col_to_plot}' not found for {sector_name} Consumption map.")
        return

    grid_display = grid_gdf.copy()

    col_lower = col_to_plot.lower()
    if 'gwh' in col_lower:
        unit_label = 'GWh'
    elif 'kwh' in col_lower:
        grid_display[col_to_plot] = grid_display[col_to_plot] / 10**3 # kWh to MWh for display
        unit_label = 'MWh'
    else:
        print(f"Warning: Could not detect a known unit (kWh, MWh, GWh) in column name '{col_to_plot}'. Plotting raw values.")

    fig, ax = plt.subplots(figsize=fig_size)
    ax.set_xlabel('Longitude (°)')
    ax.set_ylabel('Latitude (°)')

    # Create a series of only the positive values from the column
    positive_values = grid_display[col_to_plot][grid_display[col_to_plot] > 0]
    data_min = positive_values.min()
    data_max = positive_values.max()

    # --- Extend the normalization range to the nearest powers of 10 ---
    # This ensures the colorbar has a clean, readable range (e.g., 10, 100, 1000)
    log_min_power = np.floor(np.log10(data_min))
    log_max_power = np.ceil(np.log10(data_max))

    # Define the new vmin and vmax for the colormap normalization
    norm_vmin = 10**log_min_power
    norm_vmax = 10**log_max_power

    # Generate ticks for every power of 10 in the new, extended range
    ticks = [10**i for i in range(int(log_min_power), int(log_max_power) + 1)]

    plot_kwargs = {
        "ax": ax,
        "column": col_to_plot,
        "cmap": "Reds",
        "legend": True,
        "alpha": 0.9,
        "norm": colors.LogNorm(vmin=norm_vmin, vmax=norm_vmax),
        "legend_kwds": {
            "label": sector_name + " Consumption (" + unit_label + ")",
            "ticks": ticks,
        }
    }

    # Sort to ensure highest values are plotted on top if there is overlap
    sorted_grid = grid_display.sort_values(col_to_plot, ascending=True)

    if plot_as_dots:
        # Convert geometries to centroids for dot plotting
        # Warning: We filter > 0 here to avoid plotting thousands of empty dots
        dots_gdf = sorted_grid[sorted_grid[col_to_plot] > 0].copy()

        # Use centroids.
        dots_gdf['geometry'] = dots_gdf.to_crs(epsg=3857).centroid.to_crs(dots_gdf.crs)

        dots_gdf.plot(markersize=dot_markersize, **plot_kwargs)
    else:
        # Standard grid map
        sorted_grid.plot(**plot_kwargs)

    # grid_display.sort_values(col_to_plot, ascending=True).plot(
    #     ax=ax, column=col_to_plot, cmap="Reds", legend=True, alpha=0.9,
    #     norm=colors.LogNorm(vmin=norm_vmin, vmax=norm_vmax),
    #     legend_kwds={
    #     "label": sector_name + " Consumption (" + unit_label + " per cell)",
    #     "ticks": ticks,  # Use our manually created ticks
    #     }
    # )

    if admin_gdf_param is not None: admin_gdf_param.to_crs(grid_gdf.crs).plot(ax=ax, edgecolor='grey', facecolor='None', alpha=0.6)
    if region_gdf_param is not None: region_gdf_param.to_crs(grid_gdf.crs).plot(ax=ax, edgecolor='grey', facecolor='None', alpha=0.2)
    if lines_gdf is not None:
        lines_gdf = lines_gdf.to_crs(admin_gdf_param.crs)
        lines_gdf = gpd.clip(lines_gdf, admin_gdf_param)
        lines_gdf.plot(ax=ax, edgecolor='purple', color='purple', alpha=0.4)

    ax.set_aspect('equal', 'box')
    plt.rcParams.update({'font.size': 12})
    ax.tick_params(axis='both', which='major', labelsize=12)
    if app_config.AREA_OF_INTEREST == 'COUNTRY':
        region_title = app_config.COUNTRY
    else:
        region_title = app_config.AREA_OF_INTEREST
    if title:
        ax.set_title(f'{sector_name} Electricity Consumption in {region_title} ({unit_label})')

    # Scalebar
    points = gpd.GeoSeries([Point(-73.5, 40.5), Point(-74.5, 40.5)], crs=app_config.CRS_WGS84)  # Geographic WGS 84 - degrees
    points = points.to_crs(32619)  # Projected WGS 84 - meters
    distance_meters = points[0].distance(points[1])
    # distance_meters = points.iloc[0].distance(points.iloc[1])
    scalebar = ScaleBar(distance_meters, dimension="si-length", location='lower left', length_fraction=0.1, width_fraction=0.001, units='m', color='black')
    ax.add_artist(scalebar)

    suffix = "_dots" if plot_as_dots else ""
    plt.savefig(app_config.OUTPUT_DIR / f'map_{sector_name}_demand_log_{app_config.COUNTRY}{suffix}.png', bbox_inches='tight')
    # plt.show()

def plot_mining_process_breakdown(app_config):
    # 1. Load the results file produced by the previous function
    try:
        df = pd.read_csv(app_config.MINES_OUTPUT_CSV)
    except FileNotFoundError:
        print(f"Error: Could not find {app_config.MINES_OUTPUT_CSV}. Run calc_energy_per_site first.")
        return

    # 2. Define the columns corresponding to the steps
    step_columns = [
        "Elec_Step_Mining_TJ",
        "Elec_Step_Milling_TJ",
        "Elec_Step_Smelting_TJ",
        "Elec_Step_Refining_TJ",
        "Elec_Step_Leaching_EW_TJ"
    ]

    # 3. Sum the columns to get totals
    # If you want Copper only, uncomment the next line:
    # df = df[df["DsgAttr02"] == "Copper"]

    totals = df[step_columns].sum()

    # 4. Prepare data for plotting
    # Rename for cleaner labels in the chart
    labels_map = {
        "Elec_Step_Mining_TJ": "Mining (Extraction)",
        "Elec_Step_Milling_TJ": "Milling (Crushing/Grinding)",
        "Elec_Step_Smelting_TJ": "Smelting",
        "Elec_Step_Refining_TJ": "Refining (Electro-refining)",
        "Elec_Step_Leaching_EW_TJ": "Leaching & Electrowinning"
    }

    labels = [labels_map[col] for col in totals.index]
    sizes = totals.values

    # Calculate Total for title (convert TJ to TWh for readability if needed, or keep TJ)
    total_tj = sizes.sum()

    # 5. Create the Pie Chart
    # Professional colors (blues/greens or distinct categorical colors)
    colors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f']

    fig, ax = plt.subplots(figsize=(10, 7))

    # Create pie chart with percentage labels
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None, # We'll add a legend instead to keep it clean
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        pctdistance=0.85, # Distance of the percentage text from center
        explode=[0.05] * len(sizes) # Slight separation for all slices
    )

    # Style the text
    for text in texts:
        text.set_fontsize(12)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_weight('bold')
        autotext.set_fontsize(10)

    # Add a donut hole (optional, looks modern)
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig.gca().add_artist(centre_circle)

    # 6. Add Legend and Title
    ax.legend(wedges, labels,
              title="Production process",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1))

    plt.setp(autotexts, size=10, weight="bold")

    # ax.set_title(f"Share of Industrial Electricity Consumption by Process Step\n(Total Modeled: {total_tj/3600:.2f} TWh)", fontsize=14)
    print(f"Share of Industrial Electricity Consumption by Process Step\n(Total Modeled: {total_tj/3600:.2f} TWh)")
    plt.tight_layout()

    # 7. Save or Show
    filename = app_config.INDUSTRY_OUTPUT_DIR / "Mining_Breakdown.png"
    plt.savefig(filename, dpi=300)
    # print("Pie chart saved as Mining_Breakdown.png")
    plt.show()
