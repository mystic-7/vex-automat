import re

from sqlalchemy import func

class calc:
    def __init__(self, amount):
        self.amount = amount

    def tolerance(self):
        if self.amount <=3:
            return 0.02
        elif self.amount >=3 and self.amount <10 :
            return 0.02
        elif self.amount >=10 and self.amount <30:
            return 0.02
        elif self.amount >=30 and self.amount <60:
            return 0.02
        elif self.amount >=60:
            return 0.02

class format:
    def __init__(self, string):
        self.string = string
        
    def side_spaces(self):
        return "".join(self.string.rstrip().lstrip())

    def clean_string(self):
        special_characters = ['!','#','$','%','&','@','[',']',']','_','.',',',':','{','}']
        dirty=self.string
        for i in special_characters:
            cleanstring = dirty.replace(i,'')
            dirty = cleanstring
        return dirty

    def clean_html(self):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', self.string)
        return cleantext

class any_ec:
    """ Use with WebDriverWait to combine expected_conditions
        in an OR.
    """
    def __init__(self, *args):
        self.ecs = args
    def __call__(self, driver):
        for fn in self.ecs:
            try:
                res = fn(driver)
                if res:
                    return res
                    # Or return res if you need the element found
            except:
                pass

class mail_body:
    def __init__(self) -> None:
        pass

    def op(self, op_id, benef, ammount, bank, date, time, err_msg):
        self.op_id = op_id
        self.benef = benef
        self.ammount = ammount
        self.bank = bank
        self.date = date
        self.time = time
        self.err_msg = err_msg
        b = """
        La siguiente transacción no pudo ser completada:

            -------------------
            ID de operación: {0} (back-end)
            Beneficiario: {1} 
            Monto: BsS {2} 
            Banco: {3} 
            Fecha de operación: {4}
            Hora de solicitud: {5}
            -------------------

        Mensaje devuelto por el banco:

        {6}

        Por favor verificar en portal. 
        
        Para completar la operación se puede:
        
        1 - Rechazarla y solicitar al cliente que verifique los datos y vuelva a montarla.
        2 - Procesar manualmente.
            """.format(op_id[-6:], benef, ammount, bank, date, time, err_msg)
        return(b)
    def alert(self, function, file):
        self.function = function
        self.file = file
        b = f"""
        Se esta registrando un error en el metodo {function} del archivo {file}, por favor notificar al proveedor.
            """
        return(b)