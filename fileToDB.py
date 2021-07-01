#!/usr/bin/env python
import requests, json,os, argparse
from enum import Enum

# URLs
# LOCAL: http://localhost:8000/api/user/tenants
# DCIM: https://api.chibois.net/api/dcim/racks/
# NETBX: https://dcim.chibois.net/api/dcim/racks


#Auth Token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'
head = {'Authorization': 'Bearer {}'.format(token)}

#CONSTANTS
class Hierarchy(Enum):
    TENANT = 0
    SITE = 1
    BLDG = 2
    ROOM = 3
    RACK = 4
    DEVICE = 5
    SUBDEVICE = 6
    SUBDEVICE1 = 7

objToHierarchyDict = {
    "tenant": Hierarchy.TENANT,
    "site" : Hierarchy.SITE,
    "bldg": Hierarchy.BLDG,
    "building": Hierarchy.BLDG,
    "group": Hierarchy.ROOM,
    "rack": Hierarchy.RACK,
    "device": Hierarchy.DEVICE,
    "subdevice": Hierarchy.SUBDEVICE,
    "subdevice1": Hierarchy.SUBDEVICE1
}

TenantDict = {}
SiteDict = {}
SiteNameBldgIDDict = {}
BldgDict = {}
RoomDict = {}
RackDict = {}
DeviceDict = {}
SubdeviceDict = {}

EID = 0

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

tenantJson = {
  "name": "", #tenant['name'],
  "id": None, #API doesn't allow non Server Generated IDs
  "parentId": None,
  "category": "tenant",
  "description": "", #[tenant['description']],
  "domain": "Connector Domain",
  "attributes": {
    "color": "Connector Color",
    "mainContact": None,
    "mainPhone": None,
    "mainEmail": None
  }
}

siteJson = {
  "name": "", #entry['name'],
  "id": None, #API doesn't allow non Server Generated IDs
  "parentId":"", # eid, #No site in Netbox has an existing tenant => place in Exaion 
  "category": "site",
  "description": "", #[entry['description']],
  "domain": "Connector Domain",
  "attributes": {
    "orientation": "NW",
    "usableColor": "ExaionColor",
    "reservedColor": "ExaionColor",
    "technicalColor": "ExaionColor",
    "address": "", #entry['physical_address'],
    "zipcode": None,
    "city": None,
    "country": None,
    "gps": None # None of the sites have coordinates
  }
}

