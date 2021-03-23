#!/usr/bin/env python
import requests, json

#Auth Token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'
dcim_token = '95d2a16ddb3670eecacb1018e0de484d1b8267e7'


head = {'Authorization': 'Bearer {}'.format(token)}
dhead = {'Authorization': 'Token {}'.format(dcim_token)}

# URLs
# LOCAL: http://localhost:8000/api/user/tenants
# DCIM: https://api.chibois.net/api/dcim/racks/
# NETBX: https://dcim.chibois.net/api/dcim/racks


# Obtain the big list of Sites
r = requests.get("https://dcim.chibois.net/api/dcim/sites/", headers=dhead)
# print(r.json())
# ITERATE THROUGH EACH ELEMENT AND SEND AN API REQUEST
#for site in r.json()['results']:
#    print("Here's a site!")



# Obtain the big list of Devices 

r = requests.get("https://dcim.chibois.net/api/dcim/devices/", headers=dhead)
# print(r.json()['results'])

for d in r.json()['results']:
    if d['tenant'] != None:
        print("U NOT LIKE ME")


# Obtain the big list of Racks 

r = requests.get("https://dcim.chibois.net/api/dcim/racks/", headers=dhead)
# print(r.json()['results'])

for d in r.json()['results']:
    if d['tenant'] != None:
        print("U NOT LIKE ME")






# Obtain the big list of Tenants
r = requests.get("https://dcim.chibois.net/api/tenancy/tenants/", headers=dhead)

for tn in r.json()['results']:
    npq = {
  "name": tn['name'],
  "id": int(tn['id']),
  "parentId": None,
  "category": "tenant",
  "description": [tn['description']],
  "domain": "Connector Domain",
  "attributes": {
    "color": "Connector Color",
    "mainContact": None,
    "mainPhone": None,
    "mainEmail": None
  }
}
    pr = requests.post("https://api.chibois.net/api/user/tenants", headers=head, data=json.dumps(npq) )
    print(pr.json())



### Test with Current API @ https://api.chibois.net/api/user/
### To check that a request is successful, 
# use r.raise_for_status() or check r.status_code is what you expect

