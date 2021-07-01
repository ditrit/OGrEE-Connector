import requests,json,random
from enum import Enum
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
BldgDict = {}
RoomDict = {}
RackDict = {}
DeviceDict = {}
SubdeviceDict = {}

dcim_token = '95d2a16ddb3670eecacb1018e0de484d1b8267e7'
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'
head = {'Authorization': 'Bearer {}'.format(token)}
dhead = {'Authorization': 'Token {}'.format(dcim_token)}

def searchPID(entType, x):
  if entType == 0:
    url = "https://ogree.chibois.net/api/user/tenants"
  if entType == 1:
    url = "https://ogree.chibois.net/api/user/sites"
  if entType == 2:
    url = "https://ogree.chibois.net/api/user/buildings"
  if entType == 3:
    url = "https://ogree.chibois.net/api/user/rooms"
  if entType == 4:
    url = "https://ogree.chibois.net/api/user/racks"
  if entType == 5:
    url = "https://ogree.chibois.net/api/user/devices"
  
  r = requests.get(url, headers=head)
  for idx in r.json()['data']['objects']:
    if idx['name'] == x:
      return idx['parentId']

  print('No parent found while obtaining PID!')
  return r.json()['data']['objects'][0]['parentId']

def getEntityIDDict(x):
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


def getParentDict(entype):
    if entype == 0:
        return

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

def getRandName(x):
  num = random.randint(0, 64)
  objName = list(objToHierarchyDict.keys())[list(objToHierarchyDict.values()).index(Hierarchy(x))]
  return 'Exaion_'+objName+str(num)

def genParent(item, entType):
  if entType != -1:
    parent = list(objToHierarchyDict.keys())
    [list(objToHierarchyDict.values()).index(Hierarchy(entType -1 ))]
    if parent not in item:
      pid = genParent(item, entType - 1)
    else:
      pid = getEntityIDDict(entType)[item[parent]]
      if pid == None:
        pid = genParent(item, entType - 1)
      
    PJ = getStdJson(entType)
    if 'name' not in item or item['name'] == None:
      name = getRandName(entType)
    else:
      name = item['name']
    
    
    PJ = getStdJson(entType - 1)
    PJ['parentId'] = searchPID(entType, name)
    PJ['name'] = name

    
    if entType == 0:
      url = "https://ogree.chibois.net/api/user/tenants"
    if entType == 1:
      url = "https://ogree.chibois.net/api/user/sites"
    if entType == 2:
      url = "https://ogree.chibois.net/api/user/buildings"
    if entType == 3:
      url = "https://ogree.chibois.net/api/user/rooms"
    if entType == 4:
      url = "https://ogree.chibois.net/api/user/racks"
    if entType == 5:
      url = "https://ogree.chibois.net/api/user/devices"
    
    r = requests.post(url, 
      headers=head,  data=json.dumps(PJ))
    if r.status_code != 201:
      print("Error while creating parent!")
      print(r.text)
      exit(-1)
    
    getEntityIDDict(entType)[name] = r.json()['data']['id']
    return r.json()['data']['id']
  else:
    PJ = getStdJson(-1)
    PJ['name']= 'Exaion'
    r = requests.post("https://ogree.chibois.net/api/user/tenants", 
      headers=head,  data=json.dumps(PJ))
    if r.status_code != 201:
      print("Error while creating parent!")
      print(r.text)
      exit(-1)

    getEntityIDDict(entType)['Exaion'] = r.json()['data']['id']
    return r.json()['data']['id']



def createTenant(item):
    stdJ = tenantJson
    stdJ['name'] = item['name']
    stdJ['description'] = [item['description']]

    return stdJ

def createItem(item, entType):
    stdJ = getStdJson(entType)
    stdJ['name'] = item['name']
    stdJ['description'] = [item['description']]
    parent = list(objToHierarchyDict.keys())[list(objToHierarchyDict.values()).index(Hierarchy(entType))]
    if parent not in item:
      genParent(item, entType)
    else:
      pid = getEntityIDDict(entType)[item[parent]]
    
    if pid == None:
      genParent(item, entType)
    

    if entType == 1: # Site
      stdJ['address'] = item['physical_address']
      stdJ['name'] = item['name']
      stdJ['parentId'] = searchPID(entType, item['name'])
    if entType == 2:
      


    return stdJ