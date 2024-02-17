from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
import bcrypt
import jwt
import datetime
from dotenv import load_dotenv
import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from unidecode import unidecode
from elasticsearch import Elasticsearch
from flask_swagger_ui import get_swaggerui_blueprint
import re

app = Flask(__name__)

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')

es = Elasticsearch(['http://127.0.0.1:9200/'])

client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["target_data"]
users = db["users"]

def createToken(user_id):
    # Definir payload do token
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=720)  # Token expira em 720 horas
    }
    # Gerar token JWT
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def verifyToken(token):
    try:
        # Decodificar token JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return { "status": True, "payload": payload }
    except jwt.ExpiredSignatureError:
        # Token expirou
        return { "status": False, "message": 'Token expirado. Faça login novamente.'}
    except jwt.InvalidTokenError:
        # Token inválido
        return { "status": False, "message": 'Token inválido. Faça login novamente.'}

def generateLog(index_name, user_id, level, message):
    log_message = {
        '@timestamp': datetime.datetime.now().isoformat(),
        'user_id': str(user_id),
        'level': level,
        'message': message
    }

    res = es.index(index=index_name, body=log_message)

    print(res['result'])

    return True

@app.route('/user', methods=['GET', 'POST'])
def userRoute():
    if (request.method == 'POST'):
        user = request.form['user']

        if (not user):
            return jsonify({"status": False, "message": "Nome de usário não enviado."}), 401

        password = request.form['password']

        if (not password):
            return jsonify({"status": False, "message": "Senha não enviada."}), 401
        
        password_bytes = password.encode('utf-8')
        password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        user_created = db.users.insert_one({"user": user, "password_hash": password_hash})
        generateLog('logs', user_created.inserted_id, 'INFO', f'{str(user_created.inserted_id)} se cadastrou às {datetime.datetime.now().isoformat()}.')
        return jsonify({"status": True, "message": 'ID do usuário inserido:' + str(user_created.inserted_id)}), 201

@app.route('/token', methods=['GET', 'POST'])
def tokenRoute():
    if (request.method == 'POST'):
        user = request.form['user']

        if (not user):
            return jsonify({"status": False, "message": "Nome de usuário inválido."}), 401

        password = request.form['password']

        if (not password):
            return jsonify({"status": False, "message": "Senha inválida."}), 401

        password_bytes = password.encode('utf-8')

        find_user = users.find_one({"user": user})

        if (not find_user):
            return jsonify({"status": False, "message": "Usuário não encontrado."}), 401
        
        if (bcrypt.hashpw(password_bytes, find_user['password_hash']) == find_user['password_hash']):
            token = createToken(str(find_user['_id']))
            generateLog('logs', str(find_user['_id']), 'INFO', f'{str(find_user["_id"])} gerou um token às {datetime.datetime.now().isoformat()}.')
            return jsonify({"token": token, "status": True}), 200
        return jsonify({"status": False, "message": "Credenciais inválidas."}), 401

@app.route('/cep', methods=['GET', 'POST'])
def cepRoute():
    if (request.method == 'POST'):
        result_token = verifyToken(request.form['token'])

        if (not result_token["status"]):
            return jsonify(result_token)
        
        cep = request.form['CEP']
        if (cep):

            regex = r'^\d+$'
            if (not re.match(regex, cep)):
                return jsonify({"status": False, "message": "Insira apenas números no CEP."}), 401

            if (len(cep) != 8):
                return jsonify({"status": False, "message": "O CEP precisa ter apenas 8 caracteres." }), 401

            response_cep = requests.get(f'https://viacep.com.br/ws/{cep}/json')

            if (response_cep.status_code != 200):
                return {"status": False, "message": "ViaCEP apresentou uma falha na requsição.", "error_code": response_cep.status_code }, 401
            
            response_cep_data = response_cep.json()
            
            localidade = response_cep_data['localidade']
            response_list_cities = requests.get(f'http://servicos.cptec.inpe.br/XML/listaCidades?city={quote(unidecode(localidade.lower()))}')

            if (response_list_cities.status_code != 200):
                return {"status": False, "message": "INPE - listaCidades - apresentou uma falha na requsição.", "error_code": response_list_cities.status_code }, 401
    
            root = ET.fromstring(response_list_cities.content)
            city_id = root.find('cidade').find('id').text

            response_prev_time = requests.get(f'http://servicos.cptec.inpe.br/XML/cidade/{city_id}/previsao.xml')

            if (response_prev_time.status_code != 200):
                return {"status": False, "message": "INPE - previsão - apresentou uma falha na requsição.", "error_code": response_cep.status_code }, 401
                        
            root = ET.fromstring(response_prev_time.content)

            result = { **response_cep_data }
            serialize_prev_time = { 
                root.find('nome').tag: root.find('uf').text,
                root.find('uf').tag: root.find('uf').text,
                root.find('atualizacao').tag: root.find('atualizacao').text,
                'previsao': []
            }

            for item in root.findall('previsao'):
                serialize_prev_time['previsao'].append({
                    "dia": item.find("dia").text,
                    "tempo": item.find("tempo").text,
                    "maxima": item.find("maxima").text,
                    "minima": item.find("minima").text,
                    "iuv": item.find("iuv").text
                })

            result['inpe'] = { **serialize_prev_time }

            generateLog('logs', result_token["payload"]["user_id"], 'INFO', f'{result_token["payload"]["user_id"]} consultou um CEP às {datetime.datetime.now().isoformat()}.')

            return jsonify(result)
        return jsonify({ "status": False, "message": "CEP não enviado"}), 401
        
@app.route('/logs', methods=['GET'])
def logsRoute():
    if (request.method == 'GET'):
        result_token = verifyToken(request.args.get('token'))

        if (not result_token["status"]):
            return jsonify(result_token)
        
        # Consulta simples para obter todos os logs do usuário especificado
        query = {
            "query": {
                "match": {
                    "user_id": result_token["payload"]["user_id"]
                }
            }
        }

        # Nome do índice onde os logs foram indexados
        index_name = "logs"

        # Realiza a consulta
        res = es.search(index=index_name, body=query)

        generateLog('logs', result_token["payload"]["user_id"], 'INFO', f'{result_token["payload"]["user_id"]} consultou os logs às {datetime.datetime.now().isoformat()}.')

        return jsonify({"status": True, "result": res["hits"]["hits"]}), 200
    
@app.route('/api/docs')
def docs():
    return send_from_directory('.', 'swagger.yaml')
    
SWAGGER_URL = '/docs'
API_URL = 'http://127.0.0.1:5000/api/docs'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Technical Test application"
    },
)

app.register_blueprint(swaggerui_blueprint)

if __name__ == '__main__':
    app.run(debug=True)