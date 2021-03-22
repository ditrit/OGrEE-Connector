#!/usr/bin/env irb
require 'net/http'
require 'json'

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjY0MTQ2OTIzMTIwOTI4MzU4NX0.F3ccBSNVGNoDao4aLpavuTios9w1ahGM1_XO9Uw-ZvQ'
tenantURL = 'https://api.chibois.net/api/user/tenants'
tenantURI = URI(tenantURL)
# response = Net::HTTP.get(tenantURI)

req = Net::HTTP::Get.new(tenantURI)
req['authorization'] = "Authorization: Bearer #{token}"
rp = Net::HTTP.get(req)
JSON.parse(rp)