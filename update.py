#!/usr/bin/env python
import requests, json, argparse

#Auth Token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'
dcim_token = '95d2a16ddb3670eecacb1018e0de484d1b8267e7'

head = {'Authorization': 'Bearer {}'.format(token)}
dhead = {'Authorization': 'Token {}'.format(dcim_token)}


#URLS
NBURL = "https://dcim.chibois.net/api"
API = "https://ogree.chibois.net/api/user"


#COMMAND OPTIONS
parser = argparse.ArgumentParser(description='Update data in OGREE from Netbox data.')
parser.add_argument('--APIurl', 
                    help="""Specify which API URL to send data""")
parser.add_argument('--NBURL',
                    help="""Specify URL of Netbox""")
parser.add_argument("--APItoken", help="(Optionally) Specify a Bearer token for API")
parser.add_argument("--NBtoken", help="(Optionally) Specify a Netbox auth token")
parser.add_argument('--objects', choices=["tenant","site", "bldg", "room", 
                    "rack", "device", "subdevice", "subdevice1"],
                    help="""Option to select which objects to add.
                    Note they are inclusive . Default: Rack""")
parser.add_argument("--inclusive",
                    help="""Specifies whether to include eveything until object 
                    (ie if subdevices and inclusive were specified 
                    then everything until subdevices will be imported). 
                    If not enabled then false""", action="store_true")

#INIT ARGS
args = vars(parser.parse_args())
if ('NBURL' in args and args['NBURL'] != None and args['NBURL'] != ''):
    NBURL = args['NBURL']
else:
    print('Netbox URL not specified... using default URL')
    

if ('APIurl' in args and args['APIurl'] != None and args['APIurl'] != ''):
    API = args['APIurl']
else:
    print('API URL not specified... using default URL')
    

if (args['APItoken'] != None and args['APItoken'] != ''):
  token = args['APItoken']
  head = {'Authorization': 'Bearer {}'.format(token)}

if args['NBtoken'] != None and args['NBtoken'] != '':
  dcim_token = args['NBtoken']
  dhead = {'Authorization': 'Token {}'.format(dcim_token)}


print("Selected: ", args['objects'])