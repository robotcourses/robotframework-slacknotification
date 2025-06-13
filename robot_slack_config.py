from dotenv import load_dotenv
import os

load_dotenv()

# Configurações obrigatórias do Slack
SLACK_API_TOKEN=os.getenv('SLACK_API_TOKEN', "")
SLACK_CHANNEL=os.getenv('SLACK_CHANNEL', "")

# Configurações opcionais de grupos por suite
SUITE_SLACK_GROUPS = {
    "Test Slack": ["grupo_dev", "grupo_test"],
}