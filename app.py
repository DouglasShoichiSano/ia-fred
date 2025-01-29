import os 
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from dotenv import load_dotenv
import random
from datetime import datetime
import pytz
from groq import Groq
from pymongo import MongoClient
import time
from pymongo import MongoClient
from jinja2 import Template
import uvicorn
import base64
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from bson import ObjectId
import pandas as pd
from difflib import SequenceMatcher
from twilio.rest import Client
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


# Definindo as listas com os links
manha = [
    "https://drive.google.com/uc?export=download&id=1xIAbK0lflRb0GYi9pn2_1RNwGJO5RgOI",
    "https://drive.google.com/uc?export=download&id=1mqILBgwzJ1QSfN2ePOmIg16c45iHAAdO",
    "https://drive.google.com/uc?export=download&id=1LrpBbd0nQK5j1hEb8tbZ-kyHMzXUrZkp",
    "https://drive.google.com/uc?export=download&id=1YGfvohufrRO4pxfZixIOq2taLuuWbO2f",
    "https://drive.google.com/uc?export=download&id=1m4LjfLhf2gbcDlzC7U3j_KWaEDL1ljbY"
]

tarde = [
    "https://drive.google.com/uc?export=download&id=1AgX2K-YpW_BzR3_p80BNeiJOdpNbpPSO",
    "https://drive.google.com/uc?export=download&id=1Ix3cCD8IM-uBVUD42ddF0qSiSG-23bgk",
    "https://drive.google.com/uc?export=download&id=1tX51j3HRo1sm8yn8SfpsAJqz220qCmmN",
    "https://drive.google.com/uc?export=download&id=1oDjM3mq6wghqgDyE77ZyOdjJS3CojaNt",
    "https://drive.google.com/uc?export=download&id=1m4LjfLhf2gbcDlzC7U3j_KWaEDL1ljbY"
]

noite = [
    "https://drive.google.com/uc?export=download&id=1N6LXqNGI0KHeGWXKQf4of_CBf2RNnuY7",
    "https://drive.google.com/uc?export=download&id=1ztdpZ5NDQSohDCcrspIKiHzTPEfNztcV",
    "https://drive.google.com/uc?export=download&id=1Xttx5iVXq8FR7HneSTY9xV3JaBMyTcmu",
    "https://drive.google.com/uc?export=download&id=1m4LjfLhf2gbcDlzC7U3j_KWaEDL1ljbY"
]


# Inicializar o histórico do chat
chat_history = [
        {'role': 'system', 'content':f"""seu objetivo é preencher a seguinte lista 
         Tipo do cliente: (entregador ou visitante)
         Nome do cliente: (caso o tipo do cliente seja entregador esse campo pode ser preenchido como entregador também)
         Nome do morador: 
         Numero do Apartamento:
         seu desafio é o seguinte, você tem uma conversa de um cliente e um porteiro, porém as mensagens do cliente você não tem acesso, ou seja dessa conversa você só tera a mensagem do porteiro 
         com base nas mensagens do porteiro você deve chegar nas resposta para preencher a lista acima, mas uma regra, você só pode responder a lista preenchida e nada mais
         pois sua resposta vai ser armazenada em uma variavel e sera usada como jason então preciso que responda somente a lista preenchida e nada mais 
         exemplo: 
         Mensagem numero 1 Claro, senhor. Pode me informar seu nome, por favor? E confirmando, o apartamento do Victor é o 23B, certo?
         Mensagem numero 2 Entendi, então seu nome é Douglas e quer visitar o Victor do 23A, correto? Por favor, aguarde um momento enquanto ligo para o senhor Victor para confirmar sua entrada.
         Mensagem numero 3 Muito obrigado por aguardar, senhor Douglas. Estou ligando para o senhor Victor agora mesmo para confirmar sua entrada. Por favor, aguarde mais um instante.
         sua resposta:
         Tipo do cliente: visitante
         Nome do cliente: Douglas
         Nome do morador: Victor
         Numero do Apartamento: 23A
         exemplo_2:
         Mensagem numero 1 Entrega está no nome de quem?
         Mensagem numero 2 Entendi, então você quer realizar uma entrega para ANA do 44 B, agurde um minuto enquanto ligo para senhora ANA para retirar sua entrega
         sua resposta:
         Tipo do cliente: entregador
         Nome do cliente: entregador
         Nome do morador: ANA
         Numero do Apartamento: 44 B
         desafio:

"""}
    ]


