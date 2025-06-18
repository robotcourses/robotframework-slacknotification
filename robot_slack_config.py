from dotenv import load_dotenv
import os

load_dotenv()

# Configurações obrigatórias do Slack
SLACK_API_TOKEN=os.getenv('SLACK_API_TOKEN', "")
SLACK_CHANNEL=os.getenv('SLACK_CHANNEL', "")

# Configuração de debug
DEBUG_LOGS = True  # Ativa/desativa logs detalhados no console (True/False)

# Configurações opcionais de grupos por suite
SUITE_SLACK_GROUPS = {
    # Exemplo de configuração para diferentes níveis de suite
    # "Pix": ["grupo_dev", "grupo_test"],  # Nível mais alto
    # "Pix.PixAutomatico": ["grupo_dev"],  # Nível intermediário
    # "Pix.PixAutomatico.Pagador": ["grupo_test"],  # Nível intermediário
    "Pix.PixAutomatico.Pagador.Jornada1": ["grupo_dev", "grupo_test"],  # Nível mais baixo
    "Pix.PixAutomatico.Pagador.Jornada2": ["grupo_dev", "grupo_test"],  # Nível mais baixo
}