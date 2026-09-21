import pytest


@pytest.fixture(autouse=True)
def _isolate_integrations(settings):
    """Tests never call the real Next.js revalidation endpoint or wait on background threads."""
    settings.NEXT_REVALIDATE_URL = ""
    settings.REVALIDATE_ASYNC = False
    settings.NOVA_POSHTA_API_KEY = ""
    settings.TELEGRAM_BOT_TOKEN = ""
