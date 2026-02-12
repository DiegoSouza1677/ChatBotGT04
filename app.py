import os
import dotenv
import requests
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime

print("🚀 Iniciando aplicação Flask...")

app = Flask(__name__)

print("✅ App Flask criado")

# Carrega variáveis de ambiente
dotenv.load_dotenv()

print("✅ Variáveis de ambiente carregadas")

# Configurações - usa SECRET_KEY do .env ou gera uma
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())

print("✅ SECRET_KEY configurada")

# --- HELPERS ---

def conversar_gemini(modelo='gemini-1.5-flash', payload=''):
    """
    Faz requisição para a API do Gemini
    """
    API_KEY = os.getenv('GEMINI_API_KEY')
    
    if not API_KEY:
        return {"error": {"message": "GEMINI_API_KEY não encontrada no arquivo .env"}}
    
    url_base = "https://generativelanguage.googleapis.com/v1beta/models"
    url = f"{url_base}/{modelo}:generateContent?key={API_KEY}"
    
    try:
        resposta = requests.post(url, json=payload, timeout=30)
        resposta.raise_for_status()
        return resposta.json()
    except requests.exceptions.Timeout:
        return {"error": {"message": "Timeout: A API demorou muito para responder"}}
    except requests.exceptions.RequestException as e:
        return {"error": {"message": f"Erro na requisição: {str(e)}"}}

print("✅ Função conversar_gemini definida")

def criar_payload_inicial():
    """
    Cria o payload inicial para cada nova sessão
    """
    hora_atual = datetime.now()
    
    return {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        f"Você é um atendente virtual de uma pizzaria. "
                        f"Horário atual: {hora_atual.strftime('%H:%M')}. "
                        f"Regras: "
                        f"- Fale sempre em português "
                        f"- Seja educado e objetivo "
                        f"- Faça apenas uma pergunta por vez "
                        f"- Não crie promoções "
                        f"- Sempre confirme o pedido antes de finalizar "
                        f"- Se faltar alguma informação, pergunte e não suponha "
                        f"- O horário de funcionamento é das 10h às 23h "
                        f"- Pergunte o nome do cliente "
                        f"- Apresente o cardápio quando apropriado "
                        f"- Cardápio: Pizza Margherita (R$ 35), Pizza Calabresa (R$ 38), "
                        f"Pizza Portuguesa (R$ 40), Pizza 4 Queijos (R$ 42), "
                        f"Refrigerante (R$ 5), Suco Natural (R$ 8)"
                    )
                }
            ]
        },
        "contents": [],
        "generationConfig": {
            "maxOutputTokens": 200,
            "temperature": 0.1,
        }
    }

print("✅ Função criar_payload_inicial definida")

def limitar_historico(contents, max_mensagens=20):
    """
    Limita o histórico de mensagens para não exceder o limite da API
    """
    if len(contents) > max_mensagens:
        return contents[-max_mensagens:]
    return contents

print("✅ Função limitar_historico definida")

# --- ROTAS ---

@app.route('/')
def index():
    """Rota principal que carrega a interface do chatbot."""
    session['payload'] = criar_payload_inicial()
    return render_template('index.html')

print("✅ Rota / definida")

@app.route('/enviar_mensagem', methods=['POST'])
def enviar_mensagem():
    """Processa mensagem do usuário e retorna resposta da IA"""
    dados = request.get_json()
    mensagem_usuario = dados.get('mensagem', '').strip()

    if not mensagem_usuario:
        return jsonify({"resposta": "Mensagem vazia", "status": "erro"}), 400

    payload = session.get('payload')
    
    if not payload:
        payload = criar_payload_inicial()
        session['payload'] = payload

    content_usuario = {"role": "user", "parts": [{"text": mensagem_usuario}]}
    payload['contents'].append(content_usuario)

    payload['contents'] = limitar_historico(payload['contents'])

    resposta_json = conversar_gemini(payload=payload)

    if resposta_json and 'candidates' in resposta_json:
        try:
            conteudo_ia = resposta_json['candidates'][0]['content']
            texto_ia = conteudo_ia['parts'][0]['text']
            
            payload['contents'].append(conteudo_ia)
            session['payload'] = payload

            return jsonify({
                "resposta": texto_ia,
                "status": "sucesso"
            })
            
        except (KeyError, IndexError) as e:
            print(f"Erro ao processar estrutura do JSON: {e}")
            print(f"Resposta completa: {resposta_json}")
            return jsonify({
                "resposta": "Erro ao processar resposta da IA.",
                "status": "erro"
            }), 500
    else:
        mensagem_erro = resposta_json.get('error', {}).get('message', 'Erro desconhecido na API')
        print(f"Falha na Resposta da API Gemini: {mensagem_erro}")
        print(f"Resposta completa: {resposta_json}")
        
        return jsonify({
            "resposta": f"Ops! Tive um problema: {mensagem_erro}",
            "status": "erro"
        }), 500

print("✅ Rota /enviar_mensagem definida")

@app.route('/limpar_historico', methods=['POST'])
def limpar_historico():
    """Limpa o histórico da conversa e reinicia a sessão"""
    session['payload'] = criar_payload_inicial()
    return jsonify({"status": "sucesso", "mensagem": "Histórico limpo"})

print("✅ Rota /limpar_historico definida")

# --- TRATAMENTO DE ERROS ---

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"erro": "Erro interno do servidor"}), 500

print("✅ Error handlers definidos")

print("🔥 Chegando no if __name__ == '__main__'...")

if __name__ == '__main__':
    print("🎯 Dentro do if __name__ == '__main__'")
    
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  ATENÇÃO: GEMINI_API_KEY não encontrada no arquivo .env")
        print("📝 Crie um arquivo .env com: GEMINI_API_KEY=sua_chave_aqui")
    
    print("🚀 Iniciando servidor Flask...")
    app.run(debug=True, port=5000)