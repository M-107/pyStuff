import os
import shutil
import sys
import urllib.request
from PIL import Image

print(f"VSCHT Book Downloader\n")
print(f"This tool downloads and merges books from the VSCHT website.\nThe expected URL format is 'https://vydavatelstvi.vscht.cz/katalog/publikace?uid=uid_isbn-XXX-XX-XXXX-XXX-X'\n")
# Example (62 pages)
# https://vydavatelstvi.vscht.cz/katalog/publikace?uid=uid_isbn-978-80-7592-112-3
urlBase = input("URL: ")
url = f"https://vydavatelstvi-old.vscht.cz/knihy/uid_isbn-{urlBase[-17:]}/img/"
name = input("Name of the book: ")
savePath = f"{os.path.join(os.getenv('USERPROFILE'), 'Downloads')}"
tempDir = f"{savePath}\{name}_temp"
os.mkdir(tempDir)
counter = 1
while True:
    currentUrl = f"{url}{counter:0>3}.png"
    currentPng = f"{tempDir}\{counter:0>3}.png"
    try:
        urllib.request.urlretrieve(currentUrl, currentPng)
        print(f"Downloading page {counter}", end="\r")
    except:
        break
    counter += 1
imageList = []
for image in os.listdir(tempDir):
    imagePath = os.path.join(tempDir, image)
    if image == "001.png":
        firstOpen = Image.open(imagePath)
        firstRGB = firstOpen.convert("RGB")
    else:
        imageOpen = Image.open(imagePath)
        imageRGB = imageOpen.convert("RGB")
        imageList.append(imageRGB)
firstRGB.save(f"{savePath}\{name}.pdf", save_all=True, append_images=imageList)
shutil.rmtree(tempDir)
os.startfile(savePath)
sys.exit()