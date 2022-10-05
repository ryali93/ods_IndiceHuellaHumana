# -*- coding: utf-8 -*-
"""
Module for creating the Human Footprint maps of Peru and Ecuador.

Version 20220519 (Training Peru)

This script will read spatial datasets of pressures, prepared them by
converting them all to a raster format with identical dimensions, then
score them to reflect their expected human influence.
The scored pressures will then be added to calculate a Human Footprint map.

The structure of the module requires the following:
    - HF_main.py (this script) to control the higher level of the process.
    - HF_settings to control the general settings.
    - HF_tasks to call all functions according to the HF workflow.
    - HF_spatial to provide all spatial functions and classes.
    - HF_scores to provide scores of humnan influence.
    - HF_layers for the settings related to layers (e.g. paths).

This is part of the project Life on Land, with UNDP, the Ministries of the
Environment of each country, and funded by NASA.

Created on Thu Jun 18 18:26:00 2020

@author: Jose Aragon-Osejo aragon@unbc.ca / jose.luis.aragon.ec@gmail.com

"""

import time
from datetime import timedelta
start_time = time.monotonic()

from HF_tasks import begin_HF

# HF purpose, version or set of maps
purposes = [
    'SDG15', 
    # 'Full', 
    # 'Official', 
    # 'Current', 
    # 'Multitemporal',
    ]

# Indicate tasks to perform (leave other commented out)
tasks = [
    "Preparing",
    "Scoring",
    "Combining",  # Enable this when calculating navigable waterways
    "Calculating_maps",  # Enable this when calculating navigable waterways
]

# Main folder on the same level as the scripts. Keep format '/folder//'
country_processing = 'Peru_HH'

# Delete auxiliary files
remove_aux = True
# remove_aux = False


# Don't change the following
# Process Human Footprint maps according to settings
for purpose in purposes:
    begin_HF(purpose, tasks, country_processing, remove_aux)


end_time = time.monotonic()
print('\007')
print(f'Total time: {timedelta(seconds=end_time - start_time)}')
print("------ FIN ------")
