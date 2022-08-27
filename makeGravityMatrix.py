#
# This script reads a csv file and creates a new CSV file which
# contains a grid of the relative probability of travelling between
# each pair of cities.
#
# This script will take several minutes to complete.
#
# This probability is computed analogously to the formula for gravity
# Gm1m2/r^2 except "mass" is population and "radius" is straight-line
# distance between the two in miles.  And, 'G' is omitted to be added
# later in the model. I.e., pop1 * pop2 / dist^2 is shown in the data
# grid.
#
import csv
from geopy.distance import geodesic # `pip install geopy` to get this


input_filename = "USA_Major_Cities.csv"
output_filename = "matrix.csv"
cities = []

# Open the file and load the data into format {lat: w, lon: x, pop: y, id: z} for each
with open(input_filename, 'r', encoding="utf-8") as dataFile:
    fileReader = csv.DictReader(dataFile)
    for row in fileReader:
        # If using a new dataset, must edit the column names in row[xyz] to match
        cities.append({"lat": row["Y"], "lon": row["\ufeffX"], "pop": row["POPULATION"], "id": row["FID"]})

# Build a matrix in format { "id1": [{ "idN": multiplier }, ...] }
matrix = {city["id"]: {} for city in cities}
for city1 in cities:
    for city2 in cities:
        if city1["id"] == city2["id"]:
            multiplier = 0
        else:
            pop1 = int(city1["pop"])
            pop2 = int(city2["pop"])
            dist = geodesic((city1["lat"], city1["lon"]), (city2["lat"], city2["lon"])).miles
            multiplier = pop1 * pop2 / (dist * dist)

        matrix[city1["id"]][city2["id"]] = multiplier

# Save it all to a file
fieldnames = ["city"] + [city["id"] for city in cities]
with open(output_filename, 'w', encoding="utf-8") as outfile:
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    for city1 in cities:
        row = {city2["id"]: matrix[city1["id"]][city2["id"]] for city2 in cities}
        row.update({"city": city1["id"]})
        writer.writerow(row)

