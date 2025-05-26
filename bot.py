import discord
import requests
from bs4 import BeautifulSoup
import asyncio
import re
from flask import Flask
from threading import Thread
import json
import os

# —————————————————————————————————————————————
# Persistência de comentários já processados
# —————————————————————————————————————————————
POSTED_COMMENTS_FILE = "posted_comments.json"

def load_posted_comments():
    if os.path.exists(POSTED_COMMENTS_FILE):
        with open(POSTED_COMMENTS_FILE, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_posted_comments(ids):
    with open(POSTED_COMMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, indent=2)

posted_comment_ids = load_posted_comments()

# —————————————————————————————————————————————
# Configurações do bot
# —————————————————————————————————————————————
TOKEN = "INSERT_TOKEN"
CHANNEL_ID = INSERT_DISCORD_CHANNEL_ID
CHECK_INTERVAL = 300
BASE_URL = "https://www.divine-pride.net"
API_KEY = "INSERT_DIVINE_PRIDE_API_KEY"
SERVER = "INSERT_SERVER" #ex: bRO, kRO, latam, iRO

intents = discord.Intents.default()
client = discord.Client(intents=intents)

posted_comment_ids = load_posted_comments()
FORCE_ONCE = False

# —————————————————————————————————————————————
# Keep-alive com Flask + Thread
# —————————————————————————————————————————————
app = Flask('')

@app.route('/')
def home():
    return "Estou viva!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()


# —————————————————————————————————————————————
# Funções utilitárias
# —————————————————————————————————————————————
def clean_ro_content(text):
    text = re.sub(r'\^[0-9A-Fa-f]{6}', '', text)
    text = re.sub(r'-{20,}', '─' * 20, text)
    return text.strip()

def get_latest_latam_topic():
    forum_url = f"{BASE_URL}/forum/index.php?/forum/6-changelog/"
    resp = requests.get(forum_url)
    if resp.status_code != 200:
        print(f"❌ Falha ao acessar o fórum: {resp.status_code}")
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.select("a[href*='topic/']"):
        title = a.get_text(strip=True)
        if "LATAM changelog" in title:
            href = a["href"]
            full_url = href if href.startswith("http") else BASE_URL + href
            return title, full_url
    return None

def check_for_changed_sections(post):
    # detecta qualquer <span style="...underline..."><font size="3">Changed</font>
    return bool(post.select_one('span[style*="underline"] font[size="3"]:contains("Changed"), span[style*="underline"] font[size="3"]:contains("Alterado")'))

def process_content(post):
    id_pattern = re.compile(r"Id:\s*\((\d+)\)")
    elements = []
    current_section = "Added"
    current_item = {"id": None, "text": [], "images": [], "section": current_section}

    def detect_section(element):
        nonlocal current_section
        if element.name == 'span' and 'underline' in element.get('style', ''):
            font = element.find('font', size="3")
            if font:
                sec = font.get_text(strip=True).lower()
                if sec in ('added', 'changed', 'alterado'):
                    current_section = sec.capitalize()
                    return True
        return False

    for el in post.descendants:
        if detect_section(el):
            if current_item["id"] or current_item["text"] or current_item["images"]:
                current_item["section"] = current_section
                elements.append(current_item)
                current_item = {"id": None, "text": [], "images": [], "section": current_section}
            continue

        if el.name == 'img':
            img = el.get('src', '')
            if img:
                current_item["images"].append(img)

        elif isinstance(el, str):
            txt = clean_ro_content(el)
            if txt:
                m = id_pattern.search(txt)
                if m:
                    if current_item["id"] or current_item["text"] or current_item["images"]:
                        current_item["section"] = current_section
                        elements.append(current_item)
                    current_item = {"id": m.group(1), "text": [txt], "images": [], "section": current_section}
                else:
                    current_item["text"].append(txt)

        elif el.name == 'br':
            current_item["text"].append('\n')

    if current_item["id"] or current_item["text"] or current_item["images"]:
        current_item["section"] = current_section
        elements.append(current_item)

    return elements

# —————————————————————————————————————————————
# Evento on_ready: loop principal
# —————————————————————————————————————————————
@client.event
async def on_ready():
    print(f"✅ Bot logado como {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Canal não encontrado.")
        return

    global FORCE_ONCE
    while True:
        topic = get_latest_latam_topic()
        if topic:
            title, url = topic
            print(f"🔍 Tópico: {title} — {url}")
            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")
            posts = soup.select("div[data-commentid]")

            for post_div in posts:
                cid = post_div.get("data-commentid")
                if cid in posted_comment_ids and not FORCE_ONCE:
                    continue

                content = post_div.select_one(".ipsComment_content, .cPost_contentWrap, .post_body, .entry-content")
                if not content or not check_for_changed_sections(content):
                    continue

                # Processa e envia
                header = f"📢 **{title}**\n🔗 {url}#comment-{cid}"
                await channel.send(header)

                items = process_content(content)
                added = [i for i in items if i["section"] == "Added"]
                changed = [i for i in items if i["section"] == "Changed"]

                # Enviar cada item adicionado
                for item in added:
                    text = "\n".join(item["text"])
                    text = clean_ro_content(text)
                    if text:
                        block = f"```{text[:1500]}```"
                        await channel.send(block)
                    if item["images"]:
                        await channel.send("\n".join(item["images"][:4]))
                    await asyncio.sleep(1)

                # Aviso de changed
                if changed:
                    await channel.send("⚠️ *Este post contém alterações importantes.*")

                # Marca como processado
                posted_comment_ids.add(cid)
                save_posted_comments(posted_comment_ids)

            FORCE_ONCE = False

        await asyncio.sleep(CHECK_INTERVAL)

client.run(TOKEN)