bldgJson = {
  "name": "BldgA",
  "id": None, #API doesn't allow non Server Generated IDs
  "parentId": "", #siteID['id'],
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

roomJson = {
    "id": None,
    "name": "", #idx['name'],
    "parentId": "", #siteNamebldgIDDict[idx['site']['name']],
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


rackJson = {
    "id": "", #None,
    "name": "", #str(name),
    "parentId": "", #str(pid),
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
        "height": "", #str(idx['u_height']),
        "heightUnit": "U",
        "vendor": "someVendor",
        "type": "someType",
        "model": "someModel",
        "serial": "someSerial"
    }
}

#COMMAND OPTIONS
parser = argparse.ArgumentParser(description='Import from file to DB .')
parser.add_argument('--objects', choices=["tenant","site", "bldg", "room", 
                    "rack", "device", "subdevice", "subdevice1"],
                    help="""Option to select which objects to add.
                    Note they are inclusive (ie specifying subdevices
                    will import everything until subdevices). Default: Rack""")
parser.add_argument('--dir',
                    help="""Location of JSON files.
                    All files shall be in the form {entity}List.json
                    '""")

#FUNCTION DEFINTIONS
def getListFromFile(entType):
    filename = dir+"/"+entType.name.lower()+"List.json"
    with open(filename) as f:
        objList = f.read()

    return json.loads(objList)

def getStdJson(x):
    if x == -1:
        return exaionJson
    if x == 0:
        return tenantJson
    if x == 1:
        return siteJson
    if x == 2:
        return bldgJson
    if x == 3:
        return roomJson
    if x == 4:
        return rackJson
    if x == 5:
        return None

def createExaionTenant():
    j = exaionJson
    r = requests.post("https://ogree.chibois.net/api/user/tenants", 
        headers=head, json=j)
    return r.json()['data']['id']
    
def post(item, url):
    r = requests.post(url, headers=head, json=item)
    if r.status_code != 201:
        print("Error while creating obj!")
        print(r.text)
        print(item)
        exit(-1)
    
    return r.json()['data']['id']

def genBldgForSite(url, sid, sname):
    bj = bldgJson
    bj['parentId'] = sid
    r = requests.post(url, headers=head, json=bj)
    SiteNameBldgIDDict[sname] = r.json()['data']['id']

def getCorrespondingDict(x):
    if x == 0:
        return TenantDict
    if x == 1:
      return SiteDict
    if x == 2:
      return BldgDict
    if x == 3:
      return RoomDict
    if x == 4:
      return RackDict
    if x == 5:
      return DeviceDict
    if x == 6:
      return SubdeviceDict

def GetRoomName(siteName, BldgID):
  pr = requests.get(
    "https://ogree.chibois.net/api/user/buildings/"+str(BldgID)+"/rooms",
     headers=head )
  return (pr.json()['data']['objects'][0]['name'], 
    pr.json()['data']['objects'][0]['id'])

#PARSE ARGUMENTS
args = vars(parser.parse_args())
if ('dir' not in args or args['dir'] == None):
    print('Directory not specified... using current dir')
    dir = "."
else:
    dir = args['dir']

if args['objects'] != None:
    depth = objToHierarchyDict[args['objects']].value
else:
    print('Objects not specified... using Device as dump limit')
    depth = Hierarchy(5).value #DEVICE


#START
EID = createExaionTenant()
x = 0
while x < depth:
    sj = getStdJson(x)
    #if x == 0: # TENANT
    #    url = "https://ogree.chibois.net/api/user/tenants"
    #if x == 1: # SITE
    #    url = "https://ogree.chibois.net/api/user/sites"
    #if x == 2: # BLDG --> ROOM
    #    print("No such thing as buildings, skipping")
    #    x+=1
    #    url = "https://ogree.chibois.net/api/user/rooms"
    #if x == 4: # RACK
    #    url = "https://ogree.chibois.net/api/user/racks"
    #if x == 5: # DEVICE
    #    url = "https://ogree.chibois.net/api/user/devices"

    if x != 2:
        objList = getListFromFile(Hierarchy(x))
    
    for idx in objList:
        if x == 0: # TENANT
            url = "https://ogree.chibois.net/api/user/tenants"
            sj['name'] = idx['name']
            sj['description'] = [idx['description']]
            r = post(sj, url)
        if x == 1: # SITE
            url = "https://ogree.chibois.net/api/user/sites"
            sj['name'] = idx['name']
            sj['description'] = [idx['description']]
            sj['parentId'] = EID #No site in Netbox has an existing tenant => place in Exaion 
            r = post(sj, url)
        if x == 2: # BLDG --> ROOM
            print("No such thing as buildings, generating rand bldgs...")
            #x+=1
            url = "https://ogree.chibois.net/api/user/rooms"
            sj = getStdJson(x+1)
            sj['name'] = idx['name']
            #print(idx)
            sj['parentId'] = SiteNameBldgIDDict[idx['name']]
            print(sj['name'])
            r = post(sj, url)
        if x == 4: # RACK
            url = "https://ogree.chibois.net/api/user/racks"
            sj['id'] = None
            sj['name'] = idx['name']

            if idx['group'] == None:
                nameIDSet = GetRoomName(idx['site']['name'], 
                    SiteNameBldgIDDict[idx['site']['name']])
                name = nameIDSet[0]
                print(RoomDict)
                pid = nameIDSet[1]
            else:
                name = idx['name']
                pid = RoomDict[idx['group']['name']]

            sj['parentId'] = pid
            sj['attributes']['height'] = str(idx['u_height'])
            r = post(sj, url)
        if x == 5: # DEVICE
            url = "https://ogree.chibois.net/api/user/devices"
            r = post(sj, url)

        
        if x == 1:
            genBldgForSite("https://ogree.chibois.net/api/user/buildings",
            r, idx['name'])
        getCorrespondingDict(x)[idx['name']] = r
    x+=1

