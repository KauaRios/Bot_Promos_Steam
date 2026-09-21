from banco.db import listar_jogos_monitorados, atualizar_preco
from scrapers.steam import buscar_promo_st
from notificacoes.telegram import enviar
from notificacoes.discord import enviar_mensagem_discord
from logs_erros.logs import salvar_logs
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 8


def _parse_preco(valor):
    if valor == "Gratuito!":
        return 0.0
    limpo = valor.replace("R$", "").replace(".", "").replace(",", ".")
    return float(limpo.strip())


def _processar_jogo(id_salvo, nome_salvo, preco_banco):
    print(f"⏳ Verificando preços de: {nome_salvo}...")

    dados_hoje = buscar_promo_st(id_salvo)

    if dados_hoje is None:
        print(
            f" Não foi possível verificar {nome_salvo} (rate limit persistente ou erro)."
        )
        return

    if dados_hoje["Valor"] == "Preço indisponível (ou item inválido)":
        print(f" O jogo {nome_salvo} está sem preço na loja hoje. Pulando...")
        return

    if preco_banco == "Preço indisponível (ou item inválido)":
        print(f" O jogo {nome_salvo} está salvo sem preço no banco. Pulando...")
        return

    try:
        preco_banco_num = _parse_preco(preco_banco)
        valor_limpo = _parse_preco(dados_hoje["Valor"])
    except Exception as e:
        salvar_logs(f"Erro ao converter preço de {nome_salvo}: {e}")
        return

    if valor_limpo < preco_banco_num:

        mensagem_telegram = f"""
🚨 *ALERTA DE PROMOÇÃO!* 🚨

🎮 Jogo: *{nome_salvo}*
📉 Preço Antigo: R$ {preco_banco}
💸 *Preço Atual: {dados_hoje['Valor']}*

🛒 [Clique aqui para abrir na Steam]({dados_hoje['link']})
"""

        mensagem_discord = f"""
🚨 **ALERTA DE PROMOÇÃO NA STEAM!** 🚨
> 🎮 **Jogo:** {nome_salvo}
> 📉 **Preço Antigo:** ~~R$ {preco_banco}~~
> 💸 **Preço Atual:** **{dados_hoje['Valor']}**

🛒 [**Clique aqui para garantir a oferta**]({dados_hoje['link']})
@here
"""

        enviar(mensagem_telegram)
        enviar_mensagem_discord(mensagem_discord)

        print(f" Promoção do {nome_salvo} enviada para o Telegram!")
        print(f" Promoção do {nome_salvo} enviada para o Discord!")

        atualizar_preco(id_salvo, nome_salvo, dados_hoje["Valor"])

    elif valor_limpo > preco_banco_num:
        print(
            f"Promocao do jogo {nome_salvo} acabou. Subindo preco no banco para R${valor_limpo}"
        )
        atualizar_preco(id_salvo, nome_salvo, dados_hoje["Valor"])

    else:
        print(
            f" {nome_salvo}: Preço estável (Hoje: R$ {valor_limpo} | Preco Atual: R$ {preco_banco_num})"
        )


def verifica_promocoes():
    print(" [DEBUG] Iniciando varredura da base de jogos...")
    lista_banco = listar_jogos_monitorados()
    print(f" Total de jogos carregados do banco: {len(lista_banco)}")

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    futuros = {
        executor.submit(_processar_jogo, id_salvo, nome_salvo, preco_banco): nome_salvo
        for id_salvo, nome_salvo, preco_banco in lista_banco
    }

    try:
        for futuro in as_completed(futuros):
            nome_salvo = futuros[futuro]
            try:
                futuro.result()
            except Exception as e:
                salvar_logs(f"Erro ao processar {nome_salvo}: {e}")
    except KeyboardInterrupt:
        print("\n  Interrompido pelo usuário. Cancelando tarefas pendentes...")
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        executor.shutdown(wait=True)
