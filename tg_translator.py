#!/usr/bin/env python3
"""
TG Translator Bot — переводчик RU→EN + генератор промптов для NB Pro Edit
"""

import logging, json, asyncio, os, base64, urllib.request, urllib.error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ── CONFIG ────────────────────────────────────────────────────────────────────

BOT_TOKEN    = os.environ.get("BOT_TOKEN", "")
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
Return ONLY the final English text. No explanation, no quotes, no labels.""",
        "visual": """Character: Lucia, 21-year-old German girl.
Appearance: slim athletic build, light skin with natural glow, light brown or blonde hair (shoulder-length to mid-back, natural texture, often slightly messy), light eyes (green or blue-grey), minimal to no makeup, natural freckles sometimes visible, no heavy jewelry.
Wardrobe: white or grey fitted t-shirt, black or grey sweatpants, black shorts, jeans (medium wash), sports bra, spaghetti strap top. Adidas or Nike sneakers. Simple, casual, real-girl style — never overdressed.
Environment: small cozy apartment in Cologne — IKEA-style furniture, warm lamp light, wooden floors, plant on windowsill, unmade bed with neutral duvet, coffee mug on desk. Or: morning Starbucks uniform (black apron), or Cologne street (overcast European sky, cobblestones).
Vibe: authentic, slightly tired but warm. Girlfriend-next-door aesthetic. Not posed — candid."""
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
Return ONLY the final English text. No explanation, no quotes, no labels.""",
        "visual": """Character: Lily Moore, 23-year-old Black American girl.
Appearance: warm brown skin, natural hair (coils or loose twists, sometimes in buns or half-up), soft round facial features, warm brown eyes, minimal natural makeup, soft lip color sometimes. Warm and approachable look.
Wardrobe: cozy thrifted pieces — oversized vintage sweaters, floral dresses, denim overalls, warm earth tones and pastels (sage green, dusty rose, cream). Worn-in Converse or Mary Janes. Accessories: small gold earrings, scrunchies, canvas tote bags.
Environment: tiny cozy studio apartment — string lights, plants everywhere, stuffed animals on shelves, watercolor paintings on the wall, a mason jar labeled "Dream Fund". Or: Wonderland Toys store (colorful, warm lighting, wooden shelves with toys). Or: lakeside in Traverse City (golden hour, trees, peaceful water).
Vibe: warm, soft, cottagecore-adjacent. Like a hug in visual form."""
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
Return ONLY the final English text. No explanation, no quotes, no labels.""",
        "visual": """Character: Kamila Santos, 21-year-old mixed Brazilian-American girl.
