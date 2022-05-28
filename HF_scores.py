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

# GHF for scoring template adapted from the Global Human Footprint maps
GHF = {

    'road_scores_l1': {
        'func': 'exp',
        'max_score': 8,
        'max_score_exp': 4,
        'min_score_exp': 0,
        'max_dist': 15000,
    },

    'road_scores_l2': {
        'func': 'exp',
        'max_score': 6,
        'max_score_exp': 3,
        'min_score_exp': 0,
        'max_dist': 7500,
    },

    'road_scores_l3': {
        'func': 'exp',
        'max_score': 4,
        'max_score_exp': 2,
        'min_score_exp': 0,
        'max_dist': 3000,
    },

    'road_scores_l4': {
        'func': 'exp',
        'max_score': 2,
        'max_score_exp': 1,
        'min_score_exp': 0,
        'max_dist': 30,
    },

    'railways_scores': {
        'func': 'bins',
        'scores_by_bins': (
            ((0, 90), 8),
            ((90, np.inf), 0)),
    },

    'river_scores': {
        'func': 'exp',
        'max_score': 4,
        'max_score_exp': 4,
        'min_score_exp': 0,
        'max_dist': 10000,
        'sett_dist': 4000,
        'navi_dist': 20000,
    },

    'settlement_scores': {
        'func': 'exp',
        'max_score': 6,
        'max_score_exp': 3,
        'min_score_exp': 0,
        'max_dist': 3000,
    },

    'reservoir_scores': {
        'func': 'exp',
        'max_score': 4,
        'max_score_exp': 1,
        'min_score_exp': 0,
        'max_dist': 500,
    },

    'pollution_scores': {
        'func': 'exp',
        'max_score': 8,
        'max_score_exp': 3,
        'min_score_exp': 0,
        'max_dist': 1000,
    },

    'urban_scores': {
        'func': 'bins',
        'scores_by_bins': (
            ((0, 2), 10),
            ((2, np.inf), 0)),
    },

    'pop_scores_INEC': {
        'func': 'log',
        'max_score': 10,
        'mult_factor': 3.3333,
        'scaling_factor': 1,
        'resampling_method': 'bilinear',
    },

    'pop_scores_Fcbk_l1': {
        'func': 'exp',
        'max_score': 10,
        'max_score_exp': 5,
        'min_score_exp': 0,
        'max_dist': 15000,
        'resampling_method': 'sum',
    },

    'pop_scores_Fcbk_l2': {
        'func': 'exp',
        'max_score': 6,
        'max_score_exp': 3,
        'min_score_exp': 0,
        'max_dist': 7500,
        'resampling_method': 'sum',
    },

    'pop_scores_Fcbk_l3': {
        'func': 'exp',
        'max_score': 4,
        'max_score_exp': 2,
        'min_score_exp': 0,
        'max_dist': 3000,
        'resampling_method': 'sum',
    },

    'bins_8_.5_scores': {
        'func': 'bins',
        'scores_by_bins': (
            ((0, 500), 8),
            ((500, np.inf), 0)),
    },

    'bins_6_.15_scores': {
        'func': 'bins',
        'scores_by_bins': (
            ((0, 150), 6),
            ((150, np.inf), 0)),
    },

    'bins_6_.05_scores': {
        'func': 'bins',
        'scores_by_bins': (
            ((0, 50), 6),
            ((50, np.inf), 0)),
    },

    'bins_8_.05_scores': {
        'func': 'bins',
        'scores_by_bins': (
            ((0, 50), 8),
            ((50, np.inf), 0)),
    },

    'line_infrastructure_scores': {
        'func': 'bins',
        'scores_by_bins': (
            ((0, 2), 5),
            ((2, np.inf), 0)),
    },

    'ntl_VIIRS_scores': {
        'func': 'equal_sample_bins',
        'number_bins': 10,  # will also be max score
        'min_threshold': 1.5,
        'resampling_method': 'bilinear',
        'rounding_value': 0,
    },

    'ntl_VIIRS_gas_flares_scores': {
        'func': 'bins',
        'scores_by_bins': (
            ((0, 160), 0),  # Threshold from visual tests
            ((160, np.inf), 10),),
        'resampling_method': 'bilinear',
    },

     'ntl_Harmonized_scores': {
         'func': 'equal_sample_bins',
         'number_bins': 10,
         'min_threshold': 10,  # >7 as suggested by authors
         'resampling_method': 'bilinear',
     },

##     'bui_Harmonized_scores': {
##         'func': 'bins',
##         'scores_by_bins': (
##             ((0, 20), 0),  # Threshold from tests
##             ((20, np.inf), 10),),
##         'resampling_method': 'bilinear',
##     },

    'GHS_BUILT_scores': {
        'func': 'bins',
        'scores_by_bins': (
            ((0, 10), 0),  # Thresholds from tests
            ((10, 25), 6),
            ((25, 100), 10),),
        'resampling_method': 'bilinear',
    },

    'plantations_scores': {
        'func': 'bins',
        'scores_by_bins': (
            ((0, 2), 4),
            ((2, 200), 0),
            ((200, np.inf), 0),),
    },

    'agr_MINAGRI_scores': {
        'func': 'categories',
        'scores_by_categories': {
            'Not crops': (0, [0]),
            'Crops': (5, [1]),
        },
        'resampling_method': 'mode',
    },

    'bui_ESA_scores': {
        'func': 'categories',
        'scores_by_categories': {
            'No data, Bare areas, Water, ice': (0, (0, 200, 201, 202, 210, 220)),
            'Tree or herbaceous cover, shrubs': (0, (50, 60, 61, 62, 70, 71, 72,
                                                      80, 81, 82, 90, 160, 170, 180)),
            'Sparse vegetation, Lichens and mosses': (0, (100, 110, 120, 121, 122,
                                                          140, 150, 151, 152, 153)),
            'Grassland': (0, [130]),
            'Mosaic cropland and natural vegetation': (0, (30, 40)),
            'Cropland': (0, (10, 11, 12, 20)),
            'Urban areas': (10, [190]),
        },
        'resampling_method': 'mode',
    },

    'luc_MAAE_RS_scores': {
        'func': 'categories',
        'scores_by_categories': {
            'BOSQUE': (0, [1]),
            'VEGETACIÓN ARBUSTIVA Y HERBÁCEA': (0, [2]),
            'ARTIFICIAL, TIERRA AGROPECUARIA': (4, [3]),
            'CUERPO DE AGUA': (0, [4]),
            'ZONA ANTRÓPICA': (0, [5]),
            'OTRAS TIERRAS': (0, [6]),
        },
        'resampling_method': 'mode',
    },


    'bui_MAAE_RS_scores': {
        'func': 'categories',
        'scores_by_categories': {
            'BOSQUE': (0, [1]),
            'VEGETACIÓN ARBUSTIVA Y HERBÁCEA': (0, [2]),
            'ARTIFICIAL, TIERRA AGROPECUARIA': (0, [3]),
            'CUERPO DE AGUA': (0, [4]),
            'ZONA ANTRÓPICA': (10, [5]),
            'OTRAS TIERRAS': (0, [6]),
        },
        'resampling_method': 'mode',
    },

    'luc_ESA_scores': {
        'func': 'categories',
        'scores_by_categories': {
            'No data, Bare areas, Water, ice': (0, (0, 200, 201, 202, 210, 220)),
            'Tree or herbaceous cover, shrubs': (0, (50, 60, 61, 62, 70, 71, 72,
                                                      80, 81, 82, 90, 160, 170, 180)),
            'Sparse vegetation, Lichens and mosses': (0, (100, 110, 120, 121, 122,
                                                          140, 150, 151, 152, 153)),
            'Grassland': (0, [130]),
            'Mosaic cropland and natural vegetation': (4, (30, 40)),
            'Cropland': (4, (10, 11, 12, 20)),
            'Urban areas': (0, [190]),
        },
        'resampling_method': 'mode',
    },

    'luc_MAAE_scores': {
        'func': 'categories',
        'scores_by_categories': {
            # Class Grassland eliminated and Pastizal moved to Crops because
            # it does not exist in all time series
            'Forest': (0, ('BOSQUE', 'BOSQUE NATIVO')),
            'Shrubs, Herbaceous': (0, ('PÁRAMO', 'PARAMO', 'PRAMO',
                                        'VEGETACIÓN HERBÁEAS',
                                        'VEGETACIN HERBEAS',
                                        'VEGETACIN HERBCEA',
                                        'VEGETACION ARBUSTIVA Y HERBACEA',
                                        'VEGETACIÓN ARBUSTIVA Y HERBÁCEA',
                                        'VEGETACIN ARBUSTIVA Y HERBCEA',
                                        'VEGETACIÓN ARBUSTIVA',
                                        'VEGETACIN ARBUSTIVA',
                                        'VEGETACION ARBUSTIVA',
                                        'VEGETACION HERBACEA',)),
            'Crops': (4, ('TIERRA AGROPECUARIA', 'MOSAICO AGROPECUARIO',
                          'CULTIVO PERMANENTE', 'CULTIVO ANUAL',
                          'CULTIVO SEMI PERMANENTE',
                          'PASTIZAL',
                          )),
            'Forestry': (4, ('PLANTACION FORESTAL', 'PLANTACIÓN FORESTAL',
                              'PLANTACIN FORESTAL')),
            'Human_water': (4, ('ESPEJOS DE AGUA ARTIFICIAL', 'ARTIFICIAL')),
            'Infrastructure': (0, ('INFRAESTRUCTURA')),
            'Built': (0, ('ZONA ANTROPICA', 'ZONA ANTRÓPICA',
                            'ZONA ANTRPICA', 'AREA POBLADA')),
            'Water, Other': (0, ('ESPEJOS DE AGUA NATURAL', 'CUERPO DE AGUA',
                                  'OTRAS TIERRAS', 'GLACIAR', 'NATURAL',
                                  'ÁREA SIN COBERTURA VEGETAL',
                                  'REA SIN COBERTURA VEGETAL',
                                  'AREA SIN COBERTURA VEGETAL',
                                  'SIN INFORMACIÓN',
                                  'SIN INFORMACIN')),
        },

    },

    'bui_MAAE_scores': {
        'func': 'categories',
        'scores_by_categories': {
            'Forest': (0, ('BOSQUE', 'BOSQUE NATIVO',)),
            'Shrubs, Herbaceous': (0, ('PÁRAMO', 'PARAMO', 'PRAMO',
                                        'VEGETACIÓN HERBÁEAS',
                                        'VEGETACIN HERBEAS',
                                        'VEGETACIN HERBCEA',
                                        'VEGETACION ARBUSTIVA Y HERBACEA',
                                        'VEGETACIÓN ARBUSTIVA Y HERBÁCEA',
                                        'VEGETACIN ARBUSTIVA Y HERBCEA',
                                        'VEGETACIÓN ARBUSTIVA',
                                        'VEGETACIN ARBUSTIVA',
                                        'VEGETACION ARBUSTIVA',
                                        'VEGETACION HERBACEA',)),
            'Crops': (0, ('TIERRA AGROPECUARIA', 'MOSAICO AGROPECUARIO',
                          'CULTIVO PERMANENTE', 'CULTIVO ANUAL',
                          'CULTIVO SEMI PERMANENTE',
                          'PASTIZAL',
                          )),
            'Forestry': (0, ('PLANTACION FORESTAL', 'PLANTACIÓN FORESTAL',
                              'PLANTACIN FORESTAL')),
            'Human_water': (0, ('ESPEJOS DE AGUA ARTIFICIAL', 'ARTIFICIAL')),
            'Infrastructure': (8, ('INFRAESTRUCTURA')),
            'Built': (10, ('ZONA ANTROPICA', 'ZONA ANTRÓPICA',
                            'ZONA ANTRPICA', 'AREA POBLADA')),
            'Water, Other': (0, ('ESPEJOS DE AGUA NATURAL', 'CUERPO DE AGUA',
                                  'OTRAS TIERRAS', 'GLACIAR', 'NATURAL',
                                  'ÁREA SIN COBERTURA VEGETAL',
                                  'REA SIN COBERTURA VEGETAL',
                                  'AREA SIN COBERTURA VEGETAL',
                                  'SIN INFORMACIÓN',
                                  'SIN INFORMACIN')),
        },
    },

    'veg_MINAM_scores': {
        'func': 'categories',
        'scores_by_categories': {
            'Forest': (0, ('Bofedal',
                            'Bosque de colina alta', 'Bosque de colina alta con paca',
                            'Bosque de colina alta del Divisor', 'Bosque de colina baja',
                            'Bosque de colina baja con castaa', 'Bosque de colina baja con paca',
                            'Bosque de colina baja con shiringa', 'Bosque de llanura mendrica',
                            'Bosque de montaa', 'Bosque de montaa altimontano',
                            'Bosque de montaa basimontano',
                            'Bosque de montaa basimontano con paca', 'Bosque de montaa con paca',
                            'Bosque de montaa montano', 'Bosque de palmeras de montaa montano',
                            'Bosque de terraza alta', 'Bosque de terraza alta basimontano',
                            'Bosque de terraza alta con castaa', 'Bosque de terraza alta con paca',
                            'Bosque de terraza baja', 'Bosque de terraza baja basimontano',
                            'Bosque de terraza baja con castaa', 'Bosque de terraza baja con paca',
                            'Bosque de terraza inundable por agua negra', 'Bosque inundable de palmeras',
                            'Bosque inundable de palmeras basimontano', 'Bosque montano occidental andino',
                            'Bosque relicto altoandino', 'Bosque relicto mesoandino',
                            'Bosque relicto mesoandino de conferas', 'Bosque seco de colina alta',
                            'Bosque seco de colina baja', 'Bosque seco de lomada', 'Bosque seco de montaa',
                            'Bosque seco de piedemonte', 'Bosque seco ribereo', 'Bosque seco tipo sabana',
                            'Bosque semideciduo de montaa', 'Bosque subhmedo de montaa',
                            'Bosque xrico interandino', 'Cardonal', 'Herbazal hidroftico',
                            'Jalca', 'Loma', 'Manglar', 'Matorral arbustivo', 'Matorral arbustivo altimontano',
                            'Matorral esclerfilo de montaa montano', 'Pacal', 'Pajonal andino',
                            'Pramo', 'Sabana hidroftica con palmeras', 'Sabana xrica interandina',
                            'Tillandsial', 'Vegetacin esclerfila de arena blanca')),
            'Crops': (4, ('Agricultura costera y andina', 'Areas de no bosque amaznico')),
            'Forestry': (4, ('Plantacin Forestal')),
            'Natural vegetation': (0, ('Area altoandina con escasa y sin vegetacin',
                                        'Desierto costero', 'Humedal costero',
                                        'Albfera', 'Vegetacin de isla')),
            'Water, Other': (0, ('Banco de arena', 'Glaciar', 'Ro', 'Estero',
                                  'Lagunas, lagos y cochas', 'Canal internacional',
                                  'Estuario de virilla')),
            'Human water': (4, ('Represa')),
            'Built': (0, ('Area urbana')),
            'Mining': (0, ('Centro minero')),
            'Infrastructure': (0, ('Infraestructura')),
        },
    },

    'mining_MINAM_scores': {
        'func': 'categories',
        'scores_by_categories': {
            'Forest': (0, ('Bofedal',
                            'Bosque de colina alta', 'Bosque de colina alta con paca',
                            'Bosque de colina alta del Divisor', 'Bosque de colina baja',
                            'Bosque de colina baja con castaa', 'Bosque de colina baja con paca',
                            'Bosque de colina baja con shiringa', 'Bosque de llanura mendrica',
                            'Bosque de montaa', 'Bosque de montaa altimontano', 'Bosque de montaa basimontano',
                            'Bosque de montaa basimontano con paca', 'Bosque de montaa con paca',
                            'Bosque de montaa montano', 'Bosque de palmeras de montaa montano',
                            'Bosque de terraza alta', 'Bosque de terraza alta basimontano',
                            'Bosque de terraza alta con castaa', 'Bosque de terraza alta con paca',
                            'Bosque de terraza baja', 'Bosque de terraza baja basimontano',
                            'Bosque de terraza baja con castaa', 'Bosque de terraza baja con paca',
                            'Bosque de terraza inundable por agua negra', 'Bosque inundable de palmeras',
                            'Bosque inundable de palmeras basimontano', 'Bosque montano occidental andino',
                            'Bosque relicto altoandino', 'Bosque relicto mesoandino',
                            'Bosque relicto mesoandino de conferas', 'Bosque seco de colina alta',
                            'Bosque seco de colina baja', 'Bosque seco de lomada', 'Bosque seco de montaa',
                            'Bosque seco de piedemonte', 'Bosque seco ribereo', 'Bosque seco tipo sabana',
                            'Bosque semideciduo de montaa', 'Bosque subhmedo de montaa',
                            'Bosque xrico interandino', 'Cardonal', 'Herbazal hidroftico',
                            'Jalca', 'Loma', 'Manglar', 'Matorral arbustivo', 'Matorral arbustivo altimontano',
                            'Matorral esclerfilo de montaa montano', 'Pacal', 'Pajonal andino',
                            'Pramo', 'Sabana hidroftica con palmeras', 'Sabana xrica interandina',
                            'Tillandsial', 'Vegetacin esclerfila de arena blanca')),
            'Crops': (0, ('Agricultura costera y andina', 'Areas de no bosque amaznico')),
            'Forestry': (0, ('Plantacin Forestal')),
            'Natural vegetation': (0, ('Area altoandina con escasa y sin vegetacin',
                                        'Desierto costero', 'Humedal costero',
                                        'Albfera', 'Vegetacin de isla')),
            'Water, Other': (0, ('Banco de arena', 'Glaciar', 'Ro', 'Estero',
                                  'Lagunas, lagos y cochas', 'Canal internacional',
                                  'Estuario de virilla')),
            'Human water': (0, ('Represa')),
            'Built': (0, ('Area urbana')),
            'Mining': (8, ('Centro minero')),
            'Infrastructure': (0, ('Infraestructura')),
        },
      #   'resampling_method': 'mode',
    },

}
