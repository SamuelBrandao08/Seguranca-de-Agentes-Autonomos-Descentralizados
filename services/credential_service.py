import aiohttp
import logging
import asyncio

from services.assist_http import admin_request
from controller import schemas as sc
from core.state import (
    STATE,
    OPERADORA_ADMIN,
    CLIENTE_ADMIN
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Criar credenciais e definiões de credenciais
async def create_cred_def(session: aiohttp.ClientSession, schema, cred_def):
    # 1. Criar o Schema
    schema_id = await admin_request(
        session, 
        "GET", 
        f"{OPERADORA_ADMIN}/anoncreds/schemas", 
        {}, 
        {"schema_name": schema['schema']['name']}
    )
    
    # Verifica se o schema existe
    if not schema_id:
        resp_schema = await admin_request(
            session, 
            "POST", 
            f"{OPERADORA_ADMIN}/anoncreds/schema", 
            schema
        )
    else:
        resp_schema = {"schema_state": {"schema_id": schema_id}}
    
    if not resp_schema: return "Erro ao criar Schema de Identidade."
    schema_id = resp_schema["schema_state"]["schema_id"]
    

    # 2. Criar definição de credencial
    cred_def_id = await admin_request(
        session, 
        "GET", 
        f"{OPERADORA_ADMIN}/anoncreds/credential-definitions", 
        {}, 
        {"schema_name": schema['schema']['name']}
    )
    
    # Verificar se definicao de credencial existe
    if not cred_def_id:
        resp_cred_def = await admin_request(
            session,     
            "POST", 
            f"{OPERADORA_ADMIN}/anoncreds/credential-definition", 
            cred_def
        )
        cred_def_id = resp_cred_def["credential_definition_state"]["credential_definition_id"]
   
    if not cred_def_id: return "Erro ao criar CredDef de Identidade." 
    logging.info(f"Esquema de credencial definido. ID: {cred_def_id}")

    return schema_id, cred_def_id



async def get_cred_def(session: aiohttp.ClientSession, schema, version):
    # 1. Buscar o Schema
    response = await admin_request(
        session, 
        "GET", 
        f"{OPERADORA_ADMIN}/anoncreds/schemas", 
        {}, 
        {
            "schema_name": schema,
            "schema_version": version
        }
    )
    if not response['schema_ids']: return
    schema_id = response['schema_ids'][0]
    
    # 2. Buscar definição de credencial
    response = await admin_request(
        session, 
        "GET", 
        f"{OPERADORA_ADMIN}/anoncreds/credential-definitions", 
        {}, 
        {
            "schema_name": schema,
            "schema_version": version
        }
    )
    if not response['credential_definition_ids']: return   
    cred_def_id = response['credential_definition_ids'][0]
    
    return schema_id, cred_def_id



def issue_credential(session, connection_id, cred_def_id, attributes):
    body = {
        "connection_id": connection_id,
        "filter": {"anoncreds": {"cred_def_id": cred_def_id}},
        "credential_preview": {
            "@type": "issue-credential/2.0/credential-preview",
            "attributes": attributes
        }
    }
    admin_request(
        session,
        "POST",
        f"{OPERADORA_ADMIN}/issue-credential-2.0/send",
        body
    )


def proof_request(session: aiohttp.ClientSession, conn_id: str, cred_def_id: str, attr: str):
    body = {
        "connection_id": conn_id,
        "presentation_request": {
            "anoncreds": {
                "name": f"Proof request",
                "version": "1.0",
                "requested_attributes": {
                    "attr1": {
                        "name": attr, 
                        "restrictions": [
                            {"cred_def_id": {cred_def_id}}
                        ]
                    }
                },
                "requested_predicates": {}
            }
        },
        "auto_verify": True
    }

    admin_request(
        session,
        "POST",
        f"{OPERADORA_ADMIN}/present-proof-2.0/send-request",
        body
    )
    
    

#
async def revoke_credential(session: aiohttp.ClientSession, ):
    logging.info("Cancelando plano do usuario...")

    return

async def get_did(session: aiohttp.ClientSession, url) -> str:
    did_data = await admin_request(session, "GET", f"{url}/wallet/did/public")
    if not did_data: 
        return "Erro crítico: Não foi possível obter o DID público da Operadora. Verifique se o agente está rodando."
    did = did_data["result"]["did"]

    return did


async def send_message(session: aiohttp.ClientSession, agent_url: str, connection_id: str, msg: str):
    logging.info("Enviando mensagem...")
    
    req_body = {"content": msg}
    await admin_request(
        session, 
        "POST", 
        f"{agent_url}/connections/{connection_id}/send-message", 
        req_body
    )
    logging.info("Mensagem enviada.")