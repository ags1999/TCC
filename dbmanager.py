import psycopg2
import psycopg2.extras
import uuid
import logging
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime

logger = logging.getLogger(__name__)

conn = psycopg2.connect("dbname=ledgerBotDB user=alexandre")
cur  = conn.cursor()
psycopg2.extras.register_uuid()

months = [
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro"
]


def register_user(user_id: int, name: str) -> bool:
    """
    Registra o usuário se ainda não existir.
    Retorna True em caso de sucesso, False em caso de falha.
    """
    try:
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE user_id = %s)"
        cur.execute(query, (user_id,))
        exists = cur.fetchone()[0]

        if not exists:
            insert = "INSERT INTO users(user_id, username) VALUES (%s, %s)"
            cur.execute(insert, (user_id, name))
            conn.commit()
            logger.info(f"Novo usuário registrado: {user_id} ({name})")
        else:
            logger.debug(f"Usuário já existente: {user_id}")

        return True

    except psycopg2.Error as e:
        logger.error(f"Erro de banco ao registrar usuário {user_id}: {e}", exc_info=True)
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Erro inesperado em register_user(): {e}", exc_info=True)
        conn.rollback()
        return False


def register_transaction(transaction: dict) -> bool:
    """
    Persiste uma transação confirmada no banco.
    Retorna True em caso de sucesso, False em caso de falha.
    """
    try:
        trs_id          = uuid.uuid4()
        user_id         = transaction["ID"]
        value           = transaction["value"]
        trs_category    = transaction["category"]
        trs_date        = transaction["date"]
        trs_description = transaction.get("description")

        insert = (
            "INSERT INTO transactions"
            "(transactions_id, user_id, value, category, date, description) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        cur.execute(insert, (trs_id, user_id, value, trs_category, trs_date, trs_description))
        conn.commit()
        logger.info(f"Transação registrada: user={user_id} value={value} category={trs_category}")
        return True

    except KeyError as e:
        logger.error(f"Campo obrigatório ausente na transação: {e}")
        conn.rollback()
        return False
    except psycopg2.Error as e:
        logger.error(f"Erro de banco em register_transaction(): {e}", exc_info=True)
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Erro inesperado em register_transaction(): {e}", exc_info=True)
        conn.rollback()
        return False


def consulta_ano_mes(user_id: int, ano: int, mes: int) -> io.BytesIO | None:
    """
    Gera gráfico de pizza com os gastos do usuário no período.
    Retorna um buffer PNG em memória, ou None em caso de falha.
    """
    try:
        sql_query = """
            SELECT value, category
            FROM transactions
            WHERE user_id = %s
              AND EXTRACT(YEAR  FROM date) = %s
              AND EXTRACT(MONTH FROM date) = %s
        """
        params = [user_id, int(ano), int(mes)]
        df = pd.io.sql.read_sql(sql_query, conn, params=params)

        if df.empty:
            logger.info(f"Nenhuma transação encontrada para user={user_id} {mes}/{ano}")
            return None

        df_grouped = df.groupby("category", as_index=False)["value"].sum()

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(df_grouped["value"], labels=df_grouped["category"], autopct="%1.1f%%")
        ax.set_title(f"Gastos em {months[int(mes) - 1]}/{ano}")

        lista_texto = "\n".join(
            f"{cat}: R${val / 100:.2f}"
            for cat, val in zip(df_grouped["category"], df_grouped["value"])
        )
        plt.figtext(0.5, -0.05, lista_texto, ha="center", va="top", fontsize=12)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        logger.info(f"Gráfico gerado para user={user_id} {mes}/{ano}")
        return buf

    except psycopg2.Error as e:
        logger.error(f"Erro de banco em consulta_ano_mes(): {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Erro inesperado em consulta_ano_mes(): {e}", exc_info=True)
        plt.close("all")  # garante fechamento mesmo em erro
        return None