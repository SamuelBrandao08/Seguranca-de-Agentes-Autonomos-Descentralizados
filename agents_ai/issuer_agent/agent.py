# agent.py
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from contextlib import asynccontextmanager
import requests
import logging
import aiohttp
import json

from core.state import (
    STATE,
    OPERADORA_ADMIN,
    CLIENTE_ADMIN
)
from controller import acapy_controller
from controller import acapy_controller_v2 as ac2
from agents_ai.issuer_agent.llm import call_ollama

app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_state["session"] = aiohttp.ClientSession()
    session = app_state["session"]

    response = ""
    try:
        response = await ac2.init_telecom(session)
        print("Init telecom:", json.dumps(response))

    except Exception as e:
        print("Erro de execução:", e)

    yield
    await session.close()
    # await app_state["session"].close()

app = FastAPI(lifespan=lifespan)

class Message(BaseModel):
    sender: str
    content: str

class ChatInput(BaseModel):
    message: str
    params: str



# STATE = {
#     "my_did": None,
#     "client_did": None,
#     "kyc_schema_id": None,
#     "kyc_cred_def_id": None,
#     "plano_schema_id": None,
#     "plano_cred_def_id": None,
#     "invitation_msg_id": None,
#     "conn_id_operadora": None,
#     "conn_id_client": None
# }

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

    try:
        if func == "init_telecom":
            result = await ac2.init_telecom(session)
        elif func == "generate_schemas":
            result = await ac2.generate_schemas(session)
        elif func == "activate_plan":
            result = await ac2.activate_line(session, params)
        elif func == "change_plan":
            result = await ac2.change_plan(session)
        elif func == "suspend_service":
            result = await ac2.suspend_service(session)
        elif func == "cancel_contract":
            result = await ac2.cancel_contract(session)
        elif func == "generate_invoice":
            result = await ac2.generate_invoice(session)
        elif func == "send_message":
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

    session = app_state["session"]
    if data.get('state') == "active":
        did = data['their_did']
        await ac2.approve_connection(session, did)
        print('EXECUTOU APPROVE_CONECTION')
        STATE['conn_id_operadora'] = data['connection_id']
        STATE['invitation_msg_id'] = data['invitation_msg_id']
        STATE['operadora_did'] = data['my_did']
        STATE['client_did'] = data['their_did']

        print("\n EVENTO DE CONEXÃO RECEBIDO:")
        print(data)
        print("---------------------------------\n")
        return {"status": "ok"}
    else:        
        return {"status": "error"}


@app.post("/topic/present_proof_v2_0")
async def receive_proof(request: Request):
    data = await request.json()
    print(data)


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