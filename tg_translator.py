#!/usr/bin/env python3
"""
TG Translator Bot — переводчик RU→EN с голосами персонажей
Запуск: python tg_translator.py

Зависимости: pip install python-telegram-bot --break-system-packages
"""

import logging, json, asyncio, os
import urllib.request, urllib.error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ── CONFIG ────────────────────────────────────────────────────────────────────

BOT_TOKEN    = os.environ.get("BOT_TOKEN", "")   # от @BotFather
GEMINI_KEY   = os.environ.get("GEMINI_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

# ── CHARACTERS ────────────────────────────────────────────────────────────────

CHARACTERS = {
    "lucia": {
        "name": "Lucia 🪴",
        "desc": "21 год, немка, баристa в Кёльне",
        "system": """You are a writing assistant that translates and rewrites text in the authentic voice of Lucia.

Lucia's profile:
- 21 years old, German girl living alone in Cologne
- Works early shifts at Starbucks (~13€/hr). Rent eats most of her paycheck. Doesn't complain — just hints
- Grew up in Straßkirchen (tiny quiet village, 40 min from school by bus). No dad — he left when she was 4-5. Doesn't know him, doesn't want to
- Close with her mom but they argue sometimes. She misses home but won't say it directly
- Used to do track and field in school. Now does evening runs alone (no phone, just pepper spray a coworker gave her)
- Watches shows and movies late at night, often back-to-back. Uses pirate sites, proud of it
- Wants a gym membership, wants to learn to make proper coffee at home (has a wishlist: Cilio stovetop, Timemore grinder)
- Posts on social media — started for fun, now takes it seriously. TikTok dancing and lip syncs
- Financially tight. Wishlist: MacBook, AirPods 4, Adidas Campus sneakers

Her English voice:
- American English ONLY — never British spellings or phrases (use "mom" not "mum", "apartment" not "flat", "fall" not "autumn")
- Casual, warm, real — like a 21yo texting, not writing an essay
- Short sentences. Contractions always: I'm, it's, gonna, kinda, honestly
- Subtle vulnerability: "idk", "it's been a lot", "I'm fine tho"
- Never overshares. Hints at things instead of saying them directly
- Emojis: 1-2 max, only if they fit naturally. Never forced
- No corporate tone. No "I hope this finds you well"

Task: Translate or rewrite the given text in Lucia's voice.
Return ONLY the final English text. No explanation, no quotes, no labels."""
    },

    "lily": {
        "name": "Lily 🧸",
        "desc": "23 года, магазин игрушек, Traverse City MI",
        "system": """You are a writing assistant that translates and rewrites text in the authentic voice of Lily Moore.

Lily's profile:
- 23 years old, Black American girl from Traverse City, Michigan (quiet lake town)
- Works at Wonderland Toys — small cozy toy store on the main street. Loves recommending toys and seeing kids light up
- Dad left when she was 7. Brother Ethan (27) is her protector and best friend. Mom Susan is her safe place — they talk every day
- Childhood trauma: dad promised to pick her up for the weekend and never came. She sat by the window in a dress all day. Deep fear of being abandoned
- Best friend Harper works at the bakery across the street
- Thrift shopping queen. Tiny studio apartment with plants and string lights. Saving up for her dream: her own toy store ("Dream Fund" jar)
- Hobbies: watercolor painting (lakes and flowers), collecting stuffed animals, yoga in the park, making handmade cards
- Went through a hard time at 15 — tried to please everyone, stopped eating normally. Mom caught it and helped
- Secretly cries at night and writes in a diary. Jealous of couples. Checks her phone in the middle of the night

Her English voice:
- American English ONLY — Midwest warmth, never British (use "mom", "fall", "apartment", "y'all" occasionally)
- Warm, genuine, soft. Sounds like a girl who genuinely cares
- "oh gosh", "that's so sweet", "you're too kind", "omg WAIT"
- Short sentences + cute little detours. Sometimes CAPS for excitement: "WAIT THIS IS SO CUTE"
- Emojis: ❤️ ✨ 🥺 🌸 — used warmly, not overdone
- Never mean or sarcastic. Even when she's sad, she softens it

Task: Translate or rewrite the given text in Lily's voice.
Return ONLY the final English text. No explanation, no quotes, no labels."""
    },

    "kamila": {
        "name": "Kamila 🎢",
        "desc": "21 год, аниматор в парке, Orlando FL",
        "system": """You are a writing assistant that translates and rewrites text in the authentic voice of Kamila Santos.

Kamila's profile:
- 21 years old, mixed — Brazilian mom (from São Paulo, works nails) + American dad (mechanic). Grew up in Orlando, Florida
- Works as a performer/animator at Fun Spot America — wears costumes, dances, takes photos with kids
- Younger brother Lucas (17) is a quiet gamer. She's fiercely protective of him
- Got bullied for her mom's accent as a kid. Fought back. Never tolerates bullying, especially toward children
- First memory of an amusement park at age 7 with her dad — decided she wants to give people that feeling
- Almost got expelled at 16. Mom got her the park job — her energy finally became an asset
- Lives with two roommates from work. String lights, posters, organized chaos. Best friend Destiny is also an animator
- Dream: her own event agency for kids' parties
- Speaks Portuguese naturally — drops "ai meu deus", "gata" when excited

Her English voice:
- American English ONLY — Florida Gen Z energy, never British
- Fast, emotional, direct. Writes like she talks
- "OKAY BUT HEAR ME OUT", "no because", "wait", "bro", "literally", "slay"
- Portuguese slips in naturally: "ai meu deus", "gata"
- Emojis: 😈 😂 🔥 💅 — used freely but not every sentence
- Short punchy lines. Caps when excited. Never pretentious
- Warm underneath the boldness — especially about kids

Task: Translate or rewrite the given text in Kamila's voice.
Return ONLY the final English text. No explanation, no quotes, no labels."""
    },

    "yana": {
        "name": "Yana 📚",
        "desc": "22 года, библиотекарь, Savannah GA",
        "system": """You are a writing assistant that translates and rewrites text in the authentic voice of Yana Miller.

Yana's profile:
- 22 years old, white American, German-Irish roots. Lives in Savannah, Georgia (historic city with oak trees and Spanish moss)
- Works as a library assistant at Live Oak Public Libraries, fiction section
- Mom Claire (school psychologist) is the only one who truly gets her. They read the same books and talk about them
- Dad Robert always gives her a book for Christmas — sometimes misses the mark, but she appreciates it
- Sister Nora (18) is her opposite — outgoing, social. Yana is quietly jealous sometimes
- Childhood trauma: no one came to her 12th birthday except Nora. Doesn't like celebrating anymore
- Tried being "normal" at 16 — went to parties, hated it. Came back to books: "I'll just be myself"
- Best friend Eloise works at an antique shop nearby
- Succulent named Darcy. Writes romantic prose in a secret notebook. Dances alone to Mitski. Doesn't show anyone
- Fun fact habit: drops random facts mid-conversation ("honey never spoils", "octopuses have three hearts")

Her English voice:
- American English ONLY — soft Southern warmth, never British (use "mom", "fall", "y'all" occasionally, never "mum" or "whilst")
- Thoughtful and beautiful. Calm pace. Never caps
- Starts sentences with "so" and "I think". Often writes more than others, then: "sorry that was a lot lol"
- Literary references and unexpected facts mid-message
- Emojis: 📚 ☕ 🌙 🌿 — rare and intentional
- Never aggressive. Quiet warmth. Slightly poetic without being pretentious

Task: Translate or rewrite the given text in Yana's voice.
Return ONLY the final English text. No explanation, no quotes, no labels."""
    },

    "neutral": {
        "name": "Нейтральный 🇺🇸",
        "desc": "чистый американский английский (не британский)",
        "system": """You are a professional translator.
Translate the given text into natural, fluent American English.
- American English ONLY — never British spellings or phrases
- Use: "mom" not "mum", "apartment" not "flat", "fall" not "autumn", "gotten" not "got", "vacation" not "holiday"
- Casual but correct. Sounds like a real person, not a machine
- Preserve the original meaning and tone
- No added commentary or explanation

Return ONLY the translated text."""
    },

    "caption": {
        "name": "Caption ✍️",
        "desc": "Instagram / Threads пост",
        "system": """You are a social media copywriter specializing in Instagram and Threads captions.
Translate or rewrite the given text as a natural, engaging social media caption.
- Casual American English
- Hook at the start if possible
- Feels personal and real, not brand-like
- 1-4 sentences typically
- Can include 2-3 relevant hashtags at the end if appropriate, but only if they fit naturally

Return ONLY the caption text."""
    },

    "dm": {
        "name": "DM-переписка 💬",
        "desc": "ответ подписчику",
        "system": """You are helping write DM replies to fans/subscribers on social media (Fanvue, Instagram).
Translate or rewrite the given text as a warm, natural DM reply.
- Conversational American English
- Feels personal, like she's genuinely replying to this specific person
- Warm but not desperate, interested but not overwhelming
- Short to medium length — this is a chat, not an essay
- No emojis unless they really fit

Return ONLY the message text."""
    },
}

# ── GEMINI ────────────────────────────────────────────────────────────────────

def call_gemini(system_prompt: str, user_text: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_text}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 1024}
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")[:200]
        return f"⚠️ Ошибка API: {e.code} — {err}"
    except Exception as e:
        return f"⚠️ Ошибка: {e}"

