import json

with open('./data/1hr_json.json','r') as f:
    data = json.load(f)

id = []
du_p = []
for Each in data:
    id_ = Each['id']
    if id_ in id:
        du_p.append(Each)
    else:
        id.append(id_)

print(f"Total duplicated points: {len(du_p)}")
print(du_p)