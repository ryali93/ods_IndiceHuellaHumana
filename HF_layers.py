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
import numpy as np

# multitemporal_layers indicates which layers should be treated as multitemporal.
# The script will look first here and decide the closest layer in time according
# to the year being processed. If the layer is not here, it will look directly
# in the layers

multitemporal_layers = {

    'ntl_Harmonized':{
        'datasets': (
            'ntl_Harmonized_92',
            'ntl_Harmonized_00',
            'ntl_Harmonized_08',
            'ntl_Harmonized_15',
            'ntl_Harmonized_18',
        ),
        'purp_scores': {
            'offi': 'low',
            'finer':
                {
                    'scale': None,
                    'res': 30,
                    'unit': 'arcs',
                },
        },
        'years_datasets': list(range(1992, 2018 + 1)),

    },

    'ntl_VIIRS': {
        'datasets': (
            'ntl_VIIRS_12',
            'ntl_VIIRS_15',
            'ntl_VIIRS_18',
            'ntl_VIIRS_20',
        ),
        'purp_scores': {
            'offi': 'low',
            'finer':
                {
                    'scale': None,
                    'res': 15,
                    'unit': 'arcs',
                },
        },
        'years_datasets': list(range(2012, 2020 + 1)),
    },

    'ntl_VIIRS_gas_flares': {
        'datasets': (
            'ntl_VIIRS_gas_flares_12',
            'ntl_VIIRS_gas_flares_15',
            'ntl_VIIRS_gas_flares_18',
            'ntl_VIIRS_gas_flares_20',
        ),
        'purp_scores': {
            'offi': 'low',
            'finer':
                {
                    'scale': None,
                    'res': 15,
                    'unit': 'arcs',
                },
        },
        'years_datasets': list(range(2012, 2020 + 1)),
    },

    'bui_ESA': {
        'datasets': (
            "bui_ESA_92",
            "bui_ESA_00",
            "bui_ESA_10",
            "bui_ESA_15",
            "bui_ESA_18",
            "bui_ESA_19",
        ),
        'purp_scores': {
            'offi': 'med',
            'finer':
                {
                    'scale': None,
                    'res': 300,
                    'unit': 'm',
                },
        },
        'years_datasets': list(range(1992, 2019 + 1)),
    },
    'lc_ESA': {
        'datasets': (
            "lc_ESA_92",
            "lc_ESA_00",
            "lc_ESA_10",
            "lc_ESA_15",
            "lc_ESA_18",
            "lc_ESA_19",
            "lc_ESA_22",
        ),
        'purp_scores': {
            'offi': 'med',
            'finer':
                {
                    'scale': None,
                    'res': 300,
                    'unit': 'm',
                },
        },
        'years_datasets': list(range(1992, 2019 + 1)),
    },
}


