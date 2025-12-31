import json

with open('./data/PMsensors.json', 'r') as f:
    PMsensors = json.load(f)

with open('./data/1hr_json.json', 'r') as f:
    data = json.load(f)



location = set()
for record in data:
    if record['sensor']['sensor_type']['name'].upper() in PMsensors:
        valid = False
        for r in record['sensordatavalues']:
            if r['value_type'] in ['P1', 'P2']:
                valid = True
        if valid:
            lat = record['location']['latitude']
            lon = record['location']['longitude']
            location.add( (lat, lon) )

        
#print(location)
print(f"{len(location)} unique locations found.")
print(f"{len(data)} total records processed.")

locations_list = [
    {"lat": lat, "lon": lon}
    for lat, lon in location
]

with open("./data/locations.json", "w") as f:
    json.dump(locations_list, f)
