import re
import csv

import PyPDF2 as pdf

from Manual_Truckstop_Data import MANUAL_DATA

reader = pdf.PdfReader("./Stores-TruckStops-Allstays.pdf")

def get_locations_from_hyperlinks(page):
    url_coords_regex = ("https:\/\/maps\.google\.com\/maps\?saddr=Current"
         "\+Location&daddr=(-?\d+\.\d+)?,(-?\d+\.\d+)?")
    # https://stackoverflow.com/questions/27744210/extract-hyperlinks-from-pdf-in-python
    key = "/Annots"
    uri = "/URI"
    ank = "/A"
    out = []
    for link in page[key]:
        url = link.get_object()[ank][uri]
        regex_result = re.search(url_coords_regex, url)
        if regex_result is not None:
            if regex_result.groups(0) is not None:
                lat, lon = regex_result.groups(0)
                lat, lon = float(lat), float(lon)
            else:
                lat, lon = None, None
            out.append((lat, lon))
    return out


def get_photos_from_page(page):
    print(page.photos)


def get_num_spots_from_text(text):
    regex = "(\d+) (truck|Truck)? ?parking spaces"
    result = re.search(regex, text)
    if result is None:
        return 0
    else:
        return int(result.groups(0)[0])


def get_details_from_text(page):
    out = []

    # Every truck stop entry ends with Map - Navigation - Reviews
    # Split based on that
    delimiter = "View Map - Navigation - Add/Check Reviews"
    groups = [
        group.rstrip("\n ").lstrip("\n ").lower()
        for group in page.extract_text().split(delimiter)
        if not group.isspace()
    ]

    # Extract the info from each group
    for group in groups:
        location = {}
        items = group.split(" -")
        location["name"] = items[0]
        location["fee"] = "fee" in group or "/24" in group # /24 for "$x/24 hr"
        location["reserved"] = "reserved parking" in group
        location["parking"] = get_num_spots_from_text(group)

        out.append(location)

    return out


def get_details_from_page(page, pgnum):

    if (pgnum + 1) in MANUAL_DATA.keys():
        details = MANUAL_DATA[pgnum+1]
    else:
        locations = get_locations_from_hyperlinks(page)
        details = get_details_from_text(page)
        if len(locations) != len(details):
            raise Exception(f"{len(locations)} locations, {len(details)} text")

        for i in range(len(locations)):
            details[i]["latitude"] = locations[i][0]
            details[i]["longitude"] = locations[i][1]

    for d in details:
        d["pgnum"] = pgnum
    return details


all_stops = []
failed_pages = []
for page_num in range(1, len(reader.pages)):
    page = reader.pages[page_num]
    try:
        result = get_details_from_page(page, page_num)
        all_stops.extend(result)
    except Exception as e:
        print(e)
        failed_pages.append(page_num+1)

for i in range(len(all_stops)):
    all_stops[i]["id"] = i

for stop in all_stops:
    if stop["parking"] is None or stop["parking"] == "":
        print("Invalid parking in stop: " + stop["name"])
    if stop["latitude"] is None or stop["latitude"] == "":
        print("Invalid latitude in stop: " + stop["name"])
    if stop["longitude"] is None or stop["longitude"] == "":
        print("Invalid longitude in stop: " + stop["name"])

print(f"Successfully extracted {len(all_stops)} stops")
print(f"Failed {len(failed_pages)} pages:", failed_pages)

largest = max(all_stops, key = lambda s: s["parking"])
zeros = len([val for val in all_stops if val["parking"] == 0])
smalls = len([val for val in all_stops if val["parking"] < 5])
avg = sum([val["parking"] for val in all_stops]) / len(all_stops)

print(f"Largest stop: {largest['parking']} spots: {largest['name']} "
      f"on page {largest['pgnum']}")
print(f"No-parking stops: {zeros} stops")
print(f"Low-parking stops: {smalls} stops")
print(f"Average size: {avg}")

write = input("Write data file? [Y/n]")
if write not in ("n", "N"):
    with open("allstays-truckstop-data.csv", "w") as csvfile:
        fields = ["id", "name", "parking", "reserved", "fee", "latitude", "longitude"]
        writer = csv.DictWriter(csvfile, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_stops)
    print("Write Successful!")
