# 📦 Discord LATAM Patch Bot

Um bot de Discord criado para monitorar o fórum oficial do servidor **LATAM** de Ragnarok Online no site **divine-pride.net**, buscando por novos tópicos de changelog e postando automaticamente em um canal do Discord.

---

## ✨ Funcionalidades

- 🔍 **Monitora o fórum LATAM** a cada 5 minutos (ou intervalo configurável)
- 📢 **Posta automaticamente** o changelog mais recente no canal configurado
- 📌 Exibe:
  - Título e link do tópico
  - Lista de itens adicionados
  - Texto formatado com até 1500 caracteres por mensagem
  - Imagens relacionadas
  - Alerta adicional caso existam seções "Changed"
- ✅ Mantém histórico de tópicos postados para evitar duplicação
- 🌐 Inclui uma pequena API Flask (`/`) para manter o bot vivo com UptimeRobot ou serviços similares
- ⚙️ Preparado para deploy no [Replit](https://replit.com) com integração GitHub

---

## 🚀 Como rodar

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/discord-latam-bot.git
cd discord-latam-bot
```

### 2. Crie um ambiente virtual (opcional)

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o `.env`

Crie um arquivo `.env` com os seguintes valores:

```
TOKEN=seu_token_do_discord
API_KEY=sua_chave_da_api_divine_pride
CHANNEL_ID=ID_do_canal_do_discord
```

### 5. Rode o bot

```bash
python main.py
```

---

## 🧠 Como funciona

- O bot acessa o fórum `https://www.divine-pride.net/forum/index.php?/forum/6-changelog/`
- Procura por novos tópicos com o título contendo “LATAM changelog”
- Se encontrar um novo:
  - Faz o parsing do conteúdo HTML
  - Detecta seções como `Added` e `Changed`
  - Extrai textos, imagens e IDs de itens
  - Publica o conteúdo no Discord de forma formatada
- Uma flag `FORCE_ONCE` permite forçar o envio do último patch mesmo se ele já foi postado
- Um `set()` chamado `posted_links` mantém o controle do que já foi enviado

---

## 🛡 Segurança

- NUNCA coloque seu token diretamente no código
- Use o `.env` e adicione ele ao `.gitignore`:
  ```gitignore
  .env
  __pycache__/
  *.pyc
  ```

---

## 🧩 Tecnologias usadas

- [Discord.py](https://discordpy.readthedocs.io/)
- [Requests](https://docs.python-requests.org/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- [Flask](https://flask.palletsprojects.com/)
- [dotenv](https://pypi.org/project/python-dotenv/)

---

## 🕒 Deploy no Replit com UptimeRobot

- O bot inclui uma rota HTTP (`/`) com Flask
- O Replit pode manter o processo vivo
- Use o [UptimeRobot](https://uptimerobot.com/) para pingar a URL a cada 5 minutos
- Exemplo de URL: `https://seu-projeto.replit.app/`

---

## 🤖 Desenvolvido por

Guilda **Tadala Filhos 💧** — Ragnarok LATAM  
Contribuições são bem-vindas! ✨