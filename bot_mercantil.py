import string
import time as t
import warnings
import pandas as pd
import requests
import json
import base64
import sys

from pathlib import Path
from API.resources import format, mail_body
from gclass import gapi
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException

# Ignorar DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Llamada a Chromedriver
#CHROMEDRIVER_PATH = "/opt/homebrew/bin/chromedriver"
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
WINDOW_SIZE = "1920,1080"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--test-type")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-first-run")
chrome_options.add_argument("--no-default-browser-check")
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--start-maximazed")

# Definir Driver
driver = webdriver.Chrome(
    executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options
)
# Definir ActionChains
action = ActionChains(driver)
print("Iniciando portal del banco")
driver.get(
    "https://empresas.bancomercantil.com/MELE/control/BoleTransactional.mercantil"
)


def keep_alive():
    # Buscar alerta de inactividad
    for i in range(1, 2):
        try:
            driver.switch_to.window(driver.window_handles[i])
            print("Alerta encontrada")
            driver.close()
        except Exception:
            pass
    driver.switch_to.window(driver.window_handles[0])

def login():
    # Resetear el token
    gapi(1).reset_token()
    gapi(1).chat('Token para iniciar sesión por favor')
    # Usuario
    print("Ingresando Usuario")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='CLIENTID']"))
    ).send_keys(gapi(1).credentials("user", bank="mercantil"))
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='submitButton']"))
    ).click()
    # Clave
    print("Ingresando Clave")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='USERPASS']"))
    ).send_keys(gapi(1).credentials("password", bank="mercantil"))
    while True:
        t.sleep(12)
        keep_alive()
        error = None
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='USERTOKEN']"))
            ).send_keys(gapi(1).credentials("token"))
        except KeyError as e:
            error = e
            print("Esperando por token")
        if error is None:
            print("Token recibido, iniciando sesión")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@id='acceptButton']")
                )
            ).click()
            break
        else:
            continue
    # Preguntas
    sq1 = (
        WebDriverWait(driver, 10)
        .until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="questionForm"]/table[1]/tbody/tr[3]/td/b')
            )
        )
        .text
    )
    sq2 = (
        WebDriverWait(driver, 10)
        .until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="questionForm"]/table[1]/tbody/tr[6]/td/b')
            )
        )
        .text
    )
    sq_list = gapi(1).credentials("sq", bank="mercantil").keys()  # type: ignore
    sa_list = gapi(1).credentials("sq", bank="mercantil").values()  # type: ignore
    try:
        for q in range(len([*sq_list])):
            if str([*sq_list][q]).lower() in str(sq1).lower():
                sa1 = [*sa_list][q]
            if str([*sq_list][q]).lower() in str(sq2).lower():
                sa2 = [*sa_list][q]
    except Exception as e:
        print("Algo anda mal...", str(e))

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="response1"]'))
    ).send_keys("barqui")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="response2"]'))
    ).send_keys("barqui")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="aceptar"]'))
    ).click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="submitButton"]'))
    ).click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="endRegisterForm"]/table[2]/tbody/tr/td/input')
        )
    ).click()

# Iniciar sesión
while True:
    error = None
    try:
        login()
    except Exception as e:
        error = e
    if error == None:
        gapi(1).chat('Sesión iniciada con exito')
        break
    else:
        gapi(1).chat('No se pudo iniciar sesión en el banco, intentando de nuevo')
        print("No se pudo iniciar sesión en el banco, intentando de nuevo")
        t.sleep(1)
        driver.get(
            "https://empresas.bancomercantil.com/MELE/control/BoleTransactional.mercantil"
        )
        continue
