import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Injeta variáveis de ambiente falsas em todos os testes unitários."""
    with patch.dict("os.environ", {
        "GEMINI_API_KEY": "fake-gemini-key",
        "TELEGRAM_API_TOKEN": "fake-telegram-token",
    }):
        yield


@pytest.fixture
def mock_transaction():
    """Transação padrão reutilizável entre os testes."""
    return {
        "ID": 12345,
        "value": 5000,
        "category": "Mercado",
        "date": "2025-01-01",
    }
