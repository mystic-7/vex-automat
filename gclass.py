import pandas as pd
import numpy as np
import re
import os.path
import pickle
import base64

from API.resources import format
from datetime import date, datetime, time, timedelta
from httplib2 import Http
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from oauth2client.service_account import ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class gapi:
    def __init__(self, number):
        self.number = number

    def call(self):
        #Si se modifican los SCOPES, borrar el archivo token.pickle.
        SCOPES = ['https://mail.google.com/','https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive' ]
        #Proceso de conexión
        self.creds = None
        #Busqueda de token
        if os.path.exists('token.pickle'+str(self.number)+''):
            with open('token.pickle'+str(self.number)+'', 'rb') as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    '/Users/gerardocoronado/Documents/Vex/creds.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle'+str(self.number)+'', 'wb') as token:
                pickle.dump(self.creds, token)

    def chat(self, message):
        self.message = message
        #Llamar al API
        SCOPES = ['https://www.googleapis.com/auth/chat.bot']
        CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name('service_creds.json', SCOPES)
        #Servicio del API
        chat = build('chat', 'v1', http=CREDENTIALS.authorize(Http()))
        #Mensaje a enviar
        chat.spaces().messages().create(
            parent='spaces/AAAAJpykBR4',
            body={'text': str(message)}
        ).execute()

    def mail(self):
        #Llamar al API
        self.call()
        #Servicio del API
        gmail = build('gmail', 'v1', credentials=self.creds)

        #Encontrar LabelId de etiqutas
        results = gmail.users().labels().list(
            userId='me'
        ).execute()
        labels = results.get('labels',[])
        
        data_list = []
        tag_list = ['BOFA', 'CHASE', 'WELLS', 'REGIONS', 'PAYPAL']
        print('Buscando Correos')
        #Extraer LabelId
        for tag in tag_list:
            for label in labels:
                if label['name'] == tag:
                    id=label['id']
                    print('Etiqueta', label['name'], 'encontrada')
                    #Filtrar mensajes por lable, no leidos y sacar de spam
                    results = gmail.users().messages().list(
                        userId='me', 
                        labelIds=[str(id)],
                        q='is:unread',
                        includeSpamTrash=True
                    ).execute()
                    messages = results.get('messages', [])
                    #Extraer metadata
                    for message in messages:
                        try:
                            msg = gmail.users().messages().get(
                                userId='me', 
                                id=message['id']  
                            ).execute()
                            #Marcar como no spam
                            results = gmail.users().messages().modify(
                                userId='me',
                                id=message['id'],
                                body={
                                    "addLabelIds": [],
                                    "removeLabelIds": ['SPAM']
                                }
                            ).execute()
                            #Encontrar headers
                            headers = msg['payload']['headers']
                            for header in headers:
                                if header['name']=='To':
                                    to_index = headers.index(header)
                                elif header['name']=='Date':
                                    date_index = headers.index(header)
                                elif header['name']=='Subject':
                                    sbj_index = headers.index(header)

                            if tag == 'BOFA':
                                recipient = str(msg['payload']['headers'][to_index]['value']) #Correo receptor
                                date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                                name = str((str(msg['payload']['headers'][sbj_index]['value']).split('$'))[0]).replace('sent you','').replace('le ha enviado','').upper() #Nombre
                                amount = str((str(msg['payload']['headers'][sbj_index]['value']).split('$'))[1]) #Monto
                                data = {
                                    'msg_id':message['id'],
                                    'cuenta':recipient,
                                    'banco':tag,
                                    'fecha_deposito':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=2)).date()),
                                    'hora_deposito':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=2)).time()),
                                    'remitente':format(name).side_spaces(),
                                    'monto':float(amount.replace(',',''))   
                                }
                                data_list.append(data)
                            elif tag == 'CHASE':
                                recipient = str(msg['payload']['headers'][to_index]['value']) #Correo receptor
                                date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                                name = str((str(msg['payload']['headers'][sbj_index]['value']).split('$'))[0]).replace('sent you','').replace('te envió','').upper() #Nombre
                                amount = str((str(msg['payload']['headers'][sbj_index]['value']).split('$'))[1]) #Monto
                                data = {
                                    'msg_id':message['id'],
                                    'cuenta':recipient,
                                    'banco':tag,
                                    'fecha_deposito':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ')).date()),
                                    'hora_deposito':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ')).time()),
                                    'remitente':format(name).side_spaces(),
                                    'monto':float(amount.replace(',',''))   
                                }
                                data_list.append(data)
                            elif tag == 'WELLS':
                                recipient = str(msg['payload']['headers'][to_index]['value']) #Correo receptor
                                date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                                name = str((str((str(msg['snippet']).split('®'))[1]).split('sent you money'))[0]).upper() #Nombre
                                amount = str((str((str(msg['snippet']).split('$'))[1]).split(' '))[0])
                                data = {
                                    'msg_id':message['id'],
                                    'cuenta':recipient,
                                    'banco':tag,
                                    'fecha_deposito':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).date()),
                                    'hora_deposito':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).time()),
                                    'remitente':format(name).side_spaces(),
                                    'monto':float(amount.replace(',',''))   
                                }
                                data_list.append(data)
                            elif tag == 'REGIONS':
                                recipient = str(msg['payload']['headers'][to_index]['value']) #Correo receptor
                                date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                                name = str((str((str(msg['snippet']).split('payment from'))[1]).split('('))[0]).upper() #Nombre
                                amount = str((str((str(msg['snippet']).split('$'))[1]).split(' '))[0]) #Monto
                                data = {
                                    'msg_id':message['id'],
                                    'cuenta':recipient,
                                    'banco':tag,
                                    'fecha_deposito':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).date()),
                                    'hora_deposito':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).time()),
                                    'remitente':format(name).side_spaces(),
                                    'monto':float(amount.replace(',',''))   
                                }
                                data_list.append(data)
                            elif tag == 'PAYPAL':
                                body = base64.urlsafe_b64decode(msg.get("payload").get("body").get("data").encode("ASCII")).decode("utf-8")
                                formated = " ".join(str(format(body).clean_html()).split())
                                recipient = str(msg['payload']['headers'][to_index]['value'].split('<')[1].replace('>','')) #Correo receptor
                                date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                                name = format(str(re.split('le ha enviado|sent you',re.split('LLC|Investment|CS INV VEN',formated)[2])[0]).upper()).clean_string() #Nombre
                                amount = formated.split('$')[1].split(' ')[0]
                                data = {
                                    'msg_id':message['id'],
                                    'cuenta':recipient,
                                    'banco':tag,
                                    'fecha_deposito':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ')).date()),
                                    'hora_deposito':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ')).time()),
                                    'remitente':format(name).side_spaces(),
                                    'monto':float(amount.replace(',',''))  
                                }
                                data_list.append(data)
                        except Exception as e:
                            print(e)
        df = pd.DataFrame(data_list)
        print('Correos recogidos')
        if  df.empty == True:
            print("Nada nuevo")
        else:
            print(df)
        return(df)     

    def read(self, emails):
        self.emails = emails
        #Llamar al API
        self.call()
        #Servicio del API
        gmail = build('gmail', 'v1', credentials=self.creds)

        #Encontrar LabelIds
        results = gmail.users().labels().list(
            userId='me'
        ).execute()
        labels = results.get('labels',[])

        data = emails.to_dict('Records')
        tag_list = ['BOFA', 'PAYPAL', 'CHASE', 'WELLS', 'REGIONS']
        print('Marcando como leidos')
        #Extraer LabelId
        for tag in tag_list:
            for label in labels:
                if label['name'] == tag:
                    id=label['id']
                    print('Etiqueta', label['name'], 'encontrada')
                    #Filtrar mensajes por lable y no leidos
                    results = gmail.users().messages().list(
                        userId='me', 
                        labelIds=[str(id)],
                        q='is:unread'
                    ).execute()
                    messages = results.get('messages', [])
                    for message in messages:
                        for r in data:
                            if str(r['msg_id']) == str(message['id']):
                                #Marcar como leido
                                results = gmail.users().messages().modify(
                                    userId='me',
                                    id=message['id'],
                                    body={
                                        "addLabelIds": [],
                                        "removeLabelIds": ['UNREAD']
                                    }
                                ).execute()
                    #Filtrar threads por lable y no leidos
                    results = gmail.users().threads().list(
                        userId='me', 
                        labelIds=[str(id)],
                        q='is:unread'
                    ).execute()
                    threads = results.get('threads', [])
                    for thread in threads:
                        for r in data:
                            if str(r['msg_id']) == str(thread['id']):
                                #Marcar como leido
                                results = gmail.users().threads().modify(
                                    userId='me',
                                    id=thread['id'],
                                    body={
                                        "addLabelIds": [],
                                        "removeLabelIds": ['UNREAD']
                                    }
                                ).execute()
        print('Correos Leídos')

    def read_one(self, msg_id):
        self.msg_id = msg_id
        #Llamar al API
        self.call()
        #Servicio del API
        gmail = build('gmail', 'v1', credentials=self.creds)

        #Marcar como leido
        gmail.users().messages().modify(
            userId='me',
            id=str(msg_id),
            body={
                "addLabelIds": [],
                "removeLabelIds": ['UNREAD']
            }
        ).execute()
        print('Correo Leído')

    def send_mail(self, type, **kwargs):
        self.type = type
        self.to = kwargs.get('to', None)
        self.subject = kwargs.get('subject', None)
        self.body = kwargs.get('body', None)

        #Llamar API
        self.call()
        #Servicio del API
        gmail = build('gmail', 'v1', credentials=self.creds)

        msg = self.body
        mimeMessage = MIMEMultipart()
        mimeMessage['to'] = self.to
        mimeMessage['subject'] = self.subject
        mimeMessage.attach(MIMEText(msg, 'plain'))
        raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()

        gmail.users().messages().send(
            userId='me',
            body={'raw':raw_string}
        ).execute()

        return("Correo enviado")

    def sheets(self, answer, column, row):
        self.answer = answer
        self.column = str(column).upper()
        #self.row = str(row).lower

        #Llamar al API
        self.call()
        #Servicio del API
        sheets = build('sheets','v4', credentials=self.creds)
        spreadsheet_id = '1N3dMTlnkhIXNjuPWBQRQmIBaO0uqsi1YqBufRoI9c94'

        #Armar lista y conseguir la primera fila vacia en sheets
        rows_sheets = sheets.spreadsheets().values().get(
            spreadsheetId = spreadsheet_id,
            majorDimension = 'ROWS',
            range = 'Bandeja de entrada!A2:A'
        ).execute()
        #Crear lista con MsgId ya existentes
        log = []
        for i in range(len(rows_sheets['values'])):
            log.append(rows_sheets['values'][i][0])
        #Encontrar última fila en el log
        if row=='last':
            last_row = (len(rows_sheets['values']))+2
            print("Ultima fila con datos en el log:",last_row)
        else:
            last_row = row
        
        #Comparar
        data_list= []
        data = answer.to_dict('Records')
        for r in data:
            data_list.append(r)


        df = pd.DataFrame(data_list)
        print(df)
        entries = df.T.reset_index().T.values.tolist() #Trasponer Dataframe para exportar a sheets
        del entries[0] #Borrar headers de DataFrame

        #Crear diccionario para cumplir con parametro body
        dict = {
            'majorDimension' : 'ROWS',
            'values' : entries
        }
        #Exportar datos
        response = sheets.spreadsheets().values().update(
            spreadsheetId = spreadsheet_id,
            valueInputOption = 'USER_ENTERED',
            range = 'Bandeja de entrada!'+str(self.column)+str(last_row),
            body = dict
        )
        response.execute()
        print('Sheet actualizado')
    
    def credentials(self,type, **kwargs):
        self.type = type
        self.bank = kwargs.get('bank', None)
        
        #Llamar al API
        self.call()
        #Servicio del API
        sheets = build('sheets','v4', credentials=self.creds)
        spreadsheet_id = '1N3dMTlnkhIXNjuPWBQRQmIBaO0uqsi1YqBufRoI9c94'

        #Credenciales Banesco
        if self.type != 'token':
            credentials = sheets.spreadsheets().values().get(
                spreadsheetId = spreadsheet_id,
                majorDimension = 'COLUMNS',
                range = 'Credenciales!A6:M'
            ).execute()
        else:
            credentials = sheets.spreadsheets().values().get(
                spreadsheetId = spreadsheet_id,
                majorDimension = 'COLUMNS',
                range = 'Credenciales!B2'
            ).execute()
            response = str(credentials['values'][0][0])
        #Definir credenciales por tipo de argumento
        for i in range(len(credentials['values'])):
            if (credentials['values'][0][i]).lower() == self.bank:
                if self.type == 'user':
                    response = credentials['values'][1][i]
                elif self.type == 'password':
                    response = credentials['values'][2][i]
                elif self.type == 'sq':
                    response = {
                        credentials['values'][3][i]:credentials['values'][4][i],
                        credentials['values'][5][i]:credentials['values'][6][i],
                        credentials['values'][7][i]:credentials['values'][8][i],
                        credentials['values'][9][i]:credentials['values'][10][i],
                        credentials['values'][11][i]:credentials['values'][12][i],
                    }
                break
        return response

    def reset_token(self):
        #Llamar al API
        self.call()
        #Servicio del API
        sheets = build('sheets','v4', credentials=self.creds)
        spreadsheet_id = '1N3dMTlnkhIXNjuPWBQRQmIBaO0uqsi1YqBufRoI9c94'

        sheets.spreadsheets().values().clear(
            spreadsheetId = spreadsheet_id,
            range = 'Credenciales!B2',
            body={}
        ).execute()

    def compare(self):
        #Llamar al API
        self.call()
        #Servicio del API
        sheets = build('sheets','v4', credentials=self.creds)
        spreadsheet_id = '1N3dMTlnkhIXNjuPWBQRQmIBaO0uqsi1YqBufRoI9c94'

        #Lista de nombres en el sheet
        log = []
        names = sheets.spreadsheets().values().get(
            spreadsheetId = spreadsheet_id,
            majorDimension = 'COLUMNS',
            range = 'Bandeja de entrada!A2:G'
        ).execute()
        #Crear Dataframe para iterar
        for i in range(len(names['values'][0])):
            data = {
                'MsgId':names['values'][0][i],
                'Correo':names['values'][1][i],
                'Fecha':(datetime.strptime(names['values'][2][i],'%d %b %Y %H:%M:%S')).date(),
                'Nombre':names['values'][4][i],
                'Monto':names['values'][5][i],
                'Remitente Desk':names['values'][6][i]
            }
            log.append(data)
        df = pd.DataFrame(log)
        return df

    def new_client_pending(self):
        #Llamar al API
        self.call()
        #Servicio del API
        sheets = build('sheets','v4', credentials=self.creds)
        spreadsheet_id = '1N3dMTlnkhIXNjuPWBQRQmIBaO0uqsi1YqBufRoI9c94'

        #Lista de transid en el sheet
        log = []
        ids = sheets.spreadsheets().values().get(
            spreadsheetId = spreadsheet_id,
            majorDimension = 'COLUMNS',
            range = 'Bandeja de entrada!A2:I'
        ).execute()

        #Crear Dataframe para iterar
        index = 1
        for i in range(len(ids['values'][0])):
            index+=1
            if ids['values'][1][i] == 'POR PAGAR':
                try:
                    data = {
                        'Timestamp':ids['values'][0][i],
                        'Pago':ids['values'][1][i],
                        'Telefono':ids['values'][2][i],
                        'Banco':ids['values'][3][i],
                        'Monto':ids['values'][4][i],
                        'Tasa':ids['values'][5][i],
                        'Cuenta':ids['values'][6][i],
                        'Tipo':ids['values'][7][i],
                        'Documento':ids['values'][8][i],
                        'Index':index
                    }
                    log.append(data)
                except:
                    data = {
                        'Cuenta':'null',
                        'Index':index
                    }
                    log.append(data)

        df = pd.DataFrame(log)
        return df

    def pending(self):
        #Llamar al API
        self.call()
        #Servicio del API
        sheets = build('sheets','v4', credentials=self.creds)
        spreadsheet_id = '1N3dMTlnkhIXNjuPWBQRQmIBaO0uqsi1YqBufRoI9c94'

        #Lista de transid en el sheet
        log = []
        ids = sheets.spreadsheets().values().get(
            spreadsheetId = spreadsheet_id,
            majorDimension = 'COLUMNS',
            range = 'Bandeja de entrada!A2:F'
        ).execute()

        #Crear Dataframe para iterar
        index = 1
        for i in range(len(ids['values'][0])):
            index+=1
            if ids['values'][1][i] == 'POR PAGAR':
                try:
                    data = {
                        'Timestamp':ids['values'][0][i],
                        'Pago':ids['values'][1][i],
                        'Telefono':ids['values'][2][i],
                        'Banco':ids['values'][3][i],
                        'Monto':ids['values'][4][i],
                        'Tasa':ids['values'][5][i],
                        'Index':index
                    }
                    log.append(data)
                except:
                    data = {
                        'TransId':'null',
                        'Index':index
                    }
                    log.append(data)

        df = pd.DataFrame(log)
        return df
    
    def lookup(self,transacts):
        self.transacts = transacts
        #Llamar al API
        self.call()
        #Servicio del API
        sheets = build('sheets','v4', credentials=self.creds)
        spreadsheet_id = '1N3dMTlnkhIXNjuPWBQRQmIBaO0uqsi1YqBufRoI9c94'

        records = sheets.spreadsheets().values().get(
            spreadsheetId = spreadsheet_id,
            majorDimension = 'COLUMNS',
            range = 'Directorio!A2:F'
        ).execute()
        #Crear lista para iterar
        directory = []
        index = 1
        for i in range(len(records['values'][0])):
            index+=1
            data = {
                'Telefono':records['values'][0][i],
                'Beneficiario':records['values'][1][i],
                'Tipo':records['values'][2][i],
                'Documento':records['values'][3][i],
                'Cuenta':records['values'][4][i],
                'Banco':records['values'][5][i],
                'Index':index
            }
            directory.append(data)

        for r in directory:
            if transacts['Telefono'] == r['Telefono']:
                return r
            else:
                return "Cliente no encontrado en el directorio..."
        
    def upload(self, path, file_name):
        self.file_name = file_name
        self.path = path
        #Llamar al API
        self.call()
        #Servicio del API
        drive = build('drive','v3', credentials=self.creds)
        #Set Up
        folder_id = '15PP0iPzxZ6-sTLbRa9pCOlsCF8vJ_gee'
        mime_type = 'image/png'
        file_metadata = {
            'name':file_name,
            'parents':[folder_id]
        }
        media = MediaFileUpload('./{0}/{1}'.format(path,file_name), mimetype=mime_type)

        file = drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='webViewLink'
        ).execute()
        link = file.get("webViewLink")
        return(link)

    def bank_index(self, bank_id):
        self.bank_id = bank_id
        #Llamar al API
        self.call()
        #Servicio del API
        sheets = build('sheets','v4', credentials=self.creds)
        spreadsheet_id = '1N3dMTlnkhIXNjuPWBQRQmIBaO0uqsi1YqBufRoI9c94'
                
        records = sheets.spreadsheets().values().get(
            spreadsheetId = spreadsheet_id,
            majorDimension = 'COLUMNS',
            range = 'Directorio!A2:C'
        ).execute()
        #Crear lista para iterar
        directory = []
        index = 1
        for i in range(len(records['values'][0])):
            index+=1
            data = {
                'Codigo':records['values'][0][i],
                'Banco':records['values'][1][i],
                'Indice':records['values'][2][i],
            }
            directory.append(data)
        
        for r in directory:
            if bank_id == r['Codigo']:
                return r['Indice']
    
    def otp(self):
        #Llamar al API
        self.call()
        #Servicio del API
        gmail = build('gmail', 'v1', credentials=self.creds)

        #Encontrar LabelId de etiqutas
        results = gmail.users().labels().list(
            userId='me'
        ).execute()
        labels = results.get('labels',[])
        data_list=[]
        tag_list = ['OTP BANESCO']
        print('Esperando por OTP')
        #Extraer LabelId
        for tag in tag_list:
            for label in labels:
                if label['name'] == tag:
                    id=label['id']
                    print('Etiqueta', label['name'], 'encontrada')
                    #Filtrar mensajes por lable, no leidos y sacar de spam
                    results = gmail.users().messages().list(
                        userId='me', 
                        labelIds=[str(id)],
                        q='is:unread',
                        includeSpamTrash=True
                    ).execute()
                    messages = results.get('messages', [])
                    #Extraer metadata
                    for message in messages:
                        msg = gmail.users().messages().get(
                            userId='me', 
                            id=message['id']  
                        ).execute()
                        #Marcar como no spam
                        results = gmail.users().messages().modify(
                            userId='me',
                            id=message['id'],
                            body={
                                "addLabelIds": [],
                                "removeLabelIds": ['SPAM']
                            }
                        ).execute()
                        #Sacar snippet
                        snippet = msg['snippet'].split('Banesco es:')[1]
                        otp = format(snippet.split('.')[0]).side_spaces()
                        data={
                            'msg_id':message['id'],
                            'otp':otp
                        }
                        data_list.append(data)
                        break               
        df = pd.DataFrame(data_list)
        
        if df.empty == False:
            print('OTP recogida')
            print(df)
        else:
            print('OTP no ha llegado')
        return(df)     









        

