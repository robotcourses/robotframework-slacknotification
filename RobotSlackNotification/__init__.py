from dataclasses import dataclass
from typing import Optional, List, Tuple, Callable, Any
import os
import time
import slack_sdk
from slack_sdk.errors import SlackApiError
from RobotSlackNotification.messages import PrincipalMessage, ErrorMessage, build_group_mention_message, TRANSLATIONS
from robot.libraries.BuiltIn import BuiltIn
from functools import wraps
import importlib.util

@dataclass
class SlackConfig:
    token: str
    channel_id: str
    test_title: Optional[str] = None
    environment: str = "SDB"
    cicd_url: Optional[str] = None
    send_message: bool = True

class SlackNotificationError(Exception):
    """Exceção personalizada para erros de notificação do Slack"""
    pass

def retry_on_slack_error(max_retries: int = 3, delay: int = 1):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except SlackApiError as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                        continue
                    raise SlackNotificationError(f"Falha após {max_retries} tentativas: {str(e)}") from e
            raise last_error
        return wrapper
    return decorator

def load_slack_config():
    from robot.libraries.BuiltIn import BuiltIn
    config_path = os.path.join(os.getcwd(), "robot_slack_config.py")
    try:
        spec = importlib.util.spec_from_file_location(
            "robot_slack_config",
            config_path
        )
        if not spec or not os.path.exists(config_path):
            BuiltIn().log_to_console(
                f"[ERRO] Arquivo robot_slack_config.py não encontrado na raiz do projeto. "
                f"Crie o arquivo com as configurações necessárias antes de executar os testes."
            )
            return None
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        # Verifica se as configurações obrigatórias existem
        if not hasattr(config, "SLACK_API_TOKEN") or not hasattr(config, "SLACK_CHANNEL"):
            raise SlackNotificationError(
                "SLACK_API_TOKEN e SLACK_CHANNEL são obrigatórios no arquivo robot_slack_config.py"
            )
        return {
            "token": config.SLACK_API_TOKEN,
            "channel_id": config.SLACK_CHANNEL,
            "suite_groups": getattr(config, "SUITE_SLACK_GROUPS", {})
        }
    except Exception as e:
        raise SlackNotificationError(f"Erro ao carregar robot_slack_config.py: {str(e)}")

def get_slack_usergroup_ids(token):
    from slack_sdk import WebClient
    client = WebClient(token=token)
    try:
        response = client.usergroups_list()
        return {g["handle"]: g["id"] for g in response["usergroups"]}
    except Exception:
        return {}