layers_settings = {  # Multitemporal, official, current

#     ## NTL

 # Multitemporal
    'ntl_Harmonized_92': {'path': [
        "No_Oficial/NTL/Li_et_al.2020/Harmonized_DN_NTL_1992_calDMSP.tif", ],
                       'scoring': 'ntl_Harmonized_scores',
                       'year': 1992,
                       'units': 'Digital number',},
    'ntl_Harmonized_00': {'path': [
        "No_Oficial/NTL/Li_et_al.2020/Harmonized_DN_NTL_2000_calDMSP.tif", ],
                       'scoring': 'ntl_Harmonized_scores',
                       'year': 2000,
                       'units': 'Digital number'},
    'ntl_Harmonized_08': {'path': [
        "No_Oficial/NTL/Li_et_al.2020/Harmonized_DN_NTL_2008_calDMSP.tif", ],
                       'scoring': 'ntl_Harmonized_scores',
                       'year': 2008,
                       'units': 'Digital number'},
    'ntl_Harmonized_15': {'path': [
        "No_Oficial/NTL/Li_et_al.2020/Harmonized_DN_NTL_2015_simVIIRS.tif", ],
                       'scoring': 'ntl_Harmonized_scores',
                       'year': 2015,
                       'units': 'Digital number'},
    'ntl_Harmonized_18': {'path': [
        "No_Oficial/NTL/Li_et_al.2020/Harmonized_DN_NTL_2018_simVIIRS.tif", ],
                      'scoring': 'ntl_Harmonized_scores',
                      'year': 2018,
                      'units': 'Digital number'},

    'ntl_VIIRS_12': {'path': [
        "No_Oficial/NTL/VIIRS-DNB_V2/VNL_v2_npp_201204-201303_global_vcmcfg_c202101211500.average_PEC.tif",
    ],
        'scoring': 'ntl_VIIRS_scores',
        'year': 2012,
        'units': 'Digital number',
        'offi': 'low',
    },

    'ntl_VIIRS_15': {'path': [
        "No_Oficial/NTL/VIIRS-DNB_V2/VNL_v2_npp_2015_global_vcmslcfg_c202101211500.average_PEC.tif",
    ],
        'scoring': 'ntl_VIIRS_scores',
        'year': 2015,
        'units': 'Digital number',
        'offi': 'low',
    },

    'ntl_VIIRS_18': {'path': [
        "No_Oficial/NTL/VIIRS-DNB_V2/VNL_v2_npp_2018_global_vcmslcfg_c202101211500.average_PEC.tif",
    ],
        'scoring': 'ntl_VIIRS_scores',
        'year': 2018,
        'units': 'Digital number',
        'offi': 'low',
    },

    'ntl_VIIRS_20': {'path': [
        "No_Oficial/NTL/VIIRS-DNB_V2/VNL_v2_npp_2020_global_vcmslcfg_c202101211500.average_PEC.tif",
    ],
        'scoring': 'ntl_VIIRS_scores',
        'year': 2020,
        'units': 'Digital number',
        'offi': 'low',
    },

    'ntl_VIIRS_gas_flares_12': {'path': [
        "No_Oficial/NTL/VIIRS-DNB_V2/VNL_v2_npp_201204-201303_global_vcmcfg_c202101211500.average_PEC.tif",
    ],
        'scoring': 'ntl_VIIRS_gas_flares_scores',
        'year': 2012,
        'units': 'Digital number',
        'offi': 'low',
    },

    'ntl_VIIRS_gas_flares_15': {'path': [
        "No_Oficial/NTL/VIIRS-DNB_V2/VNL_v2_npp_2015_global_vcmslcfg_c202101211500.average_PEC.tif",
    ],
        'scoring': 'ntl_VIIRS_gas_flares_scores',
        'year': 2015,
        'units': 'Digital number',
        'offi': 'low',
    },

    'ntl_VIIRS_gas_flares_18': {'path': [
        "No_Oficial/NTL/VIIRS-DNB_V2/VNL_v2_npp_2018_global_vcmslcfg_c202101211500.average_PEC.tif",
    ],
        'scoring': 'ntl_VIIRS_gas_flares_scores',
        'year': 2018,
        'units': 'Digital number',
        'offi': 'low',
    },

    'ntl_VIIRS_gas_flares_20': {'path': [
        "No_Oficial/NTL/VIIRS-DNB_V2/VNL_v2_npp_2020_global_vcmslcfg_c202101211500.average_PEC.tif",
    ],
        'scoring': 'ntl_VIIRS_gas_flares_scores',
        'year': 2020,
        'units': 'Digital number',
        'offi': 'low',
    },

    ## Built environments

    "bui_ESA_92": {'path': ["No_Oficial/Land_use/ESA-LC/ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992-v2.0.7.tif"],
                    'scoring': 'bui_ESA_scores',
                    'year': 1992,
                    'units': '*units*',
                    'offi': 'med',
                    # 'finer': 9,
                    },
    "bui_ESA_00": {'path': ["No_Oficial/Land_use/ESA-LC/ESACCI-LC-L4-LCCS-Map-300m-P1Y-2000-v2.0.7.tif"],
                    'scoring': 'bui_ESA_scores',
                    'year': 2000,
                    'units': '*units*',
                    'offi': 'med',
                    # 'finer': 9,
                    },
    "bui_ESA_10": {'path': ["No_Oficial/Land_use/ESA-LC/ESACCI-LC-L4-LCCS-Map-300m-P1Y-2010-v2.0.7.tif"],
                    'scoring': 'bui_ESA_scores',
                    'year': 2010,
                    'units': '*units*',
                    'offi': 'med',
                    # 'finer': 9,
                    },
    "bui_ESA_15": {'path': ["No_Oficial/Land_use/ESA-LC/ESACCI-LC-L4-LCCS-Map-300m-P1Y-2015-v2.0.7.tif"],
                    'scoring': 'bui_ESA_scores',
                    'year': 2015,
                    'units': '*units*',
                    'offi': 'med',
                    },
    
    "bui_ESA_18": {'path': ["No_Oficial/Land_use/ESA-LC/C3S-LC-L4-LCCS-Map-300m-P1Y-2018-v2.1.1.tif"],
                    'scoring': 'bui_ESA_scores',
                    'check_intersection': False,
                    'year': 2018,
                    'units': '*units*',
                    'offi': 'med',
                    # 'finer': 9,
                    },
    "bui_ESA_19": {'path': ["No_Oficial/Land_use/ESA-LC/C3S-LC-L4-LCCS-Map-300m-P1Y-2019-v2.1.1.tif"],
                    'scoring': 'bui_ESA_scores',
                    'year': 2019,
                    'units': '*units*',
                    'offi': 'med',
                    # 'finer': 9,
                    },


    # Official Peru
    'bui_Pe_a_urbana_MINAM_13': {
        'path': ['Oficial/MINAM/Geoservidor/Cobertura_Vegetal/mapa_cobertura_vegetal_2015/Area_urbana.shp'],
        'scoring': 'urban_scores',
        'year': 2010,
        'units': 'meters',
        'offi': 'high',
        'finer':
            {
                'scale': 100000,
                'res': None,
                'unit': None,
            },
        },
    'bui_Pe_poblados_MINAM_11': {'path': [
        "Oficial/MINAM/Geoservidor/Vulnerabilidad_Fisica/vulnerabilidad_fisica/vulne_fisica/e_expuesto/ccpp.shp"],
                                  'scoring': 'settlement_scores',
                                  'year': 2010,
                                  'units': 'meters',
                                  'offi': 'high',
                                  'finer':
                                      {
                                          'scale': 100000,
                                          'res': None,
                                          'unit': None,
                                      },
                                  },
    'bui_Pe_pob_indig_MinCul_20': {'path': ['Oficial/DGOTA/CentroPobladoIndigena.shp'],
                                    'scoring': 'settlement_scores',
                                    'year': 2020,
                                    'units': 'meters',
                                    'offi': 'high',
                                    'finer':
                                        {
                                            'scale': None,
                                            'res': None,
                                            'unit': None,
                                        },
                                    },

    # Best
    'bui_GHS_BUILT_18': {
        'path_Ec': ["No_Oficial/Land_use/GHS_BUILT_S2/Merge_Ec.tif"],
        'path_Pe': ["No_Oficial/Land_use/GHS_BUILT_S2/Merge_Pe.tif"],
        'scoring': 'GHS_BUILT_scores',
        'no_data': 255,
        'year': 2018,
        'units': '*units*',
        'offi': 'low',
        'finer':
            {
                'scale': None,
                'res': 10,
                'unit': 'm',
            },
        'patch':{
            'patch_type': 'eliminate',
            'areas_shps': {
                'Ecuador': ["No_Oficial/Land_use/GHS_BUILT_S2/rio_a_patch_Ec.shp",
                            "No_Oficial/Land_use/GHS_BUILT_S2/isla_a_patch_Ec.shp",],
                'Peru': None,},
            'values_rasters': None,
            },
    },


#     #  ## Population


    # Best
    'Pe_pob_Facebook_18': {'path': ["No_Oficial/Population/Facebook/population_per_2018-10-01.tif"],
                            'scoring': 'pop_scores_Fcbk',
                            'threshold_divide': {
                                'l1':(10000,np.inf),
                                'l2':(5000,10000),
                                'l3':(0.01,5000),
                                },
                            'year': 2018,
                            'check_intersection': True,
                            'units': 'hab/pixel',
                            'offi': 'low',
                            'finer':
                                {
                                    'scale': None,
                                    'res': 30,
                                    'unit': 'm',
                                },
                            },

    ## Land use

    # Official Peru
    'Pe_Cob_Veg_MINAM_13': {
        'path': ['Oficial/MINAM/Geoservidor/Cobertura_Vegetal/mapa_cobertura_vegetal_2015/CobVeg_180615.shp'],
        'scoring': 'veg_MINAM_scores',
        'cat_field': 'CobVeg2013',
        'year': 2013,
        'units': 'categorical',
        'offi': 'high',
        'finer':
            {
                'scale': 100000,
                'res': None,
                'unit': None,
            },
        },
    'Pe_Censo_Agr_MIDAGRI_18': {'path': ['Oficial/MIDAGRI/Cobertura_Agricola/Peru_cober_Aagri_Dist_geowgs84.shp'],
                                'scoring': 'agr_MINAGRI_scores',
                                # 'cat_field': 'CobVeg2013',
                                'year': 2020,
                                'units': 'categorical',
                                'offi': 'high',
                                'finer':
                                    {
                                        'scale': 10000,
                                        'res': None,
                                        'unit': None,
                                    },
                                },


    # Multitemporal
    "lc_ESA_92": {'path': ["No_Oficial/Land_use/ESA-LC/ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992-v2.0.7.tif"],
                  'scoring': 'luc_ESA_scores',
                  'year': 1992,
                  'units': 'categorical',
                  'offi': 'med',
                  # 'finer': 9,
                  },
    "lc_ESA_00": {'path': ["No_Oficial/Land_use/ESA-LC/ESACCI-LC-L4-LCCS-Map-300m-P1Y-2000-v2.0.7.tif"],
                  'scoring': 'luc_ESA_scores',
                  'year': 2000,
                  'units': 'categorical',
                  'offi': 'med',
                  # 'finer': 9,
                  },
    "lc_ESA_10": {'path': ["No_Oficial/Land_use/ESA-LC/ESACCI-LC-L4-LCCS-Map-300m-P1Y-2010-v2.0.7.tif"],
                  'scoring': 'luc_ESA_scores',
                  'year': 2012,
                  'units': 'categorical',
                  'offi': 'med',
                  # 'finer': 9,
                  },
    "lc_ESA_15": {'path': ["No_Oficial/Land_use/ESA-LC/ESACCI-LC-L4-LCCS-Map-300m-P1Y-2015-v2.0.7.tif"],
                  'scoring': 'luc_ESA_scores',
                  'year': 2015,
                  'units': 'categorical',
                  'offi': 'med',
                  # 'finer': 9,
                  },
    "lc_ESA_18": {'path': ["No_Oficial/Land_use/ESA-LC/C3S-LC-L4-LCCS-Map-300m-P1Y-2018-v2.1.1.tif"],
                  'scoring': 'luc_ESA_scores',
                  'year': 2018,
                  'units': 'categorical',
                  'offi': 'med',
                  # 'finer': 9,
                  },
    "lc_ESA_19": {'path': ["No_Oficial/Land_use/ESA-LC/C3S-LC-L4-LCCS-Map-300m-P1Y-2019-v2.1.1.tif"],
                  'scoring': 'luc_ESA_scores',
                  'year': 2019,
                  'units': 'categorical',
                  'offi': 'med',
                  # 'finer': 9,
                  },

    "lc_ESA_22": {'path': ["No_Oficial/Land_use/ESA-LC/...2022-v2.1.1.tif"],
                  'scoring': 'luc_ESA_scores',
                  'year': 2022,
                  'units': 'categorical',
                  'offi': 'med',
                  # 'finer': 9,
                  },

    ## Accessibility

    # Multitemporal

     # Official Peru
    'Pe_vias_nacional_MTC_19': {'path': ['Oficial/MTC/red_vial_nacional_dic19/red_vial_nacional_dic19.shp'],
                                'scoring': 'road_scores_l1',
                                'year': 2019,
                                'units': 'meters',
                                'offi': 'high',
                                'finer':
                                    {
                                        'scale': 100000,
                                        'res': None,
                                        'unit': None,
                                    },
                                },
    'Pe_vias_deprtmtal_MTC_19': {'path': ['Oficial/MTC/red_vial_departamental_dic19/red_vial_departamental_dic19.shp'],
                                  'scoring': 'road_scores_l2',
                                  'year': 2019,
                                  'units': 'meters',
                                  'offi': 'high',
                                  'finer':
                                      {
                                          'scale': 100000,
                                          'res': None,
                                          'unit': None,
                                      },
                                  },
    'Pe_vias_vecinal_MTC_19': {'path': ['Oficial/MTC/red_vial_vecinal_dic19/red_vial_vecinal_dic19.shp'],
                                'scoring': 'road_scores_l3',
                                'year': 2019,
                                'units': 'meters',
                                'offi': 'high',
                                'finer':
                                    {
                                        'scale': 100000,
                                        'res': None,
                                        'unit': None,
                                    },
                                },
    'Pe_lin_ferreas_MTC_18': {'path': ['Oficial/MTC/linea_ferrea_dic18/linea_ferrea_dic18.shp'],
                              'scoring': 'railways_scores',
                              'year': 2018,
                              'units': 'meters',
                              'offi': 'high',
                              'finer':
                                  {
                                      'scale': 100000,
                                      'res': None,
                                      'unit': None,
                                  },
                              },
    'Pe_puertos_MINAM_11': {'path': [
        'Oficial/MINAM/Geoservidor/Vulnerabilidad_Fisica/vulnerabilidad_fisica/vulne_fisica/e_expuesto/Puertos.shp'],
                            'scoring': 'settlement_scores',
                            'year': 2010,
                            'units': 'meters',
                            'offi': 'high',
                            'finer':
                                {
                                    'scale': 100000,
                                    'res': None,
                                    'unit': None,
                                },
                            },
    'Pe_rios_MINAM_15': {
        'path': ['Oficial/MINAM/Geoservidor/Cobertura_Vegetal/mapa_cobertura_vegetal_2015/Rios_CobVeg_180615.shp'],
        'scoring': 'river_scores',
        'year': 2015,
        'units': 'meters',
        'offi': 'high',
        'finer':
            {
                'scale': 100000,
                'res': None,
                'unit': None,
            },
    },
    'Pe_costa_IGN_15': {'path': ['Oficial/IGN/Costa_IGN.shp'],
                        'scoring': 'river_scores',
                        'year': 2015,
                        'units': 'meters',
                        'offi': 'high',
                        'finer':
                            {
                                'scale': None,
                                'res': None,
                                'unit': None,
                            },
                        },


    # Best Peru
    'Pe_vias_primarias_OSM_20': {'path': ["No_Oficial/OSM/peru_vias/primaria.shp"],
                                  'scoring': 'road_scores_l1',
                                  'year': 2020,
                                  'units': 'meters',
                                  'offi': 'low',
                                  'finer':
                                      {
                                          'scale': 50000,
                                          'res': None,
                                          'unit': None,
                                      },
                                  },
    'Pe_vias_secundarias_OSM_20': {'path': ["No_Oficial/OSM/peru_vias/secundaria.shp"],
                                    'scoring': 'road_scores_l2',
                                    'year': 2020,
                                    'units': 'meters',
                                    'offi': 'low',
                                    'finer':
                                        {
                                            'scale': 50000,
                                            'res': None,
                                            'unit': None,
                                        },
                                    },
    'Pe_vias_vecinales_OSM_20': {'path': ["No_Oficial/OSM/peru_vias/vecinal.shp"],
                                  'scoring': 'road_scores_l3',
                                  'year': 2020,
                                  'units': 'meters',
                                  'offi': 'low',
                                  'finer':
                                      {
                                          'scale': 50000,
                                          'res': None,
                                          'unit': None,
                                      },
                                  },
    'Pe_vias_peatonales_OSM_20': {'path': ["No_Oficial/OSM/peru_vias/peatonal.shp"],
                                  'scoring': 'road_scores_l4',
                                  'year': 2020,
                                  'units': 'meters',
                                  'offi': 'low',
                                  'finer':
                                      {
                                          'scale': 50000,
                                          'res': None,
                                          'unit': None,
                                      },
                                  },
    'Pe_lin_ferreas_OSM_20': {'path': ["No_Oficial/OSM/peru-latest-free.shp/gis_osm_railways_free_1.shp"],
                              'scoring': 'railways_scores',
                              'year': 2020,
                              'units': 'meters',
                              'offi': 'low',
                              'finer':
                                  {
                                      'scale': 50000,
                                      'res': None,
                                      'unit': None,
                                  },
                              },

    #  ## Infrastructure

    #  # Multitemporal

     # Official Peru
    'Pe_lin_transmis_MINAM_11': {'path': [
        'Oficial/MINAM/Geoservidor/Vulnerabilidad_Fisica/vulnerabilidad_fisica/vulne_fisica/e_expuesto/electrico.shp'],
                                  'scoring': 'line_infrastructure_scores',
                                  'year': 2010,
                                  'units': 'meters',
                                  'offi': 'high',
                                  'finer':
                                      {
                                          'scale': None,
                                          'res': None,
                                          'unit': None,
                                      },
                                  },
    'Pe_oleoducto_MINAM_11': {'path': ['Oficial/MINAM_Envio/oleoducto/oleducto.shp'],
                              'scoring': 'line_infrastructure_scores',
                              'year': 2011,
                              'units': 'meters',
                              'offi': 'high',
                              'finer':
                                  {
                                      'scale': None,
                                      'res': None,
                                      'unit': None,
                                  },
                              },
    'Pe_camisea_MINAM_11': {'path': [
        'Oficial/MINAM/Geoservidor/Vulnerabilidad_Fisica/vulnerabilidad_fisica/vulne_fisica/e_expuesto/camisea.shp'],
                            'scoring': 'line_infrastructure_scores',
                            'year': 2011,
                            'units': 'meters',
                            'offi': 'high',
                            'finer':
                                {
                                    'scale': None,
                                    'res': None,
                                    'unit': None,
                                },
                            },
    'Pe_gasoducto_OSINERGMIN_18': {'path': ['Oficial/OSINERGMIN/gasoducto.shp'],
                                    'scoring': 'line_infrastructure_scores',
                                    'year': 2018,
                                    'units': 'meters',
                                    'offi': 'high',
                                    'finer':
                                        {
                                            'scale': None,
                                            'res': None,
                                            'unit': None,
                                        },
                                    },
    'Pe_oleoducto_OSINERGMIN_18': {'path': ['Oficial/OSINERGMIN/oleoducto.shp'],
                                    'scoring': 'line_infrastructure_scores',
                                    'year': 2018,
                                    'units': 'meters',
                                    'offi': 'high',
                                    'finer':
                                        {
                                            'scale': None,
                                            'res': None,
                                            'unit': None,
                                        },
                                    },
    'Pe_hidroel_OSINERGMIN_18': {'path': ['Oficial/OSINERGMIN/c_hidrolectrica.shp'],
                                  'scoring': 'bins_6_.15_scores',
                                  'year': 2018,
                                  'units': 'meters',
                                  'offi': 'high',
                                  'finer':
                                      {
                                          'scale': None,
                                          'res': None,
                                          'unit': None,
                                      },
                                  },
    'Pe_pozos_PERUPETRO_19': {'path': ["Oficial/PERUPETRO/Pozos/Pozos_petroleros_noZM.shp"],
                              'scoring': 'bins_6_.05_scores',
                              'year': 2019,
                              'units': 'meters',
                              'offi': 'high',
                              'finer':
                                  {
                                      'scale': None,
                                      'res': None,
                                      'unit': None,
                                  },
                              },
    'Pe_mineria_MINAM_13': {
        'path': ['Oficial/MINAM/Geoservidor/Cobertura_Vegetal/mapa_cobertura_vegetal_2015/CobVeg_180615.shp'],
        'scoring': 'mining_MINAM_scores',
        'cat_field': 'CobVeg2013',
        'year': 2013,
        'units': 'categorical',
        'offi': 'high',
        'finer':
            {
                'scale': 100000,
                'res': None,
                'unit': None,
            },
        },

    'in_global_mining': {'path':
                         ["No_Oficial/Mining/global_mining_polygons_v1.shp", ],
                          'scoring': 'bins_6_.05_scores',
                          'year': 2020,
                          'units': '',
                          'offi': 'low',
                          'finer':
                              {
                                  'scale': None,
                                  'res': None,
                                  'unit': None,
                              },
                          },
}
