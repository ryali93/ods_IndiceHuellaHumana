# -*- coding: utf-8 -*-
"""
Module for creating the Human Footprint maps of Peru and Ecuador.

Version 20220519 (Training Peru)

This script will read spatial datasets of pressures, prepared them by
converting them all to a raster format with identical dimensions, then
score them to reflect their expected human influence.
The scored pressures will then be added to calculate a Human Footprint map.

The structure of the module requires the following:
    - HF_main.py to control the higher level of the process.
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

from HF_spatial import VECTOR


# Settings
general_settings = {

    'Peru_HH': {
        'country': 'Peru',
        # Extent...() ,True) for clipping, False for not clipping. Clipping all
        # country extent takes too long and is unnecessary
        'extent_Polygon': ('HF_maps/01_Limits/Peru_IGN.shp', False),  # Final maps
        # "extent_Polygon": ('HF_maps/01_Limits/area_anp.shp', True),
        # "extent_Polygon": ('HF_maps/01_Limits/Peru_01.shp', True),
        'scoring_template':'GHF',
        'pixel_res': 300,
        'purpose_layers': {

            'SDG15': {

                'years': [2012, 2015, 2018],
                # 'years': [2018],

                'pressures': {

                    'Built_Environments': [
                        'bui_ESA',  # Multitemporal
                        # 'bui_GHS_BUILT_18',  # Current
                        # 'bui_Pe_a_urbana_MINAM_13',  # Official
                        'bui_Pe_poblados_MINAM_11',  # Official
                        'bui_Pe_pob_indig_MinCul_20',  # Official
                        'Pe_puertos_MINAM_11'  # Official
                    # BoTADEROS  #
                        ],

                    'Population_Density': [
                        'Pe_pob_Facebook_18',  # Current
                        ],

                    'Land_Cover': [
                        # 'Pe_Cob_Veg_MINAM_13',  # Official
                        # 'Pe_Censo_Agr_MIDAGRI_18',  # Official, Current
                        "lc_ESA",  # Multitemporal
                    ],

                    'Roads_Railways': [
                        'Pe_vias_primarias_OSM_20',  # Current
                        'Pe_vias_secundarias_OSM_20',  # Current
                        'Pe_vias_vecinales_OSM_20',  # Current
                        'Pe_vias_peatonales_OSM_20',  # Current
                        'Pe_lin_ferreas_OSM_20',  # Current
                        ],

                    'Navigable_Waterways': [ #  Enable "Combining" and "Calculating_maps" in HF_main/tasks
                        'Pe_rios_MINAM_15',  # Multitemporal, Official, Current
                        'Pe_costa_IGN_15',  # Multitemporal, Official, Current
                        ],

                    'Energy_Infrastructure': [
                        'ntl_VIIRS',  # Multitemporal, Current
                        'Pe_lin_transmis_MINAM_11',  # Official, Current
                        'Pe_hidroel_OSINERGMIN_18',  # Official, Current
                        ],

                    'Oil_Gas_Infrastructure': [
                        'Pe_oleoducto_MINAM_11',  # Official, Current
                        'Pe_camisea_MINAM_11',  # Official, Current
                        'ntl_VIIRS_gas_flares',  # Multitemporal, Current
                        'Pe_gasoducto_OSINERGMIN_18',  # Official, Current
                        'Pe_oleoducto_OSINERGMIN_18',  # Official, Current
                        'Pe_pozos_PERUPETRO_19'  # Official, Current
                        ],

                    'Mining_Infrastructure': [
                        'in_global_mining',  # Current
                        'Pe_mineria_MINAM_13',  # Official, Current
                        ],
                },
            },

            'Full': {
                # 'years': [2012, 2015, 2018],
                'years': [2018],

                'pressures': {

                    'Built_Environments': [
                        'bui_ESA',  # Multitemporal
                        'bui_GHS_BUILT_18',  # Current
                        'bui_Pe_a_urbana_MINAM_13',  # Official
                        'bui_Pe_poblados_MINAM_11',  # Official
                        'bui_Pe_pob_indig_MinCul_20',  # Official
                        'Pe_puertos_MINAM_11'  # Official
                    # BoTADEROS  #
                        ],

                    'Population_Density': [
                        # "pob_GHS",  #
                        'Pe_pob_Facebook_18',  # Current
                        ],

                    'Land_Cover': [
                        'Pe_Cob_Veg_MINAM_13',  # Official
                        'Pe_Censo_Agr_MIDAGRI_18',  # Official, Current
                        "lc_ESA",  # Multitemporal
                    ],

                    'Roads_Railways': [
                        'Pe_vias_nacional_MTC_19',  # Official
                        'Pe_vias_deprtmtal_MTC_19',  # Official
                        'Pe_vias_vecinal_MTC_19',  # Official
                        'Pe_vias_primarias_OSM_20',  # Current
                        'Pe_vias_secundarias_OSM_20',  # Current
                        'Pe_vias_vecinales_OSM_20',  # Current
                        'Pe_vias_peatonales_OSM_20',  # Current
                        'Pe_lin_ferreas_MTC_18',  # Official
                        'Pe_lin_ferreas_OSM_20',  # Current
                        ],

                    'Navigable_Waterways': [ #  Enable "Combining" and "Calculating_maps" in HF_main/tasks
                        'Pe_rios_MINAM_15',  # Multitemporal, Official, Current
                        'Pe_costa_IGN_15',  # Multitemporal, Official, Current
                        ],

                    'Energy_Infrastructure': [
                        'ntl_VIIRS',  # Multitemporal, Current
                        'Pe_lin_transmis_MINAM_11',  # Official, Current
                        'Pe_hidroel_OSINERGMIN_18',  # Official, Current
                        ],

                    'Oil_Gas_Infrastructure': [
                        'Pe_oleoducto_MINAM_11',  # Official, Current
                        'Pe_camisea_MINAM_11',  # Official, Current
                        'ntl_VIIRS_gas_flares',  # Multitemporal, Current
                        'Pe_gasoducto_OSINERGMIN_18',  # Official, Current
                        'Pe_oleoducto_OSINERGMIN_18',  # Official, Current
                        'Pe_pozos_PERUPETRO_19'  # Official, Current
                        ],

                    'Mining_Infrastructure': [
                        'in_global_mining',  # Current
                        'Pe_mineria_MINAM_13',  # Official, Current
                        ],
                },
            },

            'Official': {
                'years': [2015],

                'pressures': {

                    'Built_Environments': [
                        'bui_Pe_a_urbana_MINAM_13',  # Official
                        'bui_Pe_poblados_MINAM_11',  # Official
                        'bui_Pe_pob_indig_MinCul_20',  # Official
                        'Pe_puertos_MINAM_11'  # Official
                    # BoTADEROS  #
                        ],

                    'Population_Density': [
                        ],

                    'Land_Cover': [
                        'Pe_Cob_Veg_MINAM_13',  # Official
                        'Pe_Censo_Agr_MIDAGRI_18',  # Official, Current
                    ],

                    'Roads_Railways': [
                        'Pe_vias_nacional_MTC_19',  # Official
                        'Pe_vias_deprtmtal_MTC_19',  # Official
                        'Pe_vias_vecinal_MTC_19',  # Official
                        'Pe_lin_ferreas_MTC_18',  # Official
                        ],

                    'Navigable_Waterways': [ #  Enable "Combining" and "Calculating_maps" in HF_main/tasks
                        'Pe_rios_MINAM_15',  # Multitemporal, Official, Current
                        'Pe_costa_IGN_15',  # Multitemporal, Official, Current
                        ],

                    'Energy_Infrastructure': [
                        'Pe_lin_transmis_MINAM_11',  # Official, Current
                        'Pe_hidroel_OSINERGMIN_18',  # Official, Current
                        ],

                    'Oil_Gas_Infrastructure': [
                        'Pe_oleoducto_MINAM_11',  # Official, Current
                        'Pe_camisea_MINAM_11',  # Official, Current
                        'Pe_gasoducto_OSINERGMIN_18',  # Official, Current
                        'Pe_oleoducto_OSINERGMIN_18',  # Official, Current
                        'Pe_pozos_PERUPETRO_19'  # Official, Current
                        ],

                    'Mining_Infrastructure': [
                        'Pe_mineria_MINAM_13',  # Official, Current
                        ],
                },
            },

            'Current': {
                'years': [2018],

                'pressures': {

                    'Built_Environments': [
                        'bui_GHS_BUILT_18',  # Current
                    # BoTADEROS  #
                        ],

                    'Population_Density': [
                        'Pe_pob_Facebook_18',  # Current
                        ],

                    'Land_Cover': [
                        'Pe_Censo_Agr_MIDAGRI_18',  # Official, Current
                        # ESA?
                    ],

                    'Roads_Railways': [
                        'Pe_vias_primarias_OSM_20',  # Current
                        'Pe_vias_secundarias_OSM_20',  # Current
                        'Pe_vias_vecinales_OSM_20',  # Current
                        'Pe_vias_peatonales_OSM_20',  # Current
                        'Pe_lin_ferreas_OSM_20',  # Current
                        ],

                    'Navigable_Waterways': [ #  Enable "Combining" and "Calculating_maps" in HF_main/tasks
                        'Pe_rios_MINAM_15',  # Multitemporal, Official, Current
                        'Pe_costa_IGN_15',  # Multitemporal, Official, Current
                        ],

                    'Energy_Infrastructure': [
                        'Pe_lin_transmis_MINAM_11',  # Official, Current
                        'Pe_hidroel_OSINERGMIN_18',  # Official, Current
                        ],

                    'Oil_Gas_Infrastructure': [
                        'Pe_oleoducto_MINAM_11',  # Official, Current
                        'Pe_camisea_MINAM_11',  # Official, Current
                        'ntl_VIIRS_gas_flares',  # Multitemporal, Current
                        'Pe_gasoducto_OSINERGMIN_18',  # Official, Current
                        'Pe_oleoducto_OSINERGMIN_18',  # Official, Current
                        'Pe_pozos_PERUPETRO_19'  # Official, Current
                        ],

                    'Mining_Infrastructure': [
                        'in_global_mining',  # Current
                        'Pe_mineria_MINAM_13',  # Official, Current
                        ],
                },
            },

            'Multitemporal': {

                'years': [2012, 2015, 2018],

                'pressures': {

                    'Built_Environments': [
                        'bui_ESA',  # Multitemporal
                    # BoTADEROS  #
                        ],

                    'Population_Density': [
                        ],

                    'Land_Cover': [
                        "lc_ESA",  # Multitemporal
                        ],

                    'Roads_Railways': [
                        ],

                    'Navigable_Waterways': [ #  Enable "Combining" and "Calculating_maps" in HF_main/tasks
                        'Pe_rios_MINAM_15',  # Multitemporal, Official, Current
                        'Pe_costa_IGN_15',  # Multitemporal, Official, Current
                        ],

                    'Energy_Infrastructure': [
                        'ntl_VIIRS',  # Multitemporal, Current
                        ],

                    'Oil_Gas_Infrastructure': [
                        'ntl_VIIRS_gas_flares',  # Multitemporal, Current
                        ],

                    'Mining_Infrastructure': [
                        ],
                },
            },
        },
    },
}


class GENERAL_SETTINGS:
    """
    Class for general technical settings:
        country
        extent polygon for study area
        coordinates system (from extent polygon)
        scoring template
        pixel resolution
        Layers according to the version/purpose of the HF maps
            years to process
            pressures
                datasets per pressure
    """

    def get_crs(self, path):
        """ Gets the coordinate system of a vector """
        vector_crs = VECTOR(path)
        crs = vector_crs.crs
        vector_crs.close()
        return crs

    def __init__(self, country_processing, main_folder):
        """


        Parameters
        ----------
        main_folder : Name of folder in root for all analysis.

        Returns
        -------
        None.

        """
        settings_c = general_settings[country_processing]


        # Settings
        self.country = settings_c['country']
        # Extent...() ,True) for clipping, False for not clipping. Clipping all
        # country extent takes too long and is unnecessary
        # self.extent_Polygon = main_folder + 'HF_maps/01_Limits/Limite_CONALI_2019.shp', False  # Final maps
        self.extent_Polygon = main_folder + settings_c['extent_Polygon'][0]
        self.clip_by_Polygon = settings_c['extent_Polygon'][1]
        self.crs = self.get_crs(self.extent_Polygon) #  Don't change this
        self.scoring_template = settings_c['scoring_template']
        self.pixel_res = settings_c['pixel_res']
        self.purpose_layers = settings_c['purpose_layers']
