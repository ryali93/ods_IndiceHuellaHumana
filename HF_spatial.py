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
import copy
import math
import numbers
import numpy as np
from math import sqrt
from osgeo import gdal, ogr, osr
import HF_scores
from HF_layers import layers_settings


class RASTER():
    """
    Class for working with rasters.
    Currently only TIFFs are supported.
    """

    def __init__(self, path):
        self.path = path
        self.name = path.split('/')[-1].split('.')[-2]
        self.ds = gdal.Open(path, gdal.GA_Update)
        self.XSize = self.ds.RasterXSize
        self.YSize = self.ds.RasterYSize
        self.bd = self.ds.GetRasterBand(1)
        self.nodata = self.bd.GetNoDataValue()
        self.geotrans = self.ds.GetGeoTransform()
        self.resX = self.geotrans[1]
        self.resY = - self.geotrans[5]
        self.projref = self.ds.GetProjectionRef()
        self.dataType = self.bd.DataType
        self.dataType_name = gdal.GetDataTypeName(self.dataType)

    def get_array(self):
        """
        Initiates the array. The array is not initiated at __init__ to avoid
        memory issued if the array is not needed.

        Returns
        -------
        None.

        """
        self.array = self.bd.ReadAsArray()
        return self.array

    def close(self):
        """
        Closes the class instance. Needed to save changes.

        Returns
        -------
        None.

        """
        try:
            self.bd.ComputeStatistics(0)
        except:
            pass
        self.ds = None
        self.XSize = None
        self.YSize = None
        self.bd = None
        self.nodata = None
        # try:
        self.array = None
        # except:
        #     pass


class VECTOR():
    """
    Class for working with vectors.
    Currently only shapefiles are supported.
    """

    def get_geometry_type(self, layer):
        """
        Transforms grometry type in number format to name.
        WKB types supported by GDAL as shown here:
            http://portal.opengeospatial.org/files/?artifact_id=25355
            https://gis.stackexchange.com/questions/239289/gdal-ogr-python-getgeomtype-method-returns-integer-what-is-the-matching-geo

        Parameters
        ----------
        layer : ogr layer from which the type will be translated.

        Returns
        -------
        Geometry type as org name.

        """

        GeometryTypeToName_Translator = {
            1: ogr.wkbPoint,
            2: ogr.wkbLineString,
            3: ogr.wkbPolygon,
            4: ogr.wkbMultiPoint,
            5: ogr.wkbMultiLineString,
            6: ogr.wkbMultiPolygon,
        }
        layer_defn = layer.GetLayerDefn()
        return GeometryTypeToName_Translator[layer_defn.GetGeomType()]

    def __init__(self, path):
        self.path = path
        self.name = path.split('/')[-1].split('.')[0]
        self.driver = ogr.GetDriverByName("ESRI Shapefile")
        self.ds = self.driver.Open(path, 1)  # 1 to read and write
        self.layer = self.ds.GetLayer()
        self.crs = self.layer.GetSpatialRef()
        self.extent = self.layer.GetExtent()
        self.crs_authority = self.crs.GetAttrValue('AUTHORITY', 1)
        self.geom_type = self.get_geometry_type(self.layer)
        self.defn = self.layer.GetLayerDefn()
        self.schema = self.layer.schema

    def close(self):
        """
        Closes the class instance. Needed to save changes.

        Returns
        -------
        None.

        """
        self.ds = None
        self.layer = None
        self.crs = None
        self.geom_type = None


def compress(pressure_uncomp_path, pressure_path):
    """
    Compresses a raster.
    More info at https://gdal.org/drivers/raster/cog.html
    Parameters
    ----------
    pressure_uncomp_path : uncompressed path of existing raster.
    pressure_path : compressed output raster.

    Returns
    -------
    None.

    """

    unc_raster = RASTER(pressure_uncomp_path)
    unc_ds = unc_raster.ds
    # predictor = "3"
    creation_options = ["COMPRESS=LZW", "TILED=YES"]#, "stats=True"]  # , "PREDICTOR=3"]
    reduced_raster = gdal.Translate(pressure_path, unc_ds, creationOptions=creation_options)
    unc_raster.close()
    reduced_raster = None
    r = RASTER(pressure_uncomp_path)
    r.close()


def create_base_raster(base_path, settings):
    """
    Creates a base raster from a extent shapefile.
    Depends on the resolution from settings.
    ALL rasters produced later on will follow the same settings.

    Based on
    https://gis.stackexchange.com/questions/212795/rasterizing-shapefiles-with-gdal-and-python
    Parameters
    ----------
    base_path : path for the base raster.
    settings : general settings from GENERAL_SETTINGS class.

    Returns
    -------
    None.

    """

    extent_polygon = VECTOR(settings.extent_Polygon)
    extent = extent_polygon.extent  # tuple(w,e,s,n)

    # Create command string
    command = [
        'gdal_rasterize',
        '-l', extent_polygon.name,
        '-burn', 1.0,
        '-tr', settings.pixel_res, settings.pixel_res,
        '-a_nodata', -9999.0,
        '-te', extent[0], extent[2], extent[1], extent[3],
        '-ot', 'Float32',
        '-of', 'GTiff',
        '-co', 'COMPRESS=DEFLATE', '-co', 'PREDICTOR=2', '-co', 'ZLEVEL=9',
        f'"{settings.extent_Polygon}"',
        f'"{base_path}"',]

    command = ' '.join(str(i) for i in command)

    # Execute command line
    os.system(command)


