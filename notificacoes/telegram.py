import requests
import os
import threading
import time
import traceback
from dotenv import load_dotenv
from logs_erros.logs import salvar_logs

load_dotenv()
senha = os.getenv("TOKEN")
chat = os.getenv("ID")

_lock = threading.Lock()
_ultimo_envio = 0.0
_INTERVALO_MINIMO = 1.1


def _aguardar_intervalo():
    global _ultimo_envio
    with _lock:
        agora = time.monotonic()
        espera = _INTERVALO_MINIMO - (agora - _ultimo_envio)
        if espera > 0:
            time.sleep(espera)
        _ultimo_envio = time.monotonic()


def enviar(mensagem, tentativas=3):
    url = f"https://api.telegram.org/bot{senha}/sendMessage"
    dados = {
        "chat_id": chat,
        "text": mensagem,
        "parse_mode": "Markdown",
    }

    for tentativa in range(1, tentativas + 1):
        _aguardar_intervalo()

        try:
            resposta = requests.post(url, json=dados)

            if resposta.status_code == 200:
                return

            elif resposta.status_code == 429:
                try:
                    espera = (
                        resposta.json().get("parameters", {}).get("retry_after", 1.0)
                    )
                except Exception:
                    espera = 1.0
                print(
                    f"[Telegram] Rate limit (tentativa {tentativa}/{tentativas}). Esperando {espera}s..."
                )
                time.sleep(espera)
                continue

            else:

                erro = (
                    f"[Telegram] Falha (status {resposta.status_code}): {resposta.text}"
                )
                print(erro)
                salvar_logs(erro)
                return

        except Exception as e:
            detalhes = (
                f"[ERRO TELEGRAM] {type(e).__name__}: {e}\n"
                f"  Tipos em 'dados': "
                f"chat_id={type(dados['chat_id']).__name__}, "
                f"text={type(dados['text']).__name__}, "
                f"parse_mode={type(dados['parse_mode']).__name__}\n"
                f"{traceback.format_exc()}"
            )
            print(detalhes)
            salvar_logs(detalhes)
            return

    salvar_logs("[Telegram] Esgotadas as tentativas de envio (rate limit persistente).")


def receber():
    url = f"https://api.telegram.org/bot{senha}/getUpdates"
    try:
        resposta = requests.get(url)
        print(resposta.json())
    except Exception as e:
        print(e)
