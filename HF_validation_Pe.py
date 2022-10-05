
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# from sklearn.linear_model import LinearRegression
# import seaborn as sns
from osgeo import osr
from HF_spatial import RASTER
import os
from affine import Affine


def get_RMSE(x):
    return np.sqrt(np.average(x))


def calculate_visual_score(vis_path, fields_vis_scores, other_fields,\
                           remove_field, remove_value, keep_field, keep_value, 
                           nrows=None):

    # Read dataframe from Excel
    # ori_df = pd.read_excel(vis_path, nrows=nrows)
    ori_df = pd.read_csv(vis_path, nrows=nrows)
    
    # Validation dataframe
    vdf = ori_df[ori_df.columns.intersection(fields_vis_scores+other_fields)].copy()

    # Remove points from Colombia
    vdf = vdf[vdf[remove_field] != remove_value]
    
    # Remove more if needed
    vdf = vdf[vdf[keep_field] == keep_value]
    vdf = vdf[vdf['Certain'] == 'y']
    
    # Change any nan values to 0
    vdf[fields_vis_scores]=vdf[fields_vis_scores].fillna(0)

    # Recreate the visual score from pressures    
    vdf['Urban2'] = vdf['Urban'] * 2
    vdf['Human dwellings_6'] = vdf['Human dwellings'] * .6
    vdf['Settlements indirect_1'] = vdf['Settlements indirect'] * .1
    vdf['People'] = vdf[['Urban2', 'Human dwellings_6', 'Settlements indirect_1']].max(axis=1)

    vdf['Crops_5'] = vdf['Crops'] * .4
    vdf['Pasture_4'] = vdf['Pasture'] * .4
    vdf['Disturbed vegetation_4'] = vdf['Disturbed vegetation'] * .4
    vdf['Forestry_4'] = vdf['Forestry'] * .4
    vdf['Land_Cover'] = vdf[['Crops_5', 'Pasture_4', 'Disturbed vegetation_4', 'Forestry_4']].max(axis=1)

    vdf['Infrastructure'] = np.where(vdf['Infractructure'] > 0, 3, 0)

    vdf['Navigable waterways_4'] = vdf['Navigable waterways'] * .4
    vdf['Navigable waterways indirect_1'] = vdf['Navigable waterways indirect'] * .1
    vdf['Waterways'] = vdf[['Navigable waterways_4', 'Navigable waterways indirect_1']].max(axis=1)
 
    vdf['roads-paved_8'] = vdf['roads-paved'] * .8
    vdf['roads-unpaved_4'] = vdf['roads-unpaved'] * .4
    vdf['roads-private_2'] = vdf['roads-private'] * .2
    vdf['Railways_8'] = vdf['Railways'] * .8
    vdf['Track_1'] = vdf['Track'] * .1
    vdf['road indirect_1'] = vdf['road indirect'] * .1
    vdf['Roads'] = vdf[['roads-paved_8', 'roads-unpaved_4', 'roads-private_2', 'Railways_8', 'Track_1', 'road indirect_1']].max(axis=1)

    # Total visual score
    vdf['Visual_score'] = vdf['People'] + vdf['Land_Cover'] + vdf['Infrastructure'] +\
        vdf['Waterways'] + vdf['Roads'] + (vdf['Other'] * .1)
    
    return vdf


def settings_extract_values(raster_path, prj_file):

    # Get points coordinate system
    prj_filef = open(prj_file, 'r')
    prj_txt = prj_filef.read()
    prj_filef.close()
    srs = osr.SpatialReference()
    srs.ImportFromESRI([prj_txt])
    srs.AutoIdentifyEPSG()

    # Get raster and geotransforms according to country
    raster_obj = RASTER(raster_path)
    srRaster = osr.SpatialReference(raster_obj.ds.GetProjection())

    # No data vlaue and array
    raster_obj.get_array()
    array = raster_obj.array
    nd = raster_obj.nodata
    # affine = raster_obj.affine
    affine = Affine.from_gdal(*raster_obj.ds.GetGeoTransform()) 
    
    # Close raster
    raster_obj.close()
    
    # Transformation between from points coord sys to raster cs
    ct = osr.CoordinateTransformation(srs, srRaster)
    
    return array, ct, nd, affine


