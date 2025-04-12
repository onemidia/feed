from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

# Variáveis de ambiente
XIBO_CLIENT_ID = os.getenv("XIBO_CLIENT_ID")
XIBO_CLIENT_SECRET = os.getenv("XIBO_CLIENT_SECRET")
XIBO_DATASET_ID = os.getenv("XIBO_DATASET_ID")
XIBO_API_URL = os.getenv("XIBO_API_URL")
RSS_URL = os.getenv("RSS_URL")

# Função para obter o token de autenticação
def get_token():
    payload = {
        'grant_type': 'client_credentials',
        'client_id': XIBO_CLIENT_ID,
        'client_secret': XIBO_CLIENT_SECRET
    }
    response = requests.post(f"{XIBO_API_URL}/auth/token", data=payload)
    response.raise_for_status()  # Garante que, se a requisição falhar, uma exceção seja levantada
    return response.json().get("access_token")

# Função para parsear o feed RSS
def parse_rss():
    response = requests.get(RSS_URL)
    soup = BeautifulSoup(response.content, features="xml")
    items = soup.findAll("item")
    noticias = []
    for item in items:
        noticias.append({
            "titulo": item.title.text.strip(),
            "descricao": item.description.text.strip(),
            "link": item.link.text.strip()
        })
    return noticias[:10]  # Pode ajustar conforme necessário

# Função para limpar o dataset
def limpar_dataset(token):
    headers = {"Authorization": f"Bearer {token}"}
    dataset_url = f"{XIBO_API_URL}/dataset/data/{XIBO_DATASET_ID}"
    requests.delete(dataset_url, headers=headers)

# Função para inserir dados no dataset
def inserir_dataset(token, dados):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    dataset_url = f"{XIBO_API_URL}/dataset/data/{XIBO_DATASET_ID}"
    for item in dados:
        payload = {
            "data": {
                "titulo": item["titulo"],
                "descricao": item["descricao"],
                "link": item["link"]
            }
        }
        requests.post(dataset_url, json=payload, headers=headers)

# Rota principal
@app.route('/')
def home():
    return "✅ API Xibo Feed Convert está online."

# Rota de atualização do Xibo
@app.route('/atualiza_xibo')
def atualiza():
    try:
        print("Carregando variáveis de ambiente:")
        print(f"XIBO_CLIENT_ID: {XIBO_CLIENT_ID}")
        print(f"XIBO_CLIENT_SECRET: {XIBO_CLIENT_SECRET}")
        print(f"XIBO_DATASET_ID: {XIBO_DATASET_ID}")
        print(f"XIBO_API_URL: {XIBO_API_URL}")
        print(f"RSS_URL: {RSS_URL}")

        token = get_token()
        dados = parse_rss()
        limpar_dataset(token)
        inserir_dataset(token, dados)

        return jsonify({"status": "sucesso", "itens_inseridos": len(dados)})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
