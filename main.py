import sqlite3
import jwt
import datetime

from resources import calc, format
from thefuzz import fuzz
from functools import wraps
from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, request, make_response


app = Flask(__name__)
app.config["SECRET KEY"] = "lFZBKw5fFajh4cR4KSgwpeAFzsklGfew"

CORS(app, resources={r"/*": {"origins": "*"}})


def db_connection():
    conn = None
    try:
        conn = sqlite3.connect("bot_op.sqlite")
    except sqlite3.Error as e:
        print(e)
    return conn

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]
        if not token:
            return jsonify({"message": "Token no recibido"}), 401
        try:
            data = jwt.decode(token, app.config["SECRET KEY"], ["HS256"])
            current_user = data["user"]
        except:
            return jsonify({"message": "Token invalido"}), 401
        return f(current_user, *args, **kwargs)

    return decorated

# Autorizar consumidor
@app.route("/auth")
def auth():
    auth = request.authorization
    if auth and auth.password == "ct59YjSHDEv39Zc":
        token = jwt.encode(
            {
                "user": auth.username,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2200),
            },
            app.config["SECRET KEY"],
        )
        return jsonify({"token": token})
    return make_response("Clave incorrecta", 401)

# Listar depositos
@app.route("/depositos")
@token_required
def depositos_list(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM depositos"
        cursor.execute(sql)
        datos = cursor.fetchall()
        depositos = []
        for fila in datos:
            deposito = {
                "msg_id": fila[0],
                "cuenta": fila[1],
                "banco": fila[2],
                "fecha_deposito": fila[3],
                "hora_deposito": fila[4],
                "remitente": fila[5],
                "monto": fila[6],
                "cobro": fila[7],
                "op_id": fila[8],
            }
            depositos.append(deposito)
        return jsonify({"depositos": depositos})
    except Exception as e:
        return jsonify({"mensaje": e})

# Listar entradas
@app.route("/entradas")
@token_required
def entradas_list(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM entradas"
        cursor.execute(sql)
        datos = cursor.fetchall()
        entradas = []
        for fila in datos:
            entrada = {
                "op_id": fila[0],
                "fecha": fila[1],
                "hora": fila[2],
                "remitente": fila[3],
                "monto": fila[4],
                "banco": fila[5],
                "pago": fila[6],
            }
            entradas.append(entrada)
        return jsonify({"entradas": entradas}), 200
    except Exception as e:
        return jsonify({"mensaje": e}), 400

# Listar salidas
@app.route("/salidas")
@token_required
def salidas_list(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM salidas"
        cursor.execute(sql)
        datos = cursor.fetchall()
        salidas = []
        for fila in datos:
            salida = {
                "op_id": fila[0],
                "fecha": fila[1],
                "hora": fila[2],
                "banco": fila[3],
                "cuenta": fila[4],
                "persona": fila[5],
                "documento": fila[6],
                "beneficiario": fila[7],
                "monto": fila[8],
                "tasa": fila[9],
                "pago": fila[10],
                "restante": fila[11]
            }
            salidas.append(salida)
        return jsonify({"salidas": salidas}), 200
    except Exception as e:
        return jsonify({"mensaje": e}), 400

# Listar entradas por pagar
@app.route("/entradas/pendientes", methods=["GET"])
@token_required
def entradas_pendientes_get(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM entradas WHERE pago = False"
        cursor.execute(sql)
        datos = cursor.fetchall()
        entradas = []
        if datos != None:
            for fila in datos:
                entrada = {
                    "op_id": fila[0],
                    "fecha": fila[1],
                    "hora": fila[2],
                    "remitente": fila[3],
                    "monto": fila[4],
                    "banco": fila[5],
                    "pago": fila[6],
                }
                entradas.append(entrada)
            return jsonify({"entradas": entradas}), 200
        else:
            return jsonify({"mensaje": "Nada nuevo"}), 204
    except Exception as e:
        return jsonify({"mensaje": str(e)})

# Listar salidas por pagar
@app.route("/salidas/pendientes/<banco>", methods=["GET"])
@token_required
def salidas_pendientes_get(current_user, banco):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        if banco.upper() == "MERCANTIL":
            sql = "SELECT * FROM salidas WHERE pago = 0 and banco = '{0}'".format(
                banco.upper()
            )
        else:
            sql = "SELECT * FROM salidas WHERE pago = 0 and banco <> 'MERCANTIL'"
        cursor.execute(sql)
        datos = cursor.fetchall()
        salidas = []
        if datos != None:
            for fila in datos:
                salida = {
                    "op_id": fila[0],
                    "fecha": fila[1],
                    "hora": fila[2],
                    "banco": fila[3],
                    "cuenta": fila[4],
                    "persona": fila[5],
                    "documento": fila[6],
                    "beneficiario": fila[7],
                    "monto": fila[8],
                    "tasa": fila[9],
                    "pago": fila[10],
                    "restante": fila[11]
                }
                salidas.append(salida)
            return jsonify({"salidas": salidas}), 200
        else:
            return jsonify({"mensaje": "Nada nuevo"}), 204
    except Exception as e:
        return jsonify({"mensaje": str(e)})

# Listar un depósito
@app.route("/depositos/<msg_id>", methods=["GET"])
@token_required
def depositos_get(current_user, msg_id):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM depositos WHERE msg_id = '{0}'".format(msg_id)
        cursor.execute(sql)
        datos = cursor.fetchone()
        if datos != None:
            deposito = {
                "msg_id": datos[0],
                "cuenta": datos[1],
                "banco": datos[2],
                "fecha": datos[3],
                "hora": datos[4],
                "remitente": datos[5],
                "monto": datos[6],
                "cobro": datos[7],
            }
            return jsonify({"deposito": deposito}), 200
        else:
            return jsonify({"mensaje": "Deposito no encontrado"}), 204
    except Exception as e:
        return jsonify({"mensaje": e})

# Listar una entrada
@app.route("/entradas/<op_id>", methods=["GET"])
@token_required
def entradas_get(current_user, op_id):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM entradas WHERE op_id = '{0}'".format(op_id)
        cursor.execute(sql)
        datos = cursor.fetchall()
        for fila in datos:
            entrada = {
                "op_id": fila[0],
                "fecha": fila[1],
                "hora": fila[2],
                "remitente": fila[3],
                "monto": fila[4],
                "banco": fila[5],
                "pago": fila[6],
            }
        return jsonify({"entrada": entrada}), 200
    except Exception as e:
        return jsonify({"mensaje": e}), 400

# Listar una salida
@app.route("/salidas/<op_id>", methods=["GET"])
@token_required
def salidas_get(current_user, op_id):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM salidas WHERE op_id = '{0}'".format(op_id)
        cursor.execute(sql)
        datos = cursor.fetchall()
        salidas = []
        if datos != None:
            for fila in datos:
                salida = {
                    "op_id": fila[0],
                    "fecha": fila[1],
                    "hora": fila[2],
                    "banco": fila[3],
                    "cuenta": fila[4],
                    "persona": fila[5],
                    "documento": fila[6],
                    "beneficiario": fila[7],
                    "monto": fila[8],
                    "tasa": fila[9],
                    "pago": fila[10],
                    "restante": fila[11]
                }
            salidas.append(salida)
        return jsonify({"salida": salidas}), 200
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 400

# Encontrar match
@app.route("/match")
@token_required
def depositos_match(current_user):
    remitente = str(request.json["remitente"])
    monto = float(request.json["monto"])
    op_id = str(request.json["op_id"])
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM depositos WHERE cobro is FALSE"
        cursor.execute(sql)
        datos = cursor.fetchall()
        # Crear lista iterable con depósitos no cobrados
        depositos = []
        for fila in datos:
            deposito = {
                "msg_id": fila[0],
                "cuenta": fila[1],
                "banco": fila[2],
                "fecha_deposito": fila[3],
                "hora_deposito": fila[4],
                "remitente": fila[5],
                "monto": fila[6],
                "cobro": fila[7],
                "op_id": fila[8],
            }
            depositos.append(deposito)
        # Iterar sobre lista buscando coincidencia de nombre y monto
        counter = 0
        for r in reversed(depositos):
            # Preparar nombres
            bank_name = str(r["remitente"])
            desk_name = remitente
            # Separar nombres
            bank_name_ls = bank_name.split(" ")
            desk_name_ls = remitente.split(" ")
            # Reordenar si el nombre tiene más de 4 elementos
            if len(bank_name_ls) >= 4:
                bank_name = (
                    str(bank_name_ls[0])
                    + " "
                    + str(bank_name_ls[2] + " " + str(bank_name_ls[3]))
                )
                bank_name2 = (
                    str(bank_name_ls[0])
                    + " "
                    + str(bank_name_ls[1] + " " + str(bank_name_ls[2]))
                )
            else:
                bank_name2 = bank_name
            if len(desk_name_ls) >= 4:
                desk_name = (
                    str(desk_name_ls[0])
                    + " "
                    + str(desk_name_ls[2] + " " + str(desk_name_ls[3]))
                )
                desk_name2 = (
                    str(desk_name_ls[0])
                    + " "
                    + str(desk_name_ls[1] + " " + str(desk_name_ls[2]))
                )
            else:
                desk_name2 = desk_name
            # Parametros de comparación
            counter += 1
            monto_depositos = float(r["monto"])
            discrepancia = abs((monto - monto_depositos) / monto)
            cascada = calc(monto).tolerance()

            if (
                fuzz.token_sort_ratio(str(bank_name), str(desk_name)) >= 69
                and discrepancia < cascada
                and r["cobro"] == False
            ):
                sql = "UPDATE depositos SET cobro = {0}, op_id = '{1}' WHERE msg_id = '{2}'".format(
                    True, op_id, r["msg_id"]
                )
                cursor.execute(sql)
                conn.commit()
                r["codigo"] = "200"
                return jsonify(r)
            elif (
                fuzz.token_sort_ratio(str(bank_name2), str(desk_name)) >= 69
                and discrepancia < cascada
                and r["cobro"] == False
            ):
                sql = "UPDATE depositos SET cobro = {0}, op_id = '{1}' WHERE msg_id = '{2}'".format(
                    True, op_id, r["msg_id"]
                )
                cursor.execute(sql)
                conn.commit()
                r["codigo"] = "200"
                return jsonify(r)
            elif (
                fuzz.token_sort_ratio(str(bank_name), str(desk_name2)) >= 69
                and discrepancia < cascada
                and r["cobro"] == False
            ):
                sql = "UPDATE depositos SET cobro = {0}, op_id = '{1}' WHERE msg_id = '{2}'".format(
                    True, op_id, r["msg_id"]
                )
                cursor.execute(sql)
                conn.commit()
                r["codigo"] = "200"
                return jsonify(r)
            elif (
                fuzz.token_sort_ratio(str(bank_name2), str(desk_name2)) >= 69
                and discrepancia < cascada
                and r["cobro"] == False
            ):
                sql = "UPDATE depositos SET cobro = {0}, op_id = '{1}' WHERE msg_id = '{2}'".format(
                    True, op_id, r["msg_id"]
                )
                cursor.execute(sql)
                conn.commit()
                r["codigo"] = "200"
                return jsonify(r), 200
            elif counter == len(depositos):
                return (
                    jsonify({"mensaje": "Transaccion no existe", "codigo": "204"}), 200
                )
        return jsonify({"depositos": depositos}), 201
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 400

# Insertar deposito
@app.route("/depositos", methods=["POST"])
@token_required
def depositos_add(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = """
        INSERT INTO depositos 
        VALUES ('{0}','{1}','{2}','{3}','{4}','{5}', {6}, {7}, NULL)
        """.format(
            request.json["msg_id"],
            request.json["cuenta"],
            request.json["banco"],
            request.json["fecha_deposito"],
            request.json["hora_deposito"],
            request.json["remitente"],
            request.json["monto"],
            False,
        )
        cursor.execute(sql)
        conn.commit()
        return jsonify({"mensaje": "Deposito registrado"}), 201
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 400

# Insertar entrada
@app.route("/entradas", methods=["POST"])
@token_required
def entradas_add(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = """
        INSERT INTO entradas 
        VALUES ('{0}','{1}','{2}','{3}', {4}, '{5}', {6})
        """.format(
            request.json["op_id"],
            request.json["fecha"],
            request.json["hora"],
            format(request.json["remitente"].upper()).clean_string(),
            request.json["monto"],
            request.json["banco"],
            False,
        )
        cursor.execute(sql)
        conn.commit()
        return jsonify({"mensaje": "Entrada recibida"}), 201
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 400

# Insertar salida
@app.route("/salidas", methods=["POST"])
@token_required
def salidas_add(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = """
        INSERT INTO salidas 
        VALUES ('{0}','{1}','{2}','{3}', '{4}', '{5}', 
        {6}, '{7}', {8}, {9}, {10}, {11})
        """.format(
            request.json["op_id"],
            request.json["fecha"],
            request.json["hora"],
            request.json["banco"].upper(),
            request.json["cuenta"],
            request.json["persona"].upper(),
            request.json["documento"],
            format(request.json["beneficiario"]).clean_string().upper(),
            request.json["monto"],
            request.json["tasa"],
            0,
            "NULL"
        )
        cursor.execute(sql)
        conn.commit()
        return jsonify({"mensaje": "Salida recibida"}), 201
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 400

# Modificar entrada
@app.route("/entradas", methods=["PUT"])
@token_required
def entradas_modify(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = """
        UPDATE entradas SET pago={0} WHERE op_id='{1}'
        """.format(
            True, request.json["op_id"]
        )
        cursor.execute(sql)
        conn.commit()
        return jsonify({"mensaje": "Entrada marcada como pagada"}), 201
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 404

# Modificar salida
@app.route("/salidas", methods=["PUT"])
@token_required
def salidas_modify(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        try:
            restante = request.json["restante"]
        except:
            restante = "NULL"
        sql = """
        UPDATE salidas SET pago={0}, restante={1} WHERE op_id='{2}'
        """.format(
            request.json["pago"], 
            restante,
            request.json["op_id"],
        )
        cursor.execute(sql)
        conn.commit()
        return jsonify({"mensaje": "Salida modificada"}), 201
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 404

# Eliminar deposito
@app.route("/depositos/<id>", methods=["DELETE"])
@token_required
def depositos_delete(current_user, id):
    remitente = str(request.args.get("remitente"))
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "DELETE FROM depositos WHERE msg_id = '{0}' OR remitente = '{1}'".format(
            id, remitente
        )
        cursor.execute(sql)
        conn.commit()
        return jsonify({"mensaje": "Registro eliminado"})
    except Exception as e:
        return jsonify({"mensaje": str(e)})

# Eliminar salida
@app.route("/salidas/<id>", methods=["DELETE"])
@token_required
def salidas_delete(current_user, id):
    remitente = str(request.args.get("remitente"))
    try:
        conn = db_connection()
        cursor = conn.cursor()
        sql = "DELETE FROM salidas WHERE op_id = '{0}' OR beneficiario = '{1}'".format(
            id, remitente
        )
        cursor.execute(sql)
        conn.commit()
        return jsonify({"mensaje": "Registro eliminado"})
    except Exception as e:
        return jsonify({"mensaje": str(e)})


def pagina_no_encontrada(error):
    return jsonify({"mensaje": "Lo que estabas buscando no existe..."})


if __name__ == "__main__":
    app.register_error_handler(404, pagina_no_encontrada)
    app.run(debug=True)