def clip_raster_by_extent(out_path, raster_to_clip, settings):
    """
    Clips a raster by the study area polygon.

    Parameters
    ----------
    out_path : path where the clipped raster will be saved.
    raster_to_clip : raster to clip.
    settings : general settings from GENERAL_SETTINGS class. It provides the
    path to the extent polygon to use for clipping.

    Returns
    -------
    None.

    """

    # Set paths to layers
    extent = settings.extent_Polygon

    # Settings for warping
    kwargs = {'format': 'GTiff',
              'dstSRS': settings.crs,
              'cutlineDSName': extent,
              'cropToCutline': True,
                'outputType': gdal.GDT_Float32,
              }

    # Clip raster
    ds = gdal.Warp(out_path, raster_to_clip, **kwargs)
    bd = ds.GetRasterBand(1)
    bd.ComputeStatistics(0)
    ds = None


def GetGeoInfo(base_raster):
    """
    Returns base raster settings
    NDV, xsize, ysize, GeoT, Projection, DataType

    https://gis.stackexchange.com/questions/57005/python-gdal-write-new-raster-using-projection-from-old
    """

    NDV = base_raster.bd.GetNoDataValue()
    if NDV == None: NDV = -9999
    xsize = base_raster.ds.RasterXSize
    ysize = base_raster.ds.RasterYSize
    GeoT = base_raster.ds.GetGeoTransform()
    Projection = osr.SpatialReference()
    Projection.ImportFromWkt(base_raster.ds.GetProjectionRef())
    DataType = base_raster.dataType_name

    return NDV, xsize, ysize, GeoT, Projection, DataType

def ParseType(type):
    """
    Returns datatype in GDAL format.
    https://github.com/USGS-Astrogeology/GDAL_scripts/blob/master/gdal_baseline_slope/gdal_baseline_slope.py
    """
    if type == 'Byte':
        return gdal.GDT_Byte
    elif type == 'Int16':
        return gdal.GDT_Int16
    elif type == 'UInt16':
        return gdal.GDT_UInt16
    elif type == 'Int32':
        return gdal.GDT_Int32
    elif type == 'UInt32':
        return gdal.GDT_UInt32
    elif type == 'Float32':
        return gdal.GDT_Float32
    elif type == 'Float64':
        return gdal.GDT_Float64
    elif type == 'CInt16':
        return gdal.GDT_CInt16
    elif type == 'CInt32':
        return gdal.GDT_CInt32
    elif type == 'CFloat32':
        return gdal.GDT_CFloat32
    elif type == 'CFloat64':
        return gdal.GDT_CFloat64
    else:
        return gdal.GDT_Byte


def CreateGeoTiff(path, Array, driver, NDV,
                  xsize, ysize, GeoT, Projection, DataType):
    """
    Creates a new raster from
    path, Array, driver, NDV, xsize, ysize, GeoT, Projection, DataType

    Function to write a new file
    https://gis.stackexchange.com/questions/57005/python-gdal-write-new-raster-using-projection-from-old
    """
    DataType = ParseType(DataType)
    DataSet = driver.Create(path, xsize, ysize, 1, DataType)
    # the '1' is for band 1.
    DataSet.SetGeoTransform(GeoT)
    DataSet.SetProjection(Projection.ExportToWkt())
    # Write the array
    DataSet.GetRasterBand(1).WriteArray(Array)
    DataSet.GetRasterBand(1).SetNoDataValue(NDV)
    DataSet = None


def copy_raster(path, base_raster, Float=False, array=False):
    """
    Copies a raster to another path according to base raster.
    If array is provided, it will create a copy of base raster with new values.

    https://gis.stackexchange.com/questions/57005/python-gdal-write-new-raster-using-projection-from-old
    """

    # Open the original file
    if type(array) == bool:
        base_raster.get_array()
        Array = base_raster.array
    else:
        Array = array
    # Get the raster info
    NDV, xsize, ysize, GeoT, Projection, DataType = GetGeoInfo(base_raster)

    # Set up the GTiff driver
    driver = gdal.GetDriverByName('GTiff')

    # Change DataType to Float if necessary
    if Float:
        DataType = 'Float32'

    # Now turn the array into a GTiff.
    CreateGeoTiff(path, Array, driver, NDV,
                  xsize, ysize, GeoT, Projection, DataType)

def createRasterFromCopy(fn, ds, data):
    """ Similar method as previous, merge """ #  TODO
    driver = gdal.GetDriverByName('GTiff')
    outds = driver.CreateCopy(fn, ds, strict=0)
    band_out = outds.GetRasterBand(1)
    band_out.WriteArray(data)
    band_out.ComputeStatistics(0)
    ds = None
    outds = None
    band_out = None


