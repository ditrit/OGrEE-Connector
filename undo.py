#!/usr/bin/env python
import requests, json

#Auth Token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'
head = {'Authorization': 'Bearer {}'.format(token)}

print("Undoing the import...")

pr = requests.get(
    "https://ogree.chibois.net/api/user/tenants", headers=head )

#for x in pr.json()["data"]["objects"]:
#    if (x["domain"] == "Connector Domain" or x["domain"] == "Exaion Domain"):
#        requests.delete(
#            "https://ogree.chibois.net/api/user/tenants/"+x["id"],
#             headers=head)

for x in pr.json()["data"]["objects"]:
    if(x['description'][0] == 'ConnectorImported'):
        requests.delete("https://ogree.chibois.net/api/user/tenants/"+x['id'], headers=head)


print("Finished deleting!")