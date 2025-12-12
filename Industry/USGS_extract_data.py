import geopandas as gpd
import fiona
import os
import config

def gdb_to_csv(gdb_path, output_folder):
    # Check if output folder exists, create if not
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Get a list of all layers within the .gdb
    try:
        layers = fiona.listlayers(gdb_path)
    except Exception as e:
        print(f"Error reading GDB: {e}")
        return

    print(f"Found {len(layers)} layers. Starting conversion...")

    for layer_name in layers:
        print(f"Processing: {layer_name}")

        try:
            # Read the layer into a GeoDataFrame
            gdf = gpd.read_file(gdb_path, layer=layer_name)

            # Define output path
            csv_path = os.path.join(output_folder, f"{layer_name}.csv")

            # Convert to CSV
            # index=False removes the pandas row numbers
            gdf.to_csv(csv_path, index=False)

        except Exception as e:
            print(f"Failed to convert {layer_name}: {e}")

    print("Conversion complete.")

# --- Usage ---
gdb_file = config.USGS_DATA_PATH
out_dir = config.USGS_DATA_OUTPUT_PATH

gdb_to_csv(gdb_file, out_dir)