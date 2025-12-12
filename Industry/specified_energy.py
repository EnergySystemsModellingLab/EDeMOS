import numpy as np

# defaults
MINING_DEFAULT = "Underground"
SMELTING_DEFAULT = "Flash smelting"

## energy usage for different processes and their types
## Units: GJ/t_Cu
SPEC_ENERGY = {"Copper": {"Elec": {"Mining":{}, "Smelting":{}}, "Diesel":{"Mining":{}, "Smelting":{}}},
               "Cobalt":{"Elec":{"Mining":{}}, "Diesel":{"Mining":{}}},
               "Gold":{"Elec":{"Mining":{}}, "Diesel":{"Mining":{}}},
               "Nickel":{"Elec":{"Mining":{}}, "Diesel":{"Mining":{}}},
               "Manganese":{"Elec":{"Mining":{}}, "Diesel":{"Mining":{}}}}

### mining
SPEC_ENERGY["Copper"]["Elec"]["Mining"]["Open Pit"]= 0        # https://doi.org/10.1016/j.jclepro.2019.118978
SPEC_ENERGY["Copper"]["Diesel"]["Mining"]["Open Pit"]= 10.2   # https://doi.org/10.1016/j.jclepro.2019.118978
SPEC_ENERGY["Copper"]["Elec"]["Mining"]["Underground"]= 2.15  # https://doi.org/10.1016/j.jclepro.2019.118978
SPEC_ENERGY["Copper"]["Diesel"]["Mining"]["Underground"]= 2.15 # https://doi.org/10.1016/j.jclepro.2019.118978
SPEC_ENERGY["Copper"]["Elec"]["Milling"] = 0.4*24 # weir engeco: Mining energy consumption 2021
SPEC_ENERGY["Copper"]["Diesel"]["Milling"]= 0     # weir engeco: Mining energy consumption 2021

SPEC_ENERGY["Cobalt"]["Elec"]["Mining"][MINING_DEFAULT]= np.nan # placeholder
SPEC_ENERGY["Cobalt"]["Diesel"]["Mining"][MINING_DEFAULT]= np.nan # placeholder
SPEC_ENERGY["Cobalt"]["Elec"]["Milling"]= np.nan # placeholder
SPEC_ENERGY["Cobalt"]["Diesel"]["Milling"]= np.nan # placeholder

SPEC_ENERGY["Gold"]["Elec"]["Mining"][MINING_DEFAULT]= (24.11*10**3)/2
SPEC_ENERGY["Gold"]["Diesel"]["Mining"][MINING_DEFAULT]=(223.21+36.21)*10**3/2
SPEC_ENERGY["Gold"]["Elec"]["Milling"]= (96.71+34.81)*10**3/2
SPEC_ENERGY["Gold"]["Diesel"]["Milling"]= 0

SPEC_ENERGY["Nickel"]["Elec"]["Mining"][MINING_DEFAULT]= 18
SPEC_ENERGY["Nickel"]["Diesel"]["Mining"][MINING_DEFAULT]=12.5
SPEC_ENERGY["Nickel"]["Elec"]["Milling"]= 0       #Mining+Milling one value
SPEC_ENERGY["Nickel"]["Diesel"]["Milling"]= 0  #Mining+Milling one value

SPEC_ENERGY["Manganese"]["Elec"]["Mining"][MINING_DEFAULT]= 0.025
SPEC_ENERGY["Manganese"]["Diesel"]["Mining"][MINING_DEFAULT]= 0.17
SPEC_ENERGY["Manganese"]["Elec"]["Milling"]= 0    #Mining+Milling one value
SPEC_ENERGY["Manganese"]["Diesel"]["Milling"]= 0  #Mining+Milling one value

