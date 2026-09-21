from logs_erros.logs import salvar_logs
import requests
import threading
import time


# a cada requisição (economiza tempo em varreduras com muitos jogos)
_sessao = requests.Session()

_lock_estado = threading.Lock()
_ultima_requisicao = 0.0
_falhas_consecutivas = 0
_bloqueado_ate = 0.0  

_INTERVALO_MINIMO = 1.5         
_MAX_FALHAS_CONSECUTIVAS = 5      
_PAUSA_CIRCUITO = 120             


def _aguardar_intervalo():
    """Espera o intervalo mínimo entre requisições e respeita uma eventual
    pausa de disjuntor, se o circuito tiver 'aberto'."""
    global _ultima_requisicao
    with _lock_estado:
        agora = time.monotonic()

        if agora < _bloqueado_ate:
            time.sleep(_bloqueado_ate - agora)

        agora = time.monotonic()
        espera = _INTERVALO_MINIMO - (agora - _ultima_requisicao)
        if espera > 0:
            time.sleep(espera)
        _ultima_requisicao = time.monotonic()


def _registrar_resultado(sucesso):
    """Alimenta o disjuntor. Muitas falhas seguidas = provável bloqueio de IP,
    então paramos tudo por um tempo bem maior em vez de insistir jogo a jogo."""
    global _falhas_consecutivas, _bloqueado_ate
    with _lock_estado:
        if sucesso:
            _falhas_consecutivas = 0
            return

        _falhas_consecutivas += 1
        if _falhas_consecutivas >= _MAX_FALHAS_CONSECUTIVAS:
            salvar_logs(
                f"[CIRCUITO] {_falhas_consecutivas} falhas seguidas — provável bloqueio de IP. "
                f"Pausando TODAS as requisições por {_PAUSA_CIRCUITO}s."
            )
            print(f"⏸️  Muitos 429 seguidos — pausando {_PAUSA_CIRCUITO}s (provável bloqueio de IP)...")
            _bloqueado_ate = time.monotonic() + _PAUSA_CIRCUITO
            _falhas_consecutivas = 0
# ---------------------------------------------------------------------------


def buscar_promo_st(id_jogo, sessao=_sessao, tentativas=3):
    url = f"https://store.steampowered.com/api/appdetails?appids={id_jogo}&cc=br&l=portuguese"
    nome = None  # evita UnboundLocalError se o KeyError acontecer antes de 'nome' existir

    for tentativa in range(1, tentativas + 1):
        _aguardar_intervalo()

        try:
            resposta = sessao.get(url, timeout=10)

            if resposta.status_code == 200:
                _registrar_resultado(sucesso=True)

                dados_brutos = resposta.json()
                id_str = str(id_jogo)
                dados_jogo = dados_brutos[id_str]["data"]
                nome = dados_jogo["name"]

                if dados_jogo["is_free"]:
                    preco = "Gratuito!"
                elif "price_overview" in dados_jogo:
                    preco = dados_jogo["price_overview"]["final_formatted"]
                else:
                    preco = "Preço indisponível (ou item inválido)"

                return {
                    "id": id_jogo,
                    "Titulo": nome,
                    "Valor": preco,
                    "link": f"https://store.steampowered.com/app/{id_jogo}",
                }

            elif resposta.status_code == 429:
                _registrar_resultado(sucesso=False)

              
                retry_after = resposta.headers.get("Retry-After")
                if retry_after:
                    try:
                        espera = float(retry_after)
                    except ValueError:
                        espera = 2 ** tentativa
                else:
                    espera = 2 ** tentativa  # 2s, 4s, 8s...

                salvar_logs(
                    f"[429] Rate limit no jogo {id_jogo} (tentativa {tentativa}/{tentativas}). "
                    f"Esperando {espera}s antes de tentar de novo."
                )
                time.sleep(espera)
                continue  

            else:
                _registrar_resultado(sucesso=False)
                salvar_logs(f"[{resposta.status_code}] Erro ao buscar preço do jogo {id_jogo}")
                return None

        except KeyError:
            salvar_logs(f"Erro ao achar preço do jogo {nome or id_jogo}")
            return None

        except requests.exceptions.Timeout:
            _registrar_resultado(sucesso=False)
            salvar_logs(f"Timeout ao buscar preço do jogo {id_jogo}")
            return None

        except Exception as e:
            salvar_logs(f"Ocorreu um erro ao buscar preço do jogo {id_jogo}: {e}")
            return None

   
    salvar_logs(f"Esgotadas as tentativas para o jogo {id_jogo} (rate limit persistente)")
    return None


def buscar_por_nome(nome_jogo, sessao=_sessao):
    url = f"https://store.steampowered.com/api/storesearch/?term={nome_jogo}&l=portuguese&cc=br"

    try:
        resposta = sessao.get(url, timeout=10)

        if resposta.status_code == 200:
            dados_brutos = resposta.json()

            if dados_brutos["total"] > 0:
                primeiro_jogo = dados_brutos["items"][0]
                id_encontrado = primeiro_jogo["id"]
                print(f"[DEBUG] O Python achou o ID: {id_encontrado} para o jogo '{nome_jogo}'")
                return buscar_promo_st(id_encontrado, sessao=sessao)
            else:
                salvar_logs(f"Jogo nao encontrado na loja: -- {nome_jogo}")
                return "Jogo nao encontrado"

        elif resposta.status_code == 429:
            print(" STEAM AVISOU: Limite de requisições atingido! (Erro 429)")
            return None

        else:
            salvar_logs(f"[{resposta.status_code}] Erro ao conectar a steam")
            return "Erro ao conectar na Steam."

    except requests.exceptions.Timeout:
        salvar_logs(f"Timeout ao buscar o jogo {nome_jogo}")
        return None

    except Exception as e:
        salvar_logs(f"Erro inesperado ao buscar '{nome_jogo}': {e}")
        return None
