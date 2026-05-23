# tests/test_dbmanager.py
import pytest
import io
from unittest.mock import patch, MagicMock, call


# ─── Helpers ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_cursor():
    return MagicMock()

@pytest.fixture
def mock_conn():
    return MagicMock()


# ─── register_user ───────────────────────────────────────────────────────────

class TestRegisterUser:

    def test_usuario_novo_executa_insert(self, mock_cursor, mock_conn):
        import dbmanager
        mock_cursor.fetchone.return_value = [False]

        with patch.object(dbmanager, "cur",  mock_cursor), \
             patch.object(dbmanager, "conn", mock_conn):
            result = dbmanager.register_user(12345, "Alexandre")

        assert result is True
        assert any("INSERT" in str(c) for c in mock_cursor.execute.call_args_list)
        mock_conn.commit.assert_called_once()

    def test_usuario_existente_nao_executa_insert(self, mock_cursor, mock_conn):
        import dbmanager
        mock_cursor.fetchone.return_value = [True]

        with patch.object(dbmanager, "cur",  mock_cursor), \
             patch.object(dbmanager, "conn", mock_conn):
            result = dbmanager.register_user(12345, "Alexandre")

        assert result is True
        assert all("INSERT" not in str(c) for c in mock_cursor.execute.call_args_list)
        mock_conn.commit.assert_not_called()

    def test_falha_no_banco_retorna_false(self, mock_cursor, mock_conn):
        import dbmanager
        import psycopg2
        mock_cursor.execute.side_effect = psycopg2.Error("Conexão perdida")

        with patch.object(dbmanager, "cur",  mock_cursor), \
             patch.object(dbmanager, "conn", mock_conn):
            result = dbmanager.register_user(12345, "Alexandre")

        assert result is False
        mock_conn.rollback.assert_called_once()

    def test_excecao_generica_retorna_false(self, mock_cursor, mock_conn):
        import dbmanager
        mock_cursor.execute.side_effect = Exception("Erro inesperado")

        with patch.object(dbmanager, "cur",  mock_cursor), \
             patch.object(dbmanager, "conn", mock_conn):
            result = dbmanager.register_user(12345, "Alexandre")

        assert result is False
        mock_conn.rollback.assert_called_once()


# ─── register_transaction ────────────────────────────────────────────────────

class TestRegisterTransaction:

    def test_transacao_valida_executa_insert(self, mock_cursor, mock_conn, mock_transaction):
        import dbmanager

        with patch.object(dbmanager, "cur",  mock_cursor), \
             patch.object(dbmanager, "conn", mock_conn):
            result = dbmanager.register_transaction(mock_transaction)

        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_insere_description_none_quando_ausente(self, mock_cursor, mock_conn):
        import dbmanager
        transaction = {"ID": 99, "value": 1000, "category": "Outros", "date": "2025-01-01"}

        with patch.object(dbmanager, "cur",  mock_cursor), \
             patch.object(dbmanager, "conn", mock_conn):
            dbmanager.register_transaction(transaction)

        args = mock_cursor.execute.call_args[0][1]
        assert args[-1] is None  # description deve ser None

    def test_insere_description_quando_presente(self, mock_cursor, mock_conn):
        import dbmanager
        transaction = {
            "ID": 99, "value": 1000, "category": "Outros",
            "date": "2025-01-01", "description": "Uber para o aeroporto"
        }

        with patch.object(dbmanager, "cur",  mock_cursor), \
             patch.object(dbmanager, "conn", mock_conn):
            dbmanager.register_transaction(transaction)

        args = mock_cursor.execute.call_args[0][1]
        assert args[-1] == "Uber para o aeroporto"

    def test_campo_obrigatorio_ausente_retorna_false(self, mock_cursor, mock_conn):
        import dbmanager
        transaction_incompleta = {"ID": 99, "value": 1000}  # category e date ausentes

        with patch.object(dbmanager, "cur",  mock_cursor), \
             patch.object(dbmanager, "conn", mock_conn):
            result = dbmanager.register_transaction(transaction_incompleta)

        assert result is False
        mock_conn.rollback.assert_called_once()

    def test_falha_no_banco_retorna_false(self, mock_cursor, mock_conn, mock_transaction):
        import dbmanager
        import psycopg2
        mock_cursor.execute.side_effect = psycopg2.Error("Violação de constraint")

        with patch.object(dbmanager, "cur",  mock_cursor), \
             patch.object(dbmanager, "conn", mock_conn):
            result = dbmanager.register_transaction(mock_transaction)

        assert result is False
        mock_conn.rollback.assert_called_once()

    def test_uuid_gerado_e_unico_entre_chamadas(self, mock_cursor, mock_conn, mock_transaction):
        import dbmanager

        uuids = []
        def captura_uuid(*args):
            uuids.append(args[1][0])  # primeiro parâmetro do INSERT é o UUID

        mock_cursor.execute.side_effect = captura_uuid

        with patch.object(dbmanager, "cur",  mock_cursor), \
             patch.object(dbmanager, "conn", mock_conn):
            dbmanager.register_transaction(mock_transaction)
            dbmanager.register_transaction(mock_transaction)

        assert uuids[0] != uuids[1]

    def test_excecao_generica_retorna_false(self, mock_cursor, mock_conn, mock_transaction):
        """Cobre o except Exception de register_transaction (linhas 84-87 do dbmanager.py)."""
        import dbmanager
        with patch("dbmanager.uuid.uuid4", side_effect=Exception("Erro inesperado")), \
             patch.object(dbmanager, "cur",  mock_cursor), \
             patch.object(dbmanager, "conn", mock_conn):
            result = dbmanager.register_transaction(mock_transaction)

        assert result is False
        mock_conn.rollback.assert_called_once()


