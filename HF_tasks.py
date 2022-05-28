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

import os
from HF_settings import GENERAL_SETTINGS
from datetime import datetime
from shutil import copyfile
import numpy as np
from HF_layers import multitemporal_layers, layers_settings
from HF_spatial import *  # TODO change


class begin_HF():
    """

    """

    def __init__(self, purpose, tasks, country_processing, remove_aux):
        """

        Parameters
        ----------
        purpose : Purpose of the Human footprint maps. Will match purpose_layers
        in Class GENERAL_SETTINGS
        tasks : Tasks to perform: preparing, scoring, combining and calculating
        the maps, validating.
        main_folder : Name of folder in root for all analysis.
        remove_aux : False to keep auxiliary layers produced.

        Returns
        -------
        None.

        """

        # General settings
        self.main_folder = os.getcwd() + f'/{country_processing}//'
        settings = GENERAL_SETTINGS(country_processing, self.main_folder)
        scoring_template = settings.scoring_template
        purpose_layers = settings.purpose_layers[purpose]
        years = purpose_layers['years']

        # Prepare working folders
        self.prepare_working_folders()

        # Prepare base raster layer
        base_path, res = self.prepare_base_raster(settings)

        # Prepare results folder
        results_folder = self.create_processing_folder(settings, purpose)

        if tasks and purpose_layers['pressures']:

            # Prepare and score pressures and loop by topics first topic
            for pressure in purpose_layers['pressures']:

                if purpose_layers['pressures'][pressure] and years:
                    print()
                    print(f'Processing {pressure}')

                list_datasets = {}
                for year in years:

                    for dataset in purpose_layers['pressures'][pressure]:

                        if year not in list_datasets:
                            list_datasets[year] = []

                        # Determine year to use and scoring method
                        if dataset in multitemporal_layers:

                            # Determine which version in time is closer to year,
                            # if it's a multitemporal layer
                            closer_year = 1000000
                            for layer_aux in multitemporal_layers[dataset]['datasets']:
                                version_year = layers_settings[layer_aux]['year']
                                if abs(version_year - year) <= abs(closer_year - year):
                                    closer_year = version_year
                                    layer = layer_aux

                            # Determine scoring methods
                            # If it's a multitemporal layer, use first one for scoring
                            layer_aux = multitemporal_layers[dataset]['datasets'][0]
                            scoring_method = layers_settings[layer_aux]['scoring']

                        else:
                            layer = dataset
                            scoring_method = layers_settings[layer]['scoring']

                        list_datasets[year].append(layer)

                        if "Preparing" in tasks:
                            PREPARING(layer, year, settings, base_path, purpose,
                                      scoring_template, scoring_method,
                                      results_folder, self.main_folder,
                                      remove_aux, res)

                        if "Scoring" in tasks:
                            SCORING(layer, year, settings, base_path, purpose,
                                    scoring_template, scoring_method,
                                    self.main_folder, remove_aux, res)

                for year in years:
                    if "Combining" in tasks and list_datasets:
                        combineRasters(pressure, year, list_datasets[year],
                                        settings, base_path, purpose, res,
                                        scoring_template, results_folder,
                                        self.main_folder, remove_aux)

            # Calculate maps
            if "Calculating_maps" in tasks:
                for year in years:
                    CALCULATING_MAPS(year, settings, results_folder, purpose,
                                      scoring_template, remove_aux, res)


    def create_processing_folder(self, settings, purpose):
        """
        Creates a new folder for all results.

        Parameters
        ----------
        settings : general settings from GENERAL_SETTINGS class.
        purpose : Purpose of the Human footprint maps. Will match purpose_layers
        in Class GENERAL_SETTINGS.

        Returns
        -------
        folder_path : returns path
            'main_folder\HF_maps\b05_HF_maps/country_datetime_purpose'

        """

        # Settings and working directory
        country = settings.country
        now = datetime.now()
        dt_string = now.strftime("_%Y%m%d_%H%M%S")
        folder_path = f'{self.main_folder}/HF_maps/b05_HF_maps/{country[:2]}{dt_string}_{purpose}'
        os.mkdir(folder_path)

        scripts = ('layers', 'main', 'scores', 'settings', 'spatial', 'tasks')
        for script in scripts:
            src = f'{os.getcwd()}/HF_{script}.py'
            dst = f'{folder_path}/Backup_HF_{script}.py'
            copyfile(src, dst)

        print()
        print(f'Folder {folder_path} created with a backup of the scripts')

        return folder_path

    def prepare_working_folders(self):
        """
        Creates/restores working folders if necessary.
        Working folders are:
            b02_Base_rasters
            b03_Prepared_pressures
            b04_Scored_pressures
            b05_HF_maps
        Folders starring with 'b' can be deleted and the script will
        reconstruct them with their contents.

        Returns
        -------
        None.

        """

        # Get main folder and strings to working folders
        folders = (
            f'{self.main_folder}HF_maps/b02_Base_rasters',
            f'{self.main_folder}HF_maps/b03_Prepared_pressures',
            f'{self.main_folder}HF_maps/b04_Scored_pressures',
            f'{self.main_folder}HF_maps/b05_HF_maps',
        )

        # Check if folders exist and if not, create it
        for f in folders:
            if not os.path.exists(f):
                os.makedirs(f)

    def prepare_base_raster(self, settings):
        """
        Converts extent polygon to a raster if necessary.
        The base raster will be the model for ALL rasters to be created.

        Parameters
        ----------
        settings : general settings from GENERAL_SETTINGS class.

        Returns
        -------
        base_path : path to base raster.

        """

        # Prepare name for base raster
        extent = settings.extent_Polygon
        res = settings.pixel_res
        chunk = extent.split('/')[-1].replace('.', '_')
        base_path = f'{self.main_folder}HF_maps/b02_Base_rasters/base_{chunk}_{res}m.tif'
        base_path_uncomp = f'{self.main_folder}HF_maps/b02_Base_rasters/base_{chunk}_{res}m_uncomp.tif'

        # Search for base raster is exists
        base = os.path.isfile(base_path)

        # If base raster does not exist, create it
        if not base:
            print()
            print('Creating base raster')
            create_base_raster(base_path_uncomp, settings)

            # Compress result and delete previous version
            compress(base_path_uncomp, base_path)
            os.remove(base_path_uncomp)

        else:
            print()
            print('Base raster already existed')

        return base_path, res