def extract_values_from_points(subset_df, raster_path, field_name, prj_file,
                               xfield, yfield):
    
    # Transformations between points and raster
    array, ct, nd, affine = settings_extract_values(raster_path, prj_file)

    # List of values to populate
    results_dict = {}
    
    # Iterate point by point to extract values
    for index, row in subset_df.iterrows():

        # Get x and y from dataframe, original coord sys
        feat = subset_df[subset_df.index==index][[xfield, yfield]]
        x = feat[xfield].values[0]
        y = feat[yfield].values[0]

        # Pick value from raster
        # Coords of point in raster's coordinate syst
        xgeo,ygeo,zgeo = ct.TransformPoint(x, y, 0)
    
        # # Convert it to pixel/line on band
        rev = ~affine
        c = rev * (xgeo, ygeo)
        
        # Get value from raster
        result = array[int(round(c[1]-.5,0)),int(round(c[0]-.5,0))]
    
        # Cahnge to nan if needed, and append
        if result == nd:
            result = float('nan')
            
        # Append to dict
        results_dict[index] = result

    return pd.DataFrame.from_dict(results_dict, columns=[field_name], orient='index')



def HF_index_to_visual_df(vdf, HF_path, country_field, prj_file,
                          xfield, yfield, purpose):
    '''
    Adapted from 
    # https://stackoverflow.com/questions/13439357/extract-point-from-raster-in-gdal
    '''

    name = f'{purpose}_map'    
    vdf[name] = np.nan

    # Loop first by country, then by HF map
    # for country in HF_rasters_dict:
    HF_values = extract_values_from_points(vdf, HF_path, name,\
            prj_file, xfield, yfield)
    indices = HF_values.index
    vdf.loc[indices, name] = HF_values[name]
    return vdf

