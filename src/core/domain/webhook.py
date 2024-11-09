
class WebhookConstructor:
    def __init__(self, domain: str):
        self.url = domain
        self.webhook_path = "/bot_aiogram"

    @property
    def webhook(self) -> str:
        return f"{self.url}{self.webhook_path}"
