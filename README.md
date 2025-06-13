# RobotSlackNotification

![Exemplo de Uso](docs/example_video.gif)

## 🇧🇷 Descrição

**RobotSlackNotification** é uma biblioteca para o [Robot Framework](https://robotframework.org/) que envia notificações em tempo real para um canal do Slack com o status e os resultados dos testes automatizados. Ideal para execuções integradas com pipelines de CI/CD, como GitHub Actions, GitLab CI, Jenkins, entre outros.

### Principais Funcionalidades

- Envia mensagem principal com resumo dos testes (executados, sucesso, falha, pulados)
- Atualiza a mensagem principal conforme a execução avança
- Envia detalhes de falhas em threads da mensagem principal
- Permite menção automática a grupos do Slack (User Groups) configurados por suite

---

## ⚙️ Configuração do Projeto

### 1. Instale a biblioteca

Use o Poetry ou pip:
```bash
poetry add robotframework-slacknotification
# ou
pip install robotframework-slacknotification
```

### 2. Configure o arquivo `.env`

Crie um arquivo `.env` na raiz do projeto o API TOKEN do Slack e o ID do seu Canal:
```
SLACK_API_TOKEN=xoxb-seu-token-do-slack
SLACK_CHANNEL=ID_DO_CANAL
```

- O token deve ser do tipo "Bot User OAuth Token" e ter os escopos:
  - `chat:write`
  - `chat:write.public`
  - `usergroups:read` (para menções automáticas a grupos)

### 3. (Opcional) Configure os grupos de menção por suite

Crie um arquivo chamado `robot_slack_config.py` na raiz do seu projeto de testes, conforme o exemplo abaixo:

```python
from dotenv import load_dotenv
import os

load_dotenv()

# Configurações obrigatórias do Slack
SLACK_API_TOKEN = os.getenv('SLACK_API_TOKEN', "")
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', "")

# Configurações opcionais de grupos por suite
SUITE_SLACK_GROUPS = {
    "Test Slack": ["grupo_dev", "grupo_test"],
}
```

- O nome da suite deve ser igual ao exibido no log do Robot Framework
- Os nomes dos grupos devem ser os "handles" dos User Groups do Slack (sem o `@`)
- O arquivo é obrigatório para a biblioteca funcionar

### 4. (Opcional) Suporte a múltiplos idiomas

A biblioteca suporta mensagens em três idiomas:
- **Inglês** (padrão) = en
- **Português-BR** = pt-br
- **Espanhol** = es

Basta passar o argumento `language` ao importar a biblioteca no seu teste Robot:

```robot
Library    RobotSlackNotification
    ...    language=pt-br
```
ou
```robot
Library    RobotSlackNotification
    ...    language=es
```
Se não informar, o padrão será inglês (`en`).

Todos os textos das mensagens, labels e alertas serão enviados no idioma escolhido.

### 5. Adicione a biblioteca no seu teste Robot
Exemplo completo de uso:
```robot
Library    RobotSlackNotification
    ...    test_title=Seu Título de Teste
    ...    environment=HML
    ...    cicd_url=https://github.com/sua-org/seu-repo/actions/runs/123456789
    ...    language=pt-br
```

- `test_title` (opcional): Título do teste. Se não informado, usa o nome da suite por padrão.
- `environment` (opcional): Ambiente de execução. Se não informado, não aparece na mensagem.
- `cicd_url` (opcional): URL completa do pipeline.
- `language` (opcional): Idioma das mensagens. Padrão é inglês (`en`).

---

## 🛠️ Configuração no Slack

1. **Crie um app no Slack:**  
   - https://api.slack.com/apps → "Create New App" → "From scratch"
   - Adicione os escopos: `chat:write`, `chat:write.public`, `usergroups:read`
   - Instale o app no workspace e copie o token do bot (`xoxb-...`)

2. **Crie User Groups (Grupos de Usuários):**  
   - Acesse https://app.slack.com/user-groups
   - Crie grupos como `@grupo_dev`, `@grupo_qa`, etc.
   - O handle do grupo (ex: `grupo_dev`) é o que você usará no arquivo de configuração.

3. **Adicione o bot ao canal desejado.**

---

## 🚨 Como funcionam as menções automáticas

- No final da execução de cada suite, se houver falhas e grupos configurados para aquela suite, será enviada uma mensagem na thread da mensagem principal, marcando os grupos.
- Exemplo de mensagem automática:
  ```
  @grupo_dev @grupo_qa podem verificar?
  ```

---

## 🇺🇸 English

**RobotSlackNotification** is a [Robot Framework](https://robotframework.org/) library that sends real-time notifications to a Slack channel with the status and results of your automated tests. Perfect for executions integrated with CI/CD pipelines like GitHub Actions, GitLab CI, Jenkins, and others.

### Main Features

- Sends a main message with a summary of test results (executed, passed, failed, skipped)
- Updates the main message as execution progresses
- Sends failure details in threads under the main message
- Allows automatic mention of Slack User Groups per suite

---

## ⚙️ Project Setup

### 1. Install the library

Use Poetry or pip:
```bash
poetry add robotframework-slacknotification
# or
pip install robotframework-slacknotification
```

### 2. Configure the `.env` file

Create a `.env` file in the project root with your Slack API Token and Channel ID:
```
SLACK_API_TOKEN=xoxb-your-slack-token
SLACK_CHANNEL=YOUR_CHANNEL_ID
```

- The token must be a "Bot User OAuth Token" with scopes:
  - `chat:write`
  - `chat:write.public`
  - `usergroups:read` (for automatic group mentions)

### 3. (Optional) Configure group mentions per suite

Create a file named `robot_slack_config.py` in your test project root, as shown below:

```python
SUITE_SLACK_GROUPS = {
    "Suite Name 1": ["grupo_dev", "grupo_qa"],
    "Suite Name 2": ["grupo_ops"],
}
```
- The suite name must match exactly what is shown in the Robot Framework log
- Group names must be the User Group handles from Slack (without `@`)
- The file is optional. If it doesn't exist, no group will be mentioned.

### 4. (Optional) Multi-language support

The library supports messages in three languages:
- **English** (default) = en
- **Portuguese-BR** = pt-br
- **Spanish** = es

Just pass the `language` argument when importing the library in your Robot test:

```robot
Library    RobotSlackNotification
    ...    language=pt-br
```
or
```robot
Library    RobotSlackNotification
    ...    language=es
```
If not specified, the default is English (`en`).

All message texts, labels, and alerts will be sent in the selected language.

### 5. Add the library to your Robot test

Full usage example:
```robot
Library    RobotSlackNotification
    ...    test_title=Your Test Title
    ...    environment=HML
    ...    cicd_url=https://github.com/your-org/your-repo/actions/runs/123456789
    ...    language=en
```

- `test_title` (optional): Test title. If not provided, the suite name will be used by default.
- `environment` (optional): Execution environment. If not provided, it will not appear in the message.
- `cicd_url` (optional): Full pipeline run URL.
- `language` (optional): Message language. Default is English (`en`).

---

## 🛠️ Slack Setup

1. **Create a Slack app:**  
   - https://api.slack.com/apps → "Create New App" → "From scratch"
   - Add scopes: `chat:write`, `chat:write.public`, `usergroups:read`
   - Install the app in your workspace and copy the bot token (`xoxb-...`)

2. **Create User Groups:**  
   - Go to https://app.slack.com/user-groups
   - Create groups like `@grupo_dev`, `@grupo_qa`, etc.
   - The group handle (e.g., `grupo_dev`) is what you use in the config file.

3. **Add the bot to the desired channel.**

---

## 🚨 How automatic mentions work

- At the end of each suite, if there are failures and groups configured for that suite, a message will be sent in the thread of the main message, mentioning the groups.
- Example of automatic message:
  ```
  @grupo_dev @grupo_qa can check?
  ```

---

## Licença / License

Este projeto está licenciado sob a licença Apache 2.0.  
This project is licensed under the Apache 2.0 license.