def get_validation_metrics(vdf, HF_path, country_field, cat_fields, country,
                           purpose, folder_stats=None, graphs=True):
    
    # If True, prints results
    prints = True
    # prints = False
    
    # country = 'Peru'
    # HF_map = 'SDG15'
    HF_map = purpose
    
    # List for texts to return with validation metrics
    validation_text = []
    validation_df = pd.DataFrame(columns=('Country', 'Purpose', 'RMSE', 'Kappa', 'R2'))
    validation_df.set_index(['Country','Purpose'],inplace=True)

    # for country in HF_rasters_dict:
        
    validation_text.append(country)
        
    sub_df = vdf[vdf[country_field] == country].copy()
        
        # for HF_map in HF_rasters_dict[country]:

            
    print()
    print(f'Validation stats {country}/{HF_map}')
    
    # Normalizae visual score by subset
    sub_df['Visual_score_norm'] = sub_df['Visual_score'] / sub_df['Visual_score'].max()
    
    # Get RMSE by country
    sub_df[f'{HF_map}_norm'] = sub_df[f'{HF_map}_map'] / sub_df[f'{HF_map}_map'].max()
    sub_df['RMSE_step1'] = (sub_df['Visual_score_norm'] -\
                            sub_df[f'{HF_map}_norm'])**2
    # Remove features with no RMSE
    sub_df = sub_df[~sub_df['RMSE_step1'].isnull()]
    # Calculate RMSEs
    RMSE = get_RMSE(sub_df['RMSE_step1'])
    print(f'RMSE = {np.round(RMSE, 3)}')
    validation_text.append(f'\n\nValidation metrics {HF_map} \n')
    validation_text.append(f'RMSE = {np.round(RMSE, 2)}')
    if cat_fields:
        RMSE_cat = sub_df.groupby(cat_fields, as_index=True).agg(RMSE=('RMSE_step1', get_RMSE))
        print(f'RMSE({country}/{HF_map}) = {np.round(RMSE_cat, 3)}')
        validation_text.append(f'RMSE({country}/{HF_map}) = {np.round(RMSE_cat, 3)}')
    
    # Get Kappa 
    agr = .2  # Agreement
    sub_df['Dif'] = np.round(sub_df[f'{HF_map}_norm']-sub_df['Visual_score_norm'],2)
        
    # centre = np.average(sub_df['Dif'])
    centre = np.median(sub_df['Dif'])
    
    sub_df['HFP High'] = np.where(sub_df[f'{HF_map}_norm']-sub_df['Visual_score_norm']>agr, 1, 0)
    sub_df['HFP low'] = np.where(-(sub_df[f'{HF_map}_norm']-sub_df['Visual_score_norm'])>agr, 1, 0)
    sub_df['Agree_high'] = np.where(sub_df['HFP High']==0,\
                                np.where(sub_df['HFP low']==0,\
                                np.where(sub_df['Dif']>centre,1,0),0),0)
    sub_df['Agree_low'] = np.where(sub_df['HFP High']==0,\
                                np.where(sub_df['HFP low']==0,\
                                np.where(sub_df['Dif']<=centre,1,0),0),0)
    Ll = np.count_nonzero(sub_df['Agree_low'] == 1)
    Lh = np.count_nonzero(sub_df['HFP High'] == 1)
    Hl = np.count_nonzero(sub_df['HFP low'] == 1)
    Hh = np.count_nonzero(sub_df['Agree_high'] == 1)
    
    data = [{'low': Ll, 'high': Lh},
            {'low': Hl, 'high': Hh}]
    df_kappa = pd.DataFrame(data, index =['Low', 'High'])
    sh_sum = np.sum(df_kappa, axis=0)
    sh_sum.name = "Total_h"
    df_kappa = df_kappa.append(sh_sum)
    sv_sum = np.sum(df_kappa, axis=1)
    sv_sum.name = "Total_v"
    df_kappa = pd.concat([df_kappa, sv_sum], axis=1)
    validation_text.append(df_kappa)
    if prints: print(df_kappa)
    Agreement = df_kappa.loc['Low']['low'] + df_kappa.loc['High']['high']
    if prints: print(f'Agreement = {Agreement}')
    validation_text.append(f'Agreement = {Agreement}')
    by_ch1 = df_kappa.loc['Total_h']['low'] * df_kappa.loc['Low']['Total_v'] / df_kappa.loc['Total_h']['Total_v']
    by_ch2 = df_kappa.loc['Total_h']['high'] * df_kappa.loc['High']['Total_v'] / df_kappa.loc['Total_h']['Total_v']
    By_chance = by_ch1 + by_ch2
    if prints: print(f'By chance =  {np.round(By_chance, 2)}')
    validation_text.append(f'By chance =  {np.round(By_chance, 2)}')
    kappa = (Agreement - By_chance) / (df_kappa.loc['Total_h']['Total_v'] - By_chance)
    print(f"Cohen's kappa coefficient = {np.round(kappa, 3)}")
    validation_text.append(f"Cohen's kappa coefficient = {np.round(kappa, 3)}")
    
    # Calculate correlation
    corr = sub_df[f'{HF_map}_norm'].corr(sub_df['Visual_score_norm'])
    # corr2 = corr*corr
    print(f'Pearson correlation = {np.round(corr, 3)}')
    validation_text.append(f'Pearson correlation = {np.round(corr, 3)}')
    validation_df.loc[(country, HF_map),:] = (RMSE,kappa,corr)


    # Save a file of validation stats (overwrites)
    if folder_stats:
        validation_df.to_csv(folder_stats + 'Validation_dataframe.csv', index=True)
        text_to_write = ['\n\n' + str(i) for i in validation_text]
        file = open(folder_stats + 'Validation_metrics.txt', 'w')
        # file.write(f'Validation metrics {HF_map} \n')
        file.writelines(text_to_write)
        file.close()



############################################

