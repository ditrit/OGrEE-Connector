#!/usr/bin/env python
import requests, json

#Auth Token


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

r = requests.get("https://api.chibois.net/api/user/tenants")
print(r.json())

'''for idx in parsed:
    print(idx)'''
