import os
import dotenv
import requests
from flask import Flask, render_template, request, jsonify
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-123'


# ==============================
# FUNÇÃO GEMINI (CORRIGIDA)
# ==============================

def conversar_gemini(modelo='gemini-2.5-flash', payload=None):
    dotenv.load_dotenv()
    API_KEY = os.getenv('GEMINI_API_KEY')

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={API_KEY}"

    resposta = requests.post(url, json=payload)

    if resposta.status_code != 200:
        return {"error": {"message": resposta.text}}

    return resposta.json()


# ==============================
# SYSTEM INSTRUCTION (INALTERADO)
# ==============================

system_instruction = {
    "parts": [
        {
            "text": (
                "Você é um atendente virtual de uma pizzaria. Regras: "
                "- Fale sempre em português "
                "- Seja educado e objetivo "
                "- Faça apenas uma pergunta por vez "
                "- Não crie promoções "
                "- Sempre confirme o pedido antes de finalizar "
                "- Se faltar alguma informação, pergunte e não suponha "
                "- O horário de funcionamento é das 10h às 23h."
                "- pergunte o nome do cliente"
                "- Diga o cardápio disponivel"
                "- Se o cliente pedir um sabor que não temos, informe educadamente e ofereça opções do cardápio "
                "- Se o cliente pedir um sabor que temos, confirme o pedido e pergunte se deseja algo mais "
                "- Se o cliente pedir para finalizar o pedido, confirme o nome e o pedido completo antes de finalizar "
                "-pergunte ao cliente qual a forma de pagamento (dinheiro, cartão ou pix) e informe o tempo estimado para entrega (30-45 minutos) "
                "- Se o cliente pedir para cancelar o pedido, confirme o nome e o pedido completo antes de cancelar "
                "- Se o cliente pedir para alterar o pedido, confirme o nome e o pedido completo antes de alterar "
                "- Se o cliente pedir para falar com um atendente humano, informe que um atendente humano irá entrar em contato em breve e finalize a conversa educadamente "
                "-apos o cliente fazer o pedido, pergunte se ele deseja acompanhar o status do pedido por WhatsApp ou SMS e informe que ele receberá atualizações sobre o status do pedido (preparando, a caminho, entregue) "
                "-Apos o cliente finalizar o pedido, agradeça pela preferência e informe que ele pode entrar em contato novamente se precisar de algo mais "
                "-Cardapio:"
                "1. Margherita - R$ 25,00 "
                "2. Pepperoni - R$ 30,00 "
                "3. Calabresa - R$ 28,00 "
                "4. Portuguesa - R$ 32,00 "
                "5. Frango com Catupiry - R$ 29,00 "
                "6. Quatro Queijos - R$ 31,00 "
                "7. Vegetariana - R$ 27,00 "
                "Bebidas:"
                "1. Refrigerante - R$ 5,00 "
                "2. Suco Natural - R$ 7,00 "
                "3. Água Mineral - R$ 3,00 "
                "4. Cerveja - R$ 8,00 "
                "Acompanhamentos:"
                "1. Batata Frita - R$ 10,00 "
                "2. Onion Rings - R$ 12,00 "
                "Bordas:"
                "1. Tradicional - R$ 0,00 "
                "2. Recheada com Catupiry - R$ 5,00 "
                "3. Recheada com Chocolate - R$ 7,00 "
                "4. Recheada com Doce de Leite - R$ 7,00 "
            )
        }
    ]
}


generation_config = {
    "maxOutputTokens": 200,
    "temperature": 0.1,
}


# ==============================
# ROTAS
# ==============================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/enviar_mensagem', methods=['POST'])
def enviar_mensagem():
    dados = request.get_json()
    mensagem_usuario = dados.get('mensagem', '')

    if not mensagem_usuario:
        return jsonify({"resposta": "Mensagem vazia", "status": "erro"}), 400

    # Payload criado por requisição (corrigido)
    payload_local = {
        "systemInstruction": system_instruction,
        "contents": [
            {"role": "user", "parts": [{"text": mensagem_usuario}]}
        ],
        "generationConfig": generation_config
    }

    resposta_json = conversar_gemini(payload=payload_local)

    if resposta_json and 'candidates' in resposta_json:
        try:
            texto_ia = resposta_json['candidates'][0]['content']['parts'][0]['text']

            return jsonify({
                "resposta": texto_ia,
                "status": "sucesso"
            })

        except (KeyError, IndexError):
            return jsonify({
                "resposta": "Erro ao processar resposta da IA.",
                "status": "erro"
            }), 500
    else:
        mensagem_erro = resposta_json.get('error', {}).get('message', 'Erro desconhecido na API')

        return jsonify({
            "resposta": f"Ops! Tive um problema: {mensagem_erro}",
            "status": "erro"
        }), 500


@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', erro="Página não encontrada"),_
