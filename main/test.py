import requests


headers={
    "Content": "Application/json",
    "Authorization":"Bearer 50aa84e44de04bd8e3d963c073a3e349863c1081"

}

json={
      'title':"the", 'description':'thee', 'location':'eheh','time':'12:03', 'date':'2022-01-23',
                

}
response= requests.post("http://localhost:9000/api/",headers=headers,json=json)
print(response.json())
