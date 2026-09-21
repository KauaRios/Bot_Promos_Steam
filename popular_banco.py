from scrapers.steam import buscar_por_nome
from banco.db import adicionar_jogo
import concurrent.futures
import threading
import re


lock_banco = threading.Lock()

def processar_linha(linha):
    """
    Essa é a tarefa que cada 'operário' (thread) vai executar.
    Ela limpa o nome, busca na Steam e salva no banco.
    """
    linha = linha.strip()
    if not linha:
        return


    if re.match(r'^\d+\.', linha):
        nome_sem_rank = re.sub(r'^\d+\.\s*', '', linha)
        nome_limpo = re.split(r'\s{2,}', nome_sem_rank)[0]
    else:
        lixo_do_site = ["Skip", "Steam", "Rank", "Showing", "Table", "About", "Blog", "Discord"]
        if any(palavra in linha for palavra in lixo_do_site):
            print(f"🗑️ Ignorando lixo do site: {linha[:30]}...")
            return
        
        nome_limpo = linha

    print(f"🔍 Buscando: {nome_limpo}...")
    resultado = buscar_por_nome(nome_limpo)
    
    if type(resultado) is dict:
       
        with lock_banco:
            adicionar_jogo(resultado["id"], resultado["Titulo"], resultado["Valor"])
        print(f" {resultado['Titulo']} adicionado com sucesso!\n")
    else:
        print(f" Falha ao carregar o jogo: {nome_limpo}\n")


def populardb():

    with open("lista.txt", "r", encoding="utf-8") as arquivo:
        linhas = arquivo.readlines()
        
    if len(linhas) == 0:
        print(" ERRO: O arquivo lista.txt está VAZIO! Você esqueceu de dar Ctrl+S no VS Code?")
        return

    print(f" Iniciando processamento de {len(linhas)} linhas usando processamento paralelo...")

   
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
   
        executor.map(processar_linha, linhas)

    print(" Processo Terminado! A fila de jogos foi concluída.")

if __name__ == "__main__":
    populardb()
