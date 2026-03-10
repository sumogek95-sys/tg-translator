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
        "visual": {
            "demographics": "Young woman, 18-22, mixed Eastern European / East Asian features, slim-curvy hourglass build, approximately 165-168cm",
            "hair_color": "near-black with blue-black tint, appears natural, no highlights",
            "hair_length": "mid-back, reaching lower shoulder blades, with curtain bangs framing face",
            "hair_cut": "shag cut with wispy eyebrow-length center-parted curtain bangs, long layers throughout",
            "hair_texture": "straight to wavy type 1c-2a, slight natural wave at ends, fine to medium density",
            "hair_styling": "air-dried, lightly tousled, slight frizz and flyaways, effortless undone look, no visible product",
            "hair_part": "center part",
            "hair_volume": "moderate at roots, fuller mid-length, slight body collapse at crown",
            "skin": "very fair porcelain with cool-neutral undertones, no freckles, smooth texture, subtle natural flush on cheeks",
            "eyes": "green-gray with hazel variation, almond-shaped, slightly downturned outer corners, medium-dense natural lashes",
            "eyebrows": "dark brown-black, medium thickness, soft arch, slightly tapered ends, natural fill",
            "nose": "small slightly upturned button nose, narrow bridge",
            "lips": "full especially lower lip, soft cupid's bow, natural peachy-pink tone",
            "makeup": "winged black eyeliner cat-eye, subtle mascara, rosy blush, glossy nude-peach lip, light base",
            "accessories": "none",
            "clothing_default": "white fitted crewneck t-shirt OR grey sports bra OR black spaghetti strap top, with black/grey sweatpants OR medium-wash jeans OR black shorts. Adidas Campus sneakers or barefoot indoors. Casual, slightly fitted.",
            "environment_default": "small cozy apartment in Cologne — IKEA-style wooden furniture, warm lamp light, wooden floors, small potted plant on windowsill, unmade bed with beige/grey duvet, coffee mug nearby",
            "photo_style": "candid lifestyle photography, not posed, authentic, smartphone aesthetic, slightly brooding intense energy"
        }
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
        "visual": {
            "demographics": "Young woman, 20-25, Black / West African features, curvy plus-athletic build, approximately 163-168cm",
            "hair_color": "jet black, appears natural or lightly dyed, no highlights, deep rich tone",
            "hair_length": "shoulder-length, reaching just below collarbone",
            "hair_cut": "layered curly bob, no blunt perimeter, volume-shaped layers throughout, no bangs",
            "hair_texture": "curly type 3b-3c, defined springy curls with tight coil pattern, medium density",
            "hair_styling": "styled with curl-defining product gel or cream, low frizz, well-defined curl clumps, possibly diffused or air-dried",
            "hair_part": "center part visible at scalp",
            "hair_volume": "voluminous — full and rounded, maximum volume at sides and crown",
            "skin": "deep espresso brown, cool-neutral undertones, no freckles, smooth even-toned, healthy sheen",
            "eyes": "very dark brown nearly black, almond-shaped, dramatic lash density with lash extensions — full long wispy-tip style",
            "eyebrows": "dark brown-black, thick and bold, slightly arched, well-groomed defined shape",
            "nose": "medium-wide, slightly broad at tip, straight bridge, well-proportioned",
            "lips": "full both upper and lower lip, natural shape defined cupid's bow, warm nude-brown tone with slight gloss",
            "makeup": "full glam — matte or satin foundation, defined brows, voluminous lash extensions, subtle contour, warm nude-brown lip gloss, possible highlight on cheekbones",
            "accessories": "none visible — small gold studs optional",
            "clothing_default": "oversized vintage thrifted sweater OR floral dress OR denim overalls, in sage green, dusty rose, or cream palette. Worn-in Converse or Mary Jane flats. Cozy cottagecore-adjacent style.",
            "environment_default": "tiny cozy studio apartment — string fairy lights, plants on every surface, stuffed animals on shelves, watercolor paintings on wall, mason jar labeled Dream Fund on shelf",
            "photo_style": "confident polished Black beauty aesthetic, editorial and powerful, warm cozy light or clean natural light"
        }
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
        "visual": {
            "demographics": "Young woman, 18-23, mixed Latina / Southeast Asian features, curvy hourglass build, approximately 163-167cm",
            "hair_color": "blue-black / jet black, appears natural, no highlights, slight shine",
            "hair_length": "mid-chest to collarbone, reaching approximately mid-chest in front",
            "hair_cut": "long layers with heavy side-swept bangs falling across forehead to one side, seamless layering throughout",
            "hair_texture": "straight type 1b-1c, very smooth and sleek, minimal flyaways",
            "hair_styling": "blow-dried or flat-ironed, very smooth finish, minimal frizz, slight natural movement at ends",
            "hair_part": "deep side part on left side",
            "hair_volume": "moderate at roots, flat-ish crown, fuller through mid-lengths",
            "skin": "warm medium tan, golden-warm undertones, no freckles, very smooth luminous slightly dewy texture, no visible blemishes",
            "eyes": "olive-hazel with warm golden-brown center, almond-shaped with slight monolid influence, sparse to medium natural lashes",
            "eyebrows": "dark brown-black, medium thickness, straight with slight natural arch, full and defined",
            "nose": "medium width, slightly broad at tip, straight bridge",
            "lips": "very full especially lower lip, natural cupid's bow, warm nude-beige tone with subtle gloss",
            "makeup": "light dewy base or bare skin, minimal mascara, clear/nude lip gloss, clean-girl no-makeup look",
            "accessories": "none visible — gold hoops optional for going-out looks",
            "clothing_default": "crop top OR fitted tank top in coral, white, or yellow, with high-waisted shorts or jeans. Platform sneakers or sandals. Florida casual Gen Z energy.",
            "environment_default": "shared apartment in Orlando — colorful walls, Disney and Brazilian artist posters, fairy lights, sneaker collection on shelves, organized chaos",
            "photo_style": "clean effortless model-off-duty energy, warm lighting, natural sensuality without trying, Brazilian mixed editorial aesthetic"
        }
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
        "visual": {
            "demographics": "Young woman, 18-22, Eastern European / Southern European features, slim-curvy build, approximately 165-170cm",
            "hair_color": "dark chocolate brown, appears natural, no visible highlights, rich warm-brown tone",
            "hair_length": "mid-chest, reaching approximately upper-to-mid chest in front",
            "hair_cut": "long layers no bangs, natural curly shaping with minimal cutting structure, length follows curl shrinkage",
            "hair_texture": "curly type 3a-3b, defined spiral ringlets with medium-loose curl pattern, medium-high density",
            "hair_styling": "air-dried with light curl cream or mousse, defined but not crunchy, moderate frizz at crown and hairline, natural finish",
            "hair_part": "center part clearly visible",
            "hair_volume": "voluminous overall, full at sides, slightly flatter at crown roots, maximum volume through mid-lengths",
            "skin": "fair with warm peachy-neutral undertones, a few very faint blemishes on chest area, smooth overall, natural flush on cheeks, no freckles",
            "eyes": "gray-green cool-toned, almond-shaped with soft hooded lid, medium natural lash density",
            "eyebrows": "dark brown, thick and full, slightly unruly natural, soft arch, bushy-natural minimal grooming style",
            "nose": "straight bridge, slightly rounded tip, medium width, classically proportioned",
            "lips": "full especially lower lip, soft defined cupid's bow, natural rosy-nude tone, slight natural gloss",
            "makeup": "very light — subtle rosy-mauve eyeshadow wash, light mascara, natural lip tint or bare lips, no foundation or liner",
            "accessories": "none — small gold hardware detail occasionally",
            "clothing_default": "oversized knit sweater OR long cardigan in forest green, burgundy, cream, or navy. With corduroy pants OR midi skirt with tights. Worn-in Chelsea boots or loafers. Book or canvas tote bag nearby.",
            "environment_default": "Live Oak Public Library — warm wood bookshelves, afternoon light through tall windows, quiet reading nook. OR apartment with stacks of books, succulent on windowsill named Darcy, soft lamp light, open notebook, mug of tea",
            "photo_style": "effortlessly romantic aesthetic, wild curls bare skin soft eyes, Mediterranean Eastern European undone natural beauty with editorial edge"
        }
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

