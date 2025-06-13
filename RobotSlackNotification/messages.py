from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

TRANSLATIONS = {
	"en": {
		"general_status": "General Status:",
		"executed": "Tests Executed:",
		"passed": "Successfully Executed:",
		"failed": "Executed with Failure:",
		"skipped": "Not Executed:",
		"failures_in_thread": "Failures are listed in the thread of this message.",
		"see_more": "See more here!",
		"can_check": "can check?",
		"can_check_plural": "can check?",
		"suite": "Suite",
		"scenario": "Scenario",
		"error_message": "ERROR MESSAGE",
		"in_progress": "In Progress",
		"status_passed": "Passed",
		"status_failed": "Failed",
		"status_skipped": "Skipped"
	},
	"pt-br": {
		"general_status": "Status Geral:",
		"executed": "Testes Executados:",
		"passed": "Executados Com Sucesso:",
		"failed": "Executados Com Falha:",
		"skipped": "Não Executados:",
		"failures_in_thread": "As falhas detectadas estão listadas na thread desta mensagem.",
		"see_more": "Veja mais aqui!",
		"can_check": "pode verificar?",
		"can_check_plural": "podem verificar?",
		"suite": "Suite",
		"scenario": "Cenário",
		"error_message": "MENSAGEM DE ERRO",
		"in_progress": "Em Teste",
		"status_passed": "Passou",
		"status_failed": "Falhou",
		"status_skipped": "Pulou"
	},
	"es": {
		"general_status": "Estado General:",
		"executed": "Pruebas Ejecutadas:",
		"passed": "Ejecutadas con Éxito:",
		"failed": "Ejecutadas con Fallo:",
		"skipped": "No Ejecutadas:",
		"failures_in_thread": "Las fallas detectadas están listadas en el hilo de este mensaje.",
		"see_more": "¡Ver más aquí!",
		"can_check": "¿puede verificar?",
		"can_check_plural": "¿pueden verificar?",
		"test_context": "Contexto de Prueba:",
		"suite": "Suite",
		"scenario": "Escenario",
		"error_message": "MENSAJE DE ERROR",
		"in_progress": "En Progreso",
		"status_passed": "Pasó",
		"status_failed": "Falló",
		"status_skipped": "Omitido"
	}
}

@dataclass
class MessageBlock:
	type: str
	text: Dict[str, Any] = None
	elements: List[Dict[str, Any]] = None

	def to_dict(self) -> Dict[str, Any]:
		block = {"type": self.type}
		if self.text:
			block["text"] = self.text
		if self.elements:
			block["elements"] = self.elements
		return block

class PrincipalMessage:
	def __init__(self, context: str, environment: str, cicd_url: str, language: str = "en"):
		t = TRANSLATIONS.get(language, TRANSLATIONS["en"])
		self.blocks = [
			self.create_header(context),
			self.create_divider(),
			self.create_status_section(t["general_status"], ("white_circle", "26aa"), t),
			self.create_counter_section(0, 0, 0, 0, t),
			self.create_divider(),
			self.create_error_notice(t),
			self.create_divider()
		]
		
		# Só adiciona o bloco do CI/CD se houver uma URL
		if cicd_url:
			self.blocks.append(self.create_cicd_link(cicd_url, t))

	def create_header(self, text: str) -> MessageBlock:
		return MessageBlock(
			type="header",
			text={
				"type": "plain_text",
				"text": text,
				"emoji": True
			}
		)

	def create_divider(self) -> MessageBlock:
		return MessageBlock(type="divider")

	def create_status_section(self, status: str, icon: Tuple[str, str], t, current_status: str = None) -> MessageBlock:
		return MessageBlock(
			type="rich_text",
			elements=[{
				"type": "rich_text_section",
				"elements": [
					{"type": "text", "text": status, "style": {"bold": True}},
					{"type": "text", "text": " "},
					{"type": "emoji", "name": icon[0], "unicode": icon[1], "style": {"bold": True}},
					{"type": "text", "text": " "},
					{"type": "text", "text": current_status or t["in_progress"], "style": {"italic": True}},
					{"type": "text", "text": "\n\n"}
				]
			}]
		)

	def create_counter_section(self, executions: int, success: int, failed: int, skipped: int, t) -> MessageBlock:
		return MessageBlock(
			type="rich_text",
			elements=[{
				"type": "rich_text_list",
				"style": "bullet",
				"indent": 0,
				"border": 0,
				"elements": [
					{"type": "rich_text_section", "elements": [
						{"type": "text", "text": t["executed"], "style": {"bold": True}},
						{"type": "text", "text": str(executions)}
					]},
					{"type": "rich_text_section", "elements": [
						{"type": "text", "text": t["passed"], "style": {"bold": True}},
						{"type": "text", "text": str(success)}
					]},
					{"type": "rich_text_section", "elements": [
						{"type": "text", "text": t["failed"], "style": {"bold": True}},
						{"type": "text", "text": str(failed)}
					]},
					{"type": "rich_text_section", "elements": [
						{"type": "text", "text": t["skipped"], "style": {"bold": True}},
						{"type": "text", "text": str(skipped)}
					]}
				]
			}]
		)

	def create_error_notice(self, t) -> MessageBlock:
		return MessageBlock(
			type="rich_text",
			elements=[{
				"type": "rich_text_quote",
				"elements": [{
					"type": "text",
					"text": t["failures_in_thread"],
					"style": {"italic": True}
				}]
			}]
		)

	def create_cicd_link(self, url: str, t) -> MessageBlock:
		return MessageBlock(
			type="rich_text",
			elements=[{
				"type": "rich_text_quote",
				"elements": [{
					"type": "link",
					"url": url,
					"text": t["see_more"],
					"style": {"italic": True}
				}]
			}]
		)

	def to_dict(self) -> Dict[str, Any]:
		return {"blocks": [block.to_dict() for block in self.blocks]}

class ErrorMessage:
	def __init__(self, scenario_name: str, error_message: str, language: str = "en"):
		t = TRANSLATIONS.get(language, TRANSLATIONS["en"])
		self.blocks = [
			MessageBlock(type="divider"),
			MessageBlock(
				type="rich_text",
				elements=[{
					"type": "rich_text_section",
					"elements": [{
						"type": "text",
						"text": f"{t['scenario']}: {scenario_name}",
						"style": {"bold": True}
					}]
				}]
			),
			MessageBlock(type="divider"),
			MessageBlock(
				type="rich_text",
				elements=[{
					"type": "rich_text_preformatted",
					"border": 0,
					"elements": [{
						"type": "text",
						"text": error_message
					}]
				}]
			)
		]

	def to_dict(self) -> Dict[str, Any]:
		return {"blocks": [block.to_dict() for block in self.blocks]}

def build_group_mention_message(mention_text: str, plural: bool, language: str = "en") -> list:
	t = TRANSLATIONS.get(language, TRANSLATIONS["en"])
	phrase = t["can_check_plural"] if plural else t["can_check"]
	return [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"{mention_text} {phrase}"
			}
		}
	]

# Mantendo compatibilidade com o código existente
PRINCIPAL_MESSAGE = PrincipalMessage("pix", "sandbox", "https://github.com/stone-payments/pix-backend-testing/actions/runs/11748012173").to_dict()
ERROR_MESSAGE = ErrorMessage("Cenário: Criar Chave PIX", "MENSAGEM DE ERRO").to_dict()