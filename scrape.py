import json
import time
import requests
from gclass import gapi


def scrape():
    
    pull = gapi(1).mail()
    emails = pull.to_dict('Records')

    reqUrl = "http://134.209.220.83/depositos"
    #Leer tokens
    with open('vex_app_token.json') as f:
        data = json.load(f)
    bot_token = data.get('token')

    headers_list_bot = {
    "Content-Type": "application/json",
    "x-access-token": str(bot_token)
    }

    for i in range(len(emails)):
        error = None
        response = None
        try:
            payload = json.dumps(emails[i])
            response = requests.request("POST", reqUrl, data=payload,  headers=headers_list_bot)
            response.raise_for_status()
        except Exception as e:
            error = e
        if error is None:
            gapi(1).read_one(emails[i]['msg_id'])
        if response is not None:
            print(response.text)


while True:
    time.sleep(10)
    try:
        scrape()
    except Exception as e:
        print(e,'Volviendo a intentar')
        continue

