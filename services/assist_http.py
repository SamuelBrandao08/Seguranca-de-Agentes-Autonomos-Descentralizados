import aiohttp
import logging
import asyncio
from typing import Dict, Any


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Auxiliar HTTP ---
async def admin_request(session, method, url, json_data=None, params=None):
    try:
        async with session.request(method, url, json=json_data, params=params) as resp:
            if resp.status >= 400:
                text = await resp.text()
                logging.error(f"Erro API {resp.status} em {url}: {text}")
                return None
            return await resp.json()
    except Exception as e:
        logging.error(f"Exceção Request {url}: {e}")
        return None