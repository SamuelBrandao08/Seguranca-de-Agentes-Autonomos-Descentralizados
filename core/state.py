
OPERADORA_ADMIN = "http://localhost:8001"
CLIENTE_ADMIN = "http://localhost:8011"


# --- Estado em Memória ---
STATE = {
    "operadora_did": None,
    "cliente_did": None,
    "kyc_schema_id": None,
    "kyc_cred_def_id": None,
    "plano_schema_id": None,
    "plano_cred_def_id": None,
    "invitation_msg_id": None,
    "conn_id_operadora": None,
    "conn_id_client": None
}

ACTIVE_LINES = {}