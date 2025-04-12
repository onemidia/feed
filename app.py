from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

XIBO_AUTH_URL = os.getenv("XIBO_AUTH_URL")
XIBO_CLIENT_ID = os.getenv("XIBO_CLIENT_ID")
XIBO_CLIENT_SECRET = os.getenv("XIBO_CLIENT_SECRET")
XIBO_DATASET_ID = os.getenv("XIBO_DATASET_ID")
XIBO_API_URL = os.getenv("XIBO_API_URL")

RSS_URL = os.getenv("RSS_URL")  # ex: http://example.com/rss

def get_token():
    try:
        payload = {
            'grant_type': 'client_credentials',
            'client_id': XIBO_CLIENT_ID,
            'client_secret': XIBO_CLIENT_SECRET
        }
        response = requests.post(XIBO_AUTH_URL, data=payload)
        response.raise_for_status()  # Vai lançar uma exceção se o status não for 2xx
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter token: {e}")
        raise

def parse_rss():
    try:
        response = requests.get(RSS_URL)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
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
    except requests.exceptions.RequestException as e:
        print(f"Erro ao ler o feed RSS: {e}")
        raise

def limpar_dataset(token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        dataset_url = f"{XIBO_API_URL}/dataset/data/{XIBO_DATASET_ID}"
        response = requests.delete(dataset_url, headers=headers)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
    except requests.exceptions.RequestException as e:
        print(f"Erro ao limpar dataset: {e}")
        raise

def inserir_dataset(token, dados):
    try:
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
            response = requests.post(dataset_url, json=payload, headers=headers)
            response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
    except requests.exceptions.RequestException as e:
        print(f"Erro ao inserir dados no dataset: {e}")
        raise

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
        print(f"Erro ao atualizar Xibo: {e}")
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