def warp_raster(layer, settings, base_path, pressure_path, scoring_template, scoring_method, main_folder,
                raster_list=False): #  TODO don't use raster_list
    """
    Warps a raster to match base raster's settings.
    Special cases are considered.

    Parameters
    ----------
    layer : Layer name of the pressure/dataset.
    settings : general settings from GENERAL_SETTINGS class.
        base_path : path to base raster.
    pressure_path : path for the output warped raster.
    scoring_template : Name of the scoring template from HF_scores.
        E.g. 'GHF'.
    scoring_method : scoring method is a setting of each layer and will
        determine the type of preparing and scoring. Comes from HF_layers.
    main_folder : Name of folder in root for all analysis.
    raster_list : optional. The default is False.
        If more than one raster is to be warped, it returns a list.

    Returns
    -------
    new_in_paths : List of warped rasters, if necessary.

    """

    print(f'         Warping {layer}')
    country = settings.country

    # Search for pressure layer if exists
    if scoring_method != 'GHS_BUILT_scores':
        in_paths = layers_settings[layer]["path"]
        in_paths = [f'{main_folder}{i}' for i in in_paths]
    else:
        if country == 'Ecuador':
            in_paths =  layers_settings[layer]["path_Ec"]
        elif country == 'Peru':
            in_paths =  layers_settings[layer]["path_Pe"]
        in_paths = [f'{main_folder}{i}' for i in in_paths]
    new_in_paths = []

    # Loop over each path in layer
    for in_path in in_paths:

        # Names
        in_path_str = in_path.split('/')[-1].replace('.', '_')
        layer_name = '_'.join(in_path_str.split('_')[:-1])
        if not (len(in_paths) > 1):
            layer_name = layer

        final_path = pressure_path
        prepared_exists = os.path.isfile(final_path)

        if not prepared_exists:

            print(f'            Warping {layer_name}')

            # Get resampling mode for warping
            if scoring_method == 'pop_scores_Fcbk':
                resampling_method = 'sum'
            else:
                scores_full = getattr(HF_scores, settings.scoring_template)
                scores = scores_full[scoring_method]
                resampling_method = scores['resampling_method']

            # Adding raster to list of rasters to return
            new_in_paths.append(in_path)

            # Create raster instance for base raster
            base_raster = RASTER(base_path)

            # Get base raster dimensions
            base_XSize = base_raster.XSize
            base_YSize = base_raster.YSize

            # Set arguments for warp operation
            kwargs = {'format': 'GTiff',
                      'cutlineDSName': settings.extent_Polygon,
                      'cropToCutline': True,
                      'width': base_XSize, 'height': base_YSize,
                      'resampleAlg': resampling_method,
                      'dstSRS': settings.crs,
                      'dstNodata': base_raster.nodata,
                      'multithread': True,
                      }

            # Warping
            ds = gdal.Warp(final_path, in_path, **kwargs)
            ds = None

            # If nodata value in warp is nan, replace with 0
            in_raster = RASTER(in_path)
            if in_raster.nodata and math.isnan(in_raster.nodata):
                final_raster = RASTER(final_path)
                final_raster.get_array()
                final_ar = final_raster.array.copy()
                final_ar[final_ar == base_raster.nodata] = 0
                save_array(final_raster.bd, final_ar)
                final_raster.close()
            in_raster.close()

            # If it's hab/pixel, transform to population density
            # dividing array by km2 area
            if scoring_method in ('pop_scores', 'pop_scores_Fcbk'):
                final_raster = RASTER(final_path)
                final_raster.get_array()
                final_ar = final_raster.array.copy()
                xres = abs(final_raster.resX) / 1000
                yres = abs(final_raster.resY) / 1000
                area = xres * yres
                final_ar = final_ar / area
                save_array(final_raster.bd, final_ar)
                final_raster.close()

            # Closing base raster
            base_raster.close()

        else:
            # Adding raster to list of rasters to return
            new_in_paths.append(in_path)
            print(f'            {layer} already prepared')

    if raster_list:
        return new_in_paths

def save_array(bd, array):
    """ Saves an array into a band and computes statistics. """
    bd.WriteArray(array)
    bd.ComputeStatistics(0)


def scores_to_0(value):
    """ Used for changing arrays to 0 values. """
    return 0


def reproject_shapefile(in_path, out_path, layer, settings):
    """
    Reprojects a shapefile to match the coordinate system of the base layer.
    As defined here:
        https://pcjericks.github.io/py-gdalogr-cookbook/projection.html

    Parameters
    ----------
    in_path : path to shapefile to reproject.
    out_path : path to new reprojected shapefile.
    layer : name of the layer
    settings : general settings from GENERAL_SETTINGS class.

    Returns
    -------
    None.

    """

    print('            Copying/Reprojecting ' + layer)

    # Search for pressure layer if exists
    out_exists = os.path.isfile(out_path)

    # Continue if does not exist
    if not out_exists:

        # Get pressure vector to copy/reproject
        pressure_vector = VECTOR(in_path)
        pressure_layer = pressure_vector.layer

        # Compare coordinate systems
        out_crs = settings.crs
        out_crs_authority = out_crs.GetAttrValue('AUTHORITY', 1)
        reprojTF = (out_crs_authority != pressure_vector.crs_authority)

        # create the CoordinateTransformation
        coordTrans = osr.CoordinateTransformation(pressure_vector.crs, out_crs)

        # Create output shapefile
        projected_ds = pressure_vector.driver.CreateDataSource(out_path)
        geom_type = pressure_vector.geom_type
        outLayer = projected_ds.CreateLayer(layer, geom_type=geom_type)

        # add fields
        inLayerDefn = pressure_vector.defn
        for i in range(0, inLayerDefn.GetFieldCount()):
            fieldDefn = inLayerDefn.GetFieldDefn(i)
            outLayer.CreateField(fieldDefn)

        # get the output layer's feature definition
        outLayerDefn = outLayer.GetLayerDefn()

        # loop through the input features
        inFeature = pressure_layer.GetNextFeature()
        while inFeature:
            # get the input geometry
            geom = inFeature.GetGeometryRef()
            if geom:
                # reproject the geometry if necessary
                if reprojTF:
                    # reproject
                    geom.Transform(coordTrans)
                # create a new feature
                outFeature = ogr.Feature(outLayerDefn)
                # set the geometry and attribute
                outFeature.SetGeometry(geom)
                for i in range(0, outLayerDefn.GetFieldCount()):
                    val = inFeature.GetField(i)
                    if isinstance(val, str):
                        val = val.encode("ascii", "ignore")
                        val = val.decode("utf-8", "ignore")
                    if isinstance(val, numbers.Number):
                        val = np.round(val, 2)
                    try:
                        outFeature.SetField(
                            outLayerDefn.GetFieldDefn(i).GetNameRef(), val)
                    except:
                        outFeature.SetField(
                            outLayerDefn.GetFieldDefn(i).GetNameRef(),
                            'Check_values')
                # add the feature to the shapefile
                outLayer.CreateFeature(outFeature)
                # dereference the features and get the next input feature
                outFeature = None
            inFeature = pressure_layer.GetNextFeature()

        # Save and close the shapefiles
        inDataSet = None
        outDataSet = None

        # Create prj file for assigning the projection
        out_crs.MorphToESRI()
        prj_path = out_path[:-4] + '.prj'
        file = open(prj_path, 'w')
        file.write(out_crs.ExportToWkt())
        file.close()

    else:
        print(f'               {layer} was already reprojected')


