import aiohttp
import logging
import asyncio
from typing import Dict, Any

from controller import schemas as sc

from services import credential_service as cs 
from services.assist_http import admin_request
from services import assist_db as db

from core.state import (
    STATE,
    ACTIVE_LINES,
    OPERADORA_ADMIN,
    CLIENTE_ADMIN
)
from core.plans import PLANOS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes ---
# OPERADORA_ADMIN = "http://localhost:8001"
# CLIENTE_ADMIN = "http://localhost:8011"
# VERIFICADOR_ADMIN foi removido. A Operadora fará tudo.

# # --- Estado em Memória ---
# STATE = {
#     "operadora_did": None,
#     "kyc_schema_id": None,
#     "kyc_cred_def_id": None,
#     "plano_schema_id": None,
#     "plano_cred_def_id": None,
#     "invitation_msg_id": None,
#     "conn_id_operadora": None,
#     "conn_id_client": None
#     # conn_id_verificador removido
# }

# --- Auxiliar HTTP ---
# async def admin_request(session, method, url, json_data=None, params=None):
#     try:
#         async with session.request(method, url, json=json_data, params=params) as resp:
#             if resp.status >= 400:
#                 text = await resp.text()
#                 logging.error(f"Erro API {resp.status} em {url}: {text}")
#                 return None
#             return await resp.json()
#     except Exception as e:
#         logging.error(f"Exceção Request {url}: {e}")
#         return None


# --- Funcionalidades da Telecom ---
async def init_telecom(session: aiohttp.ClientSession):
    logging.info("Iniciando o sistema da TelecomX...")
    
    # 1. Obter DID
    op_did = await cs.get_did(session, OPERADORA_ADMIN)
    STATE["operadora_did"] = op_did
    
    # 2. Tenta pegar um Convite existente com oob_id
    # if oob_id:
    #     response = await admin_request(
    #         session, 
    #         "GET", 
    #         f"{OPERADORA_ADMIN}/out-of-band/invitations", 
    #         {},
    #         {"oob_id": oob_id}
    #     ) 

    
        # 2. Gera um novo Convite
    body = {"handshake_protocols": ["https://didcomm.org/didexchange/1.0"]}
    response = await admin_request(
        session, 
        "POST", 
        f"{OPERADORA_ADMIN}/out-of-band/create-invitation", 
        body
    )

    # 4. Retorna o convite
    invitation = response['invitation']

    return invitation


async def approve_connection(session: aiohttp.ClientSession, did):
    logging.info("Solicitando prova de credencial...")

    # 1. Checar schemas e definições de credencial
    
    schema = sc.schema_kyc['schema']['name']
    version = sc.schema_kyc['schema']['version']
    
    response = await cs.get_cred_def(session, schema, version)
    if response is None: return "Erro na definicao de schema ou credencial"

    cred_def_id = response['cred_def_id']

    STATE["kyc_cred_def_id"] = cred_def_id
    print('CRED', cred_def_id)
    
    # 2. Apresentar prova de identidade 
    attr = sc.schema_plan['schema']['attrNames'][0]
    cs.proof_request(
        session,
        STATE['conn_id_operadora'],
        cred_def_id,
        attr
    )

    #return "Conectado com a operadora!"

async def generate_schemas(session: aiohttp.ClientSession):
    logging.info("Criando schemas e definições de credenciais ...")
    
    response = await cs.create_cred_def(session, sc.schema_kyc, sc.cred_def_kyc)
    if not response[1]: return response
    
    response = await cs.create_cred_def(session, sc.schema_plan, sc.cred_def_plan)
    if not response[1]: return response

    return "Schemas gerados com sucesso."

# Emmite uma credencial referente a um plano contratado
async def activate_line(session: aiohttp.ClientSession, customer_did, plan_name):
    logging.info("Ativando a linha do cliente...")
    
    ACTIVE_LINES[customer_id] = {
        "plan_name": plan_name,
        "status": "acitve"
    }
    
    s_plan = sc.schema_plan
    cd_plan = sc.cred_def_plan
    _, cred_def_id = await cs.create_cred_def(session, s_plan, cd_plan)

    # 1. Pega os atributos do plano
    attributes = PLANOS[plan]
    
    # 2. Emitir credencial
    await cs.issue_credential(session, connection_id, cred_def_id, attributes)

    return f"Linha ativa, plano {plan_name}"


# Revoga a credencial referente ao plano do usuario
async def suspend_service(session: aiohttp.ClientSession):
    logging.info("Suspendendo serviço do usuario...")
    # 1. Revoga credencial

    return


# Emitir credencial(issue_credential): ativa a conta do clliente(plano default) 
async def change_plan(session: aiohttp.ClientSession, new_plan: str, version=None):
    logging.info("Ativando plano do cliente...")
    
    # 1. Pegar a definição de credencial pelo nome
    cred_def = await admin_request(
        session, 
        "GET", 
        f"{OPERADORA_ADMIN}/anoncreds/credential-definitions", 
        {}, 
        {"schema_name":new_plan}
    )
    if not cred_def: return f"Erro ao buscar a credencial {new_plan}"
    STATE['plano_cred_def_id'] = cred_def['redential_definition_ids'][0]
    
    # 2. Emitir a credencail referente ao novo plano
    sc.issue_cred_body['credential_preview']['attributes'] = PLANOS[new_plan]
    if PLANOS[new_plan]: body = sc.issue_cred_body
    await admin_request(session, "POST", f"{OPERADORA_ADMIN}/issue-credential-2.0/send", body)

    # 3. Revogar a credencial do plano antigo
    admin_request(
        session,
        "POST",
        f"{OPERADORA_ADMIN}/anoncreds/revocation/revoke",
        body
    )
    
    return f"Plano {new_plan} ativado!"