driver.save_screenshot("./Captures_Mercantil/login_test.png")
def operate(account_number, benef, tipo, national_id, ammount, comment, op_id):
    # Entrar en transferencias
    toggle = 0
    while toggle < 1:
        t.sleep(1)
        action.move_to_element(
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="PagosYTranferencias"]')
                )
            )
        ).perform()
        t.sleep(1)
        # Transferencias a terceros Mercantil
        action.move_to_element(
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="PagosYTranferencias"]/ul/li[3]/div/a')
                )
            )
        ).click().perform()

        directory = Select(
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//select[@name='destAccountList']")
                )
            )
        ).options
        initial = string.ascii_lowercase.index(benef[:1].lower())
        if initial > 10:
            directory = list(reversed(directory))
        dic_len = int((len(directory)*2)/3)
        print("Muestra de afiliados para buscar:", dic_len)
        # OMG
        #driver.save_screenshot("./Captures_Mercantil/nav_test.png")
        sw = t.time()
        try:
            filtered = next(filter(lambda y:account_number in y.text,directory[:dic_len+1]), None)
        except StaleElementReferenceException:
            filtered = None
        print(round(t.time()-sw,4))
        if filtered != None:
            selection = filtered.text
            print ("Beneficiario:", selection, "encontrado en:", round(t.time()-sw,4), "segundos")
            toggle = 1
            break
        else:
            agregar = add(account_number, benef, tipo, national_id)
            if agregar != 'Todo bien':
                raise Exception (agregar)
    attempts = 0
    while attempts < 4:
        try:
            Select(
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//select[@name='destAccountList']")
                    )
                )
            ).select_by_visible_text(str(selection))
            break
        except Exception:
            exc_type = sys.exc_info()
            print (exc_type, attempts)
        attempts+=1
    Select(
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//select[@name='sourceAccountList']")
            )
        )
    ).select_by_index(1)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="value"]'))
    ).send_keys(ammount * 10)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="motive"]'))
    ).send_keys(comment)
    action.move_to_element(
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='Continuar']"))
        )
    ).send_keys(Keys.RETURN).perform()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@name='Confirmar']"))
    ).submit()
    # Tomar screenshot, guardarlo y subirlo a Drive
    driver.save_screenshot("./Captures_Mercantil/capture {0}.png".format(benef + "_" + str(op_id)[-6:]))
    with open("./Captures_Mercantil/capture {0}.png".format(benef + "_" + str(op_id)[-6:]),"rb") as capture:
        file = str(base64.b64encode(capture.read()),'utf-8')
    try:
        gapi(1).upload(
            "Captures_Mercantil", "capture {0}.png".format(benef + "_" + str(op_id)[-6:])
        )
    except Exception as e:
        print(e)
    # Clickear Aceptar y volver a inicio
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@name='Submit2']"))
    ).submit()
    return (file)

def get_balance():
    #Ir a consultas y extraer saldo restante
    action.move_to_element(
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="Consultas"]')
                )
            )
        ).perform()
    action.move_to_element(
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="Consultas"]/ul/li[1]/div/a')
                )
            )
        ).click().perform()
    #Extraer saldo
    balance = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.XPATH, 
            '//*[@id="tDataCorrientes"]/tfoot/tr/td[5]'))
    ).text.replace('.','').replace(',','.')
    return (float(balance))

def add(account_number, benef, tipo, national_id):
    # Afiliar nuevo beneficiario
    print('Afiliando beneficiario')
    t.sleep(1)
    action.move_to_element(
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="AdmSeguridad"]'))
        )
    ).perform()
    t.sleep(1)
    action.move_to_element(
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="AdmSeguridad"]/ul/li[3]/div')
            )
        )
    ).perform()
    action.move_to_element(
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="AdmSeguridad"]/ul/li[3]/ul/li[1]/div/a')
            )
        )
    ).click().perform()
    Select(
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="service"]'))
        )
    ).select_by_index(1)
    Select(
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="service"]'))
        )
    ).select_by_index(1)
    action.move_to_element(
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="formService"]/table/tbody/tr[2]/td/input')
            )
        )
    ).click().perform()
    for a in range(2):
        # Solicitar token para afiliar
        gapi(1).reset_token()
        gapi(1).chat('Token para afiliar por favor')
        while True:
            t.sleep(10)
            keep_alive()
            error = None
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@id='USERTOKEN']"))
                ).send_keys(gapi(1).credentials("token"))
            except Exception as e:
                error = e
                print("Esperando por token para afiliar")
            if error is None:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="bContinuar"]'))
                ).click()
                break
            else:
                continue
        try:
            # Vaciar info bancaria
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="ACCTNUM"]'))
            ).send_keys(account_number)
            break
        except:
            if a < 1:
                pass
            else:
                return ("No se pudo completar la operación por fallo al ingresar token, se desistió para no bloquear el usuario")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="BENEF"]'))
    ).send_keys(benef)
    Select(
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="DOCTYPE"]'))
        )
    ).select_by_index(tipo)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="ID"]'))
    ).send_keys(national_id)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="EMAIL"]'))
    ).send_keys("aa@gmail.com")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="EMAILC"]'))
    ).send_keys("aa@gmail.com")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="DESC"]'))
    ).send_keys(benef)
    action.move_to_element(
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="Continuar"]'))
        )
    ).click().perform()
    try:
        err_msg = (
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="summary"]/tr/td[2]'))
            ).text
        )
    except Exception as e:
        error = e
    if error != None:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="formService"]/table/tbody/tr[8]/td/input[1]')
            )
        ).submit()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="formService"]/table/tbody/tr[8]/td/input[1]')
            )
        ).submit()
        return ("Todo bien")
    else:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="Inicio"]'))
        ).click()
        return (err_msg)