class RobotSlackNotification:

    ROBOT_LISTENER_API_VERSION = 3
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = '1.2.0'

    def __init__(self,
                 send_message: bool = True,
                 test_title: Optional[str] = None,
                 environment: Optional[str] = None,
                 cicd_url: Optional[str] = None,
                 language: str = "en") -> None:
        # Apenas armazena os argumentos, sem carregar config ainda
        self._init_args = dict(
            send_message=send_message,
            test_title=test_title,
            environment=environment,
            cicd_url=cicd_url,
            language=language
        )
        self.config = None
        self.language = language.lower()
        self.ROBOT_LIBRARY_LISTENER = self
        self.client = None
        self.cicd_url = cicd_url
        self.message_timestamp: List[str] = []
        self.status_list: List[str] = []
        self.text_fallback = None
        self.suite_name: Optional[str] = None
        self.count_total: int = 0
        self.count_pass: int = 0
        self.count_failed: int = 0
        self.count_skipped: int = 0
        self.general_result_status: Optional[str] = None
        self.suite_result_status: Optional[str] = None
        self.result_icons_list: Tuple[Tuple[str, str], ...] = (
            ("white_circle", "26aa"),
            ("large_green_circle", "1f7e2"),
            ("red_circle", "1f534"),
            ("large_yellow_circle", "1f7e1")
        )
        self.general_result_icon: Optional[Tuple[str, str]] = None
        self.suite_result_icon: Optional[Tuple[str, str]] = None
        self.suite_slack_groups = {}
        self.current_suite_groups = []
        self.usergroup_handle_to_id = {}

    def _ensure_config(self):
        if self.config is not None:
            return
        slack_config = load_slack_config()
        if not slack_config:
            raise SlackNotificationError(
                "Arquivo robot_slack_config.py não encontrado. Crie o arquivo na raiz do projeto antes de executar os testes."
            )
        self.config = SlackConfig(
            token=slack_config["token"],
            channel_id=slack_config["channel_id"],
            test_title=self._init_args["test_title"],
            environment=self._init_args["environment"],
            cicd_url=self._init_args["cicd_url"],
            send_message=self._init_args["send_message"]
        )
        self.language = self._init_args["language"].lower()
        self.client = slack_sdk.WebClient(token=self.config.token, timeout=30)
        self.cicd_url = self.config.cicd_url
        self.text_fallback = f'Aplicação em teste: {self.config.test_title}'
        self.suite_slack_groups = slack_config["suite_groups"]
        self.usergroup_handle_to_id = get_slack_usergroup_ids(self.config.token)

    def start_suite(self, data, result):
        self._ensure_config()
        # Se test_title não foi informado, usa o nome da suite
        if not self.config.test_title:
            try:
                self.config.test_title = BuiltIn().get_variable_value('${SUITE_NAME}') or result.name
            except Exception:
                self.config.test_title = result.name
        t = TRANSLATIONS.get(self.language, TRANSLATIONS["en"])
        self.general_result_status = t["in_progress"]
        self.suite_result_status = t["in_progress"]
        self.suite_name = result.name
        self.general_result_icon = self.result_icons_list[0]
        self.suite_result_icon = self.result_icons_list[0]
        # Associa grupos à suite (handles)
        self.current_suite_groups = self.suite_slack_groups.get(self.suite_name, [])
        if self.config.send_message and self.message_timestamp == []:
            message = self._build_principal_message(self.count_total, self.count_pass, self.count_failed, self.count_skipped)
            ts = self._post_principal_message(result, message)
            self.message_timestamp.append(ts)

    def end_test(self, data, result):
        if self.config.send_message:

            self.status_list.append(result.status)
            self.count_pass = self.status_list.count('PASS')
            self.count_failed = self.status_list.count('FAIL')
            self.count_skipped = self.status_list.count('SKIP')
            self.count_total = len(self.status_list)

            self.suite_result_status = result.status

            if result.passed:
                self.suite_result_icon = self.result_icons_list[1]
            elif result.failed:
                self.suite_result_icon = self.result_icons_list[2]
            else:
                self.suite_result_icon = self.result_icons_list[3]

            if result.failed:
                message = self._build_error_message(result)
                self._post_thread_message(result, message, self.message_timestamp[0])

            message = self._build_principal_message(self.count_total, self.count_pass, self.count_failed, self.count_skipped)
            self._update_principal_message(result, self.message_timestamp[0], message)

    def end_suite(self, data, result):
        if not self.config.send_message:
            return

        t = TRANSLATIONS.get(self.language, TRANSLATIONS["en"])

        if result.passed:
            self.general_result_icon = self.result_icons_list[1]
            self.general_result_status = t["status_passed"]
        elif result.failed:
            self.general_result_icon = self.result_icons_list[2]
            self.general_result_status = t["status_failed"]
        else:
            self.general_result_icon = self.result_icons_list[3]
            self.general_result_status = t["status_skipped"]

        # Envia menção aos grupos se houver falhas
        if self.count_failed > 0 and self.current_suite_groups:
            ids = [
                self.usergroup_handle_to_id.get(handle.lstrip("@"))
                for handle in self.current_suite_groups
            ]
            ids = [id_ for id_ in ids if id_]
            if ids:
                mention_text = " ".join([f"<!subteam^{gid}>" for gid in ids])
                plural = len(ids) > 1
                mention_message = build_group_mention_message(mention_text, plural, self.language)
                self._post_thread_message(
                    None,
                    mention_message,
                    self.message_timestamp[0]
                )

        message = self._build_principal_message(self.count_total, self.count_pass, self.count_failed, self.count_skipped)
        self._update_principal_message(result, self.message_timestamp[0], message)

    @retry_on_slack_error(max_retries=3)
    def _post_principal_message(self, result, message: str) -> str:
        try:
            response = self.client.chat_postMessage(
                channel=self.config.channel_id,
                blocks=message,
                text=self.text_fallback,
                unfurl_links=False,
                unfurl_media=False
            )
            return response['ts']
        except SlackApiError as e:
            BuiltIn().log_to_console(f"_post_principal_message: Erro na API do Slack: {e.response['error']}")
            raise

    @retry_on_slack_error(max_retries=3)
    def _post_thread_message(self, result, message, message_ts) -> None:
        try:
            self.client.chat_postMessage(
                channel=self.config.channel_id,
                blocks=message,
                text=self.text_fallback,
                thread_ts=message_ts
            )
        except SlackApiError as e:
            BuiltIn().log_to_console(f"_post_thread_message: Erro na API do Slack: {e.response['error']}")
            raise

    @retry_on_slack_error(max_retries=3)
    def _update_principal_message(self, result, message_timestamp, message: str) -> None:
        try:
            self.client.chat_update(
                channel=self.config.channel_id,
                blocks=message,
                text=self.text_fallback,
                ts=message_timestamp
            )
        except SlackApiError as e:
            BuiltIn().log_to_console(f"_update_principal_message: Erro na API do Slack: {e.response['error']}")
            raise
        
    def _build_principal_message(self, executions, success_executions, failed_executions, skipped_executions):
        if self.config.environment and self.config.environment.strip():
            context_header = f"{self.config.test_title} | {self.config.environment}"
        else:
            context_header = f"{self.config.test_title}"

        t = TRANSLATIONS.get(self.language, TRANSLATIONS["en"])
        message = PrincipalMessage(
            context=context_header,  # Agora será usado diretamente como header
            environment="",  # Não será usado no header, já está em context_header
            cicd_url=self.cicd_url,
            language=self.language
        )
        # Atualiza o status geral
        message.blocks[2] = message.create_status_section(
            t["general_status"],
            self.general_result_icon,
            t,
            self.general_result_status
        )
        # Atualiza os contadores
        message.blocks[3] = message.create_counter_section(
            executions,
            success_executions,
            failed_executions,
            skipped_executions,
            t
        )
        return message.to_dict()['blocks']

    def _build_error_message(self, result):
        message = ErrorMessage(
            scenario_name=result.longname,
            error_message=result.message,
            language=self.language
        )
        return message.to_dict()['blocks']