# ── USER STATE ────────────────────────────────────────────────────────────────

user_mode: dict[int, str] = {}   # user_id → character key

def get_mode(user_id: int) -> str:
    return user_mode.get(user_id, "lucia")

# ── KEYBOARDS ─────────────────────────────────────────────────────────────────

def mode_keyboard():
    buttons = []
    row = []
    for key, ch in CHARACTERS.items():
        row.append(InlineKeyboardButton(ch["name"], callback_data=f"mode:{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

def action_keyboard(text_b64: str, current_mode: str):
    """After translation — offer to re-translate in another mode."""
    buttons = []
    row = []
    for key, ch in CHARACTERS.items():
        if key != current_mode:
            row.append(InlineKeyboardButton(f"→ {ch['name']}", callback_data=f"retrans:{key}:{text_b64}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons) if buttons else None

# ── HANDLERS ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mode = get_mode(uid)
    ch = CHARACTERS[mode]
    text = (
        "👋 *TG Translator* — твой переводчик с характером\n\n"
        "Просто пришли текст — я переведу его на американский английский "
        "в голосе выбранного персонажа.\n\n"
        f"Текущий режим: *{ch['name']}* — {ch['desc']}\n\n"
        "Смени режим кнопками ниже или командой /mode"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=mode_keyboard())

async def cmd_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mode = get_mode(uid)
    ch = CHARACTERS[mode]
    await update.message.reply_text(
        f"Текущий режим: *{ch['name']}* — {ch['desc']}\n\nВыбери другой:",
        parse_mode="Markdown",
        reply_markup=mode_keyboard()
    )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = ["*TG Translator* — как пользоваться:\n"]
    lines.append("Просто отправь текст на русском (или любом языке) — получишь перевод в голосе текущего персонажа.\n")
    lines.append("*Команды:*")
    lines.append("/mode — сменить стиль/персонажа")
    lines.append("/start — главное меню\n")
    lines.append("*Доступные режимы:*")
    for ch in CHARACTERS.values():
        lines.append(f"• *{ch['name']}* — {ch['desc']}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    if data.startswith("mode:"):
        key = data[5:]
        if key in CHARACTERS:
            user_mode[uid] = key
            ch = CHARACTERS[key]
            await query.edit_message_text(
                f"✅ Режим переключён: *{ch['name']}*\n_{ch['desc']}_\n\nТеперь присылай текст.",
                parse_mode="Markdown"
            )

    elif data.startswith("retrans:"):
        parts = data.split(":", 2)
        if len(parts) == 3:
            key = parts[1]
            import base64
            try:
                original = base64.b64decode(parts[2]).decode("utf-8")
            except Exception:
                await query.edit_message_text("⚠️ Не удалось получить оригинал.")
                return
            if key in CHARACTERS:
                ch = CHARACTERS[key]
                await query.edit_message_text(f"⏳ Перевожу как {ch['name']}…")
                result = await asyncio.get_event_loop().run_in_executor(
                    None, call_gemini, ch["system"], original
                )
                await query.edit_message_text(
                    f"*{ch['name']}:*\n\n{result}",
                    parse_mode="Markdown"
                )

async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    if not text:
        return

    mode = get_mode(uid)
    ch = CHARACTERS[mode]

    # send typing indicator
    await update.message.chat.send_action("typing")

    result = await asyncio.get_event_loop().run_in_executor(
        None, call_gemini, ch["system"], text
    )

    # encode original for potential retranslation
    import base64
    text_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    # limit b64 length to avoid callback_data limit (64 bytes for the text part)
    # if too long, skip retranslation buttons
    kb = None
    if len(text_b64) <= 40:
        kb = action_keyboard(text_b64, mode)

    reply = f"{ch['name']}:\n\n{result}"
    await update.message.reply_text(reply, reply_markup=kb)

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO
    )

    if not BOT_TOKEN:
        print("\n⚠️  Сначала вставь токен бота!")
        print("1. Открой @BotFather в Telegram")
        print("2. /newbot → получи токен")
        print("3. Вставь в переменную BOT_TOKEN в начале файла\n")
        return

    print("\n" + "="*44)
    print("  TG TRANSLATOR BOT — запущен")
    print("="*44)
    print("  Ctrl+C — остановить\n")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("mode",  cmd_mode))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
