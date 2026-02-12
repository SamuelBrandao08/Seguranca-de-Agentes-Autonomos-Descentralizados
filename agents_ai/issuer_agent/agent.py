# agent.py
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from contextlib import asynccontextmanager
import requests
import logging
import aiohttp

from controller import acapy_controller
from agents_ai.issuer_agent.llm import call_ollama

app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_state["session"] = aiohttp.ClientSession()
    yield
    await app_state["session"].close()

app = FastAPI(lifespan=lifespan)

class Message(BaseModel):
    sender: str
    content: str

class ChatInput(BaseModel):
    message: str
    params: str

STATE = {
    "my_did": None,
    "client_did": None,
    "kyc_schema_id": None,
    "kyc_cred_def_id": None,
    "plano_schema_id": None,
    "plano_cred_def_id": None,
    "invitation_msg_id": None,
    "conn_id_operadora": None,
    "conn_id_client": None
    # conn_id_verificador removido
}

@app.post("/chat")
async def chat_endpoint(inp: ChatInput):
    # 1. IA interpreta
    cmd = call_ollama(inp.message)
    func = cmd.get("function_name")
    params = cmd.get("parameters", {})

    if func == "error":
        raise HTTPException(500, detail=params.get("message"))

    # 2. Controller executa
    session = app_state["session"]
    result = ""
    state = {}

    try:
        if func == "setup_telco":
            result = await acapy_controller.setup_telco(session)
        elif func == "conectar_cliente":
            result, state = await acapy_controller.conectar_cliente(session)
            STATE.update(state)
            print("DADOS DO AGENTE: ", STATE['conn_id_client'])
        elif func == "ativar_plano":
            result = await acapy_controller.ativar_plano(session, **params)
        elif func == "verificar_acesso":
            result = await acapy_controller.verificar_acesso(session)
        elif func == "enviar_mensagem":
            conn_id = acapy_controller.STATE.get("conn_id_operadora")
            url = acapy_controller.OPERADORA_ADMIN
            result = await acapy_controller.enviar_mensagem(session, url, conn_id, inp.params) # connection_id?
        else:
            result = f"Função desconhecida: {func}"
    except Exception as e:
        result = f"Erro de execução: {str(e)}"

    return {"response": result}

## WEBHOOK
@app.post("/topic/out-of-band")
async def on_invitation(request: Request):
    data = await request.json()
    print(f"Servidor disponivel... \n {data}")

@app.post("/topic/connections")
async def on_connections(request: Request):
    data = await request.json()
    if data.get('state') == "active":
        STATE['conn_id_operadora'] = data['connection_id']
        STATE['invitation_msg_id'] = data['invitation_msg_id']
        STATE['my_did'] = data['my_did']
        STATE['client_did'] = data['their_did']

        print("\n EVENTO DE CONEXÃO RECEBIDO:")
        print(data)
        print("---------------------------------\n")
        return {"status": "ok"}
    else:        
        return {"status": "error"}


@app.post("/topic/basicmessages")
async def on_message(request: Request):
    data = await request.json()
    content = data["content"]

    # response = call_ollama(
    #     f"Você recebeu uma mensagem segura DIDComm: {content}"
    # )

    print(f"Você recebeu uma mensagem segura DIDComm: {data}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)