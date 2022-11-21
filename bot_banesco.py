import time as t
import pandas as pd
import warnings
import requests
import json
import base64
import sys

from pathlib import Path
from API.resources import format, any_ec, mail_body
from gclass import gapi
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

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
driver.get("https://www.banesconline.com/mantis/Website/Login.aspx")


def login():
    driver.switch_to.frame(0)
    while True:
        # Usuario
        print("Ingresando Usuario")
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='txtUsuario']"))
        ).send_keys(gapi(1).credentials("user", bank="banesco"))
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='bAceptar']"))
        ).click()
        # Encaso de otra sesión activa, esperar 2 minutos
        error = None
        try:
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="tblInformtiva"]/tbody/tr[2]/td/div')
                )
            )
        except Exception as e:
            error = e
        if error is None:
            print("Entrando a espera por sesión activa")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='bAceptar']"))
            ).click()
            t.sleep(120)
            continue
        else:
            break
    # Preguntas
    print("Introduciendo preguntas de seguridad")
    sq1 = (
        WebDriverWait(driver, 10)
        .until(EC.presence_of_element_located((By.XPATH, '//*[@id="lblPrimeraP"]')))
        .text
    )
    sq2 = (
        WebDriverWait(driver, 10)
        .until(EC.presence_of_element_located((By.XPATH, '//*[@id="lblSegundaP"]')))
        .text
    )
    sq_list = gapi(1).credentials("sq", bank="banesco").keys()
    sa_list = gapi(1).credentials("sq", bank="banesco").values()

    try:
        for q in range(len([*sq_list])):
            if str([*sq_list][q]).lower() in str(sq1).lower():
                sa1 = [*sa_list][q]
            if str([*sq_list][q]).lower() in str(sq2).lower():
                sa2 = [*sa_list][q]
    except Exception as e:
        print("Algo anda mal...", str(e))

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='txtPrimeraR']"))
    ).send_keys(sa1)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='txtSegundaR']"))
    ).send_keys(sa2)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='bAceptar']"))
    ).click()

    while True:
        # Clave
        print("Ingresando clave")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='txtClave']"))
        ).send_keys(gapi(1).credentials("password", bank="banesco"))
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='bAceptar']"))
        ).click()
        # Encaso de otra sesión activa, esperar 2 minutos
        error = None
        try:
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="lblMensaje"]'))
            )
        except Exception as e:
            error = e
        if error is None:
            print("Esperando por sesión activa")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="bAceptar"]'))
            ).click()
            t.sleep(120)
            continue
        else:
            break
    # Abrir la pestaña de transferencias al entrar
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//span[normalize-space()='Transferencias']")
        )
    ).click()

def failsafe():
    # Buscar presencia de inicio de sesion en caso de que el banco hay expulsado
    error = None
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='txtUsuario']"))
        )
    except Exception as e:
        error = e
    # En caso de expulsión, volver a iniciar sesión
    if error == None:
        login()
    else:
        return('Seguimos dentro del banco')  # Si seguimos dentro, ignorar alerta

# ---------------------   
# Iniciar sesión
# ---------------------
try:
    login()
    print('Sesión iniciada en el banco')
except:
    print("No se pudo iniciar sesión en el banco, intentando de nuevo")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_btnSalir_lkButton"]'))
    ).click()
    login()

def operate(account_number, benef, tipo, national_id, ammount, comment, op_id):
    failsafe()
    while True:
        error = None
        try:
# ---------------------   
# Entrar a transferencias
# ---------------------
            if account_number[:4] == "0134":
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                        "//a[@href='/Mantis/WebSite/transferencias/tercerosbanesco.aspx']",))
                ).click()
            else:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                        '//*[@id="ctl00_FastMenu"]/div[2]/a[5]',))
                ).click()
                #Saltar a iframe
                driver.switch_to.frame(
                    WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                        "//iframe[@id='ctl00_cp_frmAplicacion']",))
                    )
                )
        except Exception as e:
            error = e
        if error == None:
            break
        else:
            # Abrir la pestaña de transferencias
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                     "//span[normalize-space()='Transferencias']")
                )
            ).click()
            continue