uri = "mongodb+srv://Gotham:s87CTYiYIBqZUqQx@cluster0.bcfst.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Conectar ao Atlas
client_mongo = MongoClient(uri, server_api=ServerApi('1'))

# Testar a conexão
try:
    client_mongo.admin.command('ping')
    print("Conexão com MongoDB Atlas bem-sucedida!")
except Exception as e:
    print(f"Erro ao conectar: {e}")

# Banco de dados
db = client_mongo["dados_portaria"]
colecao = db["clientes"]


def generate_response(client: Groq, chat_history: list) -> str:
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=chat_history
    )
    return response.choices[0].message.content

def selecionar_audio_boas_vindas():
    # Define o fuso horário para Brasília
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    hora_atual = datetime.now(fuso_brasilia).time()

    # Verifica o horário e seleciona a lista correspondente
    if hora_atual >= datetime.strptime("06:00", "%H:%M").time() and hora_atual <= datetime.strptime("11:59", "%H:%M").time():
        lista = manha
    elif hora_atual >= datetime.strptime("12:00", "%H:%M").time() and hora_atual <= datetime.strptime("17:59", "%H:%M").time():
        lista = tarde
    else:
        lista = noite

    # Escolhe um link aleatório da lista selecionada
    audio_boas_vindas = random.choice(lista)
    return audio_boas_vindas

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') # requires OpenAI Realtime API Access
PORT = int(os.getenv('PORT', 5050))

SYSTEM_MESSAGE = (
    "Você é um Porteiro"
    "Seu nome é fred"
    "Seu objetivo é identificar o motivo da visita do cliente ao condominio se é cliente visitante ou se é cliente entregador, mas nunca deve perguntar de forma direta."
    "Seu segundo objetivo é saber qual é o apartamento do morador que o cliente deseja visitar (lemrbesse nunca passe o numero do apartamento, pergunte para o cliente falar)"
    "caso seja visitante é só perguntar qual é o apartamento e qual o nome do morador, depois peça para agurdar enquanto você liga para o morador para confirmar a entrada do visitante"
    "caso seja entregador é só perguntar qual é o apartamento e qual é o nome do morador que você já está ligando para o morador descer"
    "não fuja do seu papel de porteiro"
    "não converse sobre assuntos que não são normais para um porteiro"
    "confirme os dados do cliente e aguarde a resposta do cliente sempre, você só pode ligar para o morador quando o cliente confirmar todos os dados, só quando houver uma confirmação como sim, correto, afirmativo, positivo"
    "Se você não entender o nome do cliente ou caso o cliente diga que o nome está incorreto, peça gentilmente para o cliente repetir o nome. Caso o cliente insista que o nome está errado, não continue o atendimento e informe que precisa do nome correto para prosseguir. "
    "Exemplo: cliente: Olá Boa tarde Você: Olá, como posso te ajudar hoje? cliente: Gostaria de visitar o ap. da fernanda você: pode me informar seu nome, e qual o apartamento da senhora fernanda? Cliente (visitante): Claro meu nome é Rafael e a fernanda é do 44 B Você: confirmando, seu nome é Rafael e quer visitar a fernanda do 44 B certo? Cliente (visitante): sim Você: aguarde um momento enquanto confirmo sua entrada com a senhora fernanda"
    "Exemplo: cliente: Ifood Você: para quem é a entraga? Cliente(entregador): entrega para claudia Você: qual é o ap da senhora claudia por favor? Cliente(entregador): 22A Você: confirmando, você deseja fazer uma entrega para senhora claudia do 22 A certo? Cliente (entregador): sim Você: certo estou ligando para a senhora claudia para retirar seu pedido, aguarde um instante por favor"
    "Exemplo: Cliente: Entrega Você: para quem é a entraga? Cliente(entregador): entrega para Ap 44B Você: pode me informar em nome de quem está? Cliente (entregador): Fernanda Você: confirmando, você deseja fazer uma entrega para senhora fernanda do 44 B certo? Cliente (entregador): sim  Você: ok estou ligando para senhora fernanda para retirar seu pedido, aguarde um momento por favor"
    "Exemplo: Cliente: Oi boa tarde, queria ir no apartamento do victor Você: Certo senhor, qual é o seu nome, e consegue me informar qual é o apartamento do senhor victor? Cliente (Visitante): o apartamento do victor é o 34 B e meu nome é Douglas Você: confirmando, seu nome é Douglas e quer visitar o Victor do 34 B certo? Cliente (visitante): sim Você: certo senhor Douglas, estou ligando para o senhor victor para confirmar sua entrada aguarde um momento por favor"
    "Exenplo: Cliente: oi boa noite, gostaria de visitar o apartamento da l(nome não identificado) Você: Certo senhor, pode me informar qual é o apartamento da senhora laura? Cliente (Visitante):é Lo(nome não identificado) Você: Desculpe senhor, parece que houve uma confusão no nome do morador, você está querendo ir no apartamento de quem? pode soletrar por favor? Cliente (Visitante): Loren L O R E N Você: certo senhor deseja visitar o apartamento do loren, pode me informar qual é o seu nome e qual é o numero do apartamento da loren? Cliente (Visitante): Meu nome é rodolfo e o apartamento da loren é um 45 C Você: ok, confirmando então o senhor é o rodolfo e deseja visitar a Loren do 45 C certo? Cliente (Visitante): sim Você: ok estou ligando para a senhora loren para confirmar sua entrada, aguarde um momento por favor "
    "Exemplo: Cliente: Oi, gostaria de visitar o apartamento da Fernanda. Você: Pode me informar seu nome e o apartamento da senhora Fernanda? Cliente: Meu nome é Rafael e o apartamento é o 44B. Você:Confirmando, seu nome é Rafael e deseja visitar a Fernanda do 44B, certo? Cliente(visitante): Não, meu nome não é Rafael, é Gabriel. Você: Perdão, senhor Gabriel. Poderia confirmar novamente, seu nome é Gabriel e deseja visitar a fernada do 44B certo? Cliente (visitante): sim Você: Maravilha, aguarde um minuto enquanto confirmo sua entrada com a senhora fernanda "

)
# "You have a penchant for dad jokes, owl jokes, and rickrolling – subtly. "
# Always stay positive, but work in a joke when appropriate.
VOICE = 'echo'
LOG_EVENT_TYPES = [
    'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created'
]

