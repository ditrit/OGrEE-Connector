#!/usr/bin/env python
import requests, json, os, argparse
from enum import Enum

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
    "room": Hierarchy.ROOM,
    "rack": Hierarchy.RACK,
    "device": Hierarchy.DEVICE,
    "subdevice": Hierarchy.SUBDEVICE,
    "subdevice1": Hierarchy.SUBDEVICE1
}
depth = Hierarchy.RACK.value
dcim_token = '95d2a16ddb3670eecacb1018e0de484d1b8267e7'
dhead = {'Authorization': 'Token {}'.format(dcim_token)}

def getObjList(url):
    """
    docstring
    """
    r = requests.get(url, headers=dhead)
    return r.json()['results']

def dumpListToFile(objList, dir, entType):
    filename = dir+"/"+entType.name.lower()+"list.txt"
    print(filename)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "a") as f:
        f.write(str(objList))

parser = argparse.ArgumentParser(description='Import data to Database.')


parser.add_argument('--nbdump', action="store_true",
                    help='Option to dump data from netbox to local file')
parser.add_argument('--objects', choices=["tenant","site", "bldg", "room", 
                    "rack", "device", "subdevice", "subdevice1"],
                    help="""Option to select which objects to add.
                    Note they are inclusive (ie specifying subdevices
                    will import everything until subdevices). Default: Rack""")

parser.add_argument('--url',
                    help='Option to dump data from netbox')
parser.add_argument('--dumpdir',
                    help="""Location to store JSON results.
                    All results will be stored in a text file named 
                    \'nbout.txt\'""")

# -import : dump NB and import to OGrEE
#  --APIurl=
#  --APItoken=
#  --fromFiles  --dumpDir=
#  --fromNB     --NBurl=   --NBtoken=
#  --overwrite
#  --objectMappings= NB-to-OGree mappings
parser.add_argument('--import',
                    help='Option to import data to database',  
                    action="store_true")
parser.add_argument('--apiurl',
                    help='Option to indicate API URL.')
parser.add_argument('--apitoken',
                    help='Option to indicate API Token bearer')
parser.add_argument('--fromdir',
                    help='Option to import from json files')
parser.add_argument('--fromnb',action="store_true",
                    help='Option to import from netbox')

agv = parser.parse_args()


args = vars(agv)
if (args['nbdump'] == True and 
('dumpdir' not in args or args['dumpdir'] == None)):
        print('To dump to the Netbox to file, you must specify a directory')
elif ((args['nbdump'] == True and args['dumpdir'] != None) and
     (args['import'] == False and args['fromdir'] == None and args['fromnb'] == False) ):

    print('OK to dump')
    dir = args['dumpdir']
    if args['objects'] != None:
        depth = objToHierarchyDict[args['objects']].value

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


elif (args['import'] == True and 
((args['fromdir'] == None or args['fromdir'] == '') and 
args['fromnb'] == False)): #Error
    print('You must specify an import source')
elif (args['import'] == True and 
((args['fromdir'] != None and args['fromdir'] != '') and 
args['fromnb'] == False)): # Import from dir
    pass
elif (args['import'] == True and 
((args['fromdir'] == None) and args['fromnb'] == True)): #Import from NB
    pass

else:
    print('Executing with default settings')

#if (args['import'])
print('FOR OBJECT HIERARCHY: ', args['objects'])