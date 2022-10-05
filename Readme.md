# Indice de Huella Humana - Peru

Herramienta en python, que dadas las capas, se puede calcular 
el índice de huella humana (IHH) a nivel nacional o una zona específica.

## Instalación
Instalar las librerías requeridas en un entorno virtual.

``` bat
gdal=3.3.2
matplotlib
seaborn
pandas
Affine
```

## Estructura de carpetas
``` bat
| Peru_HH
+---HF_maps
|   | 01_Limits
|   | b02_Base_rasters
|   | b03_Prepared_pressures
|   | b04_Scored_pressures
|   | b05_HF_maps
+---No_Oficial
|   |  Land_use
|   |  Mining
|   |  NTL
|   |  OSM
|   |  Population
+---Oficial
|   |  DGOTA
|   |  IGN
|   |  MIDAGRI
|   |  MINAM
|   |  MTC
|   |  OEFA
|   |  OSINERGMIN
|   |  PERUPETRO
+---Indicators
|   +--Shps
|   |  | ANP.shp
|   |  | CobVegetal.shp
|   |  | ZA.shp
+---Validation
\--------Sinusoidal_PEC_-74.prj
```

- **01_Limits:** límites en shapefile del área de estudio. La proyección y extensión se mantendrá para todo el proceso. Por ejemplo, límite nacional del Perú. Puede tener polígonos para pruebas.
- **b02_Base_rasters:** Rásters correspondientes al área de estudio, que servirán de molde para el resto de coberturas. Por ejemplo, ráster del límite nacional del Perú.
- **b03_Prepared_pressures:** contiene los rásters y archivos de trabajo de las presiones. Debido a la 
diversidad de formatos y esquemas de calificación, el script prepara las coberturas de presiones mediante operaciones espaciales para conseguir un ráster con el molde del ráster de base, antes de asignarse valores de influencia humana. Estos archivos tienen el formato "bui_Pe_pob_indig_MinCul_20_Peru_01_GHF_300m_prepared.tif", donde  "bui_Pe_pob_indig_MinCul_20" es el nombre de la cobertura, "Peru_01" es el nombre del área de estudio, "GHF" es el nombre del esquema de calificación (adaptado desde el Global Human Footprint), y "repared" indica que este es el archivo a usar en la siguiente etapa.
- **b04_Scored_pressures:** tiene las coberturas luego de asignárseles una calificación de huella humana. Por ejemplo "bui_Pe_pob_indig_MinCul_20_2015_Peru_01_GHF_300m_scored.tif"es el resultado de asignar una calificación de huella humana a "bui_Pe_pob_indig_MinCul_20_Peru_01_GHF_300m_prepared.tif".
El nombre sigue el mismo esquema anterior, cambiando por “scored” la parte final.
- **b05_HF_maps:** tiene carpetas con los mapas de huellas humanas, mapas de las presiones individuales y una copia de los scripts como respaldo. Se va a crear una carpeta cada vez donde el nombre indica información general de la versión del mapa y la fecha de ejecución

Las carpetas Oficial y No_Oficial tienen la información de las presiones o insumos. En la carpeta No_Oficial están las coberturas de presiones que no vienen de fuentes oficiales, por ejemplo, luces nocturnas de VIIRS. En la carpeta Oficial están las coberturas de presiones que sí vienen de fuentes oficiales, por ejemplo, la cobertura agrícola de MIDAGRI.

## Scripts
- **HF_tasks.py:** Desde aquí se ejecutan las funciones principales de preparación, calificación y cálculo de mapas. Se deben configurar las funciones de preparación y calificación correspondientes a cada cobertura.
- **HF_spatial.py:** No se espera que el usuario interactúe con esta sección. Es la más extensa dado que tiene todas las funciones y clases para las operaciones espaciales.
- **HF_settings.py:** Aquí se indican las configuraciones básicas para el propósito del mapa. El propósito "SDG15" está diseñado para el reporte de ODS15, es decir, para un rango de tiempo adecuado (al menos desde 2015) y priorizando las coberturas oficiales. Se indica la ruta al shapefile del área de estudio, el esquema de calificación ("GHF"), resolución de los mapas y los años que se procesarán.
- **HF_scores.py:** Las funciones de calificación van a tomar los valores para los respectivos cálculos desde HF_scores. Aquí se indican los valores de huella humana que serán "aplicados" a la cobertura preparada. En los casos en los que existe la etiqueta "resampling_method", esta se usa al momento de preparación de la cobertura durante el warping.
- **HF_layers.py:** Hay dos partes aquí: una lista de multitemporalidad y las configuraciones para todas las coberturas. La lista de multitemporalidad se llama "multitemporal_layers". Aquí se indican cuáles conjuntos de datos tienen más de una cobertura en el tiempo.
- **HF_main.py:** Se explica el funcionamiento del script con el ejemplo de la cobertura de ambientes construidos. La primera sección (HF_main) es el punto de partida para llamar al resto de funciones y clases. Tiene las configuraciones de nivel más alto.

- **HF_validation_Pe.py:** 
- **HF_indicators_Pe.py:** 

## Modo de uso

1. Creación de un entorno virtual (virtualenv), ya sea con Anaconda o con pip
2. Instalación de librerías necesarias (En caso se requiera, descargar archivo binario *.whl)
3. Verificar las capas necesarias para correr el código
4. Elegir las capas y configuraciones necesarias del archivo *HF_settings.py*
5. Ejecutar el código *HF_main.py*
6. Verificar el resultado en la carpeta *Peru_HH >> HF_maps >> b05_HF_maps*
7. Seleccionar la carpeta de salida del resultado de IHH, modificar la ruta en el archivo *HF_valdation_Pe.py* y ejecutar.
8. De la misma forma que el paso anterior, pero en el archivo *HF_indictors_Pe.py* y ejecutar.
9. Verificar los resultados en la carpeta *Indicators*