if __name__ == "__main__":
    
    # Read file with pressure visual scores and calculate visual score
    
    # Fields to subset dataframe to visual scores fields and needed fields
    fields_vis_scores = [
        'Crops', #'Vis_Built-environments',
        'Pasture',
        'Disturbed vegetation',
        'Forestry',
        	'roads-paved',
        'roads-unpaved',
        'roads-private',
        'Railways',
        'Track',
        'road indirect',
        'Urban',
        'Human dwellings',
        'Infractructure',
        'Settlements indirect',
        'Navigable waterways',
        'Navigable waterways indirect',
        'Other',
    ]

    other_fields = [
        'id',
        'Certain',   
        'Country',
        'position',
        'POINT_X',
        'POINT_Y',
        ]

    country = 'Peru'

    # Get values form HF rasters
    # m_folder2 = os.getcwd() + '/Peru_HH/HF_maps/00_Backup_maps/Pe_20211209_210315_Current_DGOTA//'
    # HF_path = m_folder2 + 'HF_Peru_2018_GHF.tif'
    # purpose = 'curr'
    
    m_folder2 = os.getcwd() + '/Peru_HH/HF_maps/b05_HF_maps/Pe_20220930_120709_SDG15//'
    HF_path = m_folder2 + 'HF_Peru_2018_GHF_300m.tif'
    purpose = 'SDG15'

    # Karla's Excel iwth visual scores
    m_folder = os.getcwd() + '/Peru_HH/Validation//'
    vis_path = m_folder + '210417_1_Validation_Pe_p0.csv'
    
    # Remove Colombia points
    remove_field = 'Country'
    remove_value = 'Colombia'
    
    # Keep only points for position 0  # TODO add certain parameter here
    keep_field = 'position'
    keep_value = 'p0'
    
    # prj for points
    prj_file = os.getcwd() + '/Peru_HH/Validation//Sinusoidal_PEC_-74.prj'

    # Field to look for country
    country_field = 'Country'

    # Fields for x and y
    xfield = "POINT_X"  
    yfield = "POINT_Y"
    
    
    # Calculate score from visual scores of pressures
    vdf = calculate_visual_score(vis_path, fields_vis_scores, other_fields,\
                                 remove_field, remove_value, \
                                     keep_field, keep_value, \
                                         )

    # Read all maps and create columns with their values
    # Removes rows where no value existed
    vdf = HF_index_to_visual_df(vdf, HF_path, country_field, prj_file,
                                xfield, yfield, purpose)

    # Create normalized scores  and differences for comparisons elsewhere
    # Create a copy so the fields don't get messed up for heatmaps
    vdf2 = vdf.copy()
    vdf2['Visual_score_norm'] = vdf2['Visual_score'] / vdf2['Visual_score'].max()
    
    # for country in HF_rasters_dict:
    #     for purpose in HF_rasters_dict[country]:
    vdf2[f'{purpose}_map_norm'] = vdf2[f'{purpose}_map'] / vdf2[f'{purpose}_map'].max()
    vdf2[f'Dif_vis_{purpose[3:]}_norm'] = vdf2['Visual_score_norm'] - vdf2[f'{purpose}_map_norm']
    vdf2[f'Dis_{purpose[3:]}_norm'] = np.absolute(vdf2[f'Dif_vis_{purpose[3:]}_norm'])

    # Save dataframe
    # folder_df = r'E:\OneDrive - UNBC\Validation\Results//'
    file_df = m_folder + r'DataFrame_points_validation.csv'
    vdf2.to_csv(file_df, index=True)


    # Calculate validation metrics
    
    # List of fields for categories (e.g. biome, province, etc.)
    cat_fields = []

    # Generate linear regression graphs
    # graphs = False
    graphs = True

    # Get the stats for each HF map, comparing it to the visual score
    # Prints here and creates a new csv file and graphs
    get_validation_metrics(vdf, HF_path, country_field, cat_fields, country,
                           purpose, folder_stats=m_folder, graphs=graphs)


    print('\007')
    print("------ FIN ------")
              