def run():
    print("Balance disponible:", get_balance())
    print("Buscando operaciones...")
    # Variables generales
    tipo_list = ["V", "E", "J", "P", "G"]
    error = None
    # Buscar transaciones pendientes
    reqUrl = "http://134.209.220.83/salidas/pendientes/mercantil"
    vex_url = "https://us-central1-finus-cambio.cloudfunctions.net/Api/Bot/transactions/approve"
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
    response = requests.request("GET", reqUrl, headers=headers_list_bot)
    pending = response.json()
    if pending["salidas"] == []:
        return ("Nada nuevo")
    else:
        for r in pending["salidas"]:
            print("Transacción encontrada")
            print(pd.DataFrame(r, index=[0]))
            account_number = r["cuenta"]
            national_id = r["documento"]
            ammount = round(float(r["monto"]) * float(r["tasa"]), 2)
            comment = format(r["beneficiario"]).clean_string()
            benef = format(r["beneficiario"]).clean_string()
            op_id = r["op_id"]
            restante = r["restante"]
            for i in tipo_list:
                if r["persona"] == i:
                    tipo = tipo_list.index(i) + 1
            #Operar   
            try:
                transfer = operate(account_number, benef, tipo, national_id, ammount, comment, op_id)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                error = e

            driver.save_screenshot("./Captures_Mercantil/operate_test.png")
            if error is None:
                try:
                    balance = get_balance()
                except:
                    if restante is not None:
                        balance = restante - ammount
                    else:
                        balance = "NULL"
                    gapi(1).send_mail(
                        "notify",
                        to="rruiz2396@gmail.com",
                        subject="Error en {0}".format(Path(__file__).stem),
                        body = mail_body().alert("get_balance()",(Path(__file__).stem))
                    )
                payload = json.dumps({
                    "op_id":str(op_id),
                    "monto_bs":str(ammount),
                    "monto":str(r["monto"]),
                    "receptionVoucherURL":str(transfer),
                    "aprobada":True
                })
                response = requests.request("PUT",
                    "http://134.209.220.83/salidas",
                    data=json.dumps({"op_id": op_id,"restante": balance, "pago":1}),
                    headers=headers_list_bot,
                )
                vex = requests.request("POST", 
                    vex_url, 
                    data=payload, 
                    headers=headers_list_vex,
                )
                s = f"""
                    {'-'*40}
                    # Transacción completada
                    # Mensaje del servidor: {response.text}
                    # Mensaje del portal: {vex.text}
                    {'-'*40}
                    """
                return (s)
            else:
                response = requests.request("PUT",
                    "http://134.209.220.83/salidas",
                    data=json.dumps({"op_id": op_id,"pago":2}),
                    headers=headers_list_bot,
                )
                gapi(1).send_mail(
                    "notify",
                    to="rruiz2396@gmail.com",
                    subject="Transacción {0} para {1} fallida".format(op_id[-6:], benef),
                    body = mail_body().op(op_id[-6:], benef, ammount, r["banco"], r["fecha"], r["hora"], error)
                )
                s = f"""
                    {'-'*40}
                    # Transacción fallida
                    # Mensaje del servidor: {response.text}
                    # Mensaje del bot: 
                    # Error {format(str(exc_type)).side_spaces()} 
                    # En la linea {str(exc_tb.tb_lineno)}
                    {'-'*40}
                    """
                return (s)

while True:
    # Correr run para buscar y sacar transacciones
    try:
        result = run()
        print(result)
    except Exception as e:
        print(e)
    t.sleep(5)
    keep_alive()
    # Buscar presencia de inicio de sesion en caso de que el banco hay expulsado
    error = None
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='CLIENTID']"))
        )
    except Exception as e:
        error = e
    # En caso de expulsión, volver a iniciar sesión
    if error == None:
        login()
    else:
        pass  # Si seguimos dentro, ignorar alerta
