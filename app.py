import requests
from flask import Flask, render_template, request, jsonify
import os
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)

# Configurações da API
API_KEY = os.getenv("CHAVE_API_GEMINI")

MODELO = 'gemini-3-flash-preview' # Ajustado para uma versão estável existente
URL = f'https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent?key={API_KEY}'


cardapio = {
    "Hamburguer Clássico": 12.00,
    "Batata Frita M": 10.00,
    "Refrigerante Lata": 6.50,
    "X-Burguer": 18.00,
    "X-Salada": 22.00,
    "X-Bacon": 26.00,
    "Combo Família": 85.00,
    "Nuggets (10 unid)": 15.00,
    "Milkshake Chocolate": 14.50,
    "Suco Natural": 9.00,
    "Cachorro Quente": 15.00,
    "Anéis de Cebola": 12.00,
    "Batata com Cheddar e Bacon": 22.00,
    "Hambúrguer Artesanal": 32.00,
    "Água Mineral": 4.00
}

import datetime
hora = datetime.datetime.now()
print(hora)

# Payload inicial com estrutura para System Instruction (regras do sistema)
# O campo 'system_instruction' é suportado pela API do Gemini para definir o comportamento
config_ia = {
    "system_instruction": {
        "parts": [{
            "text": f' Você é o um atendente virtual de uma lanchonete.Regras de comportamento: 1. Sempre cumprimente o cliente e seja prestativo.           2. Se o cliente perguntar sobre preços, mostre o cardápio que é esse aqui {cardapio} 3. Responda de forma curta e objetiva (máximo 3 frases). 4. Se não souber algo, peça para o cliente aguardar um atendente humano. 5. O horario de funcionamento é 18h as 00:00 e a hora atual é {hora}. 6 . Fazemos entrega até 7k de distância. 7. Para pedidos além dessa distância o cliente deve chamar um uber.8 Se o usuário fizer perguntas fora de contexto, diga que não pode falar sobre isso'
        }]
    },
    "contents": [],
    "generationConfig":{
                "maxOutputTokens":200,
                "temperature":0.1,
            }
}


def enviar_para_gemini(mensagem_usuario, historico):
    """
    Envia a mensagem para a API e retorna a resposta da IA.
    Recebe a mensagem atual e a lista do histórico de mensagens.
    """
    # Adiciona a nova pergunta do usuário ao histórico que será enviado
    historico.append({"role": "user", "parts": [{"text": mensagem_usuario}]})
    print(hora)
    payload = {
        "system_instruction": config_ia["system_instruction"],
        "contents": historico
    }

    try:
        resposta = requests.post(URL, json=payload)
        resposta.raise_for_status() # Verifica se houve erro na requisição
        dados = resposta.json()
        
        # Extrai o texto da resposta
        resposta_ia = dados['candidates'][0]['content']['parts'][0]['text']
        
        # Adiciona a resposta da IA ao histórico para manter o contexto na próxima chamada
        historico.append({"role": "model", "parts": [{"text": resposta_ia}]})
        
        return resposta_ia
    except Exception as e:
        print(f"Erro na chamada da API: {e}")
        return "Desculpe, tive um erro ao processar sua resposta."

# --- ROTAS FLASK ---

@app.route("/")
def index():
    return render_template("index.html")

# Simulação de "banco de dados" em memória para o histórico desta sessão
# Em um sistema real, usaríamos session do Flask ou Redis
chat_historico = []

@app.route("/get", methods=["POST"])
def get_bot_response():
    user_text = request.json.get("msg")
    
    if not user_text:
        return jsonify({"response": "Mensagem vazia"}), 400

    # Chama a função que você solicitou
    resposta_ia = enviar_para_gemini(user_text, chat_historico)
    
    return jsonify({"response": resposta_ia})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')