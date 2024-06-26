#!/usr/bin/env python3
import sys
import os
import urllib.parse
from multiprocessing import Pool
import numpy as np

"""
root and webroot must point to the same folder, one on filesystem and one on the webserver. Use absolut paths, e.g. /data/pictures/ and https://pictures.example.com/
"""

ROOT = "/mnt/nfs/pictures/"
WEBROOT = "https://pictures.sorogon.eu/"
imgext = [".jpg", ".jpeg", ".JPG", ".JPEG"]
rawext = [".ARW", ".tif", ".tiff", ".TIF", ".TIFF"]

thumbnails: list[tuple[str, str]] = []

HTMLHEADER = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pictures</title>
    <style>
      * {
        box-sizing: border-box;
      }
      
      body {
        margin: 0;
        font-family: Arial;
      }
      
      .header {
        text-align: center;
        padding: 32px;
        display: -ms-flexbox; /* IE10 */
        display: flex;
        -ms-flex-wrap: wrap; /* IE10 */
        flex-wrap: wrap;
        justify-content: space-evenly;
        
      }

      .header img {
        width: 100px;
        vertical-align: middle;
      }
      
      .row {
        display: -ms-flexbox; /* IE10 */
        display: flex;
        -ms-flex-wrap: wrap; /* IE10 */
        flex-wrap: wrap;
        padding: 0 2px;
      }

      figure {
        margin: 0;
      }
      
      /* Create four equal columns that sits next to each other */
      .column {
        -ms-flex: 12.5%; /* IE10 */
        flex: 12.5%;
        max-width: 12.5%;
        padding: 0 4px;
      }
      
      .column img {
        margin-top: 20px;
        vertical-align: middle;
        width: 100%;
      }
      
      /* Responsive layout - makes a four column-layout instead of eight columns */
      @media screen and (max-width: 1000px) {
        .column {
          -ms-flex: 25%;
          flex: 25%;
          max-width: 25%;
        }
        .header img {
          width: 80px;
        }
      }
      
      /* Responsive layout - makes a two column-layout instead of four columns */
      @media screen and (max-width: 800px) {
        .column {
          -ms-flex: 50%;
          flex: 50%;
          max-width: 50%;
        }
        .header img {
          width: 60px;
        }
      }
      
      /* Responsive layout - makes the two columns stack on top of each other instead of next to each other */
      @media screen and (max-width: 600px) {
        .column {
          -ms-flex: 100%;
          flex: 100%;
          max-width: 100%;
        }
        .header img {
          width: 50px;
        }
      }

      .caption {
        padding-top: 4px;
        text-align: center;
        font-style: italic;
        font-size: 12px;
        width: 100%;
        display: block;
      }
    </style>
  </head>
  <body>
"""


def thumbnail_convert(arguments: tuple[str, str]):
    folder, item = arguments
    os.system(f'magick "{os.path.join(folder, item)}" -quality 75% -define jpeg:size=1024x1024 -define jpeg:extent=100kb -thumbnail 512x512 -auto-orient "{os.path.join(ROOT, ".previews", folder.removeprefix(ROOT), item)}"')


def listfolder(folder: str):
    items: list[str] = os.listdir(folder)
    items.sort()
    images: list[str] = []
    subfolders: list[str] = []

    if not os.path.exists(os.path.join(ROOT, ".previews", folder.removeprefix(ROOT))):
        os.mkdir(os.path.join(ROOT, ".previews", folder.removeprefix(ROOT)))

    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(HTMLHEADER)
        for item in items:
            if item != "Galleries" and item != ".previews":
                if os.path.isdir(os.path.join(folder, item)):
                    subfolders.extend([f'<figure><a href="{WEBROOT}{urllib.parse.quote(folder.removeprefix(ROOT))}/{urllib.parse.quote(item)}"><img src="https://www.svgrepo.com/show/400249/folder.svg" alt="Folder icon"/></a><figcaption><a href="{WEBROOT}{urllib.parse.quote(folder.removeprefix(ROOT))}/{urllib.parse.quote(item)}">{item}</a></figcaption></figure>'])
                    listfolder(os.path.join(folder, item))
                else:
                    if os.path.splitext(item)[1] in imgext:
                        image = f'<figure><a href="{WEBROOT}{urllib.parse.quote(folder.removeprefix(ROOT))}/{urllib.parse.quote(item)}"><img src="{WEBROOT}.previews/{urllib.parse.quote(folder.removeprefix(ROOT))}/{urllib.parse.quote(item)}" alt="{item}"/></a><figcaption class="caption">{item}'
                        if not os.path.exists(os.path.join(ROOT, ".previews", folder.removeprefix(ROOT), item)):
                            thumbnails.append((folder, item))
                        for raw in rawext:
                            if os.path.exists(os.path.join(folder, os.path.splitext(item)[0] + raw)):
                                if raw == ".tif" or raw == ".tiff" or raw == ".TIF" or raw == ".TIFF":
                                    image += f': <a href="{WEBROOT}{urllib.parse.quote(folder.removeprefix(ROOT))}/{urllib.parse.quote(os.path.splitext(item)[0])}{raw}">TIFF</a>'
                                else:
                                    image += f': <a href="{WEBROOT}{urllib.parse.quote(folder.removeprefix(ROOT))}/{urllib.parse.quote(os.path.splitext(item)[0])}{raw}">RAW</a>'
                        image += "</figcaption></figure>"
                        images.extend([image])
        f.write('    <div class="header">\n')
        for subfolder in subfolders:
            f.write(subfolder)
            f.write("\n")
        f.write("    </div>\n")
        f.write('    <div class="row">\n')
        for chunk in np.array_split(images, 8):
            f.write('      <div class="column">\n')
            for image in chunk:
                f.write(f"        {image}\n")
            f.write("      </div>\n")
        f.write("    </div>\n")
        f.write("  </body>\n</html>")
        f.close()


def main():
    global ROOT
    global WEBROOT
    if not ROOT.endswith("/"):
        ROOT += "/"
    if not WEBROOT.endswith("/"):
        WEBROOT += "/"
    if not os.path.exists(os.path.join(ROOT, ".previews")):
        os.mkdir(os.path.join(ROOT, ".previews"))
    print("Generating html files...")
    listfolder(ROOT)

    with Pool(os.cpu_count()) as p:
        print("Generating thumbnails...")
        p.map(thumbnail_convert, thumbnails)


if __name__ == "__main__":
    main()
