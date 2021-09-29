#!/usr/bin/env python
import requests, json, argparse

#Auth Token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'
head = {'Authorization': 'Bearer {}'.format(token)}

#Setup Arg Parser
parser = argparse.ArgumentParser(description='Import from Netbox to file .')
parser.add_argument('--APIurl', 
                    help="""Specify which API URL to send data""")

#Setup API URL
args = vars(parser.parse_args())
if ('APIurl' not in args or args['APIurl'] == None):
    print('API URL not specified... using default URL')
    API = "https://ogree.chibois.net/api/user"
else:
    API = args['APIurl']


#START
print("Undoing the import...")
pr = requests.get(API+"/tenants", headers=head )


for x in pr.json()["data"]["objects"]:
    if(x['description'][0] == 'ConnectorImported'):
        requests.delete(API+"/tenants/"+x['_id'], headers=head)


print("Finished deleting!")