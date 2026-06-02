import json
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Helpers ─────────────────────────────────────────────────────────────────

def make_update(text=None, user_id=99, name="Teste"):
    update = MagicMock()
    update.message.chat.id             = user_id
    update.message.chat.effective_name = name
    update.message.text                = text
    update.message.date                = "2025-01-01"
    update.message.reply_text          = AsyncMock()
    update.effective_chat.id           = user_id
    return update

def make_context(user_data=None):
    context = MagicMock()
    context.user_data        = user_data or {}
    context.bot.send_message = AsyncMock()
    return context

def make_callback(data, user_id=99):
    update = MagicMock()
    update.callback_query.data                      = data
    update.callback_query.answer                    = AsyncMock()
    update.callback_query.edit_message_text         = AsyncMock()
    update.callback_query.edit_message_reply_markup = AsyncMock()
    update.callback_query.message.reply_photo       = AsyncMock()
    update.effective_chat.id                        = user_id
    return update


# ─── load_environment_variables ──────────────────────────────────────────────
# Cobre as linhas 21 e 23-25 de main.py

class TestLoadEnvironmentVariables:

    def test_token_ausente_retorna_none(self):
        """Linha 21: ValueError quando TELEGRAM_API_TOKEN é None.
        Linhas 23-25: except captura, imprime e retorna None."""
        import main as m
        with patch("main.load_dotenv"), \
             patch("main.os.getenv", return_value=None):
            result = m.load_environment_variables()
        assert result is None

    def test_excecao_inesperada_retorna_none(self):
        """Linhas 23-25: except Exception captura qualquer outra falha."""
        import main as m
        with patch("main.load_dotenv", side_effect=OSError("sem permissão")):
            result = m.load_environment_variables()
        assert result is None


# ─── handle_message ──────────────────────────────────────────────────────────

class TestHandleMessage:

    @pytest.mark.asyncio
    async def test_mensagem_valida_exibe_resumo(self):
        from main import handle_message
        update  = make_update(text="gastei 50 reais no mercado")
        context = make_context()
        with patch("main.dbm.register_user"), \
             patch("main.llm.msg_processing",
                   return_value=json.dumps({"value": 5000, "category": "Mercado"})):
            await handle_message(update, context)
        args = update.message.reply_text.call_args[0][0]
        assert "R$50.00" in args
        assert "Mercado" in args

    @pytest.mark.asyncio
    async def test_mensagem_salva_transaction_em_context(self):
        from main import handle_message
        update  = make_update(text="paguei conta de luz 200 reais")
        context = make_context()
        with patch("main.dbm.register_user"), \
             patch("main.llm.msg_processing",
                   return_value=json.dumps({"value": 20000, "category": "Contas"})):
            await handle_message(update, context)
        assert context.user_data["transaction"]["value"]    == 20000
        assert context.user_data["transaction"]["category"] == "Contas"
        assert context.user_data["transaction"]["ID"]       == 99
        assert context.user_data["new_value"]               == 0

    @pytest.mark.asyncio
    async def test_json_invalido_envia_mensagem_de_erro(self):
        from main import handle_message
        update  = make_update(text="teste")
        context = make_context()
        with patch("main.dbm.register_user"), \
             patch("main.llm.msg_processing", return_value="resposta inválida"):
            await handle_message(update, context)
        assert "Não consegui interpretar" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_campo_ausente_envia_mensagem_de_erro(self):
        from main import handle_message
        update  = make_update(text="teste")
        context = make_context()
        with patch("main.dbm.register_user"), \
             patch("main.llm.msg_processing",
                   return_value=json.dumps({"value": 100})):  # category ausente
            await handle_message(update, context)
        assert "Não consegui extrair" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_excecao_generica_envia_mensagem_de_erro(self):
        from main import handle_message
        update  = make_update(text="teste")
        context = make_context()
        with patch("main.dbm.register_user"), \
             patch("main.llm.msg_processing", side_effect=Exception("Falha inesperada")):
            await handle_message(update, context)
        assert "erro" in update.message.reply_text.call_args[0][0].lower()


# ─── handle_voice ────────────────────────────────────────────────────────────

