import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_response_factory():
    """Cria um mock de resposta da API Gemini com o texto fornecido."""
    def _factory(value: int, category: str):
        mock = MagicMock()
        mock.text = json.dumps({"value": value, "category": category})
        return mock
    return _factory


# ─── msg_processing ──────────────────────────────────────────────────────────

class TestMsgProcessing:

    @pytest.mark.asyncio
    async def test_mercado(self, mock_response_factory):
        import llm
        with patch.object(llm.client.aio.models, "generate_content",
                          new=AsyncMock(return_value=mock_response_factory(5000, "Mercado"))):
            result = json.loads(await llm.msg_processing("gastei 50 reais no mercado"))
        assert result["value"]    == 5000
        assert result["category"] == "Mercado"

    @pytest.mark.asyncio
    async def test_restaurante(self, mock_response_factory):
        import llm
        with patch.object(llm.client.aio.models, "generate_content",
                          new=AsyncMock(return_value=mock_response_factory(8750, "Restaurantes"))):
            result = json.loads(await llm.msg_processing("almoço por 87,50"))
        assert result["value"]    == 8750
        assert result["category"] == "Restaurantes"

    @pytest.mark.asyncio
    async def test_sem_valor_retorna_zero(self, mock_response_factory):
        import llm
        with patch.object(llm.client.aio.models, "generate_content",
                          new=AsyncMock(return_value=mock_response_factory(0, "Outros"))):
            result = json.loads(await llm.msg_processing("olá tudo bem"))
        assert result["value"] == 0

    @pytest.mark.asyncio
    async def test_categoria_outros_quando_ambiguo(self, mock_response_factory):
        import llm
        with patch.object(llm.client.aio.models, "generate_content",
                          new=AsyncMock(return_value=mock_response_factory(2000, "Outros"))):
            result = json.loads(await llm.msg_processing("comprei uma coisa"))
        assert result["category"] == "Outros"

    @pytest.mark.asyncio
    async def test_falha_api_retorna_fallback(self):
        import llm
        with patch.object(llm.client.aio.models, "generate_content",
                          new=AsyncMock(side_effect=Exception("API indisponível"))):
            result = json.loads(await llm.msg_processing("gastei 30 reais"))
        assert result["value"]    == 0
        assert result["category"] == "Outros"


# ─── voice_processing ────────────────────────────────────────────────────────

class TestVoiceProcessing:

    @pytest.mark.asyncio
    async def test_audio_valido(self, mock_response_factory, tmp_path):
        import llm
        audio = tmp_path / "test.ogg"
        audio.write_bytes(b"fake-ogg-content")

        with patch.object(llm.client.aio.models, "generate_content",
                          new=AsyncMock(return_value=mock_response_factory(3000, "Contas"))):
            result = json.loads(await llm.voice_processing(str(audio)))
        assert result["value"]    == 3000
        assert result["category"] == "Contas"

    @pytest.mark.asyncio
    async def test_arquivo_inexistente_retorna_fallback(self):
        import llm
        result = json.loads(await llm.voice_processing("/caminho/invalido/audio.ogg"))
        assert result["value"]    == 0
        assert result["category"] == "Outros"

    @pytest.mark.asyncio
    async def test_arquivo_vazio_retorna_fallback(self, tmp_path):
        import llm
        audio = tmp_path / "vazio.ogg"
        audio.write_bytes(b"")
        result = json.loads(await llm.voice_processing(str(audio)))
        assert result["value"]    == 0
        assert result["category"] == "Outros"

    @pytest.mark.asyncio
    async def test_falha_api_retorna_fallback(self, tmp_path):
        import llm
        audio = tmp_path / "test.ogg"
        audio.write_bytes(b"fake-ogg-content")

        with patch.object(llm.client.aio.models, "generate_content",
                          new=AsyncMock(side_effect=Exception("Timeout"))):
            result = json.loads(await llm.voice_processing(str(audio)))
        assert result["value"]    == 0
        assert result["category"] == "Outros"


# ─── photo_processing ────────────────────────────────────────────────────────

class TestPhotoProcessing:

    @pytest.mark.asyncio
    async def test_foto_valida(self, mock_response_factory, tmp_path):
        import llm
        foto = tmp_path / "nota.jpg"
        foto.write_bytes(b"fake-jpeg-content")

        with patch.object(llm.client.aio.models, "generate_content",
                          new=AsyncMock(return_value=mock_response_factory(12399, "Mercado"))):
            result = json.loads(await llm.photo_processing(str(foto)))
        assert result["value"]    == 12399
        assert result["category"] == "Mercado"

    @pytest.mark.asyncio
    async def test_arquivo_inexistente_retorna_fallback(self):
        import llm
        result = json.loads(await llm.photo_processing("/caminho/invalido/foto.jpg"))
        assert result["value"]    == 0
        assert result["category"] == "Outros"

    @pytest.mark.asyncio
    async def test_arquivo_vazio_retorna_fallback(self, tmp_path):
        import llm
        foto = tmp_path / "vazia.jpg"
        foto.write_bytes(b"")
        result = json.loads(await llm.photo_processing(str(foto)))
        assert result["value"]    == 0
        assert result["category"] == "Outros"

    @pytest.mark.asyncio
    async def test_falha_api_retorna_fallback(self, tmp_path):
        import llm
        foto = tmp_path / "test.jpg"
        foto.write_bytes(b"fake-jpeg-content")

        with patch.object(llm.client.aio.models, "generate_content",
                          new=AsyncMock(side_effect=Exception("Erro de rede"))):
            result = json.loads(await llm.photo_processing(str(foto)))
        assert result["value"]    == 0
        assert result["category"] == "Outros"


# ─── query / transaction / query_processing ───────────────────────────────────

class TestQueryProcessing:

    def test_query_imprime_mensagem(self, capsys):
        import llm
        llm.query()
        assert "Query" in capsys.readouterr().out

    def test_transaction_imprime_mensagem(self, capsys):
        import llm
        llm.transaction()
        assert "Transaction" in capsys.readouterr().out

    def test_query_processing_sucesso(self):
        import llm
        mock_response = MagicMock()
        mock_response.text = "query"

        with patch.object(llm.client.models, "generate_content",
                          return_value=mock_response):
            result = llm.query_processing("mostre meus gastos de janeiro")

        assert result == "query"

    def test_query_processing_falha_retorna_none(self):
        import llm
        with patch.object(llm.client.models, "generate_content",
                          side_effect=Exception("API indisponível")):
            result = llm.query_processing("mostre meus gastos")

        assert result is None