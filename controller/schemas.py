from core.state import STATE
from core.plans import PLANOS

# customer_id → DID interno da operadora
# cpf → Identificação brasileira
# phone_number → Número da linha (E.164 +55...)
# plan_name (ex: "Vivo Controle 15GB")
# plan_type (ex: "Movel", "Fibra")
# activated_at → Data de ativação
# status → Ativo / Suspenso / Cancelado

# Schema e definição de credencial para credencial Identidade
schema_kyc = {
    "schema": {
        "issuerId": STATE['operadora_did'], 
        "name": "identidade-assinante", 
        "version": "2.0", 
        "attrNames": [
            "customer_id",
            "name",
            "cpf"
        ]
    }
}

cred_def_kyc = {
    "credential_definition": {
        "issuerId": STATE['operadora_did'], 
        "schemaId": STATE["kyc_schema_id"], 
        "tag": "kyc"
    }
}

# Schema e definição de credencial para credencial Plano

schema_plan = {
    "schema": {
        "issuerId": STATE['operadora_did'], 
        "name": "plano", 
        "version": "2.0", 
        "attrNames": [
            "type",
            "plan",
            "validity",
            "franchise"
        ]
    }
}

cred_def_plan = {
    "credential_definition": {
        "issuerId": STATE['operadora_did'], 
        "schemaId": STATE["plano_schema_id"], 
        "tag": "plano"
    }
}

# issue_cred_body = {
#     "connection_id": STATE['conn_id_operadora'],
#     "filter": {"anoncreds": {"cred_def_id": STATE['plano_cred_def_id']}},
#     "credential_preview": {
#         "@type": "issue-credential/2.0/credential-preview",
#         "attributes": None
#     }
# }

# proof_body = {
#         "connection_id": "CONNECTION_ID",
#         "presentation_request": {
#             "anoncreds": {
#                 "name": f"",
#                 "version": "1.0",
#                 "requested_attributes": {
#                     "attr1": {"name": "", "restrictions": [{"cred_def_id": ""}]}
#                 },
#                 "requested_predicates": {}
#             }
#         }
#     }

# revoke_body = {
#   "rev_reg_id": "REV_REGISTRY_ID",
#   "cred_rev_id": "CRED_REV_ID",
#   "publish": "true"
# }