def clip_shapefile(in_path, out_path, layer, settings):
    """
    Clips vector layer to the study area.

    Parameters
    ----------
    in_path : path to shapefile to clip.
    out_path : path to new clipped shapefile.
    layer : name of the layer
    settings : general settings from GENERAL_SETTINGS class.

    Returns
    -------
    None.

    """

    print('            Clipping ' + layer)

    # Search for pressure layer if exists
    out_exists = os.path.isfile(out_path)

    # Continue if does not exist
    if not out_exists:

        # Set up driver and spatial reference
        projected_vector = VECTOR(in_path)
        projected_layer = projected_vector.layer
        projected_geom_type = projected_vector.geom_type
        driver = projected_vector.driver
        crs = settings.crs

        # Open study area polygon
        extent_path = settings.extent_Polygon
        extent_vector = VECTOR(extent_path)
        extent_layer = extent_vector.layer

        # Create clipped vector dataset
        outDataSource = driver.CreateDataSource(out_path)
        outLayer = outDataSource.CreateLayer(layer, srs=crs,
                                              geom_type=projected_geom_type)

        # Clip vector with study area polygon
        ogr.Layer.Clip(projected_layer, extent_layer, outLayer)

        # Close datasets
        outLayer = None
        projected_vector.close()
        extent_vector.close()

    else:
        print(f'               {layer} was already clipped')


def rasterize_shapefile(in_path, out_path, layer, settings, base_path):
    """
    Burns a shapefile into a raster (rasterize).
    If Field is specified in layer settings, it burns a categorical value.

    Parameters
    ----------
    in_path : path to shapefile to rasterize.
    out_path : path to new raster.
    layer : name of the layer
    settings : general settings from GENERAL_SETTINGS class.
    base_path : path to base raster.

    Returns
    -------
    None.

    """

    print('            Rasterizing ' + layer)

    # Search for pressure layer if exists
    out_exists = os.path.isfile(out_path)

    # Continue if does not exist
    if not out_exists:

        # Vector layer as a raster
        clipped_vector = VECTOR(in_path)
        clipped_layer = clipped_vector.layer

        # Get field for rasterizing
        try:
            field = layers_settings[layer]['cat_field']
        except KeyError:
            field = None

        # Is field exists, check if it'a string field
        field_is_string = False
        if field:
            for i in clipped_vector.schema:
                if i.GetName() == field:
                    field_type = (i.GetFieldTypeName(i.GetType()))
                    if field_type == 'String':
                        field_is_string = True

        # If field is string, translate to numbers in a new field
        if field_is_string:

            # Import scoring methods to assign an integer to land use categories
            scoring_method = layers_settings[layer]['scoring']
            scores_full = getattr(HF_scores, settings.scoring_template)
            scores = scores_full[scoring_method]

            # Create new field
            field_name = ogr.FieldDefn('Use_int', ogr.OFTInteger)
            clipped_layer.CreateField(field_name)

            # Create new list of strings to compare, encoded and decoded again
            new_scores = scores['scores_by_categories'].copy()
            for topic in new_scores:
                for val in scores['scores_by_categories'][topic][1]:
                    val = val.encode("ascii", "ignore")
                    val = val.decode("utf-8", "ignore")

            # Populate new field translating string to number categories
            # loop through the input features
            inFeature = clipped_layer.GetNextFeature()
            while inFeature:
                value_int = None
                value_str = inFeature.GetField(field)
                for topic in scores['scores_by_categories']:
                    if value_str in scores['scores_by_categories'][topic][1]:
                        value_int = scores['scores_by_categories'][topic][0]

                # Silly value to catch missing values
                if value_int is None:
                    print(f'Problem string {value_str}')
                    value_int = 999
                inFeature.SetField('Use_int', value_int)
                clipped_layer.SetFeature(inFeature)
                inFeature = clipped_layer.GetNextFeature()

        # Create a copy of base raster
        drv = gdal.GetDriverByName('GTiff')
        base_raster = RASTER(base_path)
        rasterized_template = drv.CreateCopy(out_path,
                                              base_raster.ds, strict=0)
        rasterized_template = None
        base_raster.close()

        # Define function for converting an array to 0s
        zero_func = np.vectorize(scores_to_0)

        # Convert clipped raster's values to 0s and save
        rasterized_raster = RASTER(out_path)
        rasterized_raster.get_array()
        rasterized_array = rasterized_raster.array
        rasterized_zeros_array = zero_func(rasterized_array)
        rasterized_raster.bd.WriteArray(rasterized_zeros_array)
        rasterized_raster.close()

        # Rasterize vector layer to template raster
        rasterized_raster = RASTER(out_path)
        if field:
            gdal.RasterizeLayer(rasterized_raster.ds,
                                [1], clipped_layer,
                                options=["ATTRIBUTE=Use_int"])
        else:
            gdal.RasterizeLayer(rasterized_raster.ds, [1], clipped_layer,
                                None, None,  # transformation info not needed
                                [1],  # value to burn
                                ['ALL_TOUCHED=TRUE']  # burn all pixels touched
                                )

        # Close everything
        rasterized_raster.close()
        clipped_vector.close()

    else:
        print(f'               {layer} was already rasterized')


