# LedgerBot — Assistente Financeiro Inteligente 🤖💰

Chatbot para Telegram que registra transações financeiras a partir de **mensagens de texto coloquiais, áudios ou fotos de recibos**, usando a API do Google Gemini para extrair automaticamente o valor e a categoria de cada gasto.

> Projeto Final de Graduação — Engenharia da Computação, PUC-Rio.
> Autor: Alexandre Gouveia Sanson · Orientador: Prof. Sérgio Colcher

## Funcionalidades

- **Registro multimodal:** envie "gastei 51 reais no mercado" por texto, grave um áudio ou fotografe a nota fiscal — o bot extrai valor e categoria via Gemini 2.5 Flash.
- **Confirmação interativa:** antes de salvar, o bot exibe os dados extraídos com botões *Confirmar / Editar / Cancelar*. A edição permite corrigir o valor (teclado numérico inline) ou a categoria.
- **Notas fiscais:** para fotos com múltiplos itens, o bot soma o total e subtrai descontos.
- **Relatórios:** o comando `/consulta` gera um gráfico de pizza dos gastos por categoria no mês selecionado, entregue direto na conversa.
- **Multiusuário:** transações persistidas em PostgreSQL, com suporte a múltiplos usuários simultâneos (arquitetura assíncrona via `asyncio`).

As transações são classificadas em seis categorias predefinidas: **Serviços · Viagens · Mercado · Restaurantes · Contas · Outros**.

## Arquitetura

```
Usuário (Telegram)
      │  texto · voz · imagem
      ▼
┌─────────────────────────────────────────────┐
│  main.py — interface e orquestração         │
│  (python-telegram-bot, long polling)        │
├──────────────────────┬──────────────────────┤
│  llm.py              │  dbmanager.py        │
│  extração com IA     │  persistência e      │
│  (Google Gemini,     │  relatórios          │
│  assíncrono)         │  (psycopg2, pandas,  │
│                      │  matplotlib)         │
└──────────┬───────────┴──────────┬───────────┘
           ▼                      ▼
     Google Gemini API       PostgreSQL
```

| Módulo | Responsabilidade |
|---|---|
| `main.py` | Handlers do Telegram, ciclo de vida das transações, estado de sessão |
| `llm.py` | Extração de `{value, category}` a partir de texto, áudio e imagem (schema Pydantic) |
| `dbmanager.py` | Registro de usuários/transações e geração de gráficos em memória |

## Pré-requisitos

- Python 3.10+ (o código usa `match/case`)
- PostgreSQL em execução local
- Uma conta no Telegram e um bot criado via [@BotFather](https://t.me/BotFather)
- Uma chave da [API do Google Gemini](https://ai.google.dev/gemini-api/docs)

## Instalação

**1. Clone o repositório e instale as dependências:**

```bash
git clone https://github.com/ags1999/TCC.git
cd TCC
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Crie o banco de dados e as tabelas:**

```sql
CREATE DATABASE "ledgerBotDB";

\c ledgerBotDB

CREATE TABLE users (
    user_id  BIGINT PRIMARY KEY,
    username VARCHAR(255)
);

CREATE TABLE transactions (
    transactions_id UUID PRIMARY KEY,
    user_id         BIGINT REFERENCES users(user_id),
    value           INTEGER NOT NULL,          -- em centavos
    category        VARCHAR(50) NOT NULL,
    date            TIMESTAMP WITH TIME ZONE,
    description     TEXT
);
```

> **Nota:** a string de conexão está definida em `dbmanager.py`
> (`dbname=ledgerBotDB user=alexandre`). Ajuste o usuário/host conforme o
> seu ambiente local.

**3. Configure as credenciais** em um arquivo `.env` na raiz do projeto:

```env
TELEGRAM_API_TOKEN=seu_token_do_botfather
GEMINI_API_KEY=sua_chave_da_api_gemini
```

**4. Execute o bot:**

```bash
python main.py
```

O bot opera via *long polling* — não é necessário servidor público nem HTTPS. Abra a conversa com o seu bot no Telegram, toque em **INICIAR** e envie um gasto.

## Uso

| Comando / Entrada | Ação |
|---|---|
| `/start` | Registra o usuário e exibe as boas-vindas |
| `/help` | Lista comandos e funcionalidades |
| `/consulta` | Seleciona ano e mês e gera o gráfico de gastos |
| Texto (ex.: *"Gastei 51 reais no mercado"*) | Extrai e propõe a transação |
| Mensagem de voz | Idem, via reconhecimento de fala |
| Foto de recibo/nota fiscal | Idem, somando itens e aplicando descontos |

Os valores são manipulados internamente **em centavos** (inteiros), evitando imprecisão de ponto flutuante. No teclado de edição de valor, digite os centavos: `5 1 0 0` → R$ 51,00.

## Testes

A suíte usa `pytest` + `unittest.mock`, com 100% de cobertura de código:

```bash
pytest --cov=. --cov-report=term-missing
```

> Os testes mockam as chamadas à API Gemini e as operações de banco, mas o
> `import` de `dbmanager.py` abre uma conexão real com o PostgreSQL — é
> necessário que o banco esteja acessível para a coleta dos testes.

## Tecnologias

[python-telegram-bot](https://python-telegram-bot.readthedocs.io/) · [google-genai](https://ai.google.dev/gemini-api/docs) (Gemini 2.5 Flash) · [psycopg2](https://www.psycopg.org/docs/) · [pandas](https://pandas.pydata.org/) · [matplotlib](https://matplotlib.org/) · [Pydantic](https://docs.pydantic.dev/) · [pytest](https://docs.pytest.org/)

## Limitações conhecidas

Este é um protótipo acadêmico. As principais limitações (detalhadas no relatório) incluem: conexão única com o banco criada na importação do módulo, estado de sessão em memória volátil, timeout fixo de 30 s nas chamadas à API, campo `description` ainda não preenchido pelo fluxo de extração e ausência de autenticação além do `user_id` do Telegram.

## Licença

Projeto acadêmico desenvolvido como requisito parcial para a obtenção do título de Engenheiro de Computação (PUC-Rio, 2026).