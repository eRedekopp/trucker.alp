import xml.etree.ElementTree as ET
import csv

xml_tree = ET.parse("rest-areas.kml")
root = xml_tree.getroot()

placemarks = root.iter("{http://www.opengis.net/kml/2.2}Placemark")
places = []

# Collect the data from the xml file
for placemark in placemarks:
    place = {}
    place["name"] = placemark.find("./{http://www.opengis.net/kml/2.2}name").text.rstrip('\n')
    data = placemark.find("./{http://www.opengis.net/kml/2.2}ExtendedData")
    for field in data:
        if not field.tag.endswith("}Data"):
            continue
        if field.attrib["name"] == "City or Town":
            place["name"] = field.find("./{http://www.opengis.net/kml/2.2}value").text.rstrip('\n') + " " + place["name"]
        elif field.attrib["name"] == "Latitude":
            place["latitude"] = field.find("./{http://www.opengis.net/kml/2.2}value").text
        elif field.attrib["name"] == "Longitude":
            place["longitude"] = field.find("./{http://www.opengis.net/kml/2.2}value").text
    places.append(place)

print(places)
print(len(places))

# Write the data to a .csv
with open("rest-areas.csv", 'w') as csvfile:
    fieldnames = ["name", "latitude", "longitude"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for place in places:
        writer.writerow(place)