def proximity_raster(in_path, out_path, layer=''):
    """
    Creates a proximity raster form a rasterized shapefile.
    Returns values in meters.

    Parameters
    ----------
    in_path : path to rasterized layer.
    out_path : path to new proximity raster.
    layer : TYPE, optional
        Name of the layer. The default is ''.

    Returns
    -------
    None.

    """

    print('            Creating proximity raster ' + layer)

    # Search for pressure layer if exists
    out_exists = os.path.isfile(out_path)

    # Continue if does not exist
    if not out_exists:

        # Proximity raster path
        rasterized_raster = RASTER(in_path)
        rasterized_bd = rasterized_raster.bd

        # Create proximity raster and open a band
        drv = gdal.GetDriverByName('GTiff')
        proximity_ds = drv.Create(out_path,
                                  rasterized_raster.XSize,
                                  rasterized_raster.YSize,
                                  1, gdal.GetDataTypeByName('Int32'))
        proximity_ds.SetGeoTransform(rasterized_raster.geotrans)
        proximity_ds.SetProjection(rasterized_raster.projref)
        proximity_bd = proximity_ds.GetRasterBand(1)

        # Compute proximity raster
        gdal.ComputeProximity(rasterized_bd, proximity_bd, ['DISTUNITS=GEO'])

        # Close rasters
        proximity_bd.ComputeStatistics(0)
        proximity_ds = None
        rasterized_raster.close()

    else:
        print(f'               {layer} proximity raster existed already')


def create_proximity_raster(layer, settings, base_path, final_path,
                            scoring_template, main_folder, res):
    """
    Controls the process of creating a proximity raster.
    It will reproject, clip, rasterize and create the proximity raster.

    Parameters
    ----------
    layer : Layer name of the pressure/dataset to prepare
    settings : general settings from GENERAL_SETTINGS class.
    base_path : path to base raster.
    final_path : path for proximity raster.
    scoring_template : Name of the scoring template from HF_scores. E.g. 'GHF'.
    main_folder : Name of folder in root for all analysis.

    Returns
    -------
    None.

    """
    # Search for pressure layer if exists
    in_path = f'{main_folder}{layers_settings[layer]["path"][0]}'
    extent = settings.extent_Polygon
    extent_str = extent.split('/')[-1].split('.')[-2]
    out_path = in_path
    final_exists = os.path.isfile(final_path)

    if not final_exists:

        # Reproject shapefile
        out_path = f'{main_folder}/HF_maps/b03_Prepared_pressures/{layer}_original_extent_proj.shp'
        reproject_shapefile(in_path, out_path, layer, settings)

        # Clip shapefile
        if settings.clip_by_Polygon:
            in_path = out_path
            out_path = f'{main_folder}/HF_maps/b03_Prepared_pressures/{layer}_{extent_str}_clip.shp'
            clip_shapefile(in_path, out_path, layer, settings)

        # Rasterize reprojected and clipped shapefile
        in_path = out_path
        out_path = f'{main_folder}/HF_maps/b03_Prepared_pressures/{layer}_{extent_str}_{res}m_rasterized.tif'
        rasterize_shapefile(in_path, out_path, layer, settings, base_path)

        # Create proximity raster
        in_path = out_path
        out_path = final_path
        proximity_raster(in_path, out_path, layer=layer)

    else:
        print(f'            {layer} already prepared')


def create_categorical_raster(layer, settings, base_path, final_path, main_folder, scoring_template):
    """
    Controls the process of creating a categorical raster.
    It will reproject, clip and rasterize.

    Parameters
    ----------
    layer : Layer name of the pressure/dataset to prepare
    settings : general settings from GENERAL_SETTINGS class.
    base_path : path to base raster.
    final_path : path for proximity raster.
    main_folder : Name of folder in root for all analysis.
    scoring_template : Name of the scoring template from HF_scores. E.g. 'GHF'.

    Returns
    -------
    None.

    """
    # Prepare in and out names
    in_path = f'{main_folder}{layers_settings[layer]["path"][0]}'
    extent = settings.extent_Polygon
    extent_str = extent.split('/')[-1].split('.')[-2]
    out_path = in_path

    # Search for pressure layer if exists
    final_exists = os.path.isfile(final_path)
    if not final_exists:

        # Reproject shapefile
        out_path = f'{main_folder}HF_maps/b03_Prepared_pressures/{layer}_{scoring_template}_original_extent_proj.shp'
        reproject_shapefile(in_path, out_path, layer, settings)

        # Clip shapefile
        if settings.clip_by_Polygon:
            in_path = out_path
            out_path = f'{main_folder}HF_maps/b03_Prepared_pressures/{layer}_{scoring_template}_{extent_str}_clip.shp'
            clip_shapefile(in_path, out_path, layer, settings)

        # Rasterize reprojected and clipped shapefile
        in_path = out_path
        out_path = final_path
        rasterize_shapefile(in_path, out_path, layer, settings, base_path)

    else:
        print(f'            {layer} already prepared')


def pixels_rivers_func(travel, maxdist):
    """ Returns 1 if value is smaller than maxdist. """
    if 0 < travel <= maxdist:
        return 1
    else:
        return 0


def close_pixels_func(close, settl, dist):
    """ Returns -1 if close == 1 and settl <= dist """
    if close == 1 and settl <= dist:
        return -1
    else:
        return 0


