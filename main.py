#!/usr/bin/env python
import requests, json

#Auth Token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'
dcim_token = '95d2a16ddb3670eecacb1018e0de484d1b8267e7'


head = {'Authorization': 'Bearer {}'.format(token)}
dhead = {'Authorization': 'Token {}'.format(dcim_token)}

# EXAION ID
eid = 0
siteNamebldgIDDict = {
    "nil": None
  }
roomNameIDDict = {}


# Helper func defs
def GetRoomName(siteName, BldgID):
  pr = requests.get(
    "https://ogree.chibois.net/api/user/buildings/"+str(BldgID)+"/rooms",
     headers=head, data=json.dumps(npq) )
  return pr.json()['data']['objects'][0]['name']

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
  eid = r.json()["data"]["id"]
elif "id" in r.json()["tenant"]: 
    print("We have the OG response")
    print("Now setting the Exaion ID...")
    eid = r.json()["tenant"]["id"]
else:
  print("this doesn't work")


# Obtain the big list of Tenants
# Then put into OGREDB
r = requests.get("https://dcim.chibois.net/api/tenancy/tenants/", 
headers=dhead)

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
    pr = requests.post("https://ogree.chibois.net/api/user/tenants",
     headers=head, data=json.dumps(npq) )
    #print(pr.json())


# Obtain the big list of Sites
# Store into Cockroach and add
# a placeholder bldg to each site
r = requests.get("https://dcim.chibois.net/api/dcim/sites/", headers=dhead)
#print(r.json())
for entry in r.json()['results']:
  npq = {
  "name": entry['name'],
  "id": None, #API doesn't allow non Server Generated IDs
  "parentId": eid, #No site in Netbox has an existing tenant => place in Exaion 
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
  #print(json.dumps(npq))
  pr = requests.post("https://ogree.chibois.net/api/user/sites",
   headers=head, data=json.dumps(npq) )
  #print(pr.json())
  siteID = pr.json()['data']
  print(siteID['id'])
  bldgJson = {
  "name": "BldgA",
  "id": None, #API doesn't allow non Server Generated IDs
  "parentId": siteID['id'],
  "category": "building",
  "description": ["Some Building"],
  "domain": "Connector Domain",
  "attributes": {
    "posXY": "99,99",
    "posXYUnit": "mm",
    "posZ":"99",
    "posZUnit": "mm",
    "size":"99",
    "sizeUnit": "mm",
    "height":"99",
    "heightUnit": "mm",
    "nbFloors":"99"
    }
  }
  tmpr = requests.post("https://ogree.chibois.net/api/user/buildings",
  headers=head, data=json.dumps(bldgJson) )
  siteNamebldgIDDict[siteID['name']] = tmpr.json()['data']['id']


# Obtain the big list of Rooms (Rack-Groups)
# Store using tenant 'Exaion' and site name
r = requests.get("https://dcim.chibois.net/api/dcim/rack-groups/",
 headers=dhead)
for idx in r.json()['results']:
  roomJson = {
    "id": None,
    "name": idx['name'],
    "parentId": siteNamebldgIDDict[idx['site']['name']],
    "category": "room",
    "domain": "Connector Domain",
    "description": [
        ""
    ],
    "attributes": {
        "posXY": "{\"x\":10,\"y\":10}",
        "posXYUnit": "m",
        "posZ": "10",
        "posZUnit": "m",
        "template": "",
        "orientation": "+N+W",
        "size": "{\"x\":10,\"y\":10}",
        "sizeUnit": "m",
        "height": "10",
        "heightUnit": "m",
        "technical": "{\"left\":1.0,\"right\":1.0,\"top\":3.0,\"bottom\":1.0}",
        "reserved": "{\"left\":2.0,\"right\":2.0,\"top\":2.0,\"bottom\":2.0}"
    }
  }
  tmpr = requests.post("https://ogree.chibois.net/api/user/rooms",
  headers=head, data=json.dumps(roomJson) )
  roomNameIDDict[idx['name']] = tmpr.json()['data']['id']


# Obtain the big list of Racks
# store using the room Name & 
# corresponding ID
r = requests.get("https://dcim.chibois.net/api/dcim/racks/",
 headers=dhead)
print("LEN: ", len(r.json()['results']))
for idx in r.json()['results']:
  #print(idx['group'])
  if idx['group'] == None:
    print("WE GOT A NULL!")
    print(idx['site']['name'])
    print(siteNamebldgIDDict[idx['site']['name']])
    name = GetRoomName(idx['site']['name'], 
      siteNamebldgIDDict[idx['site']['name']])
    pid = roomNameIDDict[name]
  else:
    name = idx['name']
    pid = roomNameIDDict[idx['group']['name']]
  rackJson = {
    "id": None,
    "name": str(name),
    "parentId": str(pid),
    "category": "rack",
    "domain": "Connector Domain",
    "description": [
      ""
    ],
    "attributes": {
        "posXY": "{\"x\":10.0,\"y\":0.0}",
        "posXYUnit": "tile",
        "posZ": "Some position",
        "posZUnit": "cm",
        "template": "Some template",
        "orientation": "front",
        "size": "{\"x\":60.0,\"y\":120.0}",
        "sizeUnit": "cm",
        "height": str(idx['u_height']),
        "heightUnit": "U",
        "vendor": "someVendor",
        "type": "someType",
        "model": "someModel",
        "serial": "someSerial"
    }
  }
  tmpr = requests.post("https://ogree.chibois.net/api/user/racks",
  headers=head, data=json.dumps(rackJson) )
  #print("ParentID: ", pid)






# ITERATE THROUGH EACH ELEMENT AND SEND AN API REQUEST
#for site in r.json()['results']:
#    print("Here's a site!")
'''








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
#'''
#    "orientation": "NW",
#    "usableColor": "ExaionColor",
#    "reservedColor": "ExaionColor",
#    "technicalColor": "ExaionColor",
#    "address": None,
#    "zipcode": None,
#    "city": None,
#    "country": None,
#    "gps": None
#'''


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