class TestHandleVoice:

    @pytest.mark.asyncio
    async def test_voz_valida_exibe_resumo(self, tmp_path):
        from main import handle_voice
        update  = make_update(user_id=99)
        context = make_context()
        (tmp_path / "99.ogg").write_bytes(b"fake-audio")
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.llm.voice_processing",
                   return_value=json.dumps({"value": 4500, "category": "Restaurantes"})), \
             patch("main.os.path.exists", return_value=True), \
             patch("main.os.remove"):
            context.bot.get_file      = AsyncMock(return_value=MagicMock(download_to_drive=AsyncMock()))
            update.message.voice      = MagicMock(file_id="abc123")
            update.message.reply_text = AsyncMock()
            await handle_voice(update, context)
        assert "R$45.00"      in update.message.reply_text.call_args[0][0]
        assert "Restaurantes" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_arquivo_nao_encontrado_apos_download(self):
        from main import handle_voice
        update  = make_update(user_id=99)
        context = make_context()
        update.message.voice      = MagicMock(file_id="abc123")
        update.message.reply_text = AsyncMock()
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=False):
            context.bot.get_file = AsyncMock(return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_voice(update, context)
        assert "Não foi possível baixar" in update.message.reply_text.call_args[0][0]


# ─── handle_photo ────────────────────────────────────────────────────────────

class TestHandlePhoto:

    @pytest.mark.asyncio
    async def test_foto_valida_exibe_resumo(self):
        from main import handle_photo
        update  = make_update(user_id=99)
        context = make_context()
        update.message.reply_text = AsyncMock()
        update.message.photo      = [MagicMock(file_id="img123")]
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=True), \
             patch("main.os.remove"), \
             patch("main.llm.photo_processing",
                   return_value=json.dumps({"value": 9800, "category": "Mercado"})):
            update.message.photo[-1].get_file = AsyncMock(
                return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_photo(update, context)
        assert "R$98.00" in update.message.reply_text.call_args[0][0]
        assert "Mercado" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_arquivo_nao_encontrado_apos_download(self):
        from main import handle_photo
        update  = make_update(user_id=99)
        context = make_context()
        update.message.reply_text = AsyncMock()
        update.message.photo      = [MagicMock(file_id="img123")]
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=False):
            update.message.photo[-1].get_file = AsyncMock(
                return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_photo(update, context)
        assert "Não foi possível baixar" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_excecao_generica_envia_mensagem_de_erro(self):
        from main import handle_photo
        update  = make_update(user_id=99)
        context = make_context()
        update.message.reply_text = AsyncMock()
        update.message.photo      = [MagicMock(file_id="img123")]
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=True), \
             patch("main.os.remove"), \
             patch("main.llm.photo_processing", side_effect=Exception("Falha")):
            update.message.photo[-1].get_file = AsyncMock(
                return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_photo(update, context)
        assert "erro" in update.message.reply_text.call_args[0][0].lower()


# ─── button ──────────────────────────────────────────────────────────────────

class TestButton:

    @pytest.mark.asyncio
    async def test_confirmar_chama_register_transaction(self):
        from main import button
        update  = make_callback("Confirmar")
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 5000, "category": "Mercado", "date": "2025-01-01"}
        })
        with patch("main.dbm.register_transaction") as mock_reg:
            await button(update, context)
        mock_reg.assert_called_once()
        update.callback_query.edit_message_text.assert_called_with(text="Transação Confirmada")

    @pytest.mark.asyncio
    async def test_cancelar_descarta_transacao(self):
        from main import button
        update  = make_callback("Cancelar")
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 5000, "category": "Mercado", "date": "2025-01-01"}
        })
        await button(update, context)
        update.callback_query.edit_message_text.assert_called_with(text="Transação Cancelada")

    @pytest.mark.asyncio
    async def test_digito_acumula_valor(self):
        from main import button
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 0, "category": "Outros", "date": "2025-01-01"},
            "new_value": 12
        })
        await button(make_callback("5"), context)
        assert context.user_data["new_value"] == 125  # 12 * 10 + 5

    @pytest.mark.asyncio
    async def test_backspace_usa_divisao_inteira(self):
        from main import button
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 0, "category": "Outros", "date": "2025-01-01"},
            "new_value": 125
        })
        await button(make_callback("←"), context)
        assert context.user_data["new_value"] == 12  # 125 // 10

    @pytest.mark.asyncio
    async def test_backspace_em_zero_permanece_zero(self):
        from main import button
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 0, "category": "Outros", "date": "2025-01-01"},
            "new_value": 0
        })
        await button(make_callback("←"), context)
        assert context.user_data["new_value"] == 0

    @pytest.mark.asyncio
    async def test_ok_atualiza_valor_da_transacao(self):
        from main import button
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 0, "category": "Mercado", "date": "2025-01-01"},
            "new_value": 4500
        })
        await button(make_callback("OK"), context)
        assert context.user_data["transaction"]["value"] == 4500
        assert context.user_data["new_value"]            == 0

    @pytest.mark.asyncio
    async def test_categoria_atualiza_transacao(self):
        from main import button
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 5000, "category": "Outros", "date": "2025-01-01"},
            "new_value": 0
        })
        await button(make_callback("Viagens"), context)
        assert context.user_data["transaction"]["category"] == "Viagens"

    @pytest.mark.asyncio
    async def test_sessao_expirada_exibe_aviso(self):
        from main import button
        update  = make_callback("Confirmar")
        context = make_context(user_data={})  # transaction ausente
        await button(update, context)
        msg = update.callback_query.edit_message_text.call_args[1]["text"]
        assert "Sessão expirada" in msg

    @pytest.mark.asyncio
    async def test_categoria_exibe_botoes_de_categoria(self):
        from main import button
        update  = make_callback("Categoria")
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 5000, "category": "Mercado", "date": "2025-01-01"},
            "new_value": 0
        })
        await button(update, context)
        msg = update.callback_query.edit_message_text.call_args[1]["text"]
        assert "categoria" in msg.lower()

    @pytest.mark.asyncio
    async def test_keyerror_no_button_exibe_erro_interno(self):
        from main import button
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 0, "date": "2025-01-01"},  # sem 'category'
            "new_value": 5000
        })
        await button(make_callback("OK"), context)
        msg = update.callback_query.edit_message_text.call_args[1]["text"] if False else \
              make_callback("OK")  # dummy — corrigido abaixo
        # rodar corretamente:
        update2  = make_callback("OK")
        context2 = make_context(user_data={
            "transaction": {"ID": 99, "value": 0, "date": "2025-01-01"},
            "new_value": 5000
        })
        await button(update2, context2)
        msg = update2.callback_query.edit_message_text.call_args[1]["text"]
        assert "incompletos" in msg

    @pytest.mark.asyncio
    async def test_excecao_inesperada_no_button_exibe_erro(self):
        from main import button
        update  = make_callback("Confirmar")
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 5000, "category": "Mercado", "date": "2025-01-01"}
        })
        with patch("main.dbm.register_transaction", side_effect=Exception("Erro inesperado")):
            await button(update, context)
        msg = update.callback_query.edit_message_text.call_args[1]["text"]
        assert "inesperado" in msg.lower()


