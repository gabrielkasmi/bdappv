#!/usr/bin/env python
# This script extract input data from SQL db and dumps it into JSON
#

import os

import pymysql
from dotenv import load_dotenv

from lib.model import *
import argparse

# For surface, image was displayed on 500 px instead of 400
from lib.utils import Campaign

SURFACE_RATIO = 0.8

CLICK_SRC_IMAGES = {
   Campaign.GOOGLE : 1,
   Campaign.IGN:2
}

POLYGON_SRC_IMAGES = {
   Campaign.GOOGLE : 4,
   Campaign.IGN:8, # TODO: to be defined, not sure
}

SQL_CLICK="""
   SELECT 
      action.coordX as x, 
      action.coordY as y,
      action.pv as isPV,
      bosseurAction.idImage as imageId,
      bosseurAction.dateAction as actionDate,
      bosseur.idBosseur as actorId,
      bosseur.region as actorRegion, 
      bosseur.pays as actorCountry
   FROM  prd_bdappv_actionPV as action  
   LEFT JOIN prd_bdappv_bosseurAction as bosseurAction ON action.idActionPV = bosseurAction.idAction
   LEFT JOIN prd_bdappv_bosseur as bosseur ON bosseurAction.idBosseur = bosseur.idBosseur
   WHERE bosseurAction.sourceImg = {SourceImg}
"""

SQL_POLYGON="""
   SELECT 
      point.coordX as x, 
      point.coordY as y,
      point.idSurface as polygonId,
      bosseurAction.idImage as imageId,
      bosseurAction.dateAction as actionDate,
      bosseur.idBosseur as actorId,
      bosseur.region as actorRegion,
      bosseur.pays as actorCountry
   FROM prd_bdappv_zoneSurfacePoint as point
   LEFT JOIN prd_bdappv_zoneSurface as surface ON point.idSurface = surface.idSurface
   LEFT JOIN prd_bdappv_bosseurAction as bosseurAction ON surface.idActionSurface = bosseurAction.idAction
   LEFT JOIN prd_bdappv_bosseur as bosseur ON bosseurAction.idBosseur = bosseur.idBosseur
   WHERE bosseurAction.sourceImg = {SourceImg}
   ORDER BY point.idSurfacePoint
"""

SQL_IMG="""
   SELECT 
         image.idImage as id, 
         image.identifiant as img_id, 
         install.ville as city,
         install.id_utilisateur as install_id,
         dep.region as region,
         dep.nom as department
   FROM prd_bdappv_image as image 
   LEFT JOIN pv_installation as install ON image.idInstallation = install.id_utilisateur
   LEFT JOIN pv_departement as dep ON dep.numero = install.departement"""



def load_imgs(campaign, filter):
   """Load image data from DB"""
   imgs = dict()

   conn = pymysql.connect(
      host=os.environ["DB_HOST"],
      port=int(os.environ["DB_PORT"]),
      user=os.environ["DB_USER"],
      password=os.environ["DB_PASS"],
      database=os.environ["DB_NAME"],
      cursorclass=pymysql.cursors.DictCursor)

   with conn :
      # Fetch all images
      with conn.cursor() as cursor :
         cursor.execute(SQL_IMG)
         for row in cursor :
            img = Image(row["img_id"], row["city"], row["department"], row["region"], row["install_id"])
            imgs[row["id"]] = img

      # Fetch clicks
      with conn.cursor() as cursor:
         cursor.execute(SQL_CLICK.format(SourceImg=CLICK_SRC_IMAGES[campaign]))
         for row in cursor:
            action = Action(row["actorCountry"], row["actorRegion"], row["actionDate"], row["actorId"])
            imageId = row["imageId"]

            if imageId is None :
               print("Bad action : ", row)
               continue

            if row["isPV"] :
               click = Click(row["x"], row["y"], action)
               imgs[imageId].clicks.append(click)
            else :
               imgs[imageId].notPvActions.append(action)

      # Fetch polygons
      with conn.cursor() as cursor:
         cursor.execute(SQL_POLYGON.format(SourceImg=POLYGON_SRC_IMAGES[campaign]))

         # Dict of polygonId => (polygon)
         polygons = dict()
         for row in cursor:
            action = Action(row["actorCountry"], row["actorRegion"], row["actionDate"], row["actorId"])
            imageId = row["imageId"]

            polygonId = row["polygonId"]
            if polygonId in polygons :
               polygon = polygons[polygonId]
            else:
               # Ne polygon ? Create it and add it to image
               polygon = Polygon(action)
               polygons[polygonId] = polygon
               imgs[imageId].polygons.append(polygon)

            point = Point(
               int(row["x"] * SURFACE_RATIO),
               int(row["y"] * SURFACE_RATIO))
            polygon.points.append(point)

   # Filter images having at least one click
   if filter :
      res = list(img for img in imgs.values() if ((len(img.clicks) > 0) or (len(img.polygons) > 0)))
   else:
      res = list(imgs.values())

   return res



if __name__ == '__main__':

   parser = argparse.ArgumentParser()
   parser.add_argument('output_file', type=str, metavar="out.json", help="Output file")
   parser.add_argument('--campaign', '-c', type=str, choices=[Campaign.IGN, Campaign.GOOGLE], help="Campaign : either 'google' (default) or 'ign'", default=Campaign.GOOGLE)
   parser.add_argument('--filter', '-f', action="store_true",
                       help="Filter out images with no click nor polygon", default=False)
   args = parser.parse_args()

   load_dotenv()
   imgs = load_imgs(args.campaign, args.filter)

   print("Found %d images" % len(imgs))

   to_json(imgs, args.output_file)




