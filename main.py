from scrapers.steam import buscar_por_nome
from logs_erros.logs import salvar_logs
from banco.db import configurar_banco, adicionar_jogo, listar_jogos_monitorados
from monitoramento.monitor import verifica_promocoes

import time

if __name__ == "__main__":
    
    try:
        configurar_banco()
    except Exception as e:
        salvar_logs(f"Erro fatal ao iniciar banco de dados: {e}")
        exit() 

    while True:
        print("\n" + "="*35)
        print("🤖 BOT DE PROMOÇÕES STEAM 🤖")
        print("="*35)
        print("[1] Adicionar novo jogo")
        print("[2]  Listar jogos salvos")
        print("[3]  Verificar promoções AGORA")
        print("[0]  Sair do Bot")
        print("="*35)
        
        escolha = input("Escolha uma opção: ")

        try:
            if escolha == "1":
                resultado = input("Digite o nome do jogo que deseja monitorar: ")
                jogo_encontrado = buscar_por_nome(resultado)
                
               
                if type(jogo_encontrado) is dict:
                    adicionar_jogo(jogo_encontrado["id"], jogo_encontrado["Titulo"], jogo_encontrado["Valor"])
                    print(f"Jogo '{jogo_encontrado['Titulo']}' adicionado com sucesso!")
                else:
                    print(f" {jogo_encontrado}")

            elif escolha == "2":
                lista_banco = listar_jogos_monitorados()
                print("\n--- MEUS JOGOS MONITORADOS ---")
                
                if not lista_banco:
                    print("Nenhum jogo salvo ainda.")
                else:
                    for id_jogo, nome, preco in lista_banco:
                        print(f"🎮 {nome} | Preco: {preco}")

            elif escolha == "3":
                print("\n Iniciando varredura de preços na Steam...")
               
                verifica_promocoes() 
                print(" Varredura concluída!")

            elif escolha == "0":
                print("Encerrando o sistema... Até mais!")
                break 

            else:
                print(" Opção inválida! Digite um número de 0 a 3.")

        except Exception as e:
            error = f"Ocorreu o erro no fluxo principal: {e}"
            print(" Ocorreu um erro interno. Verifique o arquivo de logs.")
            salvar_logs(error)
        
       