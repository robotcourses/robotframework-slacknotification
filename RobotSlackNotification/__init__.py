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
    """Custom exception for Slack notification errors"""
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
                        time.sleep(delay * (attempt + 1))  # Retentativa exponencial
                        continue
                    raise SlackNotificationError(f"Failed after {max_retries} attempts: {str(e)}") from e
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
                f"[ERROR] File robot_slack_config.py not found in the project root. "
                f"Create the file with the necessary settings before running the tests."
            )
            return None
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        # Verifica se as configurações obrigatórias existem
        if not hasattr(config, "SLACK_API_TOKEN") or not hasattr(config, "SLACK_CHANNEL"):
            raise SlackNotificationError(
                "SLACK_API_TOKEN and SLACK_CHANNEL are required in the robot_slack_config.py file"
            )
        return {
            "token": config.SLACK_API_TOKEN,
            "channel_id": config.SLACK_CHANNEL,
            "suite_groups": getattr(config, "SUITE_SLACK_GROUPS", {}),
            "debug_logs": getattr(config, 'DEBUG_LOGS', False)
        }
    except Exception as e:
        raise SlackNotificationError(f"Error loading robot_slack_config.py: {str(e)}")

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
        self.debug_logs = False
        self.executed_suite_groups = set()

    def _log_debug(self, message: str):
        """Method to display debug logs when DEBUG_LOGS is enabled"""
        if self.debug_logs:
            try:
                BuiltIn().log_to_console(f"[DEBUG] {message}")
            except Exception as e:
                # Em caso de erro, tenta usar print como fallback
                print(f"[DEBUG] {message}")
                print(f"[DEBUG] Error using BuiltIn().log_to_console: {str(e)}")

    def _ensure_config(self):
        if self.config is not None:
            return
        slack_config = load_slack_config()
        if not slack_config:
            raise SlackNotificationError(
                "File robot_slack_config.py not found. Create the file in the project root before running the tests."
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
        # Usa o nome da suite se test_title não estiver definido
        title = self.config.test_title if self.config.test_title else "Test Execution"
        self.text_fallback = f'Application under test: {title}'
        self.suite_slack_groups = slack_config["suite_groups"]
        self.usergroup_handle_to_id = get_slack_usergroup_ids(self.config.token)
        
        # Carrega a configuração de debug do slack_config
        self.debug_logs = slack_config.get("debug_logs", False)
        if self.debug_logs:
            BuiltIn().log_to_console(f"[DEBUG] DEBUG_LOGS configuration loaded: {self.debug_logs}")
        
        self._log_debug("Configuration loaded successfully")
        self._log_debug(f"Debug logs: {'Enabled' if self.debug_logs else 'Disabled'}")

    def _get_suite_groups(self, suite_name: str) -> List[str]:
        """Searches for groups configured for the suite at all levels"""
        groups = []
        # Divide o nome da suite em partes
        parts = suite_name.split('.')
        # Constrói os níveis da suite do mais alto ao mais baixo
        for i in range(len(parts)):
            level = '.'.join(parts[:i+1])
            if level in self.suite_slack_groups:
                groups.extend(self.suite_slack_groups[level])
        return list(set(groups))  # Remove duplicatas

    def _get_suite_groups_hierarchical(self, suite_longname):
        """
        Searches for groups in SUITE_SLACK_GROUPS from the most specific to the most generic.
        """
        slack_config = load_slack_config()
        suite_slack_groups = slack_config.get('suite_groups', {})
        partes = suite_longname.split('.')
        for i in range(len(partes), 0, -1):
            chave = '.'.join(partes[:i])
            grupos = suite_slack_groups.get(chave)
            if grupos:
                return grupos
        return []

    def start_suite(self, data, result):
        self._ensure_config()
        self._log_debug(f"Original suite: {result.name}")
        
        try:
            suite_source = BuiltIn().get_variable_value('${SUITE_SOURCE}')
            self._log_debug(f"SUITE_SOURCE: {suite_source}")
            
            if suite_source:
                # Monta o nome completo da suite
                self.suite_name = f"{result.longname}"
                self._log_debug(f"Full suite name: {self.suite_name}")
            else:
                # Se SUITE_SOURCE não estiver disponível, tenta usar o nome completo do result
                if "." in result.name:
                    self.suite_name = result.name
                else:
                    self.suite_name = f"{result.longname}"
                self._log_debug(f"Using suite name from result: {self.suite_name}")
        except Exception as e:
            # Em caso de erro, tenta usar o nome completo do result
            if "." in result.name:
                self.suite_name = result.name
            else:
                self.suite_name = f"{result.longname}"
            self._log_debug(f"Error getting suite name: {str(e)}")
            self._log_debug(f"Using suite name from result: {self.suite_name}")

        t = TRANSLATIONS.get(self.language, TRANSLATIONS["en"])
        self.general_result_status = t["in_progress"]
        self.suite_result_status = t["in_progress"]
        self.general_result_icon = self.result_icons_list[0]
        self.suite_result_icon = self.result_icons_list[0]
        
        # Busca hierárquica de grupos para a suite
        suite_groups = self._get_suite_groups_hierarchical(result.longname)
        self.suite_groups = suite_groups
        
        # Associa grupos à suite (handles)
        self.current_suite_groups = self._get_suite_groups(self.suite_name)
        self._log_debug(f"Groups found for suite {self.suite_name}: {self.current_suite_groups}")
        
        # Atualiza o set de grupos executados
        self.executed_suite_groups.update(self.current_suite_groups)
        
        if self.config.send_message and self.message_timestamp == []:
            self._log_debug("Sending main message...")
            message = self._build_principal_message(self.count_total, self.count_pass, self.count_failed, self.count_skipped)
            ts = self._post_principal_message(result, message)
            self.message_timestamp.append(ts)
            self._log_debug(f"Message sent with timestamp: {ts}")

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

        message = self._build_principal_message(self.count_total, self.count_pass, self.count_failed, self.count_skipped)
        self._update_principal_message(result, self.message_timestamp[0], message)

    @retry_on_slack_error(max_retries=3)
    def _post_principal_message(self, result, message: str) -> str:
        try:
            self._log_debug(f"Tentando enviar mensagem para o canal: {self.config.channel_id}")
            self._log_debug(f"Token configurado: {bool(self.config.token)}")
            response = self.client.chat_postMessage(
                channel=self.config.channel_id,
                blocks=message,
                text=self.text_fallback,
                unfurl_links=False,
                unfurl_media=False
            )
            status = "sucesso" if response.get('ok') else "falha"
            self._log_debug(f"Resposta do Slack: {status} (ts: {response.get('ts', 'não disponível')})")
            return response['ts']
        except SlackApiError as e:
            self._log_debug(f"Erro ao enviar mensagem: {str(e)}")
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
        t = TRANSLATIONS.get(self.language, TRANSLATIONS["en"])
        # Usa o nome da suite se test_title não estiver definido
        title = self.config.test_title if self.config.test_title else self.suite_name
        context_header = f"{title}"
        if self.config.environment:
            context_header += f" | {self.config.environment}"
        
        message = PrincipalMessage(
            context=context_header,
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

    def close(self):
        """Method called after all suites have finished"""
        if not self.config.send_message or not self.message_timestamp:
            return

        # Usa apenas os grupos das suites realmente executadas
        all_groups = set(self.executed_suite_groups)

        # Se houver falhas e grupos configurados, envia menção
        if self.count_failed > 0 and all_groups:
            ids = [
                self.usergroup_handle_to_id.get(handle.lstrip("@"))
                for handle in all_groups
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
