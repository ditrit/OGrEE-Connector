#!/usr/bin/env python
import requests, json, argparse, os, sys
from enum import Enum

# URLs
# LOCAL: http://localhost:3001/api/tenants
# DCIM: https://dcim.ogree.ditrit.io/api/dcim/racks/
# NETBX: https://api.ogree.ditrit.io/api/tenants


#COMMAND OPTIONS
#Will hold all the values necessary for importing
config = None

#Auth Token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'
dcim_token = '95d2a16ddb3670eecacb1018e0de484d1b8267e7'

head = {'Authorization': 'Bearer {}'.format(token)}
dhead = {'Authorization': 'Token {}'.format(dcim_token)}


# EXAION ID & Maps
eid = 0

#Dev Count
correctDevCount = 0
incorrectDevCount = 0
addedByRoom = 0
addedByBldg = 0
addedBySite = 0
addedByTenant = 0

#Maps for tracking added objs
#{DCIM-ID: (name, API-ID)}
tenantDict = {}
siteDict = {}
bldgDict = {}
roomDict = {}
rackDict = {}
deviceDict = {}

#ENUM Declaration and funcs
class Entity(Enum):
  TENANT = 0
  SITE = 1
  BUILDING = 2
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
def postObj(name, pid, oJSON, obj):
  oJSON['name'] = name
  oJSON['parentId'] = pid
  r = requests.post(config['APIURL']+"/"+obj+"s", 
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

  elif entityType == Entity.BUILDING.value:
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

  elif entityType == Entity.DEVICE.value:
    defJson['domain'] = 'Exaion'
    defJson['name'] = toImport['name']



  return defJson

def importAssignAttrsNewCustom(defJson, toImport, entity):
  for key in defJson:
    idx = defJson[key]
    if type(idx) is str:
      arr = idx.split(",")
      value = recursivelyResolve(toImport, arr, None)
      defJson[key] = value

    if type(idx) is list: #We will build an array to add
      indicator = idx[0]
      if indicator == 'manual': #Assign the value directly
        defJson[key] = idx[1]

      if indicator == 'default': #Retrieve value from default JSON
        entStr = entIntToStr(entity).lower()
        defaultJSON = getListFromFile(entStr)
        defJson[key] = defaultJSON[idx[1]]

      if indicator == 'array':
        arrLenLoc = idx[1]
        arr = arrLenLoc.split(",")
        actualLen = len(recursivelyResolve(toImport, arr, None))
        value = buildArrJson(actualLen, element, toImport)
        defJson[key] = value

  return defJson


def recursivelyResolve(toImport, arr, iterIdx):
  if len(arr) > 1:
    if arr[0] in toImport and toImport[arr[0]] != None:
      nextJson = toImport[arr[0]]
      return recursivelyResolve(nextJson, arr[1:])

  if arr[0] == "iter": #Dealing with array
    arr[0] = iterIdx
    nextJson = toImport[arr[0]]
    return recursivelyResolve(nextJson, arr[1:], None)

  if len(arr) == 1:
    if arr[0] in toImport and toImport[arr[0]] != None:
      nextJson = toImport[arr[0]]
      return nextJson
      
  return None

def buildArrJson(length, element, toImport):
  arr = []
  for i in length:
    for key in element:
      elt = element
      arr = elt[key].split(",")
      value = recursivelyResolve(toImport, arr, i)
      elt[key] = value

    arr.append(elt)

  return arr

  print()

#Gets Respective Default JSON
def getListFromFile(entType):
    filename = "defaultJSON/"+entType+".json"
    with open(filename) as f:
        objList = f.read()

    return json.loads(objList)

def loadJsonFile(path):
  filename = path
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
  if entStr == 'bldg':
    entStr = 'building'

  pRes = requests.get(config['APIURL']+"/"+entStr+"s/"+id, headers=head)
  if pRes.status_code != 200:
    print("Error while getting parent for placeholder")
    print("URL:",config['APIURL']+"/"+entStr+"s/"+id)
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

#If inserting placeholder with ancestors greater than 2
#the inserted key for the dict maps will be wrong
def fixDictKey(correct, wrong, map):
  v = map[wrong]
  map.pop(wrong)
  map[correct] = v
  

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

        

  if entityType == Entity.BUILDING.value:
    if 'site' in receivedObj:
      if receivedObj['site']!= None and 'name' in receivedObj['site'] and 'id' in receivedObj['site']:
        if receivedObj['site']['id'] in siteDict:
          #TUP -> (name, ID)
          tup = siteDict[receivedObj['site']['id']]
          return tup[1]

        #else site name given but not found
        sys.exit()


    #Use Exaion,(ID key of -1)
    #or tenant if present
    tDid = receivedObj['tenant']['id']
    tup = tenantDict[tDid]
    tid = tup[1]

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

    subTup = siteDict[(tup[0], 'siteA')]
    return subTup[1]

  
  if entityType == Entity.ROOM.value:
    if 'building' in receivedObj:
      if receivedObj['building'] != None and 'name' in receivedObj['building'] and 'id' in receivedObj['building']:
        if receivedObj['building']['id'] in bldgDict:
          #TUP -> (name, ID)
          tup = bldgDict[receivedObj['building']['id']]
          return tup[1]

        #Bldg name given but not found
        print('Bldg name given but not found')
        sys.exit()

    if 'site' in receivedObj:
      if receivedObj['site'] != None and 'name' in receivedObj['site'] and 'id' in receivedObj['site']:
        if receivedObj['site']['id'] in siteDict:
          #TUP -> (name, ID)
          sDid = receivedObj['site']['id']
          sTup = siteDict[sDid]
          sid = sTup[1]

          #Check if placeholder is present
          #otherwise create it
          if (sTup[0], 'buildingA') not in bldgDict:
            setupPlaceholderUnderObj(Entity.SITE.value, sid, sDid)

          subTup = bldgDict[(sTup[0], 'buildingA')]
          return subTup[1]

        #else site name given but not found
        print('Site name given but not found')
        sys.exit()


    #No ancestors present so let's use Exaion, index is -1
    #or tenant if it is present
    tDid = -1
    tup = tenantDict[tDid]
    tid = tup[1]
    if 'tenant' in receivedObj:
      if receivedObj['tenant'] != None and 'name' in receivedObj['tenant'] and 'id' in receivedObj['tenant']:
        if receivedObj['tenant']['id'] in tenantDict:
          tDid = receivedObj['tenant']['id']
          tup = tenantDict[tDid]
          tid = tup[1]

    if (tup[0], 'siteA') not in siteDict:
      setupPlaceholderUnderObj(Entity.TENANT.value, tid, did)

    if (tup[0], 'siteA', 'buildingA') not in bldgDict:
      sup = siteDict[(tup[0], 'siteA')]
      sid = sup[1]
      setupPlaceholderUnderObj(Entity.SITE.value, sid, None)
            
    #Unwanted key was inserted by function call
    #let's fix that
    v = bldgDict[('siteA', 'buildingA')]
    bldgDict.pop(('siteA', 'buildingA'))
    bldgDict[(tup[0], 'siteA', 'buildingA')] = v

    subTup = bldgDict[(tup[0], 'siteA', 'buildingA')]
    return subTup[1]


  if entityType == Entity.RACK.value:
    if 'location' in receivedObj:
      if receivedObj['location'] != None and 'name' in receivedObj['location'] and 'id' in receivedObj['location']:
        if receivedObj['location']['id'] in roomDict:
          rTup = roomDict[receivedObj['location']['id']]
          return rTup[1]

    if 'building' in receivedObj:
      if receivedObj['building'] != None and 'name' in receivedObj['building'] and 'id' in receivedObj['building']:
        if receivedObj['building']['id'] in bldgDict:
          bDid = receivedObj['building']['id']
          bTup = bldgDict[bDid]
          bid = bTup[1]

          if (bTup[0], 'roomA') not in roomDict:
            setupPlaceholderUnderObj(Entity.BUILDING.value, bid, None)

          subTup = roomDict[(bTup[0], 'roomA')]
          return subTup[1]

    if 'site' in receivedObj:
      if receivedObj['site'] != None and 'name' in receivedObj['site'] and 'id' in receivedObj['site']:
        if receivedObj['site']['id'] in siteDict:
          sDid = receivedObj['site']['id']
          sTup = siteDict[sDid]
          sid = sTup[1]

          if (sTup[0], 'buildingA') not in bldgDict:
            setupPlaceholderUnderObj(Entity.SITE.value, sid, None)

          if (sTup[0], 'buildingA', 'roomA') not in roomDict:
            bTup = bldgDict[(sTup[0], 'buildingA')]
            bid = bTup[1]
            setupPlaceholderUnderObj(Entity.BUILDING.value, bid, None)

            #Unwanted key was inserted at this point
            #when diff between entityType and found key is 2+
            v = roomDict[('buildingA', 'roomA')]
            roomDict.pop(('buildingA', 'roomA'))
            roomDict[(sTup[0], 'buildingA', 'roomA')] = v


          subTup = roomDict[(sTup[0], 'buildingA', 'roomA')]
          return subTup[1]


    #No ancestor found so Exaion or tenant if present
    tDid = -1
    tup = tenantDict[tDid]
    tid = tup[1]
    if 'tenant' in receivedObj:
      if receivedObj['tenant'] != None and 'name' in receivedObj['tenant'] and 'id' in receivedObj['tenant']:
        if receivedObj['tenant']['id'] in tenantDict:
          tDid = receivedObj['tenant']['id']
          tup = tenantDict[tDid]
          tid = tup[1]

    if (tup[0], 'siteA') not in siteDict:
      setupPlaceholderUnderObj(Entity.TENANT.value, tid, None)

    if (tup[0], 'siteA', 'buildingA') not in bldgDict:
      sTup = siteDict[(tup[0], 'siteA')]
      sid = sTup[1]
      setupPlaceholderUnderObj(Entity.SITE.value, sid, None)

    #Unwanted key was inserted at this point
    #when diff between entityType and found key is 2+
    v = bldgDict[('siteA', 'roomA')]
    bldgDict.pop(('siteA', 'roomA'))
    bldgDict[(tup[0], 'buildingA', 'roomA')] = v

    if (tup[0], 'siteA', 'buildingA', 'roomA') not in roomDict:
      bTup = bldgDict[(tup[0], 'siteA', 'buildingA')]
      bid = bTup[1]
      setupPlaceholderUnderObj(Entity.BUILDING.value, bid, None)

    #Unwanted key was inserted at this point
    #when diff between entityType and found key is 2+
    v = roomDict[('buildingA', 'roomA')]
    roomDict.pop(('buildingA', 'roomA'))
    roomDict[(tup[0], 'siteA', 'buildingA', 'roomA')] = v

    rTup = roomDict[(tup[0], 'siteA', 'buildingA', 'roomA')]
    return rTup[1]


  if entityType == Entity.DEVICE.value:
    global correctDevCount 
    global incorrectDevCount 
    global addedByRoom 
    global addedByBldg 
    global addedBySite 
    global addedByTenant
  
    if 'rack' in receivedObj:
      if receivedObj['rack'] != None and 'name' in receivedObj['rack'] and 'id' in receivedObj['rack']:
        if receivedObj['rack']['id'] in rackDict:
          rTup = rackDict[receivedObj['rack']['id']]
          correctDevCount += 1
          return rTup[1]

    if 'location' in receivedObj:
      if receivedObj['location'] != None and 'name' in receivedObj['location'] and 'id' in receivedObj['location']:
        if receivedObj['location']['id'] in roomDict:
          rDid = receivedObj['location']['id']
          rTup = roomDict[rDid]
          rid = rTup[1]

          if (rTup[0], 'rackA') not in rackDict:
            setupPlaceholderUnderObj(Entity.ROOM.value, rid, None)
          
          subTup = rackDict[(rTup[0], 'rackA')]
          addedByRoom += 1
          return subTup[1]


    if 'site' in receivedObj:
      if receivedObj['site'] != None and 'name' in receivedObj['site'] and 'id' in receivedObj['site']:
        if receivedObj['site']['id'] in siteDict:
          sDid = receivedObj['site']['id']
          sTup = siteDict[sDid]
          sid = sTup[1]

          if (sTup[0], 'buildingA') not in bldgDict:
            setupPlaceholderUnderObj(Entity.SITE.value, sid, None)

          if (sTup[0], 'buildingA', 'roomA') not in roomDict:
            bid = bldgDict[(sTup[0], 'buildingA')][1]
            setupPlaceholderUnderObj(Entity.BUILDING.value, bid, None)

            #Fix incorrect key 
            correctKey = (sTup[0], 'buildingA', 'roomA')
            wrongKey = ('buildingA', 'roomA')
            fixDictKey(correctKey, wrongKey, roomDict)


          if (sTup[0], 'buildingA', 'roomA', 'rackA') not in rackDict:
            rid = roomDict[(sTup[0], 'buildingA', 'roomA')][1]
            setupPlaceholderUnderObj(Entity.ROOM.value, rid, None)

            #Fix incorrect key
            correctKey = (sTup[0], 'buildingA', 'roomA', 'rackA')
            wrongKey = ('roomA', 'rackA')
            fixDictKey(correctKey, wrongKey, rackDict)


          rTup = rackDict[(sTup[0], 'buildingA', 'roomA', 'rackA')]
          addedBySite += 1
          return rTup[1]


    #Else check tenant or use Exaion
    tDid = -1
    tup = tenantDict[tDid]
    tid = tup[1]
    if 'tenant' in receivedObj:
      if receivedObj['tenant'] != None and 'name' in receivedObj['tenant'] and 'id' in receivedObj['tenant']:
        if receivedObj['tenant']['id'] in tenantDict:
          tDid = receivedObj['tenant']['id']
          tup = tenantDict[tDid]
          tid = tup[1]

    if (tup[0], 'siteA') not in siteDict:
      setupPlaceholderUnderObj(Entity.TENANT.value, tid, None)

    if (tup[0], 'siteA', 'buildingA') not in bldgDict:
      sid = siteDict[(tup[0], 'siteA')][1]
      setupPlaceholderUnderObj(Entity.SITE.value, sid, None)
      #Fix incorrect Key
      correctKey = (tup[0], 'siteA', 'buildingA')
      wrongKey = ('siteA', 'buildingA')
      fixDictKey(correctKey, wrongKey, bldgDict)


    if (tup[0], 'siteA', 'buildingA', 'roomA') not in roomDict:
      bid = bldgDict[(tup[0], 'siteA', 'buildingA')][1]
      setupPlaceholderUnderObj(Entity.BUILDING.value, bid, None)
      #Fix incorrect Key
      correctKey = (tup[0], 'siteA', 'buildingA', 'roomA')
      wrongKey = ('buildingA', 'roomA')
      fixDictKey(correctKey, wrongKey, roomDict)

    if (tup[0], 'siteA', 'buildingA', 'roomA', 'rackA') not in rackDict:
      rid = roomDict[(tup[0], 'siteA', 'buildingA', 'roomA')][1]
      setupPlaceholderUnderObj(Entity.ROOM.value, rid, None)
      #Fix incorrect Key
      correctKey = (tup[0], 'siteA', 'buildingA', 'roomA', 'rackA')
      wrongKey = ('roomA', 'rackA')
      fixDictKey(correctKey, wrongKey, rackDict)

    subTup = rackDict[(tup[0], 'siteA', 'buildingA', 'roomA', 'rackA')]
    addedByTenant += 1
    return subTup[1]


def getCorrespondingDict(entityType):
  if entityType == Entity.TENANT.value:
    return tenantDict
  elif entityType == Entity.SITE.value:
    return siteDict
  elif entityType == Entity.BUILDING.value:
    return bldgDict
  elif entityType == Entity.ROOM.value:
    return roomDict
  elif entityType == Entity.RACK.value:
    return rackDict
  elif entityType == Entity.DEVICE.value:
    return deviceDict

def getDefaultURL(entity):
  if entity == Entity.TENANT.value:
    return "https://dcim.ogree.ditrit.io/api/tenancy/tenants"
  
  ext = entIntToStr(entity).lower()+"s"
  return "https://dcim.ogree.ditrit.io/api/dcim/"+ext


#Parse Args START //////////
config = loadJsonFile("./config.json")
if config == None:
  print('Error, config file not found')
  print('Now exiting')
  sys.exit()

for i in range(Entity.DEVICE.value+1):
  ent = entIntToStr(i).lower()
  Ent = ent[0].upper()+ent[1:]
  if (Ent+'JSONTemplate' not in config or config[Ent+'JSONTemplate'] == None 
      or config[Ent+'JSONTemplate'] == ""):
      print(Ent+' Import Template not specified... using default template')
      #config[Ent+'JSONTemplate'] = getListFromFile(ent)

  if (Ent+'ImportUrl' not in config or config[Ent+'ImportUrl'] == None 
    or config[Ent+'ImportUrl'] == ""):
    print(Ent+' URL not specified... using default URL')
    config[Ent+'ImportUrl'] = getDefaultURL(i)


if ('APIURL' not in config or config['APIURL'] == None
     or config['APIURL'] == ""):
    print('API URL not specified... using default URL')
    config['APIURL'] = "https://api.ogree.ditrit.io"


if (config['APIKey'] != None):
  token = config['APIKey']
  head = {'Authorization': 'Bearer {}'.format(token)}

if config['ImportKey'] != None:
  dcim_token = config['ImportKey']
  dhead = {'Authorization': 'Token {}'.format(dcim_token)}

#Parse Args END //////////


x=0
end = Entity.DEVICE.value+1
pid = None

while(x < end):
  entity = (entIntToStr(x)).lower()
  jsonObj = getListFromFile(entity)
  Ent = entity[0].upper()+entity[1:]
  URL = config[Ent+"ImportUrl"]+"?limit=0"

  if x == Entity.SITE.value:
    pid = eid

  print(URL)
  r = requests.get(URL, headers=dhead)
  if r.status_code == 200:
    payload = r.json()['results']

    #Catch any remainder objects in the 'Next' URL
    while 'next' in r.json() and r.json()['next'] != None:
      URL = r.json()['next']
      r = requests.get(URL, headers=dhead)
      payload += r.json()['results']


    print("Number of "+entity+"s to be added: ", len(payload))


    #Iter thru all objs, assign attrs and post
    for i in  payload:
      if (Ent+'JSONTemplate' in config and
         config[Ent+'JSONTemplate'] != None and config[Ent+'JSONTemplate'] != ""):
         template = loadJsonFile(config[Ent+'JSONTemplate'])
         jsonObj = importAssignAttrsNewCustom(template, i, x)
      else:
        jsonObj = importAssignAttrs(jsonObj, i, x) 
         

      #Get ParentID before posting
      pid = getPid(x, i)
      res = postObj(jsonObj['name'], pid, jsonObj, entity)
      if res == False and jsonObj['name'] != 'Exaion':
        sys.exit()

      #Exaion is a placeholder which shall be indexed by -1
      if jsonObj['name'] == 'Exaion':
        i['id'] = -1
      
      getCorrespondingDict(x)[i['id']] = (jsonObj['name'], jsonObj['id'])


  else:
    #This means DCIM API doesn't have obj types
    #so we need to make placeholders
    #Iterate thru prevDict and add 
    #(prevEntName, PlaceHolderName) : (PlaceHolderName, placeHolderID)

    #Sometimes an ancestor is also a placeholder so it would be 
    #inserted as:
    #(AncestorName0,...,AncestorNameN, PlacHolderName) : 
    # (PlaceHolderName, placeHolderID) 

    prevDict = getCorrespondingDict(x-1)
    currDict = getCorrespondingDict(x)
    print(entity+'s were not found the Old Database')
    print('Therefore placeholders will be inserted')
    print()
    print('Adding ',len(prevDict),' placeholder '+entity+'s')
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
        correctKey = (prevDict[i][0], entIntToStr(x).lower()+"A")

      wrongKey = (prevDict[i][0], entIntToStr(x).lower()+"A")
      
      v = currDict[wrongKey]
      currDict.pop(wrongKey)
      currDict[correctKey] = v
      
    

  print('Successfully added '+entity+'s')
  print()
  x+=1


print('Device Count')
print('Added using direct parent:', correctDevCount)
print('Invalid:', incorrectDevCount)
print('Added using Room: ', addedByRoom)
print('Added using Bldg: ', addedByBldg)
print('Added using Site: ', addedBySite)
print('Added using Tenant: ', addedByTenant)
sys.exit()



#print("Num devices valid: ", numDevicesValid)
#print("Num devices with Site without Rack: ", numDevicesWithSiteWithoutRack)
#print("Num devices with Rack without Site: ", numDevicesWithRackWithoutSite)
#print("Num devices without both: ", numDevicesWithoutBoth)
#print("Num devices with NULL Rack: ", numRacksNull)
#print("Num devices with nameless Rack: ", numNamelessRacks)
#print("Num devices with unfindable Racks: ", numRackExistButNotFound)
#writeErrListToFile(deviceErrList)