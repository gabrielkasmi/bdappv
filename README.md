# Purpose

This repository contains data and scripts of the [BDApPV](https://www.bdpv.fr/_BDapPV/) campaign of annotation of images of PV panels.

# Usage

## 1) Local installation

To install the dependencies, it is recommanded to first [create a virtual environment](https://pythonbasics.org/virtualenv/). 
Then run :

    > pip install -r requirements.txt

Then you can download the `data` from the [Zenodo](https://zenodo.org/record/7358126) repository by typing:

```python
  cd bdappv
  # download from the repository
  wget 'https://zenodo.org/record/7358126/files/data.zip?download=1' -O 'data.zip'
  unzip 'data.zip' 
  # delete the zip file
  rm 'data.zip'
```

## 2) Use binder

Alternatively, you can use binder, which creates an environment and runs it online for you :

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/git/https%3A%2F%2Fgit.sophia.mines-paristech.fr%2Foie%2Fbdappv.git/HEAD)

# Notebooks 

This repository contains two Notebooks :
* [annotations.ipynb](./annotations.ipynb) [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/git/https%3A%2F%2Fgit.sophia.mines-paristech.fr%2Foie%2Fbdappv.git/HEAD?labpath=annotations.ipynb): Contains live demonstration of annotation analysis of the two phases, as well as a threshold analysis.  
* [metadata.ipynb](./metadata.ipynb) [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/git/https%3A%2F%2Fgit.sophia.mines-paristech.fr%2Foie%2Fbdappv.git/HEAD?labpath=metadata.ipynb) : Contains the code filtering and linking the metadata of the panels with the images. It also provides code to assess de quality of the overall process.

# Data 

This repository contains both input and output data, as JSON files.

Two campaigns were conducted :
1. On Google images
2. On [IGN](https://www.ign.fr/) images 

For each campaign, two phases were conducted :
1. Click on PV panels on images
2. For the images with PV panels detected on phase 1, draw polygons detouring the panels.

## Layout

* **data/** Root data folder
  * **raw** The raw crowdsourcing data and raw metadata
    * **input-google.json**
    * **input-igngoogle.json**
    * **raw-metadata.csv** 
* **replication/** Folder containing the compiled data used to generate the segmentation masks
  * **campaign-google / campagin-ign** One folder for each campaign 
    * **click-analysis.json** : Click analysis compiling raw input into a few best locations for panels
    * **polygon-analysis.json** : Polygon analysis compiling raw input into a few best polygons for panels
* **validation/** Folder containing the compiled data used for technical validation.
  * **campaign-google / campagin-ign** One folder for each campaign 
    * **click-analysis.json-thres=1.0** : Click analysis processed with low threshold, for threshold analysis
    * **polygon-analysis.json-thres=1.0** : Polygon analysis processed with low threshold, for threshold analysis
  * **metadata.csv**: The metadata of the distributed PV installations gathered by BDPV.

## Data model

### Input data

Input data is directly extracted from SQL db into a JSON file. It contains all meta data for all images, and all user contributions
on it (clicks and polygons).

| Attribute                 | Meaning                                                                        |
|---------------------------|--------------------------------------------------------------------------------|
| id                        | ID of image                                                                    |
| city                      | City of the image                                                              |
| department                | Departement of the image                                                       |
| region                    | Region of the image                                                            |
| install_id                | Possible ID linking to the PV installation, whose record is provided in the metadata.csv file. | 
| clicks[]                  | List of clicks                                                                 |
| clicks[].x                | x position of click in image                                                   |
| clicks[].y                | y position of click in image                                                   |
| clicks[].action           | Meta data of the click action                                                  |
| clicks[].action.country   | Country of actor of the click                                                  |
| clicks[].action.region    | Region of actor of the click                                                   |
| clicks[].action.date      | Date / time of click                                                           |
| clicks[].action.country   | Country of actor of the click                                                  |
| polygons[]                | List of polygons                                                               |
| polygons[].points[]       | List of point of the polygon                                                   |
| polygons[].points[].x     | x position of the point of polygon                                             |
| polygons[].points[].y     | y position of the point of polygon                                             |
| polygons[].action         | Meta data of the polygon action                                                |
| polygons[].action.country | Country of actor of the polygon                                                |
| polygons[].action.region  | Region of actor of the polygon                                                 |
| polygons[].action.date    | Date / time of polygon                                                         |
| polygons[].action.country | Country of actor of the polygon                                                |



## Output for phase 1 (clicks)

The output of click analysis contains a list of possible panel position for each image. Each image may contain one point or more : 
it should correspond to the number of panels found in it.

| Attribute      | Meaning                                                                                              |
|----------------|------------------------------------------------------------------------------------------------------|
| id             | ID of image                                                                                          |
| clicks[]       | List of detected point (local maxima)                                                                |
| clicks[].x     | x position of point in image                                                                         |
| clicks[].y     | y position of point in image                                                                         |
| clicks[].score | value of the local maxima. It should be between the threshold and the number of clicks on this image |

## Output for phase 2 (polygons)

The output of polygon analysis contains a list of polygons, as compilation of all polygons annotated by users. It should contain one or more polygon for each image, 
corresponding to the number of panels found in it.

| Attribute             | Meaning                                                                                                                                     |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| id                    | ID of image                                                                                                                                 |
| polygons[]            | List of detected polygons (sum of user polygons)                                                                                            |
| polygons[].score      | Score of the polygon (average of the value of its points). It should be between the chosen threshold and the number of actors on this image |
| polygons[].area       | Area of the polygon, in pixels                                                                                                              |
| polygons[].points[]   | Points of the polygons                                                                                                                      |
| polygons[].points[].x | x position of point in the image                                                                                                            |
| polygons[].points[].y | y position of point in the image                                                                                                            |


## Distributed PV metadata (metadata.csv)

'idInstallation', 'identifiant', 'idInverter', 'nameInverter',
       'countInverters', 'idArrays', 'nameArrays', 'countArrays', 'surface',
       'azimuth', 'typeInstallation', 'tilt', 'kWp', 'departement', 'city',
       'selfConsumption', 'isIntegrated', 'dateInstalled'

| Attribute                 | Meaning                                                                                                      |
|---------------------------|--------------------------------------------------------------------------------------------------------------|
| idInstallation            | The ID of the installation                                                                                   |
| identifiant               | The name of the image of the installation                                                                    |
| idInverter                | The ID of the inverter of the installation                                                                   |
| nameInverter              | The name of the inverter of the installation                                                                 |
| countInverters            |	The number of inverters attached to the installation                                                         |
| idArrays   	              | The ID of the solar arrays used by the installation                                                          |
| nameArrays                |	The name of the solar arrays used by the installation                                                        |
| countArrays               |	The number of PV arrays (modules) of the installation                                                        |
| surface                   |	The surface (in square meters) of the installation                                                           |
| azimuth                   |	The azimuth angle in degrees relative to the north (south = 180) of the installation.                        |
| typeInstallation          |	Indicates on which infrastructure the installation is mounted: <ul> <li> 0: Rooftop </li> </ul><ul> <li> 1: Unknown </li> </ul><ul> <li>  2: rooftop of a non-livable building </li> </ul><ul> <li>  3: ground </li> </ul><ul> <li>  4: other </li> </ul><ul> <li>  5: shade house </li> </ul><ul> <li>  6: sunshade </li> </ul><ul> <li>  7: solar tracker with 1 axis </li> </ul><ul> <li>  8: solar tracker with 2 axes </li> </ul>|
| tilt                      |	The tilt angle (in degrees) of the installation                                                              |
| kWp                       |	The installed capacity of the installation in kWp                                                            |
| departement               |	The <i> département </i> in which the installation is located                                                |
| city                      |	The <i> city </i> in which the installation is located                                                       |
| selfConsumption           |	Indicates whether the installation is used for self consumption (alternative is that PV power is reinjected into the grid)|
| isIntegrated              |	Indicates whether the installation is integrated (on the rooftop) or not|
| dateInstalled	            | The date (month, year) the installation has been installed                                                   |
| Controlled                |	Indicates whether the installations metadata are clean or not                                         |
| IGNControlled             |	Indicates whether the installation corresponds to a unique segmentation mask corresponding to an IGN image   |
| GoogleControlled          | Indicates whether the installation corresponds to a unique segmentation mask corresponding to a Google image |

## Images and segmentation masks 

## Complete records

Complete records
The full dataset record containing RGB images, ready-to-use segmentation masks of the two campaigns, and the metadata file can be downloaded on our [Zenodo repository](https://zenodo.org/record/7358126) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7358126.svg)](https://doi.org/10.5281/zenodo.7358126).

The complete records are organized as follows:

* **bdappv/** Root data folder
  * **google/ign** One folder for each campaign  
    * **img/** : Folder containing all the images presented to the users. This folder contains 28807 images for Google and 17325 images for IGN.
    * **mask/** : Folder containing all segmentations masks generated from the polygon annotations of the users. This folder contains 13303 masks for Google and 7686 masks for IGN.  
* **metadata.csv** The `.csv` file with the metadata of the installations.

# Scripts 

## export_data.py

Exports raw data from MySQL db to JSON. 

**Usage :**

   > export_data.py <out_file.json>
   
This script requires that a .env file is present in the same folder, with the following settings provided :

* **DB_HOST** : Database host
* **DB_PORT** : Database port
* **DB_USER** : Database login
* **DB_PASS** : Database password
* **DB_NAME** : Database /schema name

## click_analysis.py 

Analyse the phase1 annotations (clicks) and apply a KDE approach to find best points.
<output_file> will be like <input_file> json, with additional attribute `analysed_clicks` attached to each image.

**Usage :**

    > click_analysis.py [-h] [--display] [--parallel] [--out out_dir] [--ids id1,id2,id3] [--threshold THRESHOLD] input_file output_file

    positional arguments:
      input_file            Input file, or '-' for stdin
      output_file           Output file, or '-' for stdout
    
    optional arguments:
      -h, --help            show this help message and exit
      --display, -d         Display plots
      --parallel, -p        Parallel compute
      --out out_dir, -o out_dir
                            Output folder for processed images
      --ids id1,id2,id3, -i id1,id2,id3
                            Filter on ids
      --threshold THRESHOLD, -t THRESHOLD
                            Threshold value as absolute number of clicks (if >1) or ratio of number of clicks (if <1). 2 by default


## polygon_analysis.py 

Analyse phase2 annotation (polygons) and extract most likely polygons.
<output_file> will be like <input_file> json, with additional attribute `analysed_polygons` attached to each image.

**Usage:**

    > polygon_analysis.py [-h] [--display] [--parallel] [--out out_dir] [--ids id1,id2,id3] [--threshold THRESHOLD] [--image-type {polygon,threshold,all}] input_file output_file
    
    positional arguments:
      input_file            Input file, or '-' for stdin
      output_file           Output file, or '-' for stdout
    
    optional arguments:
      -h, --help            show this help message and exit
      --display, -d         Display plots
      --parallel, -p        Parallel compute
      --out out_dir, -o out_dir
                            Output folder for processed images
      --ids id1,id2,id3, -i id1,id2,id3
                            Filter on ids
      --threshold THRESHOLD, -t THRESHOLD
                            Threshold value as fraction of number of actors. 0.45 by default
      --image-type {polygon,threshold,all}, -it {polygon,threshold,all}
                            Type of output images. 'polygon' : Outputs binary image of best polygon. 'threshold (default)' : Outputs binary image of threshold (before detection of polygon). 'all' : Outputs both
                            raw level of detection in gray and final polygon in red.




