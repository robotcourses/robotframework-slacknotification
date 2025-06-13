from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

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
	def __init__(self, context: str, environment: str, cicd_url: str):
		self.blocks = [
			self.create_header(f"Contexto em Teste: {context}"),
			self.create_divider(),
			self.create_status_section("Em Teste", ("white_circle", "26aa")),
			self.create_counter_section(0, 0, 0, 0),
			self.create_divider(),
			self.create_error_notice(),
			self.create_divider(),
			self.create_cicd_link(cicd_url)
		]

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

	def create_status_section(self, status: str, icon: Tuple[str, str]) -> MessageBlock:
		return MessageBlock(
			type="rich_text",
			elements=[{
				"type": "rich_text_section",
				"elements": [
					{"type": "text", "text": "Status Geral:", "style": {"bold": True}},
					{"type": "text", "text": " "},
					{"type": "emoji", "name": icon[0], "unicode": icon[1], "style": {"bold": True}},
					{"type": "text", "text": " "},
					{"type": "text", "text": status, "style": {"italic": True}},
					{"type": "text", "text": "\n\n"}
				]
			}]
		)

	def create_counter_section(self, executions: int, success: int, failed: int, skipped: int) -> MessageBlock:
		return MessageBlock(
			type="rich_text",
			elements=[{
				"type": "rich_text_list",
				"style": "bullet",
				"indent": 0,
				"border": 0,
				"elements": [
					{"type": "rich_text_section", "elements": [
						{"type": "text", "text": "Testes Executados: ", "style": {"bold": True}},
						{"type": "text", "text": str(executions)}
					]},
					{"type": "rich_text_section", "elements": [
						{"type": "text", "text": "Executados Com Sucesso: ", "style": {"bold": True}},
						{"type": "text", "text": str(success)}
					]},
					{"type": "rich_text_section", "elements": [
						{"type": "text", "text": "Executados Com Falha: ", "style": {"bold": True}},
						{"type": "text", "text": str(failed)}
					]},
					{"type": "rich_text_section", "elements": [
						{"type": "text", "text": "Não Executados: ", "style": {"bold": True}},
						{"type": "text", "text": str(skipped)}
					]}
				]
			}]
		)

	def create_error_notice(self) -> MessageBlock:
		return MessageBlock(
			type="rich_text",
			elements=[{
				"type": "rich_text_quote",
				"elements": [{
					"type": "text",
					"text": "As falhas detectadas estão listadas na thread desta mensagem.",
					"style": {"italic": True}
				}]
			}]
		)

	def create_cicd_link(self, url: str) -> MessageBlock:
		return MessageBlock(
			type="rich_text",
			elements=[{
				"type": "rich_text_quote",
				"elements": [{
					"type": "link",
					"url": url,
					"text": "Veja mais aqui!",
					"style": {"italic": True}
				}]
			}]
		)

	def to_dict(self) -> Dict[str, Any]:
		return {"blocks": [block.to_dict() for block in self.blocks]}

class ErrorMessage:
	def __init__(self, scenario_name: str, error_message: str):
		self.blocks = [
			MessageBlock(type="divider"),
			MessageBlock(
				type="rich_text",
				elements=[{
					"type": "rich_text_section",
					"elements": [{
						"type": "text",
						"text": f"Cenário: {scenario_name}",
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

def build_group_mention_message(mention_text: str, plural: bool) -> list:
	phrase = "podem verificar?" if plural else "pode verificar?"
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