# ─── consulta_ano_mes ────────────────────────────────────────────────────────

class TestConsultaAnoMes:

    def test_retorna_buffer_png(self, mock_conn):
        import dbmanager
        import pandas as pd

        df = pd.DataFrame({
            "value":    [5000, 3000],
            "category": ["Mercado", "Contas"]
        })

        with patch.object(dbmanager, "conn", mock_conn), \
             patch("dbmanager.pd.io.sql.read_sql", return_value=df):
            result = dbmanager.consulta_ano_mes(99, 2025, 1)

        assert isinstance(result, io.BytesIO)
        assert result.read(4) == b"\x89PNG"  # magic bytes do PNG

    def test_sem_dados_retorna_none(self, mock_conn):
        import dbmanager
        import pandas as pd

        df_vazio = pd.DataFrame(columns=["value", "category"])

        with patch.object(dbmanager, "conn", mock_conn), \
             patch("dbmanager.pd.io.sql.read_sql", return_value=df_vazio):
            result = dbmanager.consulta_ano_mes(99, 2025, 1)

        assert result is None

    def test_falha_no_banco_retorna_none(self, mock_conn):
        import dbmanager
        import psycopg2

        with patch.object(dbmanager, "conn", mock_conn), \
             patch("dbmanager.pd.io.sql.read_sql",
                   side_effect=psycopg2.Error("Timeout")):
            result = dbmanager.consulta_ano_mes(99, 2025, 1)

        assert result is None

    def test_excecao_generica_retorna_none(self, mock_conn):
        import dbmanager

        with patch.object(dbmanager, "conn", mock_conn), \
             patch("dbmanager.pd.io.sql.read_sql",
                   side_effect=Exception("Erro inesperado")):
            result = dbmanager.consulta_ano_mes(99, 2025, 1)

        assert result is None

    def test_titulo_contem_mes_e_ano(self, mock_conn):
        import dbmanager
        import pandas as pd

        df = pd.DataFrame({"value": [2000], "category": ["Outros"]})

        with patch.object(dbmanager, "conn", mock_conn), \
             patch("dbmanager.pd.io.sql.read_sql", return_value=df), \
             patch("dbmanager.plt") as mock_plt:

            mock_fig = MagicMock()
            mock_ax  = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, mock_ax)
            mock_plt.savefig = MagicMock()
            mock_plt.close   = MagicMock()
            mock_plt.figtext = MagicMock()
            mock_plt.tight_layout = MagicMock()

            dbmanager.consulta_ano_mes(99, 2025, 3)

        titulo = mock_ax.set_title.call_args[0][0]
        assert "Março" in titulo
        assert "2025"  in titulo