class PREPARING():
    """
    Converts spatial inputs of pressures to a raster that will be later on
    scored.
    Performs all transformations regarding to format, resolution, units.

    """

    def __init__(self, layer, year, settings, base_path, purpose, scoring_template,
                  scoring_method, results_folder, main_folder, remove_aux, res):
        """


        Parameters
        ----------
        layer : Layer name of the pressure/dataset to prepare
        year : year of HF map. If it's a multitemporal layer, the closest will
        be selected.
        settings : general settings from GENERAL_SETTINGS class.
        base_path : path to base raster.
        purpose : Purpose of the Human footprint maps. Will match purpose_layers
        in Class GENERAL_SETTINGS.
        scoring_template : Name of the scoring template from HF_scores.
        E.g. 'GHF'.
        scoring_method : scoring method is a setting of each layer and will
        determine the type of preparing and scoring. Comes from HF_layers.
        results_folder : Folder in root for all results.
        main_folder : Name of folder in root for all analysis.
        remove_aux : False to keep auxiliary layers produced.

        Returns
        -------
        None.

        """

        print()
        print(f'      Preparing {layer} {year}')

        # Check if prepared layer exists
        extent = settings.extent_Polygon
        extent = extent.split('/')[-1].split('.')[-2]
        pressure_path = f'{main_folder}/HF_maps/b03_Prepared_pressures/{layer}_{extent}_{scoring_template}_{res}m_prepared.tif'
        pressure_uncompressed_path = f'{main_folder}/HF_maps/b03_Prepared_pressures/{layer}_{extent}_{scoring_template}_{res}m_uncompressed.tif'

        # If pressure does not exist, create it
        pressure_exists = os.path.isfile(pressure_path)

        if not pressure_exists:

            # Call spatial functions according to scoring method
            if scoring_method in (
                                  'pop_scores_INEC', 'GHS_BUILT_scores',
                                  'ntl_VIIRS_scores',
                                  'ntl_VIIRS_gas_flares_scores',
                                  'ntl_Harmonized_scores',
                                  'luc_ESA_scores', 'bui_ESA_scores',
                                  'luc_MAAE_RS_scores', 'bui_MAAE_RS_scores',
                                    ):

                # Warp raster
                warp_raster(layer, settings, base_path, pressure_uncompressed_path,
                            scoring_template, scoring_method, main_folder)

            elif scoring_method in ('pop_scores_Fcbk',):

                # Warp full fcbk raster
                warp_raster(layer, settings, base_path, pressure_uncompressed_path, scoring_template, scoring_method, main_folder)

                # Divide layer according to bins
                # Open full fcbk raster
                full_raster = RASTER(pressure_uncompressed_path)
                full_raster.get_array()
                full_ar = full_raster.array.copy()
                nodata = full_raster.nodata

                # Open base raster
                base_raster = RASTER(base_path)

                # Subset and create a new raster
                levels = layers_settings[layer]['threshold_divide']
                for l in levels:
                    print(f'               Fcbk subset {l}')
                    # new_path
                    new_name = full_raster.name + f'_{l}'
                    new_path_unc = full_raster.path
                    new_path_unc = new_path_unc.replace(full_raster.name, new_name)

                    # Subset
                    bott,top = levels[l][0], levels[l][1]
                    # vecfunc = np.vectorize(self.subset)
                    # sub_ar = vecfunc(full_ar, bott, top, nodata)
                    # sub_ar = ((full_ar >= bott) & (full_ar < top)).astype(int)
                    sub_ar = np.where((full_ar >= bott) & (full_ar < top), 1, 0)


                    # Copy withn ew array and compress
                    copy_raster(new_path_unc, base_raster, Float=False, array=sub_ar)
                    new_path = new_path_unc.replace('_uncompressed','')
                    prepared_path = new_path_unc.replace(f'_uncompressed_{l}',f'_prepared_{l}')
                    compress(new_path_unc, new_path)
                    if remove_aux:
                        os.remove(new_path_unc)

                    # Create proximity raster
                    proximity_raster(new_path, prepared_path, layer='')

                full_raster.close()
                base_raster.close()

            elif scoring_method in ('settlement_scores', 'road_scores_l1',
                                    'road_scores_l2', 'road_scores_l3',
                                    'road_scores_l4', 'railways_scores',
                                    'line_infrastructure_scores',
                                    'reservoir_scores', 'pollution_scores',
                                    'plantations_scores','urban_scores',
                                    'bins_6_.15_scores', 'bins_6_.05_scores',
                                    'bins_8_.05_scores', 'bins_8_.5_scores',
                                    ):

                # Get proximity raster from shapefile
                print('         Creating proximity raster for ' + layer)
                create_proximity_raster(layer, settings, base_path,
                                        pressure_uncompressed_path,
                                        scoring_template, main_folder, res)

            elif scoring_method in ('luc_MAAE_scores', 'bui_MAAE_scores',
                                    'veg_MINAM_scores', 'mining_MINAM_scores',
                                    'agr_MINAGRI_scores',):

                # Create categorical raster from vector layer
                create_categorical_raster(layer, settings, base_path, pressure_uncompressed_path,
                                          main_folder, scoring_template)

            elif scoring_method in ('river_scores'):

                # Create categorical raster from vector layer
                create_proximity_raster_from_pixels(layer, year, settings,
                                                    base_path, pressure_uncompressed_path,
                                                    scoring_template, purpose,
                                                    results_folder, main_folder,
                                                    res)

            else:
                print(f'{scoring_method} not found in preparing options')

            # Patch when needed: remove problems with layers
            country = settings.country
            if scoring_method in ('GHS_BUILT_scores') and not settings.extent_Polygon:
            # if scoring_method in ('GHS_BUILT_scores'):
                if country == 'Ecuador':
                    shapefile_paths = layers_settings[layer]['patch']['areas_shps'][country]
                    shapefile_paths = [f'{main_folder}{i}' for i in shapefile_paths]
                    patch_type = layers_settings[layer]['patch']['patch_type']
                if shapefile_paths:
                    print(f'            Patching {layer}')
                    for shape in shapefile_paths:
                        patch(layer, pressure_uncompressed_path, shape, base_path, patch_type=patch_type)

            # Compress result and delete previous version
            compress(pressure_uncompressed_path, pressure_path)
            if remove_aux:
                os.remove(pressure_uncompressed_path)

        else:
            print(f'         {layer} was already prepared')


    # def subset(self, ar, bott, top, nodata):
    #     """Vectorized numpy function. Returns 1 if values within a range"""

    #     if ar == nodata:
    #         return np.nan
    #     elif bott <= ar <= top:
    #         return 1
    #     else:
    #         return 0


