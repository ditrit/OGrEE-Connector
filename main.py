#!/usr/bin/env python
import requests, json, argparse, os, sys
from enum import Enum

# URLs
# LOCAL: http://localhost:3001/api/tenants
# DCIM: https://dcim.ogree.ditrit.io/api/dcim/racks/
# NETBX: https://api.ogree.ditrit.io/api/tenants


#COMMAND OPTIONS
parser = argparse.ArgumentParser(description='Import from Netbox to file .')
parser.add_argument('--APIurl', 
                    help="""Specify which API URL to send data""")
parser.add_argument('--NBURL',
                    help="""Specify URL of Netbox""")
parser.add_argument("--APItoken", help="(Optionally) Specify a Bearer token for API")
parser.add_argument("--NBtoken", help="(Optionally) Specify a Netbox auth token")

#Auth Token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'
dcim_token = '95d2a16ddb3670eecacb1018e0de484d1b8267e7'

head = {'Authorization': 'Bearer {}'.format(token)}
dhead = {'Authorization': 'Token {}'.format(dcim_token)}


# EXAION ID & Maps
eid = 0
placeHolderDict = {}
tenantNameIDDict = {}
siteNamebldgIDDict = {}
roomNameIDDict = {}
rackNameIDDict = {}

#Maps for tracking added objs
#{DCIM-ID: (name, API-ID)}
tenantDict = {}
siteDict = {}
bldgDict = {}
roomDict = {}
rackDict = {}
deviceDict = {}

#Tuple arrays for tracking added objs
#[ (name,ID), ... ]
tenantArr = []
siteArr = []
bldgArr = []
roomArr = []
rackArr = []
devArr = []

#The dcim api doesn't have buildings and rooms so they are
#added as place holders
#bldgs will only have 1 room each
bldgIDRoomIDDict ={} 

#JSON Dicts
exaionJson = {}
tenantJson = {}
siteJson = {}
bldgJson = {}
roomJson = {}
rackJson = {}
deviceJson = {}


class Entity(Enum):
    TENANT = 0
    SITE = 1
    BLDG = 2
    ROOM = 3
    RACK  = 4
    DEVICE  = 5
    OBJ_TEMPLATE = 6
    ROOM_TEMPLATE = 7

def entStrToInt(ent):
    return Entity[ent].value

def entIntToStr(ent):
    return Entity(ent).name


# Helper func defs
# Get a corresponding room
# if 'group' is missing
# in json
def GetRoomName(siteName, BldgID):
  pr = requests.get(
    API+"/buildings/"+str(BldgID)+"/rooms",
     headers=head )
  return pr.json()['data']['objects'][0]['name']

def postObj(name, pid, oJSON, obj):
  oJSON['name'] = name
  oJSON['parentId'] = pid
  r = requests.post(API+"/"+obj+"s", 
                                    headers=head, json=oJSON)
  if r.status_code != 201:
    print("Error while creating "+obj+"!")
    print(oJSON)
    print(r.text)
    if obj == "device":
      writeErrListToFile(oJSON, "device")
    
    return False
  
  oJSON['id'] = r.json()['data']['id']
  return True

#Assigns the attributes of objs received from
#dcim to our default JSONs
def importAssignAttrs(defJson, toImport, entityType):
  if entityType == Entity.TENANT.value:
    defJson['name'] = toImport['name']
    defJson['description'] = ["ConnectorImported",toImport['description']]
    defJson['domain'] = toImport['name']

  elif entityType == Entity.SITE.value:
    defJson['name'] = toImport['name']
    defJson['description'] = ["ConnectorImported",toImport['description']]
    defJson['domain'] = 'Exaion'
    defJson['attributes']['address'] = toImport['physical_address']

  elif entityType == Entity.BLDG.value:
    defJson['name'] = toImport['name']
    defJson['description'] = ["ConnectorImported",toImport['description']]
    defJson['domain'] = 'Exaion'

  elif entityType == Entity.ROOM.value:
    defJson['domain'] = 'Exaion'
    defJson['name'] = toImport['name']
    defJson["description"] = ["ConnectorImported",toImport['description']]

  elif entityType == Entity.RACK.value:
    defJson['domain'] = 'Exaion'
    defJson['name'] = toImport['name']
    defJson['attributes']['height'] = toImport['u_height']


  return defJson

#Gets Respective JSON
def getListFromFile(entType):
    filename = "defaultJSON/"+entType+".json"
    with open(filename) as f:
        objList = f.read()

    return json.loads(objList)

