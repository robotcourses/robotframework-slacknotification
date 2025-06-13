# RobotSlackNotification

## 🇧🇷 Descrição

**RobotSlackNotification** é uma biblioteca para o [Robot Framework](https://robotframework.org/) que envia notificações em tempo real para um canal do Slack com o status e os resultados dos testes automatizados. Ideal para integração com pipelines de CI/CD, como GitHub Actions, GitLab CI, Jenkins, entre outros.

### Principais Funcionalidades

- Envia mensagem principal com resumo dos testes (executados, sucesso, falha, pulados)
- Atualiza a mensagem principal conforme a execução avança
- Envia detalhes de falhas em threads da mensagem principal
- Suporte a ícones de status (verde, vermelho, amarelo, amarelo-claro)
- Integração fácil via variáveis de ambiente e `.env`
- Compatível com qualquer pipeline que forneça uma URL de execução

### Como Usar

1. **Instale as dependências**  
   Use o Poetry ou pip:
   ```bash
   poetry install
   # ou
   pip install -r requirements.txt
   ```

2. **Configure o arquivo `.env`**  
   Crie um arquivo `.env` na raiz do projeto com:
   ```
   SLACK_API_TOKEN=xoxb-seu-token-do-slack
   SLACK_CHANNEL=ID_DO_CANAL
   ```

3. **Adicione a biblioteca no seu teste Robot**
   ```robot
   Library    RobotSlackNotification
       ...    context=Seu Contexto
       ...    environment=HML
       ...    cicd_url=https://github.com/sua-org/seu-repo/actions/runs/123456789
   ```

   - `context` (opcional): Nome do contexto/teste. Se não informado, usa o nome da suite.
   - `environment` (opcional): Ambiente de execução. Se não informado, não aparece na mensagem.
   - `cicd_url` (opcional): URL completa do pipeline.

4. **Execute seus testes normalmente**
   ```bash
   poetry run robot tests/
   ```

---

## 🇺🇸 English

**RobotSlackNotification** is a [Robot Framework](https://robotframework.org/) library that sends real-time notifications to a Slack channel with the status and results of your automated tests. Perfect for integration with CI/CD pipelines like GitHub Actions, GitLab CI, Jenkins, and others.

### Main Features

- Sends a main message with a summary of test results (executed, passed, failed, skipped)
- Updates the main message as execution progresses
- Sends failure details in threads under the main message
- Status icons (green, red, yellow, light-yellow)
- Easy integration via environment variables and `.env` file
- Compatible with any pipeline that provides a run URL

### How to Use

1. **Install dependencies**  
   Use Poetry or pip:
   ```bash
   poetry install
   # or
   pip install -r requirements.txt
   ```

2. **Configure the `.env` file**  
   Create a `.env` file in the project root with:
   ```
   SLACK_API_TOKEN=xoxb-your-slack-token
   SLACK_CHANNEL=YOUR_CHANNEL_ID
   ```

3. **Add the library to your Robot test**
   ```robot
   Library    RobotSlackNotification
       ...    context=Your Context
       ...    environment=HML
       ...    cicd_url=https://github.com/your-org/your-repo/actions/runs/123456789
   ```

   - `context` (optional): Name of the context/test. If not provided, the suite name will be used.
   - `environment` (optional): Execution environment. If not provided, it will not appear in the message.
   - `cicd_url` (optional): Full pipeline run URL.

4. **Run your tests as usual**
   ```bash
   poetry run robot tests/
   ```

---

## Licença / License

Este projeto está licenciado sob a licença Apache 2.0.  
This project is licensed under the Apache 2.0 license.