# ---------------------   
# Vaciar info bancaria
# ---------------------
    # Cuenta a debitar
    Select(
        WebDriverWait(driver, 10).until(any_ec(
            EC.presence_of_element_located((By.XPATH,
                 "//select[@id='ctl00_cp_wz_ddlCuentaDebitar']")),
            EC.presence_of_element_located((By.XPATH,
                 "//select[@id='inputGroupSelect01']"))
        ))
    ).select_by_index(1)
    #En caso de otros bancos, seleccionar 'Codigo de Cuenta'
    if account_number[:4] != "0134":
        Select(
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                    '//*[@id="TipTrans"]')),
            )
        ).select_by_index(1)
    #Agregar a directorio
    try:
        WebDriverWait(driver, 10).until(any_ec(
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="check"]')),
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="checkcta"]'))
        )).click()
        WebDriverWait(driver, 10).until(any_ec(
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="ctl00_cp_wz_txtAlias"]')),
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="aliascta"]'))
        )).send_keys(benef+" "+str(account_number[:4]))
    except:
        pass
    # Si es a otros bancos
    if account_number[:4] != "0134":
        Select(
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="bancocta"]'))
            )
        ).select_by_value(str(account_number[:4])+"|A")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, 
                '//*[@id="benefcta"]'))
        ).send_keys(benef)
    #Numero de cuenta
    WebDriverWait(driver, 10).until(any_ec(
        EC.presence_of_element_located((By.XPATH, 
            "//input[@id='ctl00_cp_wz_txtCuentaTransferir']")),
        EC.presence_of_element_located((By.XPATH,
                '//*[@id="cuentacliente"]'))
    )).send_keys(account_number)
    #Persona
    Select(
        WebDriverWait(driver, 10).until(any_ec(
            EC.presence_of_element_located((By.XPATH, 
                "//select[@id='ctl00_cp_wz_ddlNac']")),
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="NacCliCta"]'))
        ))
    ).select_by_value(tipo)
    #Identificación
    WebDriverWait(driver, 10).until(any_ec(
        EC.presence_of_element_located((By.XPATH, 
            "//input[@id='ctl00_cp_wz_txtCedula']")),
        EC.presence_of_element_located((By.XPATH,
                '//*[@id="cedulacta"]'))
    )).send_keys(national_id)
    #Monto
    WebDriverWait(driver, 10).until(any_ec(
        EC.presence_of_element_located((By.XPATH, 
            "//input[@id='ctl00_cp_wz_txtMonto']")),
        EC.presence_of_element_located((By.XPATH,
                '//*[@id="montocta"]'))
    )).send_keys(str(ammount).replace(".", ","))
    #Comentario
    WebDriverWait(driver, 10).until(any_ec(
        EC.presence_of_element_located((By.XPATH, 
            "//input[@id='ctl00_cp_wz_txtConcepto']")),
        EC.presence_of_element_located((By.XPATH,
                '//*[@id="conceptocta"]'))
    )).send_keys(comment)
    #Continuar
    WebDriverWait(driver, 10).until(any_ec(
        EC.presence_of_element_located((By.XPATH, 
            "//input[@value='Aceptar']")),
        EC.presence_of_element_located((By.XPATH,
            '//*[@id="enviar"]'))
    )).click()
    # Buscar un mensaje de error (datos equivocados/saldo insuficiente)
    try:
        err_msg = (
            WebDriverWait(driver, 4).until(any_ec(
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="ctl00_cp_wz"]/tbody/tr[1]/td/font')),
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="ctl00_cp_wz_ctl13"]/ul/li')),
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="bancocta-error"]')),
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="benefcta-error"]')),
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="cedulacta-error"]')),
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="cuentacliente-error"]')),
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="montocta-error"]')),
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="msmcta"]')),
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="conceptocta-error"]')),
                EC.presence_of_element_located((By.XPATH, 
                    '//*[@id="aliascta-error"]')),
            )).text
        )
    except Exception as e:
        error = e
    # Si no aparece el error, procesar
    if error != None:
        #Si entrada va al directorio
        try:
            WebDriverWait(driver, 1).until(any_ec(
                EC.presence_of_element_located((By.XPATH,
                    '//*[@id="ctl00_cp_wz_StartNavigationTemplateContainerID_btnNext"]')),
               EC.presence_of_element_located((By.XPATH,
                    '//*[@id="butonPago"]'))
            )).click()
            WebDriverWait(driver, 1).until(any_ec(
                EC.presence_of_element_located((By.XPATH,
                    '//*[@id="ctl00_cp_wz_StepNavigationTemplateContainerID_btnNext"]')),
                EC.presence_of_element_located((By.XPATH,
                    '//*[@id="enviar"]'))
            )).click()
            WebDriverWait(driver, 1).until(any_ec(
                EC.presence_of_element_located((By.XPATH,
                    '//*[@id="ctl00_cp_wz_validarCoe_wzCoeOtp_StepNavigationTemplateContainerID_btnNext"]')),
                EC.presence_of_element_located((By.XPATH,
                    '//*[@id="butonPago"]'))
            )).click()
            if account_number[:4] == "0134":
                WebDriverWait(driver, 1).until(any_ec(
                    EC.presence_of_element_located((By.XPATH,
                        '//*[@id="ctl00_cp_wz_validarCoe_wzCoeOtp_StepNavigationTemplateContainerID_btnNext"]')),
                    EC.presence_of_element_located((By.XPATH,
                        '//*[@id="butonOTP"]'))
                )).click()
        except:
        #Si ya esta en directorio
            WebDriverWait(driver, 1).until(any_ec(
                EC.presence_of_element_located((By.XPATH,
                    '//*[@id="ctl00_cp_wz_StepNavigationTemplateContainerID_btnNext"]')),
                EC.presence_of_element_located((By.XPATH,
                    "//button[@id='butonPago']"))
            )).click()
        #Esperar por la solicitud de OTP
        try:
            WebDriverWait(driver, 3).until(any_ec(
                EC.presence_of_element_located((By.XPATH,
                    '//*[@id="ctl00_cp_wz_validarCoe_wzCoeOtp_StepNavigationTemplateContainerID_btnNext"]')),
                EC.presence_of_element_located((By.XPATH,
                    '//*[@id="butonOTP"]'))
            )).click()
            t.sleep(27)
            for i in range(1,3):
                response = gapi(1).otp()
                if response.empty is True:
                    t.sleep(2*i)
                    continue
                else:
                    response = gapi(1).otp().to_dict("records")
                    otp = response[0]["otp"]
                    #gapi(1).read_one(response[0]["msg_id"])
        
                WebDriverWait(driver, 10).until(any_ec(
                    EC.presence_of_element_located((By.XPATH, 
                        '//*[@id="ctl00_cp_wz_validarCoe_wzCoeOtp_txtCoeOtp"]')),
                    EC.presence_of_element_located((By.XPATH,
                        '//*[@id="form"]/div[1]/div/input'))
                )).send_keys(otp)
                WebDriverWait(driver, 10).until(any_ec(
                    EC.presence_of_element_located((By.XPATH,
                        '//*[@id="ctl00_cp_wz_FinishNavigationTemplateContainerID_btnFinishComp"]')),
                    EC.presence_of_element_located((By.XPATH,
                        '//*[@id="form"]/div[2]/div/button[2]'))
                )).click()
                #Si se ingresó la clave exitosamente, abortar loop
                try:
                    WebDriverWait(driver, 5).until(any_ec(
                        EC.presence_of_element_located((By.XPATH,
                            '//*[@id="ctl00_cp_wz_CRbo_btnReg"]')),
                        EC.presence_of_element_located((By.XPATH,
                            "//input[@name='ctl00$cp$wz$CRbo$btnReg']"))
                    ))
                    break
                except:
                    if account_number[:4] != "0134":
                        WebDriverWait(driver, 5).until(any_ec(
                            EC.presence_of_element_located((By.XPATH,
                                '//*[@id="form"]/div[1]/label'))
                        )).click
                    i+=1
                    t.sleep(2*i)
        except:
            print('No hizo falta OTP')
            i = 0

        if i == 2:
            WebDriverWait(driver, 5).until(any_ec(
                EC.presence_of_element_located((By.XPATH,
                    '//*[@id="form"]/div[2]/div/button[1]'))
            )).click
            raise Exception("La clave de operaciones especiales no llegó, por favor verificar")
        # Tomar screenshot, guardarlo y subirlo a Drive
        driver.save_screenshot("./Captures_Banesco/capture {0}.png".format(benef + "_" + str(op_id)[-6:]))
        with open("./Captures_Banesco/capture {0}.png".format(benef + "_" + str(op_id)[-6:]),"rb") as capture:
            file = str(base64.b64encode(capture.read()),'utf-8')
        try:
            gapi(1).upload(
                "Captures_Banesco", "capture {0}.png".format(benef + "_" + str(op_id)[-6:])
            )
        except Exception as e:
            print(e)
        # Clickear Aceptar y volver a inicio
        WebDriverWait(driver, 10).until(any_ec(
            EC.presence_of_element_located((By.XPATH, 
                '//*[@id="ctl00_cp_wz_CRbo_btnReg"]')),
            EC.presence_of_element_located((By.XPATH, 
                "//input[@name='ctl00$cp$wz$CRbo$btnReg']")),
            EC.presence_of_element_located((By.XPATH, 
                "//input[@value='Aceptar']"))
        )).click()
        return(file)
    else:
        WebDriverWait(driver, 10).until(any_ec(
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="ctl00_cp_wz"]/tbody/tr[2]/td/input[1]')),
            EC.presence_of_element_located((By.XPATH,
                '//*[@id="habilitar"]'))
        )).click()
        if err_msg == '':
            err_msg = 'Datos equivocados'
        raise Exception(err_msg)