#Write the unimported objects to file
def writeErrListToFile(devList, entType):
  filename = "./"+entType+"ErrList.json"
  print(filename)
  os.makedirs(os.path.dirname(filename), exist_ok=True)
  with open(filename, 'a') as f:
    json.dump(devList, f)

def setupPlaceholderUnderObj(entityType,id,did):
  #id -> use as PID for placeholder
  childInt = entityType + 1
  childEnt = entIntToStr(childInt).lower()

  entStr = entIntToStr(entityType).lower()

  pRes = requests.get(API+"/"+entStr+"s/"+id, headers=head)
  if pRes.status_code != 200:
    print("Error while getting parent for placeholder")
    print("URL:",API+"/"+entStr+"s/"+id)
    print("Entity:", entityType)
    print("ID:", id)
    print("Now exiting")
    sys.exit()



  cJSON = getListFromFile(childEnt)
  cJSON['name'] = childEnt+"A"
  cJSON['parentId'] = id
  cJSON['domain'] = pRes.json()['data']['domain']

  res = postObj(cJSON['name'], id, cJSON, childEnt)
  if res == False:
    print("Error while creating placeholder for OBJ:", id)
    sys.exit()

  #getCorrespondingDict(entityType)[did] = (cJSON['name'], cJSON['id'])
  parentIdx = (pRes.json()['data']['name'], cJSON['name'])
  getCorrespondingDict(childInt)[parentIdx] = (cJSON['name'], cJSON['id'])

  

    
def getPid(entityType, receivedObj):
  if entityType == Entity.TENANT.value:
    return None

  if entityType == Entity.SITE.value:
    if 'tenant' in receivedObj:
      if receivedObj['tenant']!= None and 'name' in receivedObj['tenant'] and 'id' in receivedObj['tenant']:
        if receivedObj['tenant']['id'] in tenantDict:
          tup = tenantDict[receivedObj['tenant']['id']]
          return tup[1]

        #Tenant name & DCIM ID given but not found
        tenantInt = Entity.TENANT.value
        tenantStr = entIntToStr(tenantInt).lower()
        tenantDID = receivedObj['tenant']['id']
        tenantName = receivedObj['tenant']['name']
        tJson = getListFromFile(tenantInt)
        tJson['domain'] = tenantName

        #Create tenant
        res = postObj(tenantName, None, tJSON, tenantStr)
        if res == False:
          print('Unable to create missing tenant')
          print('Now exiting')
          sys.exit()

        getCorrespondingDict(tenantInt)[tenantDID] = (tenantName, tJson['id'])
        return tJson['id']

    #Use Exaion otherwise.
    #It's DCIM ID was assigned -1
    #for our purposes
    tup = tenantDict[-1]
    return tup[1]

        

  if entityType == Entity.BLDG.value:
    if 'site' in receivedObj:
      if receivedObj['site']!= None and 'name' in receivedObj['site'] and 'id' in receivedObj['site']:
        if receivedObj['site']['id'] in siteDict:
          #TUP -> (name, ID)
          tup = siteDict[receivedObj['site']['id']]
          print('TUP1 return site name found')
          return tup[1]

        #else site name given but not found
        print('Site name given but not found')
        sys.exit()

    if 'tenant' in receivedObj:
      if receivedObj['tenant'] != None and 'name' in receivedObj['tenant'] and 'id' in receivedObj['tenant']:
        if receivedObj['tenant']['id'] in tenantDict:
          #TUP -> (name, ID)
          tDid = receivedObj['tenant']['id']
          tup = tenantDict[tDid]
          tid = tup[1]

          #Check if placeholder is present
          #otherwise create it
          if (tup[0], 'siteA') not in siteDict:
            setupPlaceholderUnderObj(Entity.TENANT.value, tid, tDid)

          subTup = siteDict[[tup[0], 'siteA']]
          print('SUBTUP1 return tenant name found')
          return subTup[1]

        #else tenant name given but not found
        print('Tenant name given but not found')
        sys.exit()

    else: #Both not present
      #Use Exaion, it should be there by default
      #Exaion will always have ID key of -1 for
      #our purposes
      tenantTup = tenantDict[-1]
      if (tenantTup[0], 'siteA') not in siteDict:
        setupPlaceholderUnderObj(Entity.TENANT.value, tenantTup[1], -1)
      
      subTup = siteDict[[tenantTup[0], 'siteA']]
      print('SUBTUP1 return nothing name found')
      return subTup[1]

  





