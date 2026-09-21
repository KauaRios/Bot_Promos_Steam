import requests
import os
import threading
import time
import traceback
from dotenv import load_dotenv
from logs_erros.logs import salvar_logs


load_dotenv()
url = os.getenv("DISCORD")

_lock = threading.Lock()
_ultimo_envio = 0.0
_INTERVALO_MINIMO = 0.5

def _aguardar_intervalo():
    global _ultimo_envio
    with _lock:
        agora = time.monotonic()
        espera = _INTERVALO_MINIMO - (agora - _ultimo_envio)
        if espera > 0:
            time.sleep(espera)
        _ultimo_envio = time.monotonic()


def enviar_mensagem_discord(mensagem, tentativas=3):
    url_web = url
    payload = {"content": mensagem}

    for tentativa in range(1, tentativas + 1):
        _aguardar_intervalo()

        try:
            resposta = requests.post(url_web, json=payload)

            if resposta.status_code == 204:
                print("[Sucesso] mensagem enviada com sucesso!")
                return

            elif resposta.status_code == 429:
                # Discord manda o tempo de espera exato no corpo da resposta
                try:
                    espera = resposta.json().get("retry_after", 1.0)
                except Exception:
                    espera = 1.0
                print(f"[Discord] Rate limit (tentativa {tentativa}/{tentativas}). Esperando {espera}s...")
                time.sleep(espera)
                continue

            else:
                print(f"[Falha] O envio da mensagem falhou (status {resposta.status_code}): {resposta.text}")
                return

        except Exception as e:
            detalhes = (
                f"[ERRO DISCORD] {type(e).__name__}: {e}\n"
                f"  Tipo de 'content': {type(payload['content']).__name__}\n"
                f"{traceback.format_exc()}"
            )
            print(detalhes)
            salvar_logs(detalhes)
            return

    salvar_logs("[Discord] Esgotadas as tentativas de envio (rate limit persistente).")