async def cancel_contract(session: aiohttp.ClientSession):
    logging.info("Cancelando contrato do cliente...")

    # Revogar a credencial de iodentidade do cliente

    return f"Contrato cancelado com o cliente"


# Gera uma mensagem de cobrança e envia para o usuario
async def generate_invoice(session: aiohttp.ClientSession):
    logging.info("Gerando mensagem de cobrança...")
     
    # 1. Chama send_message

    return







# --- Funcionalidades do Cliente Telecom ---

# Estabelecer conexão com a operadora
async def accept_connection(session: aiohttp.ClientSession, invitation: dict[str, Any]):
    # 1. Cliente aceita o convite para conexão
    logging.info("Conectando cliente à Operadora...")
    
    data_connection = await admin_request(
        session, 
        "POST", 
        f"{CLIENTE_ADMIN}/out-of-band/receive-invitation", 
        invitation
    )

    if not data_connection: return "Erro ao receber convite no Cliente."
    
    conn_id = data_connection['connection_id']
    STATE['conn_id_client'] = conn_id

    return f"Conectado com a operadora TelecomX."




















async def setup_telecom(session: aiohttp.ClientSession):
    """Configura Schemas e CredDefs da TelecomX no Blockchain."""
    logging.info("Iniciando setup da TelecomX...")

    # 1. Obter DID
    did_data = await admin_request(session, "GET", f"{OPERADORA_ADMIN}/wallet/did/public")
    if not did_data: 
        return "Erro crítico: Não foi possível obter o DID público da Operadora. Verifique se o agente está rodando."
    
    op_did = did_data["result"]["did"]
    STATE["operadora_did"] = op_did


    # 2. Schema e CredDef: Identidade (KYC)
    s_kyc = {"schema": {"issuerId": op_did, "name": "identidade-assinante", "version": "1.0", "attrNames": ["nome_completo", "cpf", "status_conta"]}}
    s_kyc_id = await admin_request(session, "GET", f"{OPERADORA_ADMIN}/anoncreds/schemas", {}, s_kyc['schema']['name'])
    
    # Verificar se schema existe
    if not s_kyc_id:
        resp_s_kyc = await admin_request(session, "POST", f"{OPERADORA_ADMIN}/anoncreds/schema", s_kyc)
    else:
        resp_s_kyc = {"schema_state": {"schema_id": s_kyc_id}}

    if not resp_s_kyc: return "Erro ao criar Schema de Identidade."
    STATE["kyc_schema_id"] = resp_s_kyc["schema_state"]["schema_id"]

    cd_kyc = {"credential_definition": {"issuerId": op_did, "schemaId": STATE["kyc_schema_id"], "tag": "kyc"}}
    cd_kyc_id = await admin_request(session, "GET", f"{OPERADORA_ADMIN}/anoncreds/credential-definitions", {}, STATE["kyc_cred_def_id"])
    
    # Verificar se definicao de credencial existe
    if not cd_kyc_id:
        resp_cd_kyc = await admin_request(session, "POST", f"{OPERADORA_ADMIN}/anoncreds/credential-definition", cd_kyc)
    else:
        resp_cd_kyc = {"credential_definition_state": {"credential_definition_id": cd_kyc_id}}

    if not resp_cd_kyc: return "Erro ao criar CredDef de Identidade."
    STATE["kyc_cred_def_id"] = resp_cd_kyc["credential_definition_state"]["credential_definition_id"]

    # 3. Schema e CredDef: Plano (Promoção)
    s_plano = {"schema": {"issuerId": op_did, "name": "plano-dados", "version": "1.0", "attrNames": ["nome_plano", "franquia_gb", "validade"]}}
    s_plano_id = await admin_request(session, "GET", f"{OPERADORA_ADMIN}/anoncreds/schemas", {}, s_plano['schema']['name'])
    
    # Verificar se schema existe
    if not s_plano_id:
        resp_s_plano = await admin_request(session, "POST", f"{OPERADORA_ADMIN}/anoncreds/schema", s_plano)
    else:
        resp_s_plano = {"schema_state": {"schema_id": s_plano_id}}
    
    if not resp_s_plano: return "Erro ao criar Schema de Plano."
    STATE["plano_schema_id"] = resp_s_plano["schema_state"]["schema_id"]

    cd_plano = {"credential_definition": {"issuerId": op_did, "schemaId": STATE["plano_schema_id"], "tag": "promo"}}
    cd_plano_id = await admin_request(session, "GET", f"{OPERADORA_ADMIN}/anoncreds/credential-definitions", {}, STATE["plano_cred_def_id"])
    
    # Verificar se definicao de credencial existe
    if not cd_plano_id:
        resp_cd_plano = await admin_request(session, "POST", f"{OPERADORA_ADMIN}/anoncreds/credential-definition", cd_plano)
    else:
        resp_cd_plano = {"credential_definition_state": {"credential_definition_id": cd_plano_id}}

    if not resp_cd_plano: return "Erro ao criar CredDef de Plano."
    STATE["plano_cred_def_id"] = resp_cd_plano["credential_definition_state"]["credential_definition_id"]

    return f"Infraestrutura TelecomX configurada com sucesso. DID: {op_did}"