#Generate Placeholder objects in case 
#some objects don't have parents/ancestors
def setupPlaceholders():
  idx = Entity.TENANT.value
  pid = None
  global eid

  entity = entIntToStr(idx).lower()
  entJSON = getListFromFile(entity)
  entJSON['domain'] = 'Exaion'

  postObj('Exaion', None, entJSON, entity)

  r = requests.post(API+"/"+entity+"s", 
                                    headers=head, json=entJSON)

  if r.status_code != 201:
    print("Error while creating "+entity+"!")
    print(entJSON)
    print(r.text)
    sys.exit()

  print('Assigning EID')
  eid = r.json()['data']['id'] #Lags behind for next iter
  
  #eid = r.json()['data']['id']

"""   while idx < Entity.DEVICE.value+1:
    entity = entIntToStr(idx).lower()
    entJSON = getListFromFile(entity)
    entJSON['domain'] = 'Exaion'
    entJSON['parentId'] = pid

    if idx == Entity.TENANT.value:
      entJSON['name'] = name = 'Exaion'
    else:
      entJSON['name'] = name = entity+"A"

    r = requests.post(API+"/"+entity+"s", 
                                    headers=head, json=entJSON)

    if r.status_code != 201:
      print("Error while creating "+entity+"!")
      print(entJSON)
      print(r.text)
      sys.exit()


    pid = r.json()['data']['id'] #Lags behind for next iter
    placeHolderDict[entity] = r.json()['data']['id']
    if entJSON['name'] == 'Exaion':
      print('Assigning EID')
      eid = r.json()['data']['id']

    idx += 1 """

def getCorrespondingDict(entityType):
  if entityType == Entity.TENANT.value:
    return tenantDict
  elif entityType == Entity.SITE.value:
    return siteDict
  elif entityType == Entity.BLDG.value:
    return bldgDict
  elif entityType == Entity.ROOM.value:
    return roomDict
  elif entityType == Entity.RACK.value:
    return rackDict
  elif entityType == Entity.DEVICE.value:
    return deviceDict

def getCorrespondingArr(entityType):
  if entityType == Entity.TENANT.value:
    return tenantArr
  elif entityType == Entity.SITE.value:
    return siteArr
  elif entityType == Entity.BLDG.value:
    return bldgArr
  elif entityType == Entity.ROOM.value:
    return roomArr
  elif entityType == Entity.RACK.value:
    return rackArr
  elif entityType == Entity.DEVICE.value:
    return devArr



#Parse Args START //////////
args = vars(parser.parse_args())
if ('NBURL' not in args or args['NBURL'] == None):
    print('Netbox URL not specified... using default URL')
    NBURL = "https://dcim.chibois.net/api"
else:
    NBURL = args['NBURL']

if ('APIurl' not in args or args['APIurl'] == None):
    print('API URL not specified... using default URL')
    API = "https://ogree.chibois.net/api/user"
else:
    API = args['APIurl']


if (args['APItoken'] != None):
  token = args['APItoken']
  head = {'Authorization': 'Bearer {}'.format(token)}

if args['NBtoken'] != None:
  dcim_token = args['NBtoken']
  dhead = {'Authorization': 'Token {}'.format(dcim_token)}

#Parse Args END //////////

#Setup Placeholder objs
#setupPlaceholders()

x=0
end = Entity.OBJ_TEMPLATE.value
pid = None

while(x < end):
  entity = (entIntToStr(x)).lower()
  jsonObj = getListFromFile(entity)
  if x == Entity.TENANT.value:
    URL = NBURL+"/tenancy/"+entity+"s/"

  if x == Entity.SITE.value:
    URL = NBURL+"/dcim/"+entity+"s/"
    pid = eid

  if x == Entity.BLDG.value:
    URL = NBURL+"/dcim/"+entity+"s/"

  if x == Entity.ROOM.value:
    URL = NBURL+"/dcim/locations/"

  if x == Entity.RACK.value:
    URL = NBURL+"/dcim/"+entity+"s/"



  r = requests.get(URL, headers=dhead)
  if r.status_code == 200:
    print("Number of "+entity+"s to be added: ", len(r.json()['results']))


    #Iter thru all objs, assign attrs and post
    for i in  r.json()['results']:
      jsonObj = importAssignAttrs(jsonObj, i, x)    

      #Get ParentID before posting
      if x > Entity.TENANT.value:
        #pid = getCorrespondingArr(x - 1)
        pid = getPid(x, i)

      res = postObj(jsonObj['name'], pid, jsonObj, entity)
      if res == False and jsonObj['name'] != 'Exaion':
        sys.exit()

      #getCorrespondingDict(x)[jsonObj['name']] = jsonObj['id']
      #getCorrespondingArr(x).append((jsonObj['name'], jsonObj['id']))
      if jsonObj['name'] == 'Exaion':
        i['id'] = -1
      
      getCorrespondingDict(x)[i['id']] = (jsonObj['name'], jsonObj['id'])


  else:
    #This means DCIM API doesn't have obj types
    #so we need to make placeholders
    '''print(entIntToStr(x))
    parentInt = x-1
    pArr = getCorrespondingArr(parentInt)
    for i in pArr:
      postObj(jsonObj['name'], i[1], jsonObj, entIntToStr(x).lower())
      getCorrespondingArr(x).append((jsonObj['name'], jsonObj['id']))'''

    prevDict = getCorrespondingDict(x-1)
    currDict = getCorrespondingDict(x)
    for i in prevDict:
      setupPlaceholderUnderObj(x-1, str(prevDict[i][1]), None)

      #Adding placeholder inserts unwanted keys into curr level dict
      #so we need to fix that
      correctKey = ()
      if isinstance(i, tuple):
        tmp = list(i)
        tmp += entIntToStr(x).lower()+"A"
        correctKey = tuple(tmp)
      else:
        correctKey = (i)

      wrongKey = (prevDict[i][0], entIntToStr(x).lower()+"A")
      
      v = currDict[wrongKey]
      currDict.pop(wrongKey)
      currDict[correctKey] = v
      
    

  print('Successfully added '+entity+'s')
  x+=1

