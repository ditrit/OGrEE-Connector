#!/usr/bin/env python
import requests, json, os, argparse
from enum import Enum

# URLs
# LOCAL: http://localhost:8000/api/user/tenants
# DCIM: https://api.chibois.net/api/dcim/racks/
# NETBX: https://dcim.chibois.net/api/dcim/racks


#Auth Token
dcim_token = '95d2a16ddb3670eecacb1018e0de484d1b8267e7'
dhead = {'Authorization': 'Token {}'.format(dcim_token)}

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


#COMMAND OPTIONS
parser = argparse.ArgumentParser(description='Import from Netbox to file .')
parser.add_argument('--objects', choices=["tenant","site", "bldg", "room", 
                    "rack", "device", "subdevice", "subdevice1"],
                    help="""Option to select which objects to add.
                    Note they are inclusive (ie specifying subdevices
                    will import everything until subdevices). Default: Rack""")
parser.add_argument('--dir',
                    help="""Location to store JSON results.
                    All results will be stored in a text file named 
                    \'{entity}List.json\'""")

#FUNCTION DEFINTIONS
def getObjList(url):
    """
    docstring
    """
    r = requests.get(url, headers=dhead)
    return r.json()['results']

def dumpListToFile(objList, dir, entType):
    filename = dir+"/"+entType.name.lower()+"List.json"
    print(filename)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(objList, f)



#START
args = vars(parser.parse_args())
if ('dir' not in args or args['dir'] == None):
    print('Directory not specified... using current dir')
    dir = "."
else:
    dir = args['dir']


if args['objects'] != None:
    depth = objToHierarchyDict[args['objects']].value
else:
    print('Objects not specified... using Rack as dump limit')
    depth = Hierarchy(4).value #RACK


x = 0
while x < (depth+1):
    if x == 0: # TENANT
        url = "https://dcim.chibois.net/api/tenancy/tenants/"
    if x == 1: # SITE
        url = "https://dcim.chibois.net/api/dcim/sites/"
    if x == 2: # BLDG --> ROOM
        print("No such thing as buildings, skipping")
        x+=1
        url = "https://dcim.chibois.net/api/dcim/rack-groups/"
    if x == 4: # RACK
        url = "https://dcim.chibois.net/api/dcim/racks/"
    if x == 5: # DEVICE
        url = "https://dcim.chibois.net/api/dcim/devices/"
    objList =  getObjList(url)
    dumpListToFile(objList, dir, Hierarchy(x))
    x += 1