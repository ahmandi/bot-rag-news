import discord
import requests
from bs4 import BeautifulSoup
import asyncio
import re
from flask import Flask
from threading import Thread
import json
import os

POSTED_LINKS_FILE = "posted_links.json"

def load_posted_links():
    if os.path.exists(POSTED_LINKS_FILE):
        with open(POSTED_LINKS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return set(data)
            except json.JSONDecodeError:
                return set()
    return set()

def save_posted_links(links):
    with open(POSTED_LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(links), f, indent=2)


TOKEN = "INSERT_TOKEN"
CHANNEL_ID = DISCORD_CHANNEL_ID 
CHECK_INTERVAL = 300
BASE_URL = "https://www.divine-pride.net"
API_KEY = "INSERT_API_KEY" 
SERVER = "latam" 

intents = discord.Intents.default()
client = discord.Client(intents=intents)

posted_links = load_posted_links()
FORCE_ONCE = True

app = Flask('')

@app.route('/')
def home():
    return "Estou viva!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

def clean_ro_content(text):
    # Remove códigos de cor e linhas divisórias longas
    text = re.sub(r'\^[0-9A-Fa-f]{6}', '', text)
    text = re.sub(r'-{20,}', '─'*20, text)  # Substitui por linha mais clean
    return text.strip()

#def get_item_data(item_id):
#    url = f"{BASE_URL}/api/database/Item/{item_id}?apiKey={API_KEY}"
#    try:
#        response = requests.get(url, params={"server": SERVER})
#        return response.json() if response.status_code == 200 else None
#    except Exception as e:
#        print(f"❌ Erro na API: {e}")
#        return None

def get_latest_latam_topic():
    forum_url = f"{BASE_URL}/forum/index.php?/forum/6-changelog/"
    resp = requests.get(forum_url)
    if resp.status_code != 200:
        print(f"❌ Falha ao acessar o fórum: status {resp.status_code}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.select("a[href*='topic/']"):
        title = a.get_text(strip=True)
        if "LATAM changelog" in title:
            href = a["href"]
            full_url = href if href.startswith("http") else BASE_URL + href
            return (title, full_url)
    return None

def check_for_changed_sections(post):
    # Verifica tanto 'Changed' quanto 'Alterado' (caso haja versão em PT)
    return any(
        'changed' in span.get_text(strip=True).lower()
        for span in post.select('span[style*="underline"] font[size="3"]')
    )

def process_content(post):
    id_pattern = re.compile(r"Id:\s*\((\d+)\)")
    elements = []
    current_section = "Added"  # Seção padrão
    current_item = {"id": None, "text": [], "images": [], "section": current_section}

    # Função para detectar cabeçalhos
    def detect_section(element):
        nonlocal current_section
        if element.name == 'span' and 'underline' in element.get('style', ''):
            font = element.find('font', size="3")
            if font:
                section = font.get_text(strip=True).lower()
                if section in ['added', 'changed']:
                    current_section = section.capitalize()
                    return True
        return False

    for element in post.descendants:
        if detect_section(element):
            if current_item["id"] or current_item["text"] or current_item["images"]:
                current_item["section"] = current_section
                elements.append(current_item)
                current_item = {"id": None, "text": [], "images": [], "section": current_section}
            continue

        if element.name == 'img':
            img_url = element.get('src', '')
            if img_url:
                current_item["images"].append(img_url)

        elif isinstance(element, str):
            text = clean_ro_content(element)
            if text:
                id_match = id_pattern.search(text)
                if id_match:
                    if current_item["id"] or current_item["text"] or current_item["images"]:
                        current_item["section"] = current_section
                        elements.append(current_item)
                    current_item = {
                        "id": id_match.group(1),
                        "text": [text],
                        "images": [],
                        "section": current_section
                    }
                else:
                    current_item["text"].append(text)

        elif element.name == 'br':
            current_item["text"].append('\n')

    if current_item["id"] or current_item["text"] or current_item["images"]:
        current_item["section"] = current_section
        elements.append(current_item)

    return elements

@client.event
async def on_ready():
    print(f"✅ Bot logado como {client.user}")

    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Erro: Canal não encontrado.")
        return

    global FORCE_ONCE

    while True:
        try:
            topic = get_latest_latam_topic()
            if topic:
                title, url = topic
                print(f"🔍 Verificando tópico: {title} ({url})")

                if url in posted_links and not FORCE_ONCE:
                    print("ℹ️ Tópico já foi processado.")
                else:
                    resp = requests.get(url)
                    soup = BeautifulSoup(resp.text, "html.parser")
                    post = soup.select_one(".ipsPost_content, .cPost_contentWrap, .post_body, .entry-content")

                    if not post:
                        print("⚠️ Nenhum post encontrado.")
                        continue

                    has_changed = check_for_changed_sections(post)
                    items = process_content(post)

                    # Construir cabeçalho
                    header = f"📢 **{title}**\n🔗 {url}"

                    await channel.send(header)
                    
                    added_items = [item for item in items if item["section"] == "Added"]
                    changed_items = [item for item in items if item["section"] == "Changed"]
                    
                    # Processar cada item
                    for item in added_items:
                        #item_data = get_item_data(item["id"]) if item["id"] else None
                        message = []

                        #if item_data:
                        #    message.append(f"**{item_data.get('name', 'Item Desconhecido')}**")
                        #    if desc := item_data.get('description'):
                        #        message.append(f"*{desc}*")

                        message.extend(item["text"])

                        full_text = '\n'.join(message)
                        full_text = clean_ro_content(full_text)

                        if full_text:
                            formatted = f"```diff\n{full_text[:1500]}```" if len(full_text) > 1500 else f"```{full_text}```"
                            await channel.send(formatted)

                        # Enviar imagens agrupadas
                        if item["images"]:
                            await channel.send('\n'.join(item["images"][:4]))  # Limite de 4 imagens por mensagem
                            await asyncio.sleep(0.5)

                        await asyncio.sleep(1)

                    posted_links.add(url)
                    save_posted_links(posted_links)

                    if changed_items:
                        warning = (
                            "\n\n⚠️ **ATENÇÃO:** Este post pode conter alterações importantes! "
                            "Consulte o link original para detalhes completos das mudanças."
                        )
                        await channel.send(warning)
                        
                    FORCE_ONCE = False

            else:
                print("⏳ Nenhum tópico LATAM encontrado.")

        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

client.run(TOKEN)