def change_value(array):
    """ Return -1 if value == 1, if not returns 0 """
    if array == 1:
        return -1
    else:
        return 0


def convert_0_1(array):
    """ converts positive values to 1, and the rest will be 0.
    100 value used just in case there's a numeric nodata value.
    """
    if 0 < array < 100:
        return 1
    else:
        return 0


def grow_distance_rivers(rows, cols, distnavigable, diredist, diagdist,
                          close_array, river_array, travel_array):
    """ Propagates the distance in a raster of enabled pixels. """
    # Create an array for tracking searched pixels
    # Already considered pixels will be -2
    track_array = copy.deepcopy(river_array)

    for row in range(0, rows):
        for col in range(0, cols):
            if (track_array[row, col] != -2) and (close_array[row, col] == -1):

                # Start a new cluster of pixels
                travel_array[row][col] = 1
                cluster = [(row, col)]

                # Add pixel to searched
                track_array[row, col] = -2

                # Start growing cluster
                while cluster:

                    # Get neighbour pixels that are river and
                    # have not received a distance as value
                    reviewed_list = {}
                    for old_neighb in cluster:
                        i = old_neighb[0]
                        j = old_neighb[1]
                        cond2 = travel_array[i, j] < distnavigable

                        # Check if pixel is under max distance
                        if cond2:
                            reviewed_list[old_neighb] = {}

                            neighbs = {(i + 1, j): 'direct',
                                        (i - 1, j): 'direct',
                                        (i, j + 1): 'direct',
                                        (i, j - 1): 'direct',
                                        (i + 1, j + 1): 'diagonal',
                                        (i + 1, j - 1): 'diagonal',
                                        (i - 1, j + 1): 'diagonal',
                                        (i - 1, j - 1): 'diagonal', }

                            for n in neighbs:
                                # Condition 1: it has to be river
                                try:
                                    cond1 = river_array[n[0], n[1]] == 1
                                    cond3 = track_array[n[0], n[1]] != -2
                                except IndexError:
                                    cond1 = False
                                    cond3 = False
                                # Condition 3: it should be a new pixel in track_array
                                if cond1 and cond3:
                                    reviewed_list[old_neighb][n] = neighbs[n]

                    # Loop through pixels to assign new distance as value
                    for neigh in reviewed_list:
                        for pixel in reviewed_list[neigh]:
                            i, j = pixel[0], pixel[1]

                            # Add pixel to searched pixels
                            track_array[i, j] = -2

                            # If pixel is close to settlements,
                            # distance is 1
                            if close_array[i][j] == -1:
                                travel_array[i][j] = 1

                            else:
                                # Get distance to add according to
                                # location of the pixel, direct or
                                # diagonal
                                if reviewed_list[neigh][pixel] == 'direct':
                                    dist = diredist
                                elif reviewed_list[neigh][pixel] == 'diagonal':
                                    dist = diagdist

                                # change new value if necessary
                                i2, j2 = neigh[0], neigh[1]
                                original = travel_array[i2][j2]
                                olddist = travel_array[i][j]
                                newdist = original + dist
                                if olddist == -1:
                                    if original == 1:
                                        travel_array[i][j] = dist
                                    else:
                                        travel_array[i][j] = newdist
                                elif olddist > newdist:
                                    travel_array[i][j] = newdist

                    # Change cluster for a new group of pixels
                    cluster = []
                    for neigh in reviewed_list:
                        for pixel in reviewed_list[neigh]:
                            if pixel not in cluster:
                                cluster.append(pixel)

    return travel_array