# ─── start ───────────────────────────────────────────────────────────────────

class TestStart:

    @pytest.mark.asyncio
    async def test_start_envia_boas_vindas(self):
        from main import start
        update  = make_update(user_id=99, name="Alexandre")
        context = make_context()
        with patch("main.dbm.register_user"):
            await start(update, context)
        msg = context.bot.send_message.call_args[1]["text"]
        assert "LedgerBot" in msg

    @pytest.mark.asyncio
    async def test_start_falha_envia_erro(self):
        from main import start
        update  = make_update(user_id=99, name="Alexandre")
        context = make_context()
        with patch("main.dbm.register_user", side_effect=Exception("Banco indisponível")):
            await start(update, context)
        msg = context.bot.send_message.call_args[1]["text"]
        assert "erro" in msg.lower()


# ─── consulta ────────────────────────────────────────────────────────────────

class TestConsulta:

    @pytest.mark.asyncio
    async def test_consulta_exibe_seletor_de_ano(self):
        from main import consulta
        update  = make_update(user_id=99)
        context = make_context()
        await consulta(update, context)
        assert "ano" in context.bot.send_message.call_args[1]["text"].lower()

    @pytest.mark.asyncio
    async def test_consulta_falha_envia_erro(self):
        from main import consulta
        update  = make_update(user_id=99)
        context = make_context()
        context.bot.send_message = AsyncMock(
            side_effect=[Exception("Falha no Telegram"), None]
        )
        await consulta(update, context)
        assert context.bot.send_message.call_count == 2


