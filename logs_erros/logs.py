from pathlib import Path
from datetime import datetime

def salvar_logs(dados):
     base_dir = Path(__file__).parent
     arquivo=base_dir/"erros.log"
     current_dateTime = datetime.now()
     with open(arquivo,"a",encoding="utf-8")as erros:
          erros.write(f"{dados} Time:{current_dateTime}\n")

