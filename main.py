#!/usr/bin/env python
import requests, json

#Auth Token
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjYzOTUyMDYyNzE4NDI3MTM2MX0.y34Vd-KPTzDQRowqiPlXE8Nz00TvDv5D3kF838JVBVQ'

head = {'Authorization': 'Bearer {}'.format(token)}

# URLs
# LOCAL: http://localhost:8000/api/user/tenants
# DCIM: https://api.chibois.net/api/dcim/racks/

# Obtain the big list of racks
# r = requests.get("https://dcim.chibois.net/api/dcim/racks/")
# parsed = json.loads(r)
# ITERATE THROUGH EACH ELEMENT AND SEND AN API REQUEST



# Obtain the big list of sites
# r = requests.get("https://dcim.chibois.net/api/dcim/sites/")
# parsed = json.loads(r)
# ITERATE THROUGH EACH ELEMENT AND SEND AN API REQUEST



# Obtain the big list of tenants
# r = requests.get("https://dcim.chibois.net/api/dcim/tenancy/tenants")
# parsed = json.loads(r)
# ITERATE THROUGH EACH ELEMENT AND SEND AN API REQUEST



### Test with Current API @ https://api.chibois.net/api/user/
### To check that a request is successful, 
# use r.raise_for_status() or check r.status_code is what you expect

r = requests.get("https://api.chibois.net/api/user/tenants", headers=head)
# print(r.json())

# parsed = json.loads(r.json())

""" for k in r.json():
    print(r.json()[k]) """

### print(r.json()['data'][1])

### ITERATE THROUGH EACH OBJECT IN JSON RESPONSE
'''for obj in r.json()['data']:
    print(obj)'''


""" r = requests.put("http://localhost:8000/api/user/tenants", headers=head,
data=r.json()['data'][0]) """

Q = r.json()['data'][1]
Q['id'] = None
Q['attributes']['id'] = None
Q['attributes']['color'] = "NIL"
Q['category'] = "THE HOTTEST DNB"
Q['name'] = "RONI SIZE"


print(json.dumps(Q))


fg = requests.post('http://localhost:8000/api/user/tenants',data=json.dumps(Q), headers=head)
print(fg)