# ─── button — ano e mês ──────────────────────────────────────────────────────

class TestButtonAnoMes:

    @pytest.mark.asyncio
    async def test_selecao_de_ano_salva_e_exibe_meses(self):
        from main import button, years
        ano     = years[0]
        update  = make_callback(ano)
        context = make_context(user_data={})
        await button(update, context)
        assert context.user_data["year"] == ano
        assert "mês" in update.callback_query.edit_message_text.call_args[1]["text"].lower()

    @pytest.mark.asyncio
    async def test_selecao_de_mes_envia_grafico(self):
        import io
        from main import button
        buf    = io.BytesIO(b"fake-png")
        update  = make_callback("Janeiro")
        context = make_context(user_data={"year": "2025"})
        with patch("main.dbm.consulta_ano_mes", return_value=buf):
            await button(update, context)
        update.callback_query.message.reply_photo.assert_called_once_with(photo=buf)

    @pytest.mark.asyncio
    async def test_selecao_de_mes_sem_ano_exibe_erro(self):
        from main import button
        update  = make_callback("Janeiro")
        context = make_context(user_data={})  # year ausente
        await button(update, context)
        msg = update.callback_query.edit_message_text.call_args[1]["text"]
        assert "ano não selecionado" in msg


# ─── button — Editar e Valor ─────────────────────────────────────────────────

class TestButtonEditar:

    @pytest.mark.asyncio
    async def test_editar_exibe_botoes_de_campo(self):
        from main import button
        update  = make_callback("Editar")
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 5000, "category": "Mercado", "date": "2025-01-01"}
        })
        await button(update, context)
        msg = update.callback_query.edit_message_text.call_args[1]["text"]
        assert "campo" in msg.lower()

    @pytest.mark.asyncio
    async def test_valor_exibe_teclado_numerico(self):
        from main import button
        update  = make_callback("Valor")
        context = make_context(user_data={
            "transaction": {"ID": 99, "value": 5000, "category": "Mercado", "date": "2025-01-01"},
            "new_value": 0
        })
        await button(update, context)
        update.callback_query.edit_message_text.assert_called_once()
        assert context.user_data["new_value"] == 0


# ─── handle_voice — erros específicos ────────────────────────────────────────