def build_gen_prompt_from_image(image_bytes: bytes, character_key: str, extra_details: str = "") -> str:
    """Single Gemini Vision call — image + character profile → ready prompt string."""
    char = CHARACTERS[character_key]
    visual = char["visual"]

    char_desc = f"""
Name: {char["name"]}
Demographics: {visual.get("demographics", "")}
Hair color: {visual.get("hair_color", "")}
Hair length: {visual.get("hair_length", "")}
Hair cut: {visual.get("hair_cut", "")}
Hair texture: {visual.get("hair_texture", "")}
Hair styling: {visual.get("hair_styling", "")}
Hair part: {visual.get("hair_part", "")}
Hair volume: {visual.get("hair_volume", "")}
Skin: {visual.get("skin", "")}
Eyes: {visual.get("eyes", "")}
Eyebrows: {visual.get("eyebrows", "")}
Nose: {visual.get("nose", "")}
Lips: {visual.get("lips", "")}
Makeup: {visual.get("makeup", "")}
Accessories: {visual.get("accessories", "")}
Clothing default: {visual.get("clothing_default", "")}
Environment default: {visual.get("environment_default", "")}
Photo style: {visual.get("photo_style", "")}"""

    user_overrides = f"User extra details (override defaults if provided): {extra_details}" if extra_details else "No extra details — use character defaults."

    prompt = f"""You are a prompt engineer for Nano Banana Pro Edit (NB Pro Edit), an AI image generation model that generates photorealistic images.

I am giving you a REFERENCE PHOTO and a CHARACTER PROFILE.

Your task:
- Analyze the reference photo for: exact body pose and posture, camera angle and height, framing, lighting quality and direction, color temperature, shadow style, background/environment, depth of field, photo grain and texture
- Write ONE ready-to-use NB Pro Edit image generation prompt that uses:
  → Pose, camera angle, lighting, composition FROM the reference photo
  → Appearance (face, hair, skin, eyes, body) FROM the character profile below
  → Clothing FROM the character profile (unless user overrides)
  → Environment FROM the character profile (unless user overrides)

CHARACTER PROFILE:
{char_desc}

{user_overrides}

Rules:
- Write as natural flowing sentences, 120-200 words
- Be specific about lighting (direction, quality, temperature, shadows)
- Be specific about pose (exact body position, limb placement, camera angle)
- Include character appearance details naturally in the description
- Do NOT copy the reference person's appearance — use ONLY the character profile above
- End with exactly this line: "Sharp detailed eyes with clear natural iris texture, defined eyelashes, realistic eye whites. Natural skin texture, realistic hair strands. No beauty over-smoothing, no filters. Shot on iPhone 15 Pro, 24mm main camera, f/1.78 aperture, natural computational photography, slight optical vignetting, realistic sensor noise, auto white balance."

Return ONLY the final prompt text. No explanation, no JSON, no labels, no markdown."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}},
                {"text": prompt}
            ]
        }],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1024}
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")[:300]
        return f"⚠️ Ошибка API: {e.code} — {err}"
    except Exception as e:
        return f"⚠️ Ошибка: {e}"

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
    """Single-step generation: image → Gemini Vision → ready prompt."""
    data = user_gen_data.get(uid, {})
    photo_bytes = data.get("photo_bytes")
    char_key = data.get("char", "lucia")
    ch = CHARACTERS[char_key]

    if not photo_bytes:
        await query_or_message.edit_message_text("⚠️ Фото не найдено. Начни заново.")
        return

    result = await asyncio.get_event_loop().run_in_executor(
        None, build_gen_prompt_from_image, photo_bytes, char_key, extra_details
    )

    user_state[uid] = "translate"
    user_gen_data.pop(uid, None)

    if result.startswith("⚠️"):
        try:
            await query_or_message.edit_message_text(result, reply_markup=after_gen_keyboard())
        except Exception:
            await query_or_message.message.reply_text(result, reply_markup=after_gen_keyboard())
        return

    header = f"🎨 Промпт для NB Pro Edit — {ch['name']}\n\n"
    footer = "\n\n⬆ Скопируй → вставь в NB Pro Edit вместе с портретом"
    full_text = header + result + footer

    try:
        await query_or_message.edit_message_text(full_text, reply_markup=after_gen_keyboard())
    except Exception:
        chunk_size = 4000
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        for i, chunk in enumerate(chunks):
            kb = after_gen_keyboard() if i == len(chunks) - 1 else None
            await query_or_message.message.reply_text(chunk, reply_markup=kb)


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