sys.exit()



# Obtain the big list of Sites
# Store into MDB and add
# a placeholder bldg to each site
r = requests.get(NBURL+"/dcim/sites/", headers=dhead)
print("Number of Sites to be added: ", len(r.json()['results']))
print("Adding Sites...")
siteJson = getListFromFile("site")
x = 0 
for entry in r.json()['results']:

  siteJson['name'] = entry['name']
  siteJson['description'] = ["ConnectorImported",entry['description']]
  siteJson['parentId'] = eid
  siteJson['domain'] = 'Exaion'
  siteJson['attributes']['address'] = entry['physical_address']
  print(x, ": ", entry['name'])
  x+=1
  pr = requests.post(API+"/sites",
   headers=head, data=json.dumps(siteJson) )
  if pr.status_code != 201:
    print("Error with site!")
    print(pr.text)
    exit()

  siteID = pr.json()['data']
  print("Adding corresponding building")
  #bldgJson = {
  #"name": "BldgA",
  #"id": None, #API doesn't allow non Server Generated IDs
  #"parentId": siteID['id'],
  #"category": "building",
  #"description": ["ConnectorImported","Some Building"],
  #"domain": "Exaion",
  #"attributes": {
  #  "posXY": "99,99",
  #  "posXYUnit": "mm",
  #  "posZ":"99",
  #  "posZUnit": "mm",
  #  "size":"99",
  #  "sizeUnit": "mm",
  #  "height":"99",
  #  "heightUnit": "mm",
  #  "nbFloors":"99"
  #  }
  #}

  bldgJson = getListFromFile("bldg")
  bldgJson["parentId"] = siteID['id']
  bldgJson["domain"] = "Exaion"
  bldgJson["description"] = ["ConnectorImported","Some Building"]
  tmpr = requests.post(API+"/buildings",
  headers=head, data=json.dumps(bldgJson) )
  if tmpr.status_code != 201:
    print("Error while adding bldg!")
    print(tmpr.text)
    exit()

  siteNamebldgIDDict[siteID['name']] = tmpr.json()['data']['id']
  print(bldgJson['name'])

  print("Adding corresponding room")
  roomJson = getListFromFile("bldg")
  roomJson["parentId"] = tmpr.json()["data"]["id"]
  roomJson["domain"] = "Exaion"
  roomJson["name"] = "RoomA"
  roomJson["description"] = ["ConnectorImported"]
  roomJson["attributes"] = {
    "floorUnit":'m',
      "posXY": "99,99",
      "posXYUnit": "mm",
      "posZ":"99",
      "posZUnit": "mm",
      "size":"99",
      "sizeUnit": "mm",
      "height":"99",
      "heightUnit": "mm",
      "nbFloors":"99",
      "orientation":"-E-N"
  }

  tmpr2 = requests.post(API+"/rooms",
  headers=head, data=json.dumps(roomJson) )
  if tmpr2.status_code != 201:
    print("Error while adding room!")
    print(tmpr2.text)
    exit()

  bldgIDRoomIDDict[tmpr.json()['data']['id']] = tmpr2.json()['data']['id']




