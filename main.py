#!/usr/bin/env python
import requests, json

#Auth Token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'
dcim_token = '95d2a16ddb3670eecacb1018e0de484d1b8267e7'


head = {'Authorization': 'Bearer {}'.format(token)}
dhead = {'Authorization': 'Token {}'.format(dcim_token)}

# EXAION ID
eid = 0

# URLs
# LOCAL: http://localhost:8000/api/user/tenants
# DCIM: https://api.chibois.net/api/dcim/racks/
# NETBX: https://dcim.chibois.net/api/dcim/racks


#Create EXAION Tenant
exaionJson = {
  "name": "Exaion",
  "id": None,  #API doesn't allow non Server Generated IDs
  "parentId": None,
  "category": "tenant",
  "description": ["Tenant for Herve", "A Place holder"],
  "domain": "Exaion Domain",
  "attributes": {
    "color": "Connector Color",
    "mainContact": None,
    "mainPhone": None,
    "mainEmail": None
  }
}

r = requests.post("https://ogree.chibois.net/api/user/tenants", 
headers=head, data=json.dumps(exaionJson))
if "data" in r.json():
  print("OK we are on traditional setup")
elif "id" in r.json()["tenant"]: 
    print("We have the OG response")
    print("Now setting the Exaion ID...")
    eid = r.json()["tenant"]["id"]
else:
  print("this doesn't work")


# Obtain the big list of Tenants
# Then put into OGREDB
r = requests.get("https://dcim.chibois.net/api/tenancy/tenants/", headers=dhead)

for tn in r.json()['results']:
    npq = {
  "name": tn['name'],
  "id": None, #API doesn't allow non Server Generated IDs
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
    pr = requests.post("https://ogree.chibois.net/api/user/tenants", headers=head, data=json.dumps(npq) )
    #print(pr.json())


# Obtain the big list of Sites
r = requests.get("https://dcim.chibois.net/api/dcim/sites/", headers=dhead)
#print(r.json())
for entry in r.json()['results']:
  npq = {
  "name": entry['name'],
  "id": None, #API doesn't allow non Server Generated IDs
  "parentId": eid,
  "category": "site",
  "description": [entry['description']],
  "domain": "Connector Domain",
  "attributes": {
    "orientation": "NW",
    "usableColor": "ExaionColor",
    "reservedColor": "ExaionColor",
    "technicalColor": "ExaionColor",
    "address": entry['physical_address'],
    "zipcode": None,
    "city": None,
    "country": None,
    "gps": None # None of the sites have coordinates
  }
}
  #print
  pr = requests.post("https://ogree.chibois.net/api/user/sites", headers=head, data=json.dumps(npq) )
  print(pr.json())

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







### Test with Current API @ https://api.chibois.net/api/user/
### To check that a request is successful, 
# use r.raise_for_status() or check r.status_code is what you expect



#Site Attributes
'''
    "orientation": "NW",
    "usableColor": "ExaionColor",
    "reservedColor": "ExaionColor",
    "technicalColor": "ExaionColor",
    "address": None,
    "zipcode": None,
    "city": None,
    "country": None,
    "gps": None
'''


'''
           "id": 4,
            "name": "D51",
            "slug": "d51",
            "status": {
                "value": "active",
                "label": "Active",
                "id": 1
            },
            "region": {
                "id": 1,
                "url": "https://dcim.chibois.net/api/dcim/regions/1/",
                "name": "R51",
                "slug": "r51"
            },
            "tenant": null,
            "facility": "",
            "asn": null,
            "time_zone": null,
            "description": "Secret Datacenter",
            "physical_address": "", #
            "shipping_address": "",
            "latitude": null, #
            "longitude": null, #
            "contact_name": "",
            "contact_phone": "",
            "contact_email": "",
            "comments": "",
            "tags": [],
            "custom_fields": {},
            "created": "2020-10-02",
            "last_updated": "2020-10-02T15:28:34.076024Z",
            "circuit_count": null,
            "device_count": 6,
            "prefix_count": null,
            "rack_count": 1,
            "virtualmachine_count": null,
            "vlan_count": null
            '''