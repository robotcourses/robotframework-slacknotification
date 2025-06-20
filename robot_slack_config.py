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
    "TestSuite": ["grupo_test", "grupo_dev"],
    "IntermediateSuite": ["grupo_dev"],
}