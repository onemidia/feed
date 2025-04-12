from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

# Carregando variáveis de ambiente
XIBO_AUTH_URL = os.getenv("XIBO_AUTH_URL")
XIBO_CLIENT_ID = os.getenv("XIBO_CLIENT_ID")
XIBO_CLIENT_SECRET = os.getenv("XIBO_CLIENT_SECRET")
XIBO_DATASET_ID = os.getenv("XIBO_DATASET_ID")
XIBO_API_URL = os.getenv("XIBO_API_URL")
RSS_URL = os.getenv("RSS_URL")  # ex: https://www.tribunaonline.net/feed/

# Imprimir as variáveis de ambiente para depuração
print("XIBO_AUTH_URL:", XIBO_AUTH_URL)
print("XIBO_CLIENT_ID:", XIBO_CLIENT_ID)
print("XIBO_CLIENT_SECRET:", XIBO_CLIENT_SECRET)
print("XIBO_DATASET_ID:", XIBO_DATASET_ID)
print("XIBO_API_URL:", XIBO_API_URL)
print("RSS_URL:", RSS_URL)

def get_token():
    payload = {
        'grant_type': 'client_credentials',
        'client_id': XIBO_CLIENT_ID,
        'client_secret': XIBO_CLIENT_SECRET
    }
    response = requests.post(XIBO_AUTH_URL, data=payload)
    response.raise_for_status()
    return response.json().get("access_token")

def parse_rss():
    if not RSS_URL:
        raise ValueError("A URL do feed RSS não foi fornecida. Verifique a variável de ambiente 'RSS_URL'.")

    print(f"URL do Feed RSS: {RSS_URL}")  # Log adicional

    response = requests.get(RSS_URL)
    if response.status_code != 200:
        raise ValueError(f"Erro ao acessar o feed RSS: {response.status_code}")

    soup = BeautifulSoup(response.content, features="xml")
    items = soup.findAll("item")
    noticias = []
    for item in items:
        noticias.append({
            "titulo": item.title.text.strip(),
            "descricao": item.description.text.strip(),
            "link": item.link.text.strip()
        })
    return noticias[:10]  # você pode ajustar isso

def limpar_dataset(token):
    headers = {"Authorization": f"Bearer {token}"}
    dataset_url = f"{XIBO_API_URL}/dataset/data/{XIBO_DATASET_ID}"
    requests.delete(dataset_url, headers=headers)

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

@app.route('/')
def home():
    return "✅ API Xibo Feed Convert está online."

@app.route('/atualiza_xibo')
def atualiza():
    try:
        token = get_token()
        dados = parse_rss()
        limpar_dataset(token)
        inserir_dataset(token, dados)
        return jsonify({"status": "sucesso", "itens_inseridos": len(dados)})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
