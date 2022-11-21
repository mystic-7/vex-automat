import datetime
import json
import time
import requests

def verify():
    req_url = "http://134.209.220.83/entradas/pendientes"
    match_url = "http://134.209.220.83/match"
    vex_url = "https://us-central1-finus-cambio.cloudfunctions.net/Api/Bot/transactions/approve"
    modify_url = "http://134.209.220.83/entradas"

    #Leer tokens
    with open('vex_app_token.json') as f:
        data = json.load(f)
    bot_token = data.get('token')
    with open('vex_portal_token.json') as f:
        data = json.load(f)
    portal_token = data.get('token')

    headers_list_bot = {
    "Content-Type": "application/json",
    "x-access-token": str(bot_token)
    }
    headers_list_vex = {
    "Content-Type": "application/json",
    "Authorization": "Bearer"+" "+str(portal_token)
    }

    response = requests.request("GET", req_url,  headers=headers_list_bot)
    entradas = json.loads(response.text).get("entradas")

    if entradas == []:
        s = f"""
            {'-'*30}
            # Nada que verificar
            {'-'*30}
            """
        print(s)
    else:
        for e in entradas:
            op_date = datetime.datetime.strptime(e.get('fecha'),'%d/%m/%Y').date()
            today = datetime.datetime.today().date()
            if op_date >= today:
                payload = json.dumps({
                    "remitente":e.get("remitente"),
                    "monto":float(e.get("monto")),
                    "op_id":e.get("op_id")
                })
                #/////
                response = requests.request("GET", match_url, data=payload, headers=headers_list_bot)
                s = f"""
                    {'-'*40}
                    # Respuesta del bot
                    # Estatus: {response}
                    # Mensaje: {response.text}
                    {'-'*40}
                    """
                print (s)
                match = json.loads(response.text)
                if match.get("codigo") == "200":
                    payload = json.dumps({
                        "op_id":e.get("op_id"),
                        "monto":str(match.get("monto")),
                        "aprobada":True
                    })
                    #Loop de intentos, llamada a portal
                    r = 0
                    counter = 1
                    while r == 0:
                        response = requests.request("POST", vex_url, data=payload, headers=headers_list_vex)
                        message = json.loads(response.text)
                        s = f"""
                            {'-'*40}
                            # Solicitud al portal
                            # Datos solicitados: {payload}
                            # Respuesta: {response}
                            # Mensaje: {message}
                            # Intento: {counter}
                            {'-'*40}
                            """
                        print(s)
                        counter += 1
                        if message.get("msg") != 'No op valid.':
                            r = 1
                        else:
                            time.sleep(2*counter)
                    #Si se logra modificar la op en portal, modificar en bbdd
                    payload = json.dumps({
                        "op_id":str(e.get("op_id"))
                    })
                    x = requests.request("PUT", modify_url, data=payload, headers=headers_list_bot)
                    print(x.text)

while True:
    try:
        verify()
    except:
        print('Volviendo a intentar')
        continue
    time.sleep(10)