#!/usr/bin/env python
import requests, json

# URLs
# LOCAL: http://localhost:8000/api/user/tenants
# DCIM: https://api.chibois.net/api/dcim/racks/
# NETBX: https://dcim.chibois.net/api/dcim/racks


#Auth Token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'
dcim_token = '95d2a16ddb3670eecacb1018e0de484d1b8267e7'

head = {'Authorization': 'Bearer {}'.format(token)}
dhead = {'Authorization': 'Token {}'.format(dcim_token)}


# EXAION ID & Maps
eid = 0
siteNamebldgIDDict = {}
roomNameIDDict = {}
rackNameIDDict = {}


# Helper func defs
# Get a corresponding room
# if 'group' is missing
# in json
def GetRoomName(siteName, BldgID):
  pr = requests.get(
    "https://ogree.chibois.net/api/user/buildings/"+str(BldgID)+"/rooms",
     headers=head )
  return pr.json()['data']['objects'][0]['name']

def postDevice(name, pid, devJson):
  deviceJson['name'] = name
  deviceJson['parentId'] = pid
  r = requests.post("https://ogree.chibois.net/api/user/devices", 
                                    headers=head, json=devJson)
  if r.status_code != 201:
    print("Error while creating device!")
    print(devJson)
    print(r.text)