def get_balance():
    balance = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="content-right"]/table[3]/tbody/tr/td[3]'))
    ).text.replace('.','').replace(',','.')
    return (float(balance))
    
def run():
    #print("Buscando operaciones...")
    # Variables generales
    error = None
    # Buscar transaciones pendientes
    reqUrl = "http://134.209.220.83/salidas/pendientes/banesco"
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
            start = t.time()
            print("Transacción encontrada")
            print(pd.DataFrame(r, index=[0]))
            account_number = r["cuenta"]
            national_id = r["documento"]
            ammount = round(float(r["monto"]) * float(r["tasa"]), 2)
            comment = format(r["beneficiario"]).clean_string()
            benef = format(r["beneficiario"]).clean_string()
            op_id = r["op_id"]
            restante = r["restante"]
            tipo = r["persona"]
            try:
                transfer = operate(account_number, benef, tipo, national_id, ammount, comment, op_id)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                error = e

            if error is None:
                end = t.time()
                duration = end-start
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
                    "receptionVoucherURL":transfer,
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
                    # Duración de op: {duration}
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
                    body=mail_body().op(op_id[-6:], benef, ammount, r["banco"], r["fecha"], r["hora"], error)
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
l = 0
while True:
    #Si van 10 vueltas sin conseguir operaciones
    if l == 60:
        driver.quit()
        t.sleep(30)
        driver.get("https://www.banesconline.com/mantis/Website/Login.aspx")
        try:
            login()
            print('Sesión iniciada en el banco')
            l = 0
        except:
            print("No se pudo iniciar sesión en el banco, intentando de nuevo")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_btnSalir_lkButton"]'))
            ).click()
            login()
            l = 0
    # Correr run para buscar y sacar transacciones
    try:
        result = run()
    except Exception as e:
        print(e)
    # Espera de 5 segundos para volver a buscar
    t.sleep(5)
    # Buscar alerta de inactividad
    try:
        driver.switch_to.window(driver.window_handles[1])
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="formBOL"]/center/table[2]/tbody/tr/td/input')
            )
        ).click()
        driver.switch_to.window(driver.window_handles[0])
    except Exception as e:
        pass
    # Buscar presencia de inicio de sesion en caso de que el banco hay expulsado       
    failsafe()
    #Sumar vueltas si no hay operaciones
    if result == 'Nada nuevo':
        l += 1
    