class SCORING():
    """
    Scores prepared rasters of pressures.
    Human influence scores according to scoring template in HF_scores.


    """

    def __init__(self, layer, year, settings, base_path, purpose,
                  scoring_template, scoring_method, main_folder, remove_aux, res):
        """


        Parameters
        ----------
        layer : Layer name of the pressure/dataset to prepare
        year : year of HF map. If it's a multitemporal layer, the closest will
        be selected.
        settings : general settings from GENERAL_SETTINGS class.
        base_path : path to base raster.
        purpose : Purpose of the Human footprint maps. Will match purpose_layers
        in Class GENERAL_SETTINGS.
        scoring_template : Name of the scoring template from HF_scores.
        E.g. 'GHF'.
        scoring_method : scoring method is a setting of each layer and will
        determine the type of preparing and scoring. Comes from HF_layers.
        results_folder : Folder in root for all results.
        main_folder : Name of folder in root for all analysis.
        remove_aux : False to keep auxiliary layers produced.

        Returns
        -------
        None.

        """

        print()
        print(f'      Scoring {layer} {year}')

        # Check if scored layer exists
        extent = settings.extent_Polygon
        extent_str = extent.split('/')[-1].split('.')[-2]
        in_path = f'{main_folder}/HF_maps/b03_Prepared_pressures/{layer}_{extent_str}_{scoring_template}_{res}m_prepared.tif'
        scored_path = f'{main_folder}/HF_maps/b04_Scored_pressures/{layer}_{year}_{extent_str}_{scoring_template}_{res}m_scored_not_clipped.tif'
        out_path = f'{main_folder}/HF_maps/b04_Scored_pressures/{layer}_{year}_{extent_str}_{scoring_template}_{res}m_scored.tif'
        out_path_uncomp = f'{main_folder}/HF_maps/b04_Scored_pressures/{layer}_{year}_{extent_str}_{scoring_template}_{res}m_uncomp.tif'
        score_exists = os.path.isfile(out_path)

        # If pressure does not exist, create it
        if not score_exists:

            # Define function to assign scores according to scoring method
            scoring_method = layers_settings[layer]['scoring']
            if scoring_method in (
                    'plantations_scores',
                    'GHS_BUILT_scores',
                    'ntl_VIIRS_scores',
                    'ntl_Harmonized_scores',
                    'railways_scores',
                    'bins_6_.05_scores', 'bins_6_.15_scores',
                    'bins_8_.5_scores', 'bins_8_.05_scores',
                    'line_infrastructure_scores',
                    'ntl_VIIRS_gas_flares_scores',
                    'urban_scores',
            ):
                vecfunc = np.vectorize(self.scores_from_bins)

            elif scoring_method in ('luc_ESA_scores', 'bui_ESA_scores',
                                    'agr_MINAGRI_scores',
                                    'luc_MAAE_RS_scores', 'bui_MAAE_RS_scores',):
                vecfunc = np.vectorize(self.scores_from_category)

            elif scoring_method in ('bui_MAAE_scores', 'luc_MAAE_scores',
                                    'veg_MINAM_scores', 'mining_MINAM_scores',
                                    ):
                vecfunc = np.vectorize(self.scores_remain)

            elif scoring_method in ('pop_scores_INEC',
                                    ):
                vecfunc = np.vectorize(self.scores_log10_function, otypes=[float])

            elif scoring_method in ('road_scores_l1', 'road_scores_l2',
                                    'road_scores_l3', 'road_scores_l4',
                                    'river_scores','settlement_scores',
                                    'reservoir_scores', 'pollution_scores',
                                    'pop_scores_Fcbk'
                                    ):
                vecfunc = np.vectorize(self.exp_function, otypes=[float])

            else:
                print(f'{scoring_method} not found as a scoring method in class Scoring')

            # Prepare paths if Facebook
            if scoring_method == 'pop_scores_Fcbk':
                in_paths = {}
                levels = layers_settings[layer]['threshold_divide']
                for l in levels:
                    in_paths[l] = {}
                    in_paths[l]['in_path'] = in_path.replace('prepared', f'prepared_{l}')
                    in_paths[l]['scoring_m'] = f'{scoring_method}_{l}'
                    in_paths[l]['scored_path'] = scored_path.replace('scored',f'scored_{l}')
                    in_paths[l]['out_path'] = out_path.replace('scored',f'scored_{l}')
                    in_paths[l]['out_path_uncomp'] = out_path_uncomp.replace('uncomp',f'uncomp_{l}')

            else:
                in_paths = {'':{'in_path': in_path,
                                'scoring_m': scoring_method,
                                'scored_path': scored_path,
                                'out_path': out_path,
                                'out_path_uncomp': out_path_uncomp,
                                }}

            # Loop through inpaths
            for in_path in in_paths:

                scoring_method2 = in_paths[in_path]['scoring_m']

                # Open prepared pressure raster
                not_scored_raster = RASTER(in_paths[in_path]['in_path'])
                not_scored_raster.get_array()
                not_scored_array = not_scored_raster.array

                # Assign parameters for scoring functions
                # Float True for creating a floating type raster
                Float = False
                self.nodata = not_scored_raster.nodata
                template = getattr(HF_scores, settings.scoring_template)
                scoring_method_template = template[scoring_method2]
                if scoring_method_template['func'] == 'bins':
                    self.scores = scoring_method_template['scores_by_bins']
                elif scoring_method_template['func'] == 'exp':
                    self.max_score = scoring_method_template['max_score']
                    self.max_score_exp = scoring_method_template['max_score_exp']
                    self.min_score_exp = scoring_method_template['min_score_exp']
                    self.max_dist = scoring_method_template['max_dist']
                    Float = True
                elif scoring_method_template['func'] == 'log':
                    self.max_score = scoring_method_template['max_score']
                    self.mult_factor = scoring_method_template['mult_factor']
                    self.scaling_factor = scoring_method_template['scaling_factor']
                    Float = True
                elif scoring_method_template['func'] == 'categories':
                    self.scores = scoring_method_template['scores_by_categories']
                elif scoring_method_template['func'] == 'equal_sample_bins':
                    self.number_bins = scoring_method_template['number_bins']
                    self.min_threshold = scoring_method_template['min_threshold']
                    # Get bins for distributing values in 10 equal quantiles
                    if 'bins_ntl' not in globals():
                        global bins_ntl
                        bins_ntl = self.get_bins(not_scored_array, self.min_threshold, self.nodata)
                    self.scores = bins_ntl

                # Get units of original layer
                self.units = layers_settings[layer]['units']

                # Assign scores and save new raster
                # cannot send scores as argument here, must use self.scores
                scored_array = vecfunc(not_scored_array)

                # Create scores raster dataset and save
                base_raster = RASTER(base_path)
                copy_raster(in_paths[in_path]['scored_path'], base_raster, Float)
                base_raster.close()
                scores_raster = RASTER(in_paths[in_path]['scored_path'])
                save_array(scores_raster.bd, scored_array)

                # Close rasters
                scores_raster.close()
                not_scored_raster.close()

                # Clip score raster to study area
                clip_raster_by_extent(in_paths[in_path]['out_path_uncomp'], in_paths[in_path]['scored_path'], settings)

                # Compress result and delete previous version
                compress(in_paths[in_path]['out_path_uncomp'], in_paths[in_path]['out_path'])
                if remove_aux:
                    os.remove(in_paths[in_path]['scored_path'])
                    os.remove(in_paths[in_path]['out_path_uncomp'])

            # If it's facebook, combine here
            if scoring_method == 'pop_scores_Fcbk':
                levels = layers_settings[layer]['threshold_divide']
                num = 0

                for l in levels:

                    press_path = out_path.replace('scored',f'scored_{l}')

                    # Get pressure raster array masked by NoData value
                    press_raster = RASTER(press_path)
                    nodata = press_raster.nodata
                    press_raster.get_array()
                    press_array = np.ma.masked_equal(press_raster.array, nodata)

                    # Create and add pressures to final map
                    if num != 0:
                        np.maximum(datout, press_array, out=datout)
                    else:
                        datout = press_array
                        fn1 = press_path

                    # Close pressure raster
                    press_raster.close()

                    # Add 1 to num
                    num += 1

                # Add rasters if there's at list one layer
                if num > 0:

                    # Create the raster of added pressures in results folder
                    press_raster = RASTER(fn1)
                    createRasterFromCopy(out_path_uncomp, press_raster.ds, datout)
                    press_raster.close()

                    # Compress result and delete previous version
                    compress(out_path_uncomp, out_path)
                    if remove_aux:
                        os.remove(out_path_uncomp)

        else:
            print(f'         {layer} was already scored')


    def exp_function(self, value):
        '''
        Vectorized numpy function.
        Exponential function according to GHF methods.

        '''

        if value > self.max_dist:
            return 0
        elif value == 0:
            return self.max_score
        else:
            if self.units in ('meters', 'hab/pixel'):
                return self.max_score_exp * np.exp(-(value / 1000)) + self.min_score_exp
            elif self.units == 'kilometers':
                return self.max_score_exp * np.exp(-(value)) + self.min_score_exp

    def scores_log10_function(self, value):
        '''
        Vectorized numpy function.
        Logarithmic function according to GHF methods.

        '''

        return_value = self.mult_factor * np.log10((value/self.scaling_factor) + 1)
        if return_value > self.max_score:
            return self.max_score
        else:
            return return_value

    def scores_from_bins(self, value):
        """
        Vectorized numpy function.
        Returns score according to bins in HF_scores.py/GHF/scoring_method.

        """

        if value == 65535: return 0  # Value when proximity is empty
        for i in self.scores:
            if i[0][0] <= value <= i[0][1]:
                return i[1]
        return 0

    def scores_remain(self, value):
        """
        Vectorized numpy function.
        Keeps the score, used for scored rasters from other sources.
        """

        if self.nodata != value:
            return value
        else:
            return 0

    def scores_from_category(self, value):
        ''' Returns score according to template. If a value falls in one of
        the ranges defined in "road_scores", it returns a specific value.'''

        # print(value)#, scores)
        if value == self.nodata:
            return 0
        for i in self.scores:
            # print(scores[i][1])
            if value in self.scores[i][1]:
                # print(scores[i][1])
                # if i[1] > 5:
                #     print(f'Check value in template: {i[0]}, {i[1]}')
                #     sys.exit("stop in function scores_from_category in class scoring")
                return self.scores[i][0]
        return 0

    def get_bins(self, array, min_th, nd):
        """


        Parameters
        ----------
        array : array from nightime lights raster.
        min_th : minimum threshold used to filter out possible noise in the
        form of very small values.
        nd : Nodata value from nightime lights raster.

        Returns
        -------
        scores : bins of scores in the form of:
                ((0, 500), 1), #  Bin 1
                ((500, 1000), 2), #  Bin 2
                ...
                ((1500, np.inf), 10) #  Bin 10

        """

        ar_f = array.flatten()
        ar_f = np.delete(ar_f, np.where(ar_f < min_th))
        ar_f = np.delete(ar_f, np.where(ar_f == 0))
        ar_f = np.delete(ar_f, np.where(ar_f == nd))

        r = range(0,11)
        limits = [np.quantile(ar_f, i/10, interpolation='midpoint') for i in r]
        scores = [[[limits[i], limits[i+1]],i+1] for i in r if i < 10]

        scores[-1][0][1] = np.inf
        return scores


class CALCULATING_MAPS():
    """
    Call all functions for calculating maps.

    """

    def __init__(self, year, settings, results_folder, purpose,
                  scoring_template, remove_aux, res):
        """

        Parameters
        ----------
        year : year of HF map. If it's a multitemporal layer, the closest will
        be selected.
        settings : general settings from GENERAL_SETTINGS class.
        purpose : Purpose of the Human footprint maps. Will match purpose_layers
        in Class GENERAL_SETTINGS.
        scoring_template : Name of the scoring template from HF_scores.
        E.g. 'GHF'.
        results_folder : Folder in root for all results.
        remove_aux : False to keep auxiliary layers produced.

        Returns
        -------
        None.

        """

        print()
        print(f'Calculating {year} Human Footprint map')

        # Create sum of pressures maps
        if settings.purpose_layers[purpose]:

            # Add topic rasters, create statistics
            addRasters(year, settings, results_folder, purpose,
                        scoring_template, remove_aux, res)

            # Create graph summary for HF map