#Create EXAION Tenant
exaionJson = {
  "name": "Exaion",
  "id": None,  #API doesn't allow non Server Generated IDs
  "parentId": None,
  "category": "tenant",
  "description": ["Tenant for Herve", "A Place holder"],
  "domain": "Connector Domain",
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
print("Number of tenants to be added: ", len(r.json()['results']))
for tenant in r.json()['results']:
    tenantJson = {
  "name": tenant['name'],
  "id": None, #API doesn't allow non Server Generated IDs
  "parentId": None,
  "category": "tenant",
  "description": [tenant['description']],
  "domain": "Connector Domain",
  "attributes": {
    "color": "Connector Color",
    "mainContact": None,
    "mainPhone": None,
    "mainEmail": None
  }
}
    # Add to Cockroach
    pr = requests.post("https://ogree.chibois.net/api/user/tenants",
     headers=head, data=json.dumps(tenantJson) )


# Obtain the big list of Sites
# Store into Cockroach and add
# a placeholder bldg to each site
r = requests.get("https://dcim.chibois.net/api/dcim/sites/", headers=dhead)
print("Number of Sites to be added: ", len(r.json()['results']))
print("Adding Sites...")
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

  pr = requests.post("https://ogree.chibois.net/api/user/sites",
   headers=head, data=json.dumps(npq) )

  siteID = pr.json()['data']
  print("Adding corresponding building")
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
print("Number of Racks to be added: ", len(r.json()['results']))
print("Adding Racks...")
for idx in r.json()['results']:
  if idx['group'] == None:
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
  rackNameIDDict[str(name)] = tmpr.json()['data']['id']



#GET Devices from Netbox
deviceJson = {
    "name": None,
    "id": None,
    "parentId": None,
    "category": "device",
    "description": [''
    ],
    "domain": "Connector Domain",
    "attributes": {
        "posXY": "0",
        "posXYUnit": "tile",
        "posZ": "0",
        "posZUnit": "tile",
        "size": "0",
        "sizeUnit": "mm",
        "height": "0",
        "heightUnit": "U",
        "template": "",
        "orientation": "front",
        "vendor": "",
        "type": "",
        "model": "",
        "serial": ""
    }
}

numDevicesValid = 0
numDevicesWithSiteWithoutRack = 0
numDevicesWithRackWithoutSite = 0
numDevicesWithoutBoth = 0
res = requests.get("https://dcim.chibois.net/api/dcim/devices/?limit=2000",
 headers=dhead)
r = requests.get(res.json()['next'], headers=dhead)
devices = res.json()['results'] + r.json()['results']

print("Number of Devices to check: ", len(devices))
print("Checking Devices...")
x = 0
for idx in devices:
  print(x)

  if 'rack' in idx and 'site' in idx:
    if idx['rack'] != None and idx['site'] != None:
      if 'name' in idx['rack'] and 'name' in idx['site']:
        #Check slightly more
        if (idx['rack']['name'] != None and idx['site']['name'] != None):
          #Check Dict 
          if (idx['site']['name'] in siteNamebldgIDDict and
            idx['rack']['name'] in rackNameIDDict) :
            numDevicesValid+=1
            postDevice(idx['name'], rackNameIDDict[idx['rack']['name']], deviceJson)
          
          elif (idx['site']['name'] in siteNamebldgIDDict and
            idx['rack']['name'] not in rackNameIDDict) :
            numDevicesWithSiteWithoutRack+=1

          elif (idx['site']['name'] not in siteNamebldgIDDict and
            idx['rack']['name'] in rackNameIDDict) :
            numDevicesWithRackWithoutSite+=1
          
          else: #Both not in Dict
            numDevicesWithoutBoth+=1
        
        elif idx['rack']['name'] != None and idx['site']['name'] == None:
          #Check Dict
          if idx['rack']['name'] in rackNameIDDict:
            numDevicesWithRackWithoutSite+=1
          else: #Both not in Dict
            numDevicesWithoutBoth+=1
            

        elif idx['rack']['name'] == None and idx['site']['name'] != None:
          #Check Dict
          if idx['site']['name'] in siteNamebldgIDDict:
            numDevicesWithSiteWithoutRack+=1
          else: #Both not in Dict
            numDevicesWithoutBoth+=1
            
        else: #Rack&Site not Named
          numDevicesWithoutBoth+=1

      elif 'name' in idx['rack'] and 'name' not in idx['site']:
        #Check slightly more 2
        if idx['rack']['name'] != None:
          #Check dict
          if idx['rack']['name'] in rackNameIDDict:
            numDevicesWithRackWithoutSite+=1
          else: #Both not in Dict
            numDevicesWithoutBoth+=1
        
        else: #Both not named
          numDevicesWithoutBoth+=1

      elif 'name' not in idx['rack'] and 'name' in idx['site']:
        #Check slightly more 2
        if idx['site']['name'] != None:
          #Check Dict
          if idx['site']['name'] in siteNamebldgIDDict:
            numDevicesWithSiteWithoutRack +=1
          else: #Both not in Dict
            numDevicesWithoutBoth+=1
        
        else: #Both not named
          numDevicesWithoutBoth+=1

      else: # Name not in both
        numDevicesWithoutBoth+=1


    elif idx['rack'] == None and idx['site'] != None:
      #Check more 2
      if 'name' in idx['site']:
        #Check slightly more
        if idx['site']['name'] != None:
          #Check Dict
          if idx['site']['name'] in siteNamebldgIDDict:
            numDevicesWithSiteWithoutRack+=1
          else: #Name not in both
            numDevicesWithoutBoth+=1
        
        else: #Name not in both
          numDevicesWithoutBoth+=1
      
      else: #Name not in both
        numDevicesWithoutBoth+=1

    elif idx['rack'] != None and idx['site'] == None:
      #Check more 2
      if 'name' in idx['rack']:
        #Check slightly more
        if idx['rack']['name'] != None:
          #Check Dict
          if idx['rack']['name'] in rackNameIDDict:
            numDevicesWithRackWithoutSite+=1
          else: #Name not in both
            numDevicesWithoutBoth+=1

        else: #Name not in both
          numDevicesWithoutBoth+=1

      else: #Name not in both
        numDevicesWithoutBoth+=1

    else: #Both indexes are None
      numDevicesWithoutBoth+=1

  elif 'rack' in idx and 'site' not in idx:
    if idx['rack'] != None:
      #Check more
      if 'name' in idx['rack']:
        #Check slightly more
        if idx['rack']['name'] != None:
          #Check Dict
          if idx['rack']['name'] in rackNameIDDict:
            numDevicesWithRackWithoutSite+=1

          else: #Name not in both
            numDevicesWithoutBoth+=1

        else: #Name not in both
          numDevicesWithoutBoth+=1

      else: #No name in both
        numDevicesWithoutBoth+=1

    else: #No rack no site
      numDevicesWithoutBoth+=1

  elif 'rack' not in idx and 'site' in idx:
    if idx['site'] != None:
      #Check more
      if 'name' in idx['site']:
        #Check slightly more
        if idx['site']['name'] != None:
          #Check Dict
          if idx['site']['name'] in rackNameIDDict:
            numDevicesWithSiteWithoutRack+=1

          else: #Name not in both
            numDevicesWithoutBoth+=1
            
        else: #Name not in both
          numDevicesWithoutBoth+=1

      else: #No name in both
        numDevicesWithoutBoth+=1

    else: #No rack no site
      numDevicesWithoutBoth+=1

  else:
    numDevicesWithoutBoth+=1
  
  x+=1


print("Num devices valid: ", numDevicesValid)
print("Num devices with Site without Rack: ", numDevicesWithSiteWithoutRack)
print("Num devices with Rack without Site: ", numDevicesWithRackWithoutSite)
print("Num devices without both: ", numDevicesWithoutBoth)