Appearance: warm tan/olive skin, dark brown wavy or curly hair (medium length, often down or in a messy half-up), dark expressive eyes, natural bold features, sometimes colorful eyeshadow or bold lip. Energetic and expressive look.
Wardrobe: Florida casual — crop tops, high-waisted shorts or jeans, tank tops, bright colors and patterns (coral, yellow, white), Fun Spot uniform (when at work: colorful polo + shorts), platform sneakers or sandals. Gold hoop earrings always. Sometimes a cap backwards.
Environment: shared apartment in Orlando — colorful, posters of Disney and Brazilian artists, fairy lights, sneaker collection visible. Or: Fun Spot America park (bright rides, sunny Florida sky, kids running around). Or: Orlando street (palm trees, warm golden light, vibrant atmosphere).
Vibe: high energy, fun, unapologetically herself. Florida girl aesthetic."""
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
- American English ONLY — soft Southern warmth, never British
- Thoughtful and beautiful. Calm pace. Never caps
- Starts sentences with "so" and "I think". Often writes more than others, then: "sorry that was a lot lol"
- Literary references and unexpected facts mid-message
- Emojis: 📚 ☕ 🌙 🌿 — rare and intentional
- Never aggressive. Quiet warmth. Slightly poetic without being pretentious

Task: Translate or rewrite the given text in Yana's voice.
Return ONLY the final English text. No explanation, no quotes, no labels.""",
        "visual": """Character: Yana Miller, 22-year-old white American girl.
Appearance: fair skin, light freckles, soft features, hazel or green eyes, medium brown or auburn hair (often in a loose bun or down with natural waves), minimal makeup — maybe just mascara or tinted lip balm. Quiet, thoughtful look.
Wardrobe: dark academia / cozy librarian — oversized knit sweaters, long cardigans, corduroy or linen pants, midi skirts with tights, forest green / burgundy / cream / navy palette. Worn-in Chelsea boots or loafers. Small stud earrings, sometimes a delicate chain necklace. Always carrying a book or tote bag.
Environment: Live Oak Public Library (warm wood shelves, afternoon light through tall windows, quiet reading nooks). Or: her apartment — stacks of books everywhere, one succulent on the windowsill (named Darcy), soft lamp light, open notebook, mug of tea. Or: Savannah street (Spanish moss on oak trees, historic brick buildings, golden afternoon light).
Vibe: quiet, warm, literary. Dark academia meets Southern softness."""
    },

    "neutral": {
        "name": "Нейтральный 🇺🇸",
        "desc": "чистый американский английский",
        "system": """You are a professional translator.
Translate the given text into natural, fluent American English.
- American English ONLY — never British spellings or phrases
- Use: "mom" not "mum", "apartment" not "flat", "fall" not "autumn", "gotten" not "got", "vacation" not "holiday"
- Casual but correct. Sounds like a real person, not a machine
- Preserve the original meaning and tone
- No added commentary or explanation

Return ONLY the translated text.""",
        "visual": None
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

Return ONLY the caption text.""",
        "visual": None
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

Return ONLY the message text.""",
        "visual": None
    },
}

# Characters that support image generation (have visual profile)
GEN_CHARACTERS = {k: v for k, v in CHARACTERS.items() if v.get("visual")}

# ── GEMINI ────────────────────────────────────────────────────────────────────

def call_gemini(system_prompt: str, user_text: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_text}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 1024}
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")[:200]
        return f"⚠️ Ошибка API: {e.code} — {err}"
    except Exception as e:
        return f"⚠️ Ошибка: {e}"


def call_gemini_vision(image_bytes: bytes, text_prompt: str) -> str:
    """Gemini Vision — анализ изображения."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}},
                {"text": text_prompt}
            ]
        }],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1500}
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")[:200]
        return f"⚠️ Ошибка API: {e.code} — {err}"
    except Exception as e:
        return f"⚠️ Ошибка: {e}"

# ── ПРОМПТ ГЕНЕРАТОР ──────────────────────────────────────────────────────────

VISION_EXTRACT_PROMPT = """Analyze this reference photo and extract ONLY the following technical elements. 
Ignore the person's face, identity, hair, skin, and clothing completely.

Extract and describe:
1. POSE & BODY POSITION: exact body positioning, posture, angle relative to camera, weight distribution, limb positions
2. CAMERA ANGLE: height (eye-level / low angle / high angle / overhead), distance (close-up / medium / full body), tilt
3. LIGHTING: quality (hard/soft), direction, color temperature (warm/cool/neutral), intensity, shadow style, atmosphere
4. COMPOSITION: framing, rule of thirds or centered, what fills the frame
5. TECHNICAL FEEL: depth of field (background blur level), grain/noise level, overall photo mood

Be specific and technical. Output as a clean structured list. No commentary."""


def build_gen_prompt(vision_analysis: str, character_key: str, extra_details: str = "") -> str:
    char = CHARACTERS[character_key]
    visual_profile = char["visual"]

    system = """You are a prompt engineer for Nano Banana Pro Edit (NB Pro Edit), an AI image generation model.
Your task: write a single ready-to-use image generation prompt.