def create_proximity_raster_from_pixels(layer, year, settings, base_path,
                                        final_path, scoring_template, purpose,
                                        results_folder, main_folder, res):
    """
    Controls the creation of a raster of proximity from human influenced
    sections of rivers.
    It consideres built environments as starting points. Built environments
    have a maximum distance to rivers.
    It propagates the distance from this contact points up and dowm, up to a
    maximum distance.
    It creates a proximity raster from these sections of human influenced
    rivers.
    """


    # Prepare in and out names
    in_path_rivers = f"{main_folder}{layers_settings[layer]['path'][0]}"
    extent = settings.extent_Polygon
    extent_str = extent.split('/')[-1].split('.')[-2]
    template = getattr(HF_scores, settings.scoring_template)
    scoring_method_template = template['river_scores']
    distsettlements = scoring_method_template['sett_dist']
    distnavigable = scoring_method_template['navi_dist']
    out_path = in_path_rivers

    # Search for pressure layer if exists
    final_exists = os.path.isfile(final_path)
    if not final_exists:

        ## Rasterize rivers, 1 or 0

        # Reproject shapefile
        out_path = f'{main_folder}HF_maps/b03_Prepared_pressures/{layer}_original_extent_proj.shp'
        reproject_shapefile(in_path_rivers, out_path, layer, settings)

        # # Clip shapefile
        if settings.clip_by_Polygon:
            in_path = out_path
            out_path = f'{main_folder}HF_maps/b03_Prepared_pressures/{layer}_{extent_str}_clip.shp'
            clip_shapefile(in_path, out_path, layer, settings)

        # Rasterize reprojected and clipped shapefile
        in_path = out_path
        out_path = f'{main_folder}HF_maps/b03_Prepared_pressures/{layer}_{extent_str}_{res}m_rasterized.tif'
        rasterize_shapefile(in_path, out_path, layer, settings, base_path)
        rivers_rasterized_path = out_path

        ## Detect pixels under 4 km of settlements

        # Convert values to 1 if any value or 0
        built_0_1_path = f'{main_folder}HF_maps/b03_Prepared_pressures/{layer}_built_0_1_{year}_{extent_str}_{scoring_template}_{res}m.tif'

        # Create a copy of base raster
        drv = gdal.GetDriverByName('GTiff')
        base_raster = RASTER(base_path)
        built_0_1 = drv.CreateCopy(built_0_1_path, base_raster.ds, strict=0)
        built_0_1 = None
        base_raster.close()

        # Define function for converting an array
        zero_func = np.vectorize(convert_0_1)

        # Convert built raster's values to 1 or 0
        built_path = f'{results_folder}/p_Built_Environments_{year}_{extent_str}_{scoring_template}_{res}m.tif'
        built_raster = RASTER(built_path)
        built_raster.get_array()
        built_array = built_raster.array
        results_array = zero_func(built_array)
        built_raster.close()

        # Save to raster
        built_0_1_raster = RASTER(built_0_1_path)
        built_0_1_raster.bd.WriteArray(results_array)
        built_0_1_raster.close()

        # Create proximity raster to settlements
        proximity_built_path = f'{main_folder}HF_maps/b03_Prepared_pressures/{layer}_built_proximity_{year}_{extent_str}_{scoring_template}_{res}m.tif'
        proximity_raster(built_0_1_path, proximity_built_path)

        # Create raster of river pixels close to settlements

        # Check if it was already created
        close_path = f'{main_folder}HF_maps/b03_Prepared_pressures/{layer}_close_pixels_{year}_{extent_str}_{scoring_template}_{res}m.tif'
        close_exists = os.path.isfile(close_path)
        if not close_exists:
            # Create a copy of base raster
            drv = gdal.GetDriverByName('GTiff')
            base_raster = RASTER(base_path)
            close_pixels = drv.CreateCopy(close_path, base_raster.ds, strict=0)
            close_pixels = None
            base_raster.close()

            # Define function for converting an array
            zero_func = np.vectorize(close_pixels_func)

            # Convert clipped raster's values to -1 or 0
            # according to distance to rivers
            settl_raster = RASTER(proximity_built_path)
            settl_raster.get_array()
            settl_array = settl_raster.array
            river_raster = RASTER(rivers_rasterized_path)
            river_raster.get_array()
            river_array = river_raster.array
            results_array = zero_func(river_array, settl_array, distsettlements)
            settl_raster.close()
            river_raster.close()

            # Save to raster
            close_raster = RASTER(close_path)
            close_raster.bd.WriteArray(results_array)
            close_raster.close()

        # Grow distance from settlement pixels
        # Function similar to grass function grow

        # Check if it was already created
        travel_path = f'{main_folder}HF_maps/b03_Prepared_pressures/{layer}_travel_{year}_{extent_str}_{scoring_template}_{res}m.tif'
        travel_exists = os.path.isfile(travel_path)
        if not travel_exists:
            print('            Detecting navigable pixels')

            # Open rasters and settings
            close_raster = RASTER(close_path)
            close_raster.get_array()
            close_array = close_raster.array
            river_raster = RASTER(rivers_rasterized_path)

            rows = river_raster.YSize - 1
            cols = river_raster.XSize - 1
            xdist = river_raster.resX
            ydist = river_raster.resY
            diredist = (xdist + ydist) / 2
            diagdist = sqrt((xdist * xdist) + (ydist * ydist))

            # Create raster for new distance values
            Float = False
            copy_raster(travel_path, river_raster, Float)
            travel_raster = RASTER(travel_path)
            travel_raster.get_array()
            travel_array = travel_raster.array

            # Change values to -1 and save
            change_func = np.vectorize(change_value)
            results_array = change_func(travel_array)
            travel_raster.bd.WriteArray(results_array)
            travel_raster.close()

            # Detect clusters of pixels in rivers close to settlements, and
            # grow distance from there until maxdist
            travel_raster = RASTER(travel_path)
            travel_raster.get_array()
            travel_array = travel_raster.array

            # Vectorize and call function to grow distance
            # neighb_func = np.vectorize(neighb_pixels)
            river_raster.get_array()
            river_array = river_raster.array
            results_array = grow_distance_rivers(rows, cols, distnavigable,
                                                  diredist, diagdist,
                                                  close_array, river_array, travel_array)

            # Close and save
            travel_raster.bd.WriteArray(results_array)
            travel_raster.close()

            # Convert to 0 and 1

            # Create a copy
            travel_raster = RASTER(travel_path)
            navigable_path = f'{main_folder}HF_maps/b03_Prepared_pressures/{layer}_navigable_{year}_{extent_str}_{scoring_template}_{res}m.tif'
            Float = False
            copy_raster(navigable_path, travel_raster, Float)

            # Define function for converting an array
            zero_func = np.vectorize(pixels_rivers_func)

            # Convert clipped raster's values to 1 or 0
            travel_raster.get_array()
            travel_array = travel_raster.array
            results_array = zero_func(travel_array, distnavigable)

            # Save to raster
            navi_raster = RASTER(navigable_path)
            navi_raster.bd.WriteArray(results_array)
            navi_raster.close()
            travel_raster.close()

            # Create proximity raster from navigable waterways
            proximity_raster(navigable_path, final_path, layer=layer)

            # Close everything
            close_raster.close()
            river_raster.close()

        else:
            print('            Navigable pixels already prepared')

    else:
        print(f'            {layer} already prepared')