### smelting
SPEC_ENERGY["Copper"]["Elec"]["Smelting"]["Flash smelting"]= 9.266 # https://link.springer.com/article/10.1007/s11837-015-1380-1
SPEC_ENERGY["Copper"]["Diesel"]["Smelting"]["Flash smelting"]= 1.518 # https://link.springer.com/article/10.1007/s11837-015-1380-1
SPEC_ENERGY["Copper"]["Elec"]["Smelting"]["Isasmelt"]= 6.903 # https://link.springer.com/article/10.1007/s11837-015-1380-1
SPEC_ENERGY["Copper"]["Diesel"]["Smelting"]["Isasmelt"]= 4.175 # https://link.springer.com/article/10.1007/s11837-015-1380-1
SPEC_ENERGY["Copper"]["Elec"]["Smelting"]["Mitsubishi"]= 8.508 # https://link.springer.com/article/10.1007/s11837-015-1380-1
SPEC_ENERGY["Copper"]["Diesel"]["Smelting"]["Mitsubishi"]= 2.498 # https://link.springer.com/article/10.1007/s11837-015-1380-1
SPEC_ENERGY["Copper"]["Elec"]["Smelting"]["average"]= 0.4*8.9 # https://elib.dlr.de/130069/1/Renewable%20energy%20in%20copper%20production%20-%20a%20review.pdf
SPEC_ENERGY["Copper"]["Diesel"]["Smelting"]["average"]= 0.6*8.9 # https://elib.dlr.de/130069/1/Renewable%20energy%20in%20copper%20production%20-%20a%20review.pdf

### refining
SPEC_ENERGY["Copper"]["Elec"]["Refining"]= 3.2*0.4 + 5.76 # https://elib.dlr.de/130069/1/Renewable%20energy%20in%20copper%20production%20-%20a%20review.pdf
                                                          # https://www.bmwk.de/Redaktion/DE/Downloads/E/energiewende-in-der-industrie-ap2a-branchensteckbrief-metall.pdf?__blob=publicationFile&v=4
SPEC_ENERGY["Copper"]["Diesel"]["Refining"]= 3.2*0.6  + 7.2 # https://elib.dlr.de/130069/1/Renewable%20energy%20in%20copper%20production%20-%20a%20review.pdf
                                                            # https://www.bmwk.de/Redaktion/DE/Downloads/E/energiewende-in-der-industrie-ap2a-branchensteckbrief-metall.pdf?__blob=publicationFile&v=4

### leaching, solvent extraction and electrowinning
SPEC_ENERGY["Copper"]["Elec"]["Hydrometallurgical"]= 14.7*0.85 + 5.76 # https://elib.dlr.de/130069/1/Renewable%20energy%20in%20copper%20production%20-%20a%20review.pdf
                                                                    # https://www.bmwk.de/Redaktion/DE/Downloads/E/energiewende-in-der-industrie-ap2a-branchensteckbrief-metall.pdf?__blob=publicationFile&v=4
SPEC_ENERGY["Copper"]["Diesel"]["Hydrometallurgical"]= 14.7*0.15 + 7.2 # https://elib.dlr.de/130069/1/Renewable%20energy%20in%20copper%20production%20-%20a%20review.pdf
                                                                # https://www.bmwk.de/Redaktion/DE/Downloads/E/energiewende-in-der-industrie-ap2a-branchensteckbrief-metall.pdf?__blob=publicationFile&v=4
### smelting, refining = processing
SPEC_ENERGY["Cobalt"]["Elec"]["Smelting/Refining"]= 13.57
SPEC_ENERGY["Cobalt"]["Diesel"]["Smelting/Refining"]= 0

SPEC_ENERGY["Gold"]["Elec"]["Smelting/Refining"]= (52.08+38.86)*10**3/2 # Asuming total energy = elec
SPEC_ENERGY["Gold"]["Diesel"]["Smelting/Refining"]= 0

SPEC_ENERGY["Nickel"]["Elec"]["Smelting/Refining"]= 200 # Asuming total energy = elec
SPEC_ENERGY["Nickel"]["Diesel"]["Smelting/Refining"]= 0

SPEC_ENERGY["Manganese"]["Elec"]["Smelting/Refining"]= 18.01
SPEC_ENERGY["Manganese"]["Diesel"]["Smelting/Refining"]= 13.02

#-----------------------------------