class TestHandleVoiceErros:

    @pytest.mark.asyncio
    async def test_json_invalido_envia_erro(self):
        from main import handle_voice
        update  = make_update(user_id=99)
        context = make_context()
        update.message.voice      = MagicMock(file_id="abc123")
        update.message.reply_text = AsyncMock()
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=True), \
             patch("main.os.remove"), \
             patch("main.llm.voice_processing", return_value="json inválido"):
            context.bot.get_file = AsyncMock(return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_voice(update, context)
        assert "Não consegui interpretar" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_campo_ausente_envia_erro(self):
        from main import handle_voice
        update  = make_update(user_id=99)
        context = make_context()
        update.message.voice      = MagicMock(file_id="abc123")
        update.message.reply_text = AsyncMock()
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=True), \
             patch("main.os.remove"), \
             patch("main.llm.voice_processing",
                   return_value=json.dumps({"value": 100})):  # category ausente
            context.bot.get_file = AsyncMock(return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_voice(update, context)
        assert "Não consegui extrair" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_finally_erro_na_limpeza_nao_propaga(self):
        from main import handle_voice
        update  = make_update(user_id=99)
        context = make_context()
        update.message.voice      = MagicMock(file_id="abc123")
        update.message.reply_text = AsyncMock()
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=True), \
             patch("main.os.remove", side_effect=OSError("Permissão negada")), \
             patch("main.llm.voice_processing", side_effect=Exception("Falha")):
            context.bot.get_file = AsyncMock(return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_voice(update, context)
        assert "erro" in update.message.reply_text.call_args[0][0].lower()


# ─── handle_photo — erros específicos ────────────────────────────────────────

class TestHandlePhotoErros:

    @pytest.mark.asyncio
    async def test_json_invalido_envia_erro(self):
        from main import handle_photo
        update  = make_update(user_id=99)
        context = make_context()
        update.message.reply_text = AsyncMock()
        update.message.photo      = [MagicMock(file_id="img123")]
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=True), \
             patch("main.os.remove"), \
             patch("main.llm.photo_processing", return_value="json inválido"):
            update.message.photo[-1].get_file = AsyncMock(
                return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_photo(update, context)
        assert "Não consegui interpretar" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_campo_ausente_envia_erro(self):
        from main import handle_photo
        update  = make_update(user_id=99)
        context = make_context()
        update.message.reply_text = AsyncMock()
        update.message.photo      = [MagicMock(file_id="img123")]
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=True), \
             patch("main.os.remove"), \
             patch("main.llm.photo_processing",
                   return_value=json.dumps({"value": 100})):  # category ausente
            update.message.photo[-1].get_file = AsyncMock(
                return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_photo(update, context)
        assert "Não consegui extrair" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_finally_erro_na_limpeza_nao_propaga(self):
        from main import handle_photo
        update  = make_update(user_id=99)
        context = make_context()
        update.message.reply_text = AsyncMock()
        update.message.photo      = [MagicMock(file_id="img123")]
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=True), \
             patch("main.os.remove", side_effect=OSError("Permissão negada")), \
             patch("main.llm.photo_processing", side_effect=Exception("Falha")):
            update.message.photo[-1].get_file = AsyncMock(
                return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_photo(update, context)
        assert "erro" in update.message.reply_text.call_args[0][0].lower()


# ─── help_command ─────────────────────────────────────────────────────────────

class TestHelpCommand:

    @pytest.mark.asyncio
    async def test_help_envia_mensagem(self):
        from main import help_command
        update  = make_update(user_id=99)
        context = make_context()
        await help_command(update, context)
        msg = context.bot.send_message.call_args[1]["text"]
        assert "LedgerBot"  in msg
        assert "/consulta"  in msg
        assert "/help"      in msg

    @pytest.mark.asyncio
    async def test_help_falha_envia_erro(self):
        from main import help_command
        update  = make_update(user_id=99)
        context = make_context()
        context.bot.send_message = AsyncMock(
            side_effect=[Exception("Falha no Telegram"), None]
        )
        await help_command(update, context)
        assert context.bot.send_message.call_count == 2
        assert "possível" in context.bot.send_message.call_args[1]["text"]


# ─── timeout da API Gemini ────────────────────────────────────────────────────

class TestTimeoutGemini:
    """
    asyncio.wait_for é mockado com side_effect=TimeoutError().
    llm.* é mockado com side_effect=lambda que retorna None (função síncrona),
    impedindo a criação de qualquer corrotina que ficaria sem await e geraria
    RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited.
    """

    @pytest.mark.asyncio
    async def test_timeout_em_handle_message(self):
        from main import handle_message
        update  = make_update(text="gastei 50 reais")
        context = make_context()
        with patch("main.dbm.register_user"), \
             patch("main.llm.msg_processing", side_effect=lambda *a, **k: None), \
             patch("main.asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            await handle_message(update, context)
        assert "demorou demais" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_timeout_em_handle_voice(self):
        from main import handle_voice
        update  = make_update(user_id=99)
        context = make_context()
        update.message.voice      = MagicMock(file_id="abc123")
        update.message.reply_text = AsyncMock()
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=True), \
             patch("main.os.remove"), \
             patch("main.llm.voice_processing", side_effect=lambda *a, **k: None), \
             patch("main.asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            context.bot.get_file = AsyncMock(return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_voice(update, context)
        assert "demorou demais" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_timeout_em_handle_photo(self):
        from main import handle_photo
        update  = make_update(user_id=99)
        context = make_context()
        update.message.reply_text = AsyncMock()
        update.message.photo      = [MagicMock(file_id="img123")]
        with patch("main.dbm.register_user"), \
             patch("main.os.makedirs"), \
             patch("main.os.path.exists", return_value=True), \
             patch("main.os.remove"), \
             patch("main.llm.photo_processing", side_effect=lambda *a, **k: None), \
             patch("main.asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            update.message.photo[-1].get_file = AsyncMock(
                return_value=MagicMock(download_to_drive=AsyncMock()))
            await handle_photo(update, context)
        assert "demorou demais" in update.message.reply_text.call_args[0][0]