def combineRasters(pressure, year, layers, settings, base_path, purpose, res,
                    scoring_template, results_folder, main_folder, remove_aux):
    """
    Takes all datasets of a pressure and combines them by maximum value.

    Parameters
    ----------
    pressure : Name of the pressure.
    year : year of HF map.
    layers : datasets to be combined.
    settings : general settings from GENERAL_SETTINGS class.
    base_path : path to base raster.
    purpose : Purpose of the Human footprint maps. Will match purpose_layers
        in Class GENERAL_SETTINGS.
    scoring_template : Name of the scoring template from HF_scores. E.g. 'GHF'.
    results_folder : Folder in root for all results.
    main_folder : Name of folder in root for all analysis.
    remove_aux : False to keep auxiliary layers produced.

    Returns
    -------
    None.

    """
    print()
    print(f'      Combining {pressure} {year}')

    num = 0

    for layer in layers:

        # Get path of scored layer and of copy in results folder
        extent = settings.extent_Polygon
        extent_str = extent.split('/')[-1].split('.')[-2]
        press_path = f'{main_folder}HF_maps/b04_Scored_pressures/{layer}_{year}_{extent_str}_{scoring_template}_{res}m_scored.tif'

        # Create copy of scored pressure in results folder
        # press_raster = raster(press_path)

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
        added_path_uncomp = f'{results_folder}/p_{pressure}_{year}_{extent_str}_{scoring_template}_{res}m_uncomp.tif'
        added_path = f'{results_folder}/p_{pressure}_{year}_{extent_str}_{scoring_template}_{res}m.tif'

        press_raster = RASTER(fn1)
        createRasterFromCopy(added_path_uncomp, press_raster.ds, datout)
        press_raster.close()

        # Compress result and delete previous version
        compress(added_path_uncomp, added_path)
        if remove_aux:
            os.remove(added_path_uncomp)


def addRasters(year, settings, results_folder, purpose, scoring_template,
               remove_aux, res):
    """
    Adds pressure maps to the final HF map for a given year.

    Parameters
    ----------
    year : year of HF map.
    settings : general settings from GENERAL_SETTINGS class.
    results_folder : Folder in root for all results.
    purpose : Purpose of the Human footprint maps. Will match purpose_layers
        in Class GENERAL_SETTINGS.
    scoring_template : Name of the scoring template from HF_scores. E.g. 'GHF'.
    remove_aux : False to keep auxiliary layers produced.

    Returns
    -------
    None.

    """

    print('   Adding pressures')

    num = 0
    for pressure in settings.purpose_layers[purpose]['pressures']:

        # Continue if there are layers in pressures
        if settings.purpose_layers[purpose]['pressures'][pressure]:

            # Get path of scored layer and of copy in results folder
            extent = settings.extent_Polygon
            extent_str = extent.split('/')[-1].split('.')[-2]
            press_path = f'{results_folder}/p_{pressure}_{year}_{extent_str}_{scoring_template}_{res}m.tif'

            # # Create copy of scored pressure in results folder
            press_raster = RASTER(press_path)

            # Get pressure raster array masked by NoData value
            nodata = press_raster.nodata
            press_raster.get_array()
            press_array = np.ma.masked_equal(press_raster.array, nodata)

            # Create and add pressures to final map
            if num != 0:
                datout = datout + press_array

            else:
                datout = press_array
                fn1 = press_path

            # Close pressure raster
            press_raster.close()

            # Add 1 to num
            num += 1

    # Create the raster of added pressures if at least one topic was processed
    if num > 0:
        country = settings.country
        added_path = f'{results_folder}/HF_{country}_{year}_{scoring_template}_{res}m.tif'
        added_path_uncomp = f'{results_folder}/HF_{country}_{year}_{scoring_template}_{res}m_uncomp.tif'
        press_raster = RASTER(fn1)
        copy_raster(added_path_uncomp, press_raster, Float=True, array=datout)
        press_raster.close()

        # Compress result and delete previous version
        compress(added_path_uncomp, added_path)
        if remove_aux:
            os.remove(added_path_uncomp)


def eliminate_area(target, patch):
    """Vectorized numpy function. Changes to 0 if patch is 1"""
    if patch != 1:
        return target
    else:
        return 0


def patch_other_raster(target, patch, values):
    """Vectorized numpy function. Returns value if patch is 1"""
    if patch != 1:
        return target
    else:
        return values


def patch_raster_function(patch_type, target, patch, values=None):
    """Controls type of patching"""

    # Define function to assign scores according to scoring method
    if patch_type == 'eliminate':
        vecfunc = np.vectorize(eliminate_area)
        new_array = vecfunc(target, patch)
    if patch_type == 'replace':
        vecfunc = np.vectorize(patch_other_raster)
        new_array = vecfunc(target, patch, values)

    return new_array


def patch(layer, target_path, shapefile_path, base_path,
          patch_type='eliminate_area', values_path=None):
    """
    Patch a raster if problematic areas exist.
    Can eliminate areas (changing them to 0) or changing to values from
    another raster.
    """

    # Name
    patch_path = shapefile_path[:-4] + '.tif'

    # Create patch raster: raster where values will indicate where to change
    rasterize_shapefile(shapefile_path, patch_path, 'patch layer', None, base_path)

    # Open necessary arrays
    target_raster = RASTER(target_path)
    target_raster.get_array()
    target_array = target_raster.array
    patch_raster = RASTER(patch_path)
    patch_raster.get_array()
    patch_array = patch_raster.array
    values_array = None
    if values_path:
        values_raster = RASTER(values_path)
        values_raster.get_array()
        values_array = values_raster.array

    # Run patching eliminate
    new_array = patch_raster_function(patch_type, target_array, patch_array, values=values_array)

    # Copy new array to scores raster and save
    target_bd = target_raster.bd
    target_bd.WriteArray(new_array)
    target_bd.ComputeStatistics(0)

    # Close rasters
    target_raster.close()
    patch_raster.close()
    if values_path:
        values_raster.close()