# Obtain the big list of Rooms (Rack-Groups)
# Store using tenant 'Exaion' and site name
#r = requests.get(NBURL+"/dcim/rack-groups/",
# headers=dhead)
'''r = requests.get(NBURL+"/dcim/racks/",
 headers=dhead)
x = 0
for idx in r.json()['results']:
  print(x, ": ", idx['name'], ": PARENT: ", idx['site']['name'])
  roomJson = {
    "id": None,
    "name": idx['name'],
    "parentId": bldgIDRoomIDDict[siteNamebldgIDDict[idx['site']['name']]],
    "category": "room",
    "domain": "Exaion",
    "description": [
        "ConnectorImported"
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
  tmpr = requests.post(API+"/rooms",
  headers=head, data=json.dumps(roomJson) )
  roomNameIDDict[idx['name']] = tmpr.json()['data']['id']
  x+=1'''


# Obtain the big list of Racks
# store using the room Name & 
# corresponding ID
r = requests.get(NBURL+"/dcim/racks/?limit=0",
 headers=dhead)
totalRacks = r.json()['results']
print("Number of Racks to be added: ", len(totalRacks))
print("Adding Racks...")
x = 0
for idx in totalRacks:
  #print(x, ": ", idx['name'])
  #if idx['group'] == None:
    #name = 
    #pid = roomNameIDDict[GetRoomName(idx['site']['name'], 
    #  siteNamebldgIDDict[idx['site']['name']])]
  pid = bldgIDRoomIDDict[siteNamebldgIDDict[idx['site']['name']]]
  name = idx['name']
  #else:
  #  print('PROBLEM CASE ENCOUNTERED')
  #  name = idx['name']
  #  pid = roomNameIDDict[idx['group']['name']]
  #print(x, ": ", str(name))
  rackJson = {
    "id": None,
    "name": str(name),
    "parentId": str(pid),
    "category": "rack",
    "domain": "Exaion",
    "description": [
      "ConnectorImported"
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
  tmpr = requests.post(API+"/racks",
  headers=head, data=json.dumps(rackJson) )
  x+=1
  if 'data' in tmpr.json():
    if 'id' in tmpr.json()['data']:
      rackNameIDDict[str(name)] = tmpr.json()['data']['id']
  else:
    print('Error with rack: ', str(name))
    print(tmpr.json()['message'])
    writeErrListToFile(rackJson, "rack")


#GET Devices from Netbox
deviceJson = {
    "name": None,
    "id": None,
    "parentId": None,
    "category": "device",
    "description": ["ConnectorImported"
    ],
    "domain": "Exaion",
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
numRacksNull = 0
numRackExistButNotFound = 0
numNamelessRacks = 0
res = requests.get(NBURL+"/dcim/devices/?limit=2000",
 headers=dhead)
r = requests.get(res.json()['next'], headers=dhead)
devices = res.json()['results'] + r.json()['results']
#deviceErrList = []

print("Number of Devices to check: ", len(devices))
print("Checking Devices...")
x = 0
for idx in devices:
  print(x, ": ", idx['name'])
  #print()

  if 'rack' in idx and 'site' in idx:
    if idx['rack'] != None and idx['site'] != None:
      if 'name' in idx['rack'] and 'name' in idx['site']:
        #Check slightly more
        if (idx['rack']['name'] != None and idx['site']['name'] != None):
          #Check Dict 
          if (idx['site']['name'] in siteNamebldgIDDict and
            idx['rack']['name'] in rackNameIDDict) :
            numDevicesValid+=1
            postObj(idx['name'], rackNameIDDict[idx['rack']['name']], deviceJson, "device")
          
          elif (idx['site']['name'] in siteNamebldgIDDict and
            idx['rack']['name'] not in rackNameIDDict) :
            numDevicesWithSiteWithoutRack+=1
            numNamelessRacks+=1
            writeErrListToFile(idx, "device")
            #deviceErrList += idx

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
            numRacksNull+=1
            numDevicesWithSiteWithoutRack+=1
            writeErrListToFile(idx, "device")
            #deviceErrList += idx
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
            numNamelessRacks+=1
            writeErrListToFile(idx, "device")
            #deviceErrList += idx
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
            numRacksNull+=1
            numDevicesWithSiteWithoutRack+=1
            writeErrListToFile(idx, "device")
            #deviceErrList += idx
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
            numRacksNull+=1
            writeErrListToFile(idx, "device")
            #deviceErrList += idx

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
print("Num devices with NULL Rack: ", numRacksNull)
print("Num devices with nameless Rack: ", numNamelessRacks)
print("Num devices with unfindable Racks: ", numRackExistButNotFound)
#writeErrListToFile(deviceErrList)


