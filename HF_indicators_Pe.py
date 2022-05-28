# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 16:10:35 2021

@author: aragon

Within each country, shapefiles should have the same projection
Shapefiles should not have empty geometry features
Explode buffers, does not work with only one feature

"""

import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib
# from HF_spatial import zonal_stats
from matplotlib.patches import Rectangle
import matplotlib.lines as mlines
# from pylab import *
from osgeo import gdal, ogr#, osr


def zonal_stats(HF_path, polygons_path, categories, stats, nh_thres):
    'https://towardsdatascience.com/zonal-statistics-algorithm-with-python-in-4-steps-382a3b66648a'
    'https://www.youtube.com/watch?v=q2nR3PZnh7s'

    def boundingBoxToOffsets(bbox, geot):
        '''Convert the coordinates of the bounding box of polygons to cell coordinates'''
        col1 = int((bbox[0] - geot[0]) / geot[1])
        col2 = int((bbox[1] - geot[0]) / geot[1]) + 1
        row1 = int((bbox[3] - geot[3]) / geot[5])
        row2 = int((bbox[2] - geot[3]) / geot[5]) + 1
        return [row1, row2, col1, col2]

    def geotFromOffsets(row_offset, col_offset, geot):
        '''Create new Geotranform'''
        new_geot = [
            geot[0] + (col_offset * geot[1]),
            geot[1],
            0.0,
            geot[3] + (row_offset * geot[5]),
            0.0,
            geot[5]
        ]
        return new_geot

    # Create temporary raster and vector layers
    mem_driver = ogr.GetDriverByName("Memory")
    mem_driver_gdal = gdal.GetDriverByName("MEM")
    shp_name = "temp"

    r_ds = gdal.Open(HF_path)
    p_ds = ogr.Open(polygons_path)

    lyr = p_ds.GetLayer()
    geot = r_ds.GetGeoTransform()
    nodata = r_ds.GetRasterBand(1).GetNoDataValue()

    zstats = []

    p_feat = lyr.GetNextFeature()

    while p_feat:
        if p_feat.GetGeometryRef() is not None:

            # Read values from fields of categories
            cat_values_list = []

            for cat in categories:
                # Read cat values
                val = p_feat.GetField(cat)

                # Encoding needed to avoid unicode errors
                if isinstance(val, str):
                    # val = val.encode("ascii", "replace")
                    val = val.encode("ascii", "ignore")
                    val = val.decode("utf-8", "ignore")

                # Append to cat_values_list
                cat_values_list.append(val)

            # delete temporary raster if it already exists
            if os.path.exists(shp_name):
                mem_driver.DeleteDataSource(shp_name)

            # create a new, empty raster in memory
            tp_ds = mem_driver.CreateDataSource(shp_name)

            # create a temporary polygon layer
            tp_lyr = tp_ds.CreateLayer('polygons', None, ogr.wkbPolygon)

            # copy the current feature to the temporary polygon layer
            tp_lyr.CreateFeature(p_feat.Clone())

            # get the bounding box of the polygon feature and convert the coordinates to cell offsets
            offsets = boundingBoxToOffsets(p_feat.GetGeometryRef().GetEnvelope(), geot)

            # calculate the new geotransform for the polygonized raster
            new_geot = geotFromOffsets(offsets[0], offsets[2], geot)

            # create the raster for the rasterized polygon in memory
            tr_ds = mem_driver_gdal.Create(
                "",
                offsets[3] - offsets[2],
                offsets[1] - offsets[0],
                1,
                gdal.GDT_Byte)

            # set the geotransfrom the rasterized polygon
            tr_ds.SetGeoTransform(new_geot)

            # rasterize the polygon feature
            # gdal.RasterizeLayer(tr_ds, [1], tp_lyr, burn_values=[1])
            gdal.RasterizeLayer(tr_ds, [1], tp_lyr,
                                None, None,  # transformation info not needed
                                burn_values=[1],
                                options=['ALL_TOUCHED=FALSE'])
                                # options=['ALL_TOUCHED=TRUE'])

            # read data from the rasterized polygon
            tr_array = tr_ds.ReadAsArray()

            # read data from the input raster that corresponds to the location of the rasterized polygon
            r_array = r_ds.GetRasterBand(1).ReadAsArray(
                offsets[2],
                offsets[0],
                offsets[3] - offsets[2],
                offsets[1] - offsets[0])

            # get the ID of the polygon feature, you can use a different attribute field
            id = p_feat.GetFID()

            # print(id)
            # if id == 1:
            #     print('wait')

            if r_array is not None:

                # Mask input data to polygon zones
                maskarray = np.ma.MaskedArray(r_array,
                                              mask=np.logical_or(r_array == nodata, np.logical_not(tr_array)))

                # Calculate values
                if maskarray is not None:
                    stats_dict = {}
                    if "id" in stats:
                        stats_dict["id"] = id
                    if "min" in stats:
                        stats_dict["min"] = maskarray.filled(0).min()
                    if "max" in stats:
                        stats_dict["max"] = maskarray.filled(0).max()
                    if "mean" in stats:
                        stats_dict["mean"] = np.nanmean(maskarray)
                        # stats_dict["mean"] = maskarray.filled(0).mean()
                        # TODO np.nanmean(arr)) this one ignores nan values
                    if "median" in stats:
                        stats_dict["median"] = np.ma.median(maskarray.filled(0))
                    if "sd" in stats:
                        stats_dict["sd"] = maskarray.filled(0).std()
                    if "sum" in stats:
                        stats_dict["sum"] = np.nansum(maskarray)
                        # stats_dict["sum"] = maskarray.filled(0).sum()
                    if "count" in stats:
                        stats_dict["count"] = np.sum(~np.isnan(maskarray))
                        # stats_dict["count"] = np.count_nonzero(~np.isnan(maskarray))
                        # stats_dict["count"] = maskarray.count()
                    # pixels under threshold of natural habitat
                    if "nh" in stats:
                        stats_dict["nh"] = np.sum(maskarray.filled(nh_thres + 1) < nh_thres)
                    if "categories" in stats:
                        stats_dict["categories"] = cat_values_list
                    zstats.append(stats_dict)

            tp_lyr = None
            tp_ds = None
            tr_ds = None

            p_feat = lyr.GetNextFeature()

    return zstats if zstats else None


###############################################################################

# main folder
m_folder = os.getcwd() + '/Peru_HH/Indicators//'

# lan = 'En'
lan = 'Sp'
    
years = (
    2012,
    2015,
    2018,
    )


# indicator[1] the extra stats besides id, count, sum, categories
indicators = [
    ('Natural_habitat',['nh']),
    ('Protected_areas',['']),
    ('Around_protected_Areas',['']),
              ]

settings = {
    # Real data or test?
    'ecosystem_settings': 'peru',
    
    # Save results?
    'save_docs': True,
    # 'save_docs': False,
    }

for indicator in indicators:

    if settings['ecosystem_settings'] == 'peru':
        eco = {
        'HF_folder': f'{os.getcwd()}/Peru_HH/HF_maps/b05_HF_maps/Pe_20220526_125158_SDG15//',

        ## Ecosistemas MINAM
        'ecosyst_path': f'{os.getcwd()}/Peru_HH/Indicators/Shps/CobVeg_180615.shp',
        'categories': ['CobVeg2013'], # Categories for calculating statsa
        'forest': ['keep', 'Boscoso', ['Bosque']],
        'natural_not_forest': ['keep', 'Boscoso', ['No Bosque']],
        'anp_path': f'{os.getcwd()}/Peru_HH/Indicators/Shps/ANPNacionalDefinitivas_UTM18S.shp',
        'anp_buffer_path': f'{os.getcwd()}/Peru_HH/Indicators/Shps/ZonasdeAmortiguamiento_UTM_18S.shp',
        'safety_text': '_preliminar',
        'country': 'Peru',
        'res': 300,
        }

    res = eco['res']

    if 'Natural_habitat' == indicator[0]:
        print()
        print('Natural habitat indicator')
        polygons_path = eco['ecosyst_path']
        aggr_dict = {'count': 'sum', 'nh': 'sum', }
        ind_col = 'green'
        if lan == 'Sp':
            title = 'Cambio de Hábitat Natural'
            ylabel = '% Hábitat Natural (HH<4)'
        elif lan == 'En':
            title = 'Natural Habitat change'
            ylabel = '% Natural Habitat (HF<4)'
        deal_forest = eco['natural_not_forest']
        categories = True
        # labels = True
        labels = False
        # remove = True
        rnd = 2
    
    else:
        aggr_dict = {'count': 'sum', 'sum': 'sum', }
        # remove_forest = False
        deal_forest = None
        categories = False
        labels = True
        if lan == 'Sp':
            ylabel = 'Promedio de Huella Humana'
        elif lan == 'En':
            ylabel = 'Human Footprint average'   

        if 'Protected_areas' == indicator[0]:
            print()
            print('Protected areas indicator')
            polygons_path = eco['anp_path']
            ind_col = 'blue'
            if lan == 'Sp':
                title = 'Cambio de Huella Humana en Áreas Protegidas'
            elif lan == 'En':
                title = 'Change of Human Footprint within Protected areas'
            rnd = 4
    
        if 'Around_protected_Areas' == indicator[0]:
            print()
            print('Around protected areas indicator')
            polygons_path = eco['anp_buffer_path']
            ind_col = 'red'
            if lan == 'Sp':
                title = 'Cambio de Huella Humana alrededor de Áreas Protegidas'
            elif lan == 'En':
                title = 'Change of Human Footprint around Protected areas'
            rnd = 2

    # Settings for slicing
    if not categories:
        eco['categories'] = []
    # if remove_forest:
    if deal_forest:
        eco['categories'].append(deal_forest[1])

    # Read or create full csv?
    ##########################
    csv_name_full = m_folder + f'{eco["country"]}_{indicator[0]}_completa{eco["safety_text"]}.csv'
    csv_exists = os.path.isfile(csv_name_full)

    # if csv_exists:
    #     nh_df_years_full = pd.read_csv(csv_name_full)
    if False:
        pass

    else:
        # Settings for calculations
        nh_df_list = []
        nh_thres = 4  # natural habitat < threshold

        # Get stats for each year
        for year in years:

            print(f'   Processing {year}')

            # HF map name
            HF_path = f'{eco["HF_folder"]}HF_{eco["country"]}_{year}_GHF_{res}m.tif'

            # Get_natural_habitat stats
            # Add default stats to list of stats
            stats = indicator[1] + ['id', 'count', 'sum', 'categories']
            nh = zonal_stats(HF_path, polygons_path, eco['categories'], stats, nh_thres)

            # Stats to a dataframe
            nh_df = pd.DataFrame(nh)

            # Unpack categorical values
            nh_df[eco['categories']] =\
                pd.DataFrame(nh_df['categories'].tolist(), index= nh_df.index)

            # Remove field categories
            nh_df.drop('categories', inplace=True, axis=1)

            # Create field for year
            nh_df['year'] = year

            # Add to list of dataframes
            nh_df_list.append(nh_df)

        # Create full dataframe and save
        nh_df_years_full = pd.concat(nh_df_list, ignore_index=True, sort=False)
        
        # Replace values if needed
        dict_replace = {
                        'Herbazal hidroftico': 'Herbazal hidrofítico',
                        'Matorral esclerfilo de montaa montano':'Matorral esclerófilo de montaña montano',
                        'Pramo':'Páramo',
                        'Sabana hidroftica con palmeras':'Sabana hidrofítica con palmeras',
                        'Sabana xrica interandina':'Sabana xérica interandina',
                        'Vegetacin esclerfila de arena blanca':'Vegetación esclerófila de arena blanca',
                        'Bosque de colina baja con castaa': 'Bosque de colina baja con castaña',
                        'Bosque de llanura mendrica': 'Bosque de llanura meándrica',
                        'Bosque de montaa': 'Bosque de montaña',
                        'Bosque de montaa altimontano': 'Bosque de montaña altimontano',
                        'Bosque de montaa basimontano': 'Bosque de montaña basimontano',
                        'Bosque de montaa basimontano con paca': 'Bosque de montaña basimontano con paca',
                        'Bosque de montaa con paca': 'Bosque de montaña con paca',
                        'Bosque de montaa montano': 'Bosque de montaña montano',
                        'Bosque de palmeras de montaa montano': 'Bosque de palmeras de montaña montano',
                        'Bosque de terraza alta con castaa': 'Bosque de terraza alta con castaña',
                        'Bosque de terraza baja con castaa': 'Bosque de terraza baja con castaña',
                        'Bosque relicto mesoandino de conferas': 'Bosque relicto mesoandino de coníferas',
                        'Bosque seco de montaa': 'Bosque seco de montaña',
                        'Bosque seco ribereo': 'Bosque seco ribereño',
                        'Bosque semideciduo de montaa': 'Bosque semideciduo de montaña',
                        'Bosque subhmedo de montaa': 'Bosque subhúmedo de montaña',
                        'Bosque xrico interandino': 'Bosque xérico interandino',
                        }

        if eco['country'] == 'Ecuador' and "ecosistema" in nh_df_years_full:
            nh_df_years_full['ecosistema'].replace(dict_replace, inplace=True)
        elif eco['country'] == 'Peru' and "CobVeg2013" in nh_df_years_full:
            nh_df_years_full['CobVeg2013'].replace(dict_replace, inplace=True)
    
        # Save
        if settings['save_docs']:
            nh_df_years_full.to_csv(csv_name_full, header=True)#, encoding='iso-8859-1')

    # Subset of dataframe, i.e. remove forested ecosystems if needed
    ################################################################
    # If index is to be calculated for a subset, use this and define the subtitle:
    if deal_forest:
        field = nh_df_years_full[deal_forest[1]]
        values = deal_forest[2]
        if deal_forest[0] == 'keep':
            nh_df_years = nh_df_years_full.loc[field.isin(values)]
        elif deal_forest[0] == 'remove':
            nh_df_years = nh_df_years_full.loc[~field.isin(values)]
        
        if lan == 'Sp' and 'Natural_habitat' == indicator[0]:
            subtitle = f'Ecosistemas No Boscosos - {eco["country"]}' + eco['safety_text']
        elif lan == 'En' and 'Natural_habitat' == indicator[0]:
            subtitle = f'Non-forest ecosystems - {eco["country"]}' + eco['safety_text']
        elif lan == 'Sp' and 'Natural_habitat_forest' == indicator[0]:
            subtitle = f'Ecosistemas Boscosos - {eco["country"]}' + eco['safety_text']
        elif lan == 'En' and 'Natural_habitat_forest' == indicator[0]:
            subtitle = f'Forest ecosystems - {eco["country"]}' + eco['safety_text']
    else:
        nh_df_years = nh_df_years_full
        if lan == 'Sp':
            subtitle = f'Ecosistemas terrestres - {eco["country"]}' + eco['safety_text']
        elif lan == 'En':
            subtitle = f'Terrestrial ecosystems - {eco["country"]}' + eco['safety_text']


    # Prepare dataframes for graphs
    ###############################
    #Prepare categories
    if categories:
        eco['categories'].remove(deal_forest[1])  # Not needed anymore
        eco['categories'].append('year')
    else:
        eco['categories'] = 'year'

    # Aggregate dataframes
    nh_df_years = nh_df_years[nh_df_years['count'] != '--']
    nh_aggr_df = nh_df_years.groupby(eco['categories'], as_index=False).agg(aggr_dict)

    # Calculate results for indicator
    if indicator[0] in ('Natural_habitat', 'Natural_habitat_forest'):
        nh_aggr_df['indicator'] = 100 * nh_aggr_df["nh"] / nh_aggr_df['count']
    else:
        nh_aggr_df['indicator'] = np.round(nh_aggr_df["sum"] / nh_aggr_df['count'],5)
        
    print()
    print('Cumulative dataframe')
    print(nh_aggr_df)       
    

    # Create graphs
    ###############
    if categories: # Natural habitat
        
        # Create wide dataframe
        df_wide = nh_aggr_df.pivot('year', eco['categories'][0], 'indicator')
    
        # Set resolution higher than default
        plt.figure(dpi=250)
    
        # Dict colours
        # # colors = np.random.rand(len(df_wide.columns),3)
        # cmap = cm.get_cmap('seismic', len(df_wide.columns))
        # col_dict = dict(zip(df_wide.columns, cmap))

        # Graph of trend from df_nf
        col_dict = {}
        len_ = len(df_wide.columns)
        cmap = matplotlib.cm.get_cmap('tab20')
        
        # Paz
        # cmap = matplotlib.cm.get_cmap('hsv')
        
        for i, col in enumerate(df_wide.columns):
            col_ind = i/len_
            rgba = cmap(col_ind)
            col_dict[col] = rgba
            ax = df_wide[col].plot(marker='o', c=col_dict[col])
 
        # Set limits in years
        lim1 = years[0]
        lim2 = years[-1]
        plt.xlim(lim1 - 0.5, lim2 + 1)

        df_wide.loc['ch'] = None
        for ecos in df_wide.keys():
            if df_wide.loc[lim1][ecos] == 0:
                df_wide.loc['ch'][ecos] = 0
            else:
                df_wide.loc['ch'][ecos] = (df_wide[ecos].loc[lim2] - df_wide.loc[lim1][ecos])/df_wide.loc[lim1][ecos]

        # Sort Dataframe by average
        df_wide = df_wide.sort_values(by=2018, axis=1, ascending=False)
        df_wide = df_wide.dropna(axis=1, how='any')
        
        # https://stackoverflow.com/questions/25830780/tabular-legend-layout-for-matplotlib/25995730
        # create blank rectangle
        extra = Rectangle((0, 0), 1, 1, fc="w", fill=False, edgecolor='none', linewidth=0)
    
        #Create organized list containing all handles for table. Extra represents empty space
        legend_handle = [extra] +\
            [mlines.Line2D([],[],color=col_dict[col]) for col in df_wide.columns] +\
            [extra] * len(df_wide.keys()) * 2 + [extra] * 2
    
        #organize labels for table construction
        if lan == 'Sp':
            legend_labels = [''] + [''] * len(df_wide.keys()) + [r'$\mathbf{Ecosistema}$'] +\
                list(df_wide.keys()) + \
                [r'$\mathbf{Cambio-HN}$'] +\
                    [f'{np.round(100*df_wide.loc["ch"][col], rnd)} %' for col in df_wide.columns]
        elif lan == 'En':
            legend_labels = [''] + [''] * len(df_wide.keys()) + [r'$\mathbf{Ecosystem (Sp)}$'] +\
                list(df_wide.keys()) + \
                [r'$\mathbf{Change-NH}$'] +\
                    [f'{np.round(100*df_wide.loc["ch"][col], rnd)} %' for col in df_wide.columns]
        
        
        #Create legend
        plt.legend(legend_handle, legend_labels, 
              bbox_to_anchor=(1, 1.1),  #loc = 1, \
              ncol = 3, shadow = True, handletextpad = -1.5)

        # Ancillary information
        plt.suptitle(title, fontsize=14)
        plt.title(subtitle, fontsize=12)
        plt.grid(True)
        # # plt.set_cmap('viridis')
        if lan == 'Sp':
            plt.xlabel('Año', fontsize=10)
        elif lan == 'En':
            plt.xlabel('Year', fontsize=10)
        plt.ylabel(ylabel, fontsize=10)

        # Add labels
        if labels:
            for i, col in enumerate(df_wide.columns):
                for x,y in zip(df_wide.index, df_wide[col]):
                    label = np.round(y,rnd)
                    plt.annotate(
                        label, # this is the text
                        (x,y), # this is the point to label
                        textcoords="offset points", # how to position the text
                        xytext=(0,-5), # distance from text to points (x,y)
                        ha='center', # horizontal alignment can be left, right or center
                        fontsize=8,
                        ) 
    
        # #Save graph
        if settings['save_docs']:
            graph_name = f'{eco["country"]}_{indicator[0]}_categorias{eco["safety_text"]}.png'
            plt.savefig(m_folder + graph_name, bbox_inches='tight')
            csv_name_aggr = f'{eco["country"]}_{indicator[0]}_categorias{eco["safety_text"]}.csv'
            nh_aggr_df.to_csv(m_folder + csv_name_aggr, header=True)
    
    else:

        # Set resolution higher than default
        fig = plt.figure(figsize=(6, 6), dpi=250)
        
        # Create graph
        ax = fig.add_subplot()
        ax = plt.plot(nh_aggr_df['year'], nh_aggr_df['indicator'], color=ind_col, marker='o')
    
        # Ancillary information
        plt.suptitle(title, fontsize=14)
        plt.title(subtitle, fontsize=12)
        plt.grid(True)
        # # plt.set_cmap('viridis')
        if lan == 'Sp':
            plt.xlabel('Año', fontsize=10)
        elif lan == 'En':
            plt.xlabel('Year', fontsize=10)
        plt.ylabel(ylabel, fontsize=10)
        
        # Set limits in years
        lim1 = years[0] - 0.5
        lim2 = years[-1] + 1
        plt.xlim(lim1, lim2)
        
        # Include indicator change in graph
        start = nh_aggr_df.loc[nh_aggr_df['year'] == years[0]]['indicator'].get(0)
        end = nh_aggr_df.loc[nh_aggr_df['year'] == years[-1]]['indicator'].get(len(years)-1)
        change = np.round(100 * (end - start) / start, 1)
        if lan == 'Sp':
            change_text = f'Cambio = {"+" if change>0 else ""}{change}%'
            # change_text = f'Cambio = {"+" if change>0 else "-"}{change}%'
        elif lan == 'En':
            change_text = f'Change = {"+" if change>0 else ""}{change}%'
            # change_text = f'Change = {"+" if change>0 else "-"}{change}%'
        plt.text(0.98, 0.02, change_text, transform=plt.gca().transAxes,
                 bbox=dict(boxstyle='square', fc='lightgrey', linewidth=0.1),
                 fontsize=14, ha='right', va='bottom', color='black')

        # Add labels
        if labels:
            for x,y in zip(nh_aggr_df['year'], nh_aggr_df['indicator']):
            
                label = np.round(y,rnd)
            
                plt.annotate(
                    label, # this is the text
                    (x,y), # this is the point to label
                    textcoords="offset points", # how to position the text
                    xytext=(20,0), # distance from text to points (x,y)
                    ha='center', # horizontal alignment can be left, right or center
                    fontsize=8
                              ) 
    
        # #Save graph
        if settings['save_docs']:
            graph_name = f'{eco["country"]}_{indicator[0]}{eco["safety_text"]}.png'
            plt.savefig(m_folder + graph_name, bbox_inches='tight')
            csv_name_aggr = f'{eco["country"]}_{indicator[0]}{eco["safety_text"]}.csv'
            nh_aggr_df.to_csv(m_folder + csv_name_aggr, header=True)

print('\007')
print("------ FIN ------")