app = FastAPI()

# Modelo de dados para a requisição
class StatusUpdate(BaseModel):
    id: str
    status: str
    nome: str

# Adiciona a rota para servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")



# Função para verificar similaridade entre strings
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')

@app.get("/", response_class=HTMLResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    audio_Boas_vindas = selecionar_audio_boas_vindas()
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    # response.say("Please wait while we connect your call to the A. I. voice assistant, powered by Twilio and the Open-A.I. Realtime API")
    response.play(f"{audio_Boas_vindas}")
    # response.say("O.K. you can start talking!")
    host = request.url.hostname
    print(host)
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await send_session_update(openai_ws)
        stream_sid = None

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.open:
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid
            transcricao_da_IA = ""
            texto_da_IA = ""
            numero_da_resposta = 0
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)
                    if response['type'] == 'session.updated':
                        print("Session updated successfully:", response)
                    if response['type'] == 'input_audio_buffer.speech_started':
                        await websocket.send_json({ "event": "clear",
                                                    "streamSid": stream_sid })
                    if response['type'] == 'response.audio.delta' and response.get('delta'):
                        # Audio from OpenAI
                        try:
                            audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": audio_payload
                                }
                            }
                            await websocket.send_json(audio_delta)
                        except Exception as e:
                            print(f"Error processing audio data: {e}")
                    # Capturando o transcript
                    if response['type'] == 'response.done':
                        # Procurando pelo item que contém o transcript
                        for output in response.get('response', {}).get('output', []):
                            if output['type'] == 'message' and 'content' in output:
                                for content in output['content']:
                                    if content['type'] == 'audio' and 'transcript' in content:
                                        transcricao_da_IA = content['transcript']
                                        numero_da_resposta  += 1
                                        texto_da_IA += (f"Resposta numero {numero_da_resposta} {transcricao_da_IA}\n")
                                        print (f"{texto_da_IA}")
                                        if "ligo" in transcricao_da_IA.lower() or "aguarde" in transcricao_da_IA.lower():
                                            chat_history.append({'role': 'user', 'content': texto_da_IA})
                                            variavel_teste = generate_response(client_groq ,chat_history)
                                            # Separando o texto em linhas
                                            linhas = variavel_teste.splitlines()

                                            # Criando o dicionário a partir das linhas
                                            dicionario = {}
                                            for linha in linhas:
                                                chave, valor = linha.split(":", 1)
                                                dicionario[chave.strip()] = valor.strip()
                                            # Adicionando a data e hora atual no formato DD/MM/AA HH:MM
                                            data_hora_atual = datetime.now().strftime("%d/%m/%y %H:%M")
                                            dicionario["Data"] = data_hora_atual
                                            condominio = "Residencial Brooklin"
                                            dicionario["Condominio"] = condominio
                                            print(f"o dicionario ficou: {dicionario}")
                                            # Conectar ao MongoDB
                                            uri = "mongodb+srv://Gotham:s87CTYiYIBqZUqQx@cluster0.bcfst.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
                                            # Conectar ao Atlas
                                            client_mongo = MongoClient(uri, server_api=ServerApi('1'))

                                            # Testar a conexão
                                            try:
                                                client_mongo.admin.command('ping')
                                                print("Conexão com MongoDB Atlas bem-sucedida!")
                                            except Exception as e:
                                                print(f"Erro ao conectar: {e}")

                                            # Selecionar/criar um banco de dados
                                            db = client_mongo["dados_portaria"]

                                            # Selecionar/criar uma coleção
                                            colecao = db["clientes"]

                                            # Inserir os dados no MongoDB
                                            resultado = colecao.insert_one(dicionario)

                                            # Mostrar o ID do documento inserido
                                            print(f"Dados inseridos com ID: {resultado.inserted_id}")

                                            # Carregar a planilha Excel
                                            # Caminho do arquivo Excel
                                            caminho_arquivo = r"C:\Users\DELL\Desktop\IA_Port\report (2).xlsx"
                                            df = pd.read_excel(caminho_arquivo)

                                           # Pegar os valores do dicionário
                                            ap_busca = dicionario["Numero do Apartamento"].strip().lower()
                                            nome_busca = dicionario["Nome do morador"].strip().lower()
                                            nome_visitante = dicionario["Nome do cliente"].strip()

                                            print(f"Buscando: Apartamento -> {ap_busca}, Nome -> {nome_busca}, Visitante -> {nome_visitante}")

                                            # Filtrar as linhas que contêm o AP desejado (ignorar maiúsculas/minúsculas)
                                            resultado_ap = df[df['Grupos de unidade e unidades'].str.contains(ap_busca, case=False, na=False)]
                                            # Filtrar pela similaridade do nome com pelo menos 80% de correspondência
                                            resultado_final = resultado_ap[resultado_ap['Nome'].apply(lambda x: similar(nome_busca.lower(), str(x).lower()) >= 0.80)]
                                            # Informações da sua conta Twilio (você encontra no painel de controle do Twilio)
                                            account_sid = 'AC25aa3ccc494830251d246d12790547f9'
                                            auth_token = '46a8b0f49a18814bd20cf4623948272a'
                                            client = Client(account_sid, auth_token)

                                            # Se encontrar a linha, armazena o valor da coluna 'Telefones' na variável 'to'
                                            if not resultado_final.empty:
                                                numero = str(resultado_final.iloc[0]['Telefones']).replace('.0', '').strip()
                                                # Enviando a mensagem
                                                message = client.messages.create(
                                                    body=f'Olá {nome_busca}! O visitante {nome_visitante} está na porta aguardando sua confirmação para subir.',  # Conteúdo da mensagem
                                                    from_='+14138893037',  # Seu número Twilio
                                                    to=f"+{numero}"  # Número do destinatário
                                                )
                                                print(f"Mensagem enviada para o número: +{numero}")
                                            else:
                                                print("Nenhuma linha encontrada com os critérios fornecidos.")


                                            time.sleep(9)
                                                                                

            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def send_session_update(openai_ws):
    """Send session update to OpenAI WebSocket."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

# Rota para exibir o histórico
@app.get("/historico", response_class=HTMLResponse)
async def historico():
    clientes = list(colecao.find())
    with open("templates/index.html", "r", encoding="utf-8") as file:
        template = Template(file.read())
    rendered_html = template.render(clientes=clientes)
    return HTMLResponse(content=rendered_html)

@app.post("/atualizar-status")
async def atualizar_status(dados: StatusUpdate):
    cliente_id = dados.id
    status = dados.status
    nome = dados.nome
    # Atualizando o documento
    result = colecao.update_one(
        {"_id": ObjectId(cliente_id)},
        {"$set": {"status": status}}
    )

    # Verificando se a atualização foi bem-sucedida
    if result.modified_count > 0:
        print("Status atualizado com sucesso.")
    else:
        print("Nenhum documento foi atualizado.")
    print (f"Cliente: {nome} ID: {cliente_id} {status}")
# Rota raiz para confirmar que o servidor está ativo
@app.get("/")
async def root():
    return {"mensagem": "API está ativa!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
