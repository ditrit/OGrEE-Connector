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

  elif entityType == Entity.DEVICE.value:
    defJson['domain'] = 'Exaion'
    defJson['name'] = toImport['name']



  return defJson

#Gets Respective Default JSON
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
  if entStr == 'bldg':
    entStr = 'building'

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

        

  if entityType == Entity.BLDG.value:
    if 'site' in receivedObj:
      if receivedObj['site']!= None and 'name' in receivedObj['site'] and 'id' in receivedObj['site']:
        if receivedObj['site']['id'] in siteDict:
          #TUP -> (name, ID)
          tup = siteDict[receivedObj['site']['id']]
          return tup[1]

        #else site name given but not found
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

          subTup = siteDict[(tup[0], 'siteA')]
          return subTup[1]

        #else tenant name given but not found
        sys.exit()

    else: #Both not present
      #Use Exaion, it should be there by default
      #Exaion will always have ID key of -1 for
      #our purposes
      tenantTup = tenantDict[-1]
      if (tenantTup[0], 'siteA') not in siteDict:
        setupPlaceholderUnderObj(Entity.TENANT.value, tenantTup[1], -1)
      
      subTup = siteDict[(tenantTup[0], 'siteA')]
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
          if (sTup[0], 'bldgA') not in bldgDict:
            setupPlaceholderUnderObj(Entity.SITE.value, sid, sDid)

          subTup = bldgDict[(sTup[0], 'bldgA')]
          return subTup[1]

        #else site name given but not found
        print('Site name given but not found')
        sys.exit()

    if 'tenant' in receivedObj:
      if receivedObj['tenant'] != None and 'name' in receivedObj['tenant'] and 'id' in receivedObj['tenant']:
        if receivedObj['tenant']['id'] in tenantDict:
          tDid = receivedObj['tenant']['id']
          tup = tenantDict[tDid]
          tid = tup[1]

          if (tup[0], 'siteA') not in siteDict:
            setupPlaceholderUnderObj(Entity.TENANT.value, tid, did)

          if (tup[0], 'siteA', 'bldgA') not in bldgDict:
            sup = siteDict[(tup[0], 'siteA')]
            sid = sup[1]
            setupPlaceholderUnderObj(Entity.SITE.value, sid, None)
            
            #Unwanted key was inserted by function call
            #let's fix that
            v = bldgDict[('siteA', 'bldgA')]
            bldgDict.pop(('siteA', 'bldgA'))
            bldgDict[(tup[0], 'siteA', 'bldgA')] = v

          subTup = bldgDict[(tup[0], 'siteA', 'bldgA')]
          return subTup[1]

    else: #No ancestors present so let's use Exaion, index is -1
      tDid = -1
      tup = tenantDict[tDid]
      tid = tup[1]

      if (tup[0], 'siteA') not in siteDict:
        setupPlaceholderUnderObj(Entity.TENANT.value, tid, None)

      if (tup[0], 'siteA', 'bldgA') not in bldgDict:
        sup = siteDict[(tup[0], 'siteA')]
        sid = sup[1]
        setupPlaceholderUnderObj(Entity.SITE.value, sid, None)
            
        #Unwanted key was inserted by function call
        #let's fix that
        v = bldgDict[('siteA', 'bldgA')]
        bldgDict.pop(('siteA', 'bldgA'))
        bldgDict[(tup[0], 'siteA', 'bldgA')] = v

      subTup = bldgDict[(tup[0], 'siteA', 'bldgA')]
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
            setupPlaceholderUnderObj(Entity.BLDG.value, bid, None)

          subTup = roomDict[(bTup[0], 'roomA')]
          return subTup[1]

    if 'site' in receivedObj:
      if receivedObj['site'] != None and 'name' in receivedObj['site'] and 'id' in receivedObj['site']:
        if receivedObj['site']['id'] in siteDict:
          sDid = receivedObj['site']['id']
          sTup = siteDict[sDid]
          sid = sTup[1]

          if (sTup[0], 'bldgA') not in bldgDict:
            setupPlaceholderUnderObj(Entity.SITE.value, sid, None)

          if (sTup[0], 'bldgA', 'roomA') not in roomDict:
            bTup = bldgDict[(sTup[0], 'bldgA')]
            bid = bTup[1]
            setupPlaceholderUnderObj(Entity.BLDG.value, bid, None)

            #Unwanted key was inserted at this point
            #when diff between entityType and found key is 2+
            v = roomDict[('bldgA', 'roomA')]
            roomDict.pop(('bldgA', 'roomA'))
            roomDict[(sTup[0], 'bldgA', 'roomA')] = v


          subTup = roomDict[(sTup[0], 'bldgA', 'roomA')]
          return subTup[1]

    if 'tenant' in receivedObj:
      if receivedObj['tenant'] != None and 'name' in receivedObj['tenant'] and 'id' in receivedObj['tenant']:
        if receivedObj['tenant']['id'] in tenantDict:
          tDid = receivedObj['tenant']['id']
          tup = tenantDict[tDid]
          tid = tup[1]

          if (tup[0], 'siteA') not in siteDict:
            setupPlaceholderUnderObj(Entity.TENANT.value, tid, None)

          if (tup[0], 'siteA', 'bldgA') not in bldgDict:
            sTup = siteDict[(tup[0], 'siteA')]
            sid = sTup[1]
            setupPlaceholderUnderObj(Entity.SITE.value, sid, None)

            #Unwanted key was inserted at this point
            #when diff between entityType and found key is 2+
            v = bldgDict[('siteA', 'roomA')]
            bldgDict.pop(('siteA', 'roomA'))
            bldgDict[(tup[0], 'bldgA', 'roomA')] = v

          if (tup[0], 'siteA', 'bldgA', 'roomA') not in roomDict:
            bTup = bldgDict[(tup[0], 'siteA', 'bldgA')]
            bid = bTup[1]
            setupPlaceholderUnderObj(Entity.BLDG.value, bid, None)

            #Unwanted key was inserted at this point
            #when diff between entityType and found key is 2+
            v = roomDict[('bldgA', 'roomA')]
            roomDict.pop(('bldgA', 'roomA'))
            roomDict[(tup[0], 'siteA', 'bldgA', 'roomA')] = v

          rTup = roomDict[(tup[0], 'siteA', 'bldgA', 'roomA')]
          return rTup[1]

    else: #No valid ancestor present so let's use Exaion
      tup = tenantDict[-1]
      tid = tup[1]
      if (tup[0], 'siteA') not in siteDict:
        setupPlaceholderUnderObj(Entity.TENANT.value, tid, None)

      if (tup[0], 'siteA', 'bldgA') not in bldgDict:
        sTup = siteDict[(tup[0], 'siteA')]
        sid = sTup[1]
        setupPlaceholderUnderObj(Entity.SITE.value, sid, None)

        #Unwanted key was inserted at this point
        #when diff between entityType and found key is 2+
        v = bldgDict[('siteA', 'bldgA')]
        bldgDict.pop(('siteA', 'bldgA'))
        bldgDict[(tup[0], 'bldgA', 'roomA')] = v

      if (tup[0], 'siteA', 'bldgA', 'roomA') not in roomDict:
        bTup = bldgDict[(tup[0], 'siteA', 'bldgA')]
        bid = bTup[1]
        setupPlaceholderUnderObj(Entity.BLDG.value, bid, None)

        #Unwanted key was inserted at this point
        #when diff between entityType and found key is 2+
        v = roomDict[('bldgA', 'roomA')]
        roomDict.pop(('bldgA', 'roomA'))
        roomDict[(tup[0], 'siteA', 'bldgA', 'roomA')] = v

      rTup = roomDict[(tup[0], 'siteA', 'bldgA', 'roomA')]
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

          if (sTup[0], 'bldgA') not in bldgDict:
            setupPlaceholderUnderObj(Entity.SITE.value, sid, None)

          if (sTup[0], 'bldgA', 'roomA') not in roomDict:
            bid = bldgDict[(sTup[0], 'bldgA')][1]
            setupPlaceholderUnderObj(Entity.BLDG.value, bid, None)

            #Fix incorrect key 
            correctKey = (sTup[0], 'bldgA', 'roomA')
            wrongKey = ('bldgA', 'roomA')
            v = roomDict[wrongKey]
            roomDict.pop(wrongKey)
            roomDict[correctKey] = v


          if (sTup[0], 'bldgA', 'roomA', 'rackA') not in rackDict:
            rid = roomDict[(sTup[0], 'bldgA', 'roomA')][1]
            setupPlaceholderUnderObj(Entity.ROOM.value, rid, None)

            #Fix incorrect key
            correctKey = (sTup[0], 'bldgA', 'roomA', 'rackA')
            wrongKey = ('roomA', 'rackA')
            #v = rackDict[wrongKey]
            #rackDict.pop(wrongKey)
            #rackDict[correctKey] = v
            fixDictKey(correctKey, wrongKey, rackDict)


          rTup = rackDict[(sTup[0], 'bldgA', 'roomA', 'rackA')]
          addedBySite += 1
          return rTup[1]

    if 'tenant' in receivedObj:
      if receivedObj['tenant'] != None and 'name' in receivedObj['tenant'] and 'id' in receivedObj['tenant']:
        if receivedObj['tenant']['id'] in tenantDict:
          tDid = receivedObj['tenant']['id']
          tup = tenantDict[tDid]
          tid = tup[1]

          if (tup[0], 'siteA') not in siteDict:
            setupPlaceholderUnderObj(Entity.TENANT.value, tid, None)

          if (tup[0], 'siteA', 'bldgA') not in bldgDict:
            sid = siteDict[(tup[0], 'siteA')][1]
            setupPlaceholderUnderObj(Entity.SITE.value, sid, None)
            #Fix incorrect Key
            correctKey = (tup[0], 'siteA', 'bldgA')
            wrongKey = ('siteA', 'bldgA')
            fixDictKey(correctKey, wrongKey, bldgDict)


          if (tup[0], 'siteA', 'bldgA', 'roomA') not in roomDict:
            bid = bldgDict[(tup[0], 'siteA', 'bldgA')][1]
            setupPlaceholderUnderObj(Entity.BLDG.value, bid, None)
            #Fix incorrect Key
            correctKey = (tup[0], 'siteA', 'bldgA', 'roomA')
            wrongKey = ('bldgA', 'roomA')
            fixDictKey(correctKey, wrongKey, roomDict)

          if (tup[0], 'siteA', 'bldgA', 'roomA', 'rackA') not in rackDict:
            rid = roomDict[(tup[0], 'siteA', 'bldgA', 'roomA')][1]
            setupPlaceholderUnderObj(Entity.ROOM.value, rid, None)
            #Fix incorrect Key
            correctKey = (tup[0], 'siteA', 'bldgA', 'roomA', 'rackA')
            wrongKey = ('roomA', 'rackA')
            fixDictKey(correctKey, wrongKey, rackDict)

          subTup = rackDict[(tup[0], 'siteA', 'bldgA', 'roomA', 'rackA')]
          addedByTenant += 1
          return subTup[1]



  incorrectDevCount += 1



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
#end = Entity.OBJ_TEMPLATE.value
end = Entity.DEVICE.value+1
pid = None

while(x < end):
  entity = (entIntToStr(x)).lower()
  jsonObj = getListFromFile(entity)
  if x == Entity.TENANT.value:
    URL = NBURL+"/tenancy/"+entity+"s/"

  if x == Entity.SITE.value:
    URL = NBURL+"/dcim/"+entity+"s?limit=0"
    pid = eid

  if x == Entity.BLDG.value:
    URL = NBURL+"/dcim/"+entity+"s?limit=0"

  if x == Entity.ROOM.value:
    URL = NBURL+"/dcim/locations?limit=0"

  if x == Entity.RACK.value:
    URL = NBURL+"/dcim/"+entity+"s?limit=0"

  if x == Entity.DEVICE.value:
    URL = NBURL+"/dcim/"+entity+"s?limit=0"



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




'''
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
'''

