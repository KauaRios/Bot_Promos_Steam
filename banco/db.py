from logs_erros.logs import salvar_logs
import sqlite3
import os


def configurar_banco():
    try:
        conexao=sqlite3.connect("promocoes.db")
        cursor=conexao.cursor()


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jogos_monitorados (
            id_steam TEXT PRIMARY KEY,
            nome TEXT,
            preco_alvo TEXT
        )
    """)
        conexao.commit()
        conexao.close()
        print("Sistema de Banco De dados Configurado Com Sucesso!!!!!!!!!!!!!!!")

    except Exception as e:
        salvar_logs(f"Erro ao conectar ao banco {e}")

def adicionar_jogo(id_steam, nome, preco_atual):
   
    conexao = None 
    try:
        conexao = sqlite3.connect("promocoes.db")
        cursor = conexao.cursor()

        
        comando_sql = """
            INSERT INTO jogos_monitorados (id_steam, nome, preco_alvo)
            VALUES (?, ?, ?)
        """
        
        
        cursor.execute(comando_sql, (id_steam, nome, preco_atual))
        

        conexao.commit()
        print(f"[SUCESSO] '{nome}' foi adicionado à sua lista de monitoramento!")

    except sqlite3.IntegrityError:

        salvar_logs(f"[AVISO] O jogo '{nome}' já está na sua lista! Não duplicamos dados.")
        
    except Exception as e:

        salvar_logs(f"[ERRO DE BANCO] {e}")
     
        
    finally:

        if conexao:
            conexao.close()
def listar_jogos_monitorados():
    conexao = None
    try:
        conexao = sqlite3.connect("promocoes.db")
        cursor = conexao.cursor()

        
        cursor.execute("SELECT * FROM jogos_monitorados")
        
       
        lista_de_jogos = cursor.fetchall()
        
        return lista_de_jogos

    except Exception as e:
        print(f"[ERRO DE LEITURA] {e}")
       
        return [] 
        
    finally:
        if conexao:
            conexao.close()

def atualizar_preco(id_jogo,nome_jogo,novo_preco):
    conexao=None
    try:
        conexao=sqlite3.connect("promocoes.db")
        cursor=conexao.cursor()

        sql_command=("UPDATE jogos_monitorados SET preco_alvo=? WHERE id_steam=?")
        cursor.execute(sql_command,(novo_preco,id_jogo))
        conexao.commit()

        print(f"[SUCESSO] {nome_jogo} foi atualizado Valor no banco com sucesso ")
    
    
            
    except Exception as e:
    
        salvar_logs(f"[ERRO DE BANCO] {e}")
   
    finally:
    
        if conexao:
            conexao.close()