You will receive:
1. TECHNICAL ANALYSIS of a reference photo (pose, lighting, camera — NOT the person)
2. CHARACTER PROFILE (who to generate instead)
3. Optional extra details from the user

Rules:
- Take pose, camera angle, lighting, composition FROM the technical analysis
- Take appearance, clothing, environment FROM the character profile
- If user provided extra details, apply them (they override defaults)
- Write as natural flowing sentences, 100-180 words
- End with exactly this quality line: "Sharp detailed eyes with clear natural iris texture, defined eyelashes, realistic eye whites. Natural skin texture, realistic hair strands. No beauty over-smoothing, no filters. Shot on iPhone 15 Pro, 24mm main camera, f/1.78 aperture, natural computational photography, slight optical vignetting, realistic sensor noise, auto white balance."
- Output ONLY the final prompt. Nothing else."""

    user_input = f"""TECHNICAL ANALYSIS FROM REFERENCE PHOTO:
{vision_analysis}

CHARACTER PROFILE:
{visual_profile}

USER EXTRA DETAILS:
{extra_details if extra_details else "None — use character defaults"}

Write the NB Pro Edit prompt now."""

    return call_gemini(system, user_input)

# ── USER STATE ────────────────────────────────────────────────────────────────

user_mode: dict[int, str] = {}       # user_id → translation character key
user_state: dict[int, str] = {}      # user_id → "translate" | "gen_select" | "gen_photo" | "gen_details"
user_gen_data: dict[int, dict] = {}  # user_id → {"char": key, "photo_id": file_id}

def get_mode(user_id: int) -> str:
    return user_mode.get(user_id, "lucia")

def get_state(user_id: int) -> str:
    return user_state.get(user_id, "translate")

# ── KEYBOARDS ─────────────────────────────────────────────────────────────────

def main_keyboard():
    """Main menu — translation characters + generation button."""
    buttons = []
    row = []
    for key, ch in CHARACTERS.items():
        row.append(InlineKeyboardButton(ch["name"], callback_data=f"mode:{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🎨 Генерация промпта", callback_data="gen:start")])
    return InlineKeyboardMarkup(buttons)


def gen_char_keyboard():
    """Character selection for generation mode."""
    buttons = []
    row = []
    for key, ch in GEN_CHARACTERS.items():
        row.append(InlineKeyboardButton(ch["name"], callback_data=f"gen_char:{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data="gen:cancel")])
    return InlineKeyboardMarkup(buttons)


def skip_details_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Пропустить (использовать дефолт)", callback_data="gen:skip_details")]
    ])


def after_gen_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Сгенерировать ещё раз", callback_data="gen:start")],
        [InlineKeyboardButton("↩️ В главное меню", callback_data="gen:cancel")]
    ])

# ── HANDLERS ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_state[uid] = "translate"
    mode = get_mode(uid)
    ch = CHARACTERS[mode]
    text = (
        "👋 *TG Translator* — переводчик + генератор промптов\n\n"
        "Пришли текст — переведу в голосе персонажа.\n"
        "Нажми *🎨 Генерация промпта* — создам промпт для NB Pro Edit по твоему рефу.\n\n"
        f"Текущий режим перевода: *{ch['name']}* — {ch['desc']}"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())


async def cmd_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_state[uid] = "translate"
    mode = get_mode(uid)
    ch = CHARACTERS[mode]
    await update.message.reply_text(
        f"Текущий режим: *{ch['name']}* — {ch['desc']}\n\nВыбери другой:",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = ["*TG Translator + Генератор* — как пользоваться:\n"]
    lines.append("*Перевод:* просто пришли текст → получишь перевод в голосе персонажа\n")
    lines.append("*Генерация промпта для NB Pro Edit:*")
    lines.append("1. Нажми 🎨 Генерация промпта")
    lines.append("2. Выбери персонажа")
    lines.append("3. Пришли реф-фото (любое фото с нужной позой/светом)")
    lines.append("4. Добавь детали или пропусти")
    lines.append("5. Получи готовый промпт → вставь в NB Pro Edit\n")
    lines.append("*Команды:* /mode /start /help")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    # ── Translation mode switch ──
    if data.startswith("mode:"):
        key = data[5:]
        if key in CHARACTERS:
            user_mode[uid] = key
            user_state[uid] = "translate"
            ch = CHARACTERS[key]
            await query.edit_message_text(
                f"✅ Режим переключён: *{ch['name']}*\n_{ch['desc']}_\n\nТеперь присылай текст.",
                parse_mode="Markdown"
            )

    # ── Generation flow ──
    elif data == "gen:start":
        user_state[uid] = "gen_select"
        await query.edit_message_text(
            "🎨 *Генерация промпта для NB Pro Edit*\n\nВыбери персонажа:",
            parse_mode="Markdown",
            reply_markup=gen_char_keyboard()
        )

    elif data == "gen:cancel":
        user_state[uid] = "translate"
        user_gen_data.pop(uid, None)
        mode = get_mode(uid)
        ch = CHARACTERS[mode]
        await query.edit_message_text(
            f"↩️ Вернулся в режим перевода.\nТекущий: *{ch['name']}*",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )

    elif data.startswith("gen_char:"):
        key = data[9:]
        if key in GEN_CHARACTERS:
            user_gen_data[uid] = {"char": key}
            user_state[uid] = "gen_photo"
            ch = CHARACTERS[key]
            await query.edit_message_text(
                f"✅ Персонаж: *{ch['name']}*\n\n"
                f"📸 Теперь пришли реф-фото.\n"
                f"_Это фото из которого я возьму позу, угол камеры и освещение. "
                f"Лицо и одежда на рефе не важны — всё заменим на {ch['name']}._",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Отмена", callback_data="gen:cancel")
                ]])
            )

    elif data == "gen:skip_details":
        if uid in user_gen_data and "photo_bytes" in user_gen_data[uid]:
            await query.edit_message_text("⏳ Генерирую промпт...")
            await _run_generation(query, uid, extra_details="")
        else:
            await query.edit_message_text("⚠️ Сначала пришли фото.")

    elif data == "gen:start":
        user_state[uid] = "gen_select"
        await query.edit_message_text(
            "🎨 *Генерация промпта*\n\nВыбери персонажа:",
            parse_mode="Markdown",
            reply_markup=gen_char_keyboard()
        )


async def _run_generation(query_or_message, uid: int, extra_details: str):
    """Core generation logic — runs vision analysis + prompt building."""
    data = user_gen_data.get(uid, {})
    photo_bytes = data.get("photo_bytes")
    char_key = data.get("char", "lucia")

    if not photo_bytes:
        await query_or_message.edit_message_text("⚠️ Фото не найдено. Начни заново.")
        return

    # Step 1: extract technical data from photo
    vision_result = await asyncio.get_event_loop().run_in_executor(
        None, call_gemini_vision, photo_bytes, VISION_EXTRACT_PROMPT
    )

    if vision_result.startswith("⚠️"):
        await query_or_message.edit_message_text(vision_result)
        return

    # Step 2: build NB Pro Edit prompt
    final_prompt = await asyncio.get_event_loop().run_in_executor(
        None, build_gen_prompt, vision_result, char_key, extra_details
    )

    ch = CHARACTERS[char_key]
    result_text = (
        f"🎨 *Промпт для NB Pro Edit* — {ch['name']}\n\n"
        f"`{final_prompt}`\n\n"
        f"_Скопируй промпт → вставь в NB Pro Edit вместе с портретом {ch['name']}_"
    )

    user_state[uid] = "translate"
    user_gen_data.pop(uid, None)

    try:
        await query_or_message.edit_message_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=after_gen_keyboard()
        )
    except Exception:
        # If message is too long or edit fails, send new message
        await query_or_message.message.reply_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=after_gen_keyboard()
        )


async def on_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = get_state(uid)

    if state != "gen_photo":
        await update.message.reply_text(
            "📸 Фото получено, но сейчас не в режиме генерации.\n"
            "Нажми *🎨 Генерация промпта* чтобы начать.",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return

    # Download photo (highest quality)
    photo = update.message.photo[-1]
    file = await ctx.bot.get_file(photo.file_id)

    # Download bytes
    import io
    bio = io.BytesIO()
    await file.download_to_memory(bio)
    photo_bytes = bio.getvalue()

    # Store in session
    if uid not in user_gen_data:
        user_gen_data[uid] = {}
    user_gen_data[uid]["photo_bytes"] = photo_bytes

    user_state[uid] = "gen_details"

    char_key = user_gen_data[uid].get("char", "lucia")
    ch = CHARACTERS[char_key]

    await update.message.reply_text(
        f"✅ Фото получено!\n\n"
        f"Хочешь добавить детали? Например:\n"
        f"• _ночное освещение_\n"
        f"• _кухня_\n"
        f"• _грустное выражение_\n"
        f"• _чёрный топ_\n\n"
        f"Или нажми «Пропустить» — и я возьму стандартную среду {ch['name']}.",
        parse_mode="Markdown",
        reply_markup=skip_details_keyboard()
    )


async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    if not text:
        return

    state = get_state(uid)

    # ── Generation: waiting for extra details ──
    if state == "gen_details":
        if uid not in user_gen_data or "photo_bytes" not in user_gen_data[uid]:
            user_state[uid] = "translate"
            await update.message.reply_text("⚠️ Сессия сброшена. Начни заново.", reply_markup=main_keyboard())
            return

        await update.message.chat.send_action("typing")
        msg = await update.message.reply_text("⏳ Анализирую фото и генерирую промпт...")

        # Create a fake query-like object to reuse _run_generation
        class MsgWrapper:
            def __init__(self, m): self._m = m
            async def edit_message_text(self, text, **kwargs):
                await self._m.edit_text(text, **kwargs)

        await _run_generation(MsgWrapper(msg), uid, extra_details=text)
        return

    # ── Translation mode ──
    mode = get_mode(uid)
    ch = CHARACTERS[mode]

    await update.message.chat.send_action("typing")

    result = await asyncio.get_event_loop().run_in_executor(
        None, call_gemini, ch["system"], text
    )

    import base64 as b64
    text_b64 = b64.b64encode(text.encode("utf-8")).decode("ascii")
    kb = None
    if len(text_b64) <= 40:
        buttons = []
        row = []
        for key, c in CHARACTERS.items():
            if key != mode and c.get("visual") is None:  # only translation chars in retrans
                pass
            if key != mode:
                row.append(InlineKeyboardButton(f"→ {c['name']}", callback_data=f"retrans:{key}:{text_b64}"))
                if len(row) == 2:
                    buttons.append(row)
                    row = []
        if row:
            buttons.append(row)
        if buttons:
            kb = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(result)
    await update.message.reply_text(f"{ch['name']} ⬆", reply_markup=kb)


async def on_callback_retrans(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle retranslation — already merged into on_callback below."""
    pass

# ── Patch on_callback to handle retrans ──────────────────────────────────────

_orig_on_callback = on_callback

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):  # noqa: F811
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    if data.startswith("retrans:"):
        parts = data.split(":", 2)
        if len(parts) == 3:
            key = parts[1]
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
                await query.edit_message_text(f"*{ch['name']}:*\n\n{result}", parse_mode="Markdown")
        return

    await _orig_on_callback(update, ctx)

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO
    )

    if not BOT_TOKEN:
        print("\n⚠️  Сначала вставь BOT_TOKEN в переменные Railway!\n")
        return

    print("\n" + "="*44)
    print("  TG TRANSLATOR + GENERATOR — запущен")
    print("="*44)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("mode",  cmd_mode))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
