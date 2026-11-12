"""KomekStud Telegram боты.

Іске қосу: BOT_TOKEN және ADMIN_CHAT_ID айнымалыларын қойып, `python bot.py`.
"""
import asyncio
import html
import logging
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


def load_dotenv(path: str = ".env") -> None:
    """Қарапайым .env оқу (қосымша кітапханасыз)."""
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    if not os.path.exists(here):
        return
    with open(here, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


load_dotenv()

PHONE = "77002339520"
WHATSAPP = f"https://wa.me/{PHONE}"
INSTAGRAM = "https://instagram.com/komekstud.kz"
SITE = "https://ntbm9zp678-cmyk.github.io/komekstud/"

# Сайттағы script.js-пен бірдей бағалар. prices: [антиплагиатпен, тексеріссіз]
SERVICES = {
    "diploma": {"name": "🎓 Дипломдық жұмыс", "fixed": "150 000 – 250 000 ₸",
                "note": "Нақты баға тақырып пен талаптарға қарай келісіледі."},
    "dissertation": {"name": "📚 Диссертация", "fixed": "200 000 ₸-ден",
                     "note": "Нақты баға тақырып пен көлемге қарай есептеледі."},
    "course": {"name": "📝 Курстық жұмыс", "unit": "Бет саны", "prices": [850, 450],
               "note": "Титул парағы, жоспар және әдебиеттер тізімі тегін."},
    "presentation": {"name": "📊 Презентация", "unit": "Слайд саны", "prices": [400, 200],
                     "free": 2, "note": "Бірінші және соңғы слайд тегін."},
    "referat": {"name": "📄 Реферат", "unit": "Бет саны", "prices": [500, 250],
                "note": "Титул парағы, жоспар және әдебиеттер тізімі тегін."},
    "essay": {"name": "🖋️ Эссе", "unit": "Бет саны", "prices": [1500, 800]},
    "article": {"name": "📰 Мақала", "unit": "Бет саны", "prices": [1500], "no_plag": True,
                "from": True, "note": "Бет бағасы 1 500 ₸-ден басталады."},
    "video": {"name": "🎬 Видео дайындау", "video": {"30": 2500, "60": 5000}},
    "kmzh": {"name": "🗓️ Қысқа мерзімді жоспар (ҚМЖ)", "unit": "Жоспар саны",
             "prices": [2500], "no_plag": True},
    "resume": {"name": "👔 Резюме жазу (дизайнмен)", "fixed": "1 000 ₸"},
    "originality": {"name": "🚀 Оригиналдылықты көтеру / ИИ түсіру", "fixed": "Келісім бойынша",
                    "note": "Кодировка, оригиналдылықты көтеру, ИИ түсіру — 80–100%."},
}

BTN_ORDER = "🛒 Тапсырыс беру"
BTN_PRICES = "💰 Қызметтер мен бағалар"
BTN_STEPS = "📋 Қалай жұмыс істейміз?"
BTN_TERMS = "✅ Кепілдіктер"
BTN_CONTACT = "📞 Байланыс"
BTN_CANCEL = "❌ Бас тарту"

MAIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_ORDER)],
        [KeyboardButton(text=BTN_PRICES), KeyboardButton(text=BTN_STEPS)],
        [KeyboardButton(text=BTN_TERMS), KeyboardButton(text=BTN_CONTACT)],
    ],
    resize_keyboard=True,
)
CANCEL_KB = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=BTN_CANCEL)]], resize_keyboard=True)


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ") + " ₸"


def estimate(key: str, qty: int | None = None, plag: bool = True, video: str | None = None) -> str:
    s = SERVICES[key]
    if "fixed" in s:
        return s["fixed"]
    if "video" in s:
        return fmt(s["video"][video or "30"])
    n = max(1, min(500, qty or 1))
    price = s["prices"][0] if s.get("no_plag") or plag else s["prices"][1]
    paid = max(0, n - s.get("free", 0))
    return fmt(paid * price) + ("-ден" if s.get("from") else "")


def services_kb(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=s["name"], callback_data=f"{prefix}:{k}")]
                         for k, s in SERVICES.items()]
    )


def prices_text() -> str:
    lines = ["<b>💰 Қызметтер мен бағалар</b>", ""]
    for s in SERVICES.values():
        if "fixed" in s:
            price = s["fixed"]
        elif "video" in s:
            price = "30 сек — 2 500 ₸, 1 мин — 5 000 ₸"
        elif s.get("no_plag"):
            unit = "дана" if s["unit"] == "Жоспар саны" else "бет"
            price = fmt(s["prices"][0]) + ("-ден" if s.get("from") else "") + f" / {unit}"
        else:
            unit = "слайд" if s["unit"] == "Слайд саны" else "бет"
            price = f"антиплагиатпен {fmt(s['prices'][0])}, тексеріссіз {fmt(s['prices'][1])} / {unit}"
        lines.append(f"<b>{s['name']}</b> — {price}")
    lines += ["", "Тапсырыс беру үшін «🛒 Тапсырыс беру» батырмасын басыңыз."]
    return "\n".join(lines)


STEPS_TEXT = (
    "<b>📋 Қалай жұмыс істейміз?</b>\n\n"
    "1️⃣ <b>Өтінім қалдырасыз</b> — жұмыс түрін, тақырыбын, көлемін және мерзімін жазасыз.\n"
    "2️⃣ <b>Бағаны келісеміз</b> — талаптарды нақтылап, бағасы мен мерзімін айтамыз.\n"
    "3️⃣ <b>Төлем жасайсыз</b> — келісілген төлемнен кейін бастаймыз. Дипломдық пен диссертацияға бөліп төлеу бар.\n"
    "4️⃣ <b>Жұмысты орындаймыз</b> — талаптарға сай жазып, рәсімдейміз, қажет болса антиплагиаттан өткіземіз.\n"
    "5️⃣ <b>Тапсырамыз және түзетеміз</b> — ескертулер болса, шарттарға сай түзетеміз."
)
TERMS_TEXT = (
    "<b>✅ Кепілдіктеріміз</b>\n\n"
    "🎓 <b>Дипломдық және диссертация</b> — қорғауға дейін түзетулер енгізіледі.\n"
    "🔁 <b>Курстық, презентация, эссе</b> — бір рет түзету қарастырылған.\n"
    "💰 <b>Қаражатты қайтару</b> — қате біздің командадан кеткен жағдайда қаражат қайтарылады."
)
CONTACT_TEXT = (
    "<b>📞 Байланыс</b>\n\n"
    "Телефон: +7 700 233 95 20\n"
    f'💬 <a href="{WHATSAPP}">WhatsApp-қа жазу</a>\n'
    f'📸 <a href="{INSTAGRAM}">Instagram: @komekstud.kz</a>\n'
    f'🌐 <a href="{SITE}">Сайт</a>'
)


class Order(StatesGroup):
    qty = State()
    plag = State()
    video = State()
    topic = State()
    deadline = State()
    name = State()
    phone = State()
    confirm = State()


router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Сәлеметсіз бе! 👋 <b>KomekStud</b> ботына қош келдіңіз.\n\n"
        "Біз студенттерге оқу жұмыстарын дайындау, өңдеу және рәсімдеуге көмектесеміз: "
        "дипломдық, курстық, диссертация, реферат, эссе, мақала, презентация, ҚМЖ, резюме.\n\n"
        "Төмендегі мәзірден таңдаңыз 👇",
        reply_markup=MAIN_KB,
    )


@router.message(Command("id"))
async def chat_id(message: Message) -> None:
    await message.answer(f"Бұл чаттың ID-і: <code>{message.chat.id}</code>")


@router.message(Command("cancel"))
@router.message(F.text == BTN_CANCEL)
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Тапсырыс тоқтатылды.", reply_markup=MAIN_KB)


@router.message(F.text == BTN_PRICES)
@router.message(Command("prices"))
async def prices(message: Message) -> None:
    await message.answer(prices_text())


@router.message(F.text == BTN_STEPS)
async def steps(message: Message) -> None:
    await message.answer(STEPS_TEXT)


@router.message(F.text == BTN_TERMS)
async def terms(message: Message) -> None:
    await message.answer(TERMS_TEXT)


@router.message(F.text == BTN_CONTACT)
@router.message(Command("contact"))
async def contact(message: Message) -> None:
    await message.answer(CONTACT_TEXT, disable_web_page_preview=True)


# ---------- Тапсырыс ----------

@router.message(F.text == BTN_ORDER)
@router.message(Command("order"))
async def order_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Тапсырысты бастаймыз. Бас тарту үшін «❌ Бас тарту».", reply_markup=CANCEL_KB)
    await message.answer("Жұмыс түрін таңдаңыз:", reply_markup=services_kb("svc"))


@router.callback_query(F.data.startswith("svc:"))
async def order_service(cb: CallbackQuery, state: FSMContext) -> None:
    key = cb.data.split(":", 1)[1]
    if key not in SERVICES:
        await cb.answer()
        return
    s = SERVICES[key]
    await state.clear()
    await state.update_data(service=key)
    await cb.message.edit_text(f"Жұмыс түрі: <b>{s['name']}</b>")
    await cb.answer()
    if "unit" in s:
        await state.set_state(Order.qty)
        await cb.message.answer(f"{s['unit']} қанша? (санмен жазыңыз)")
    elif "video" in s:
        await state.set_state(Order.video)
        await cb.message.answer("Видео ұзақтығы:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="30 секунд — 2 500 ₸", callback_data="vid:30"),
            InlineKeyboardButton(text="1 минут — 5 000 ₸", callback_data="vid:60"),
        ]]))
    else:
        await ask_topic(cb.message, state)


@router.message(Order.qty)
async def order_qty(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or not 1 <= int(text) <= 500:
        await message.answer("1-ден 500-ге дейінгі санды жазыңыз.")
        return
    await state.update_data(qty=int(text))
    s = SERVICES[(await state.get_data())["service"]]
    if s.get("no_plag"):
        await ask_topic(message, state)
        return
    await state.set_state(Order.plag)
    await message.answer("Антиплагиаттан өткізу керек пе?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Иә", callback_data="plag:yes"),
        InlineKeyboardButton(text="Жоқ", callback_data="plag:no"),
    ]]))


@router.callback_query(Order.plag, F.data.startswith("plag:"))
async def order_plag(cb: CallbackQuery, state: FSMContext) -> None:
    yes = cb.data == "plag:yes"
    await state.update_data(plag=yes)
    await cb.message.edit_text(f"Антиплагиат: <b>{'иә' if yes else 'жоқ'}</b>")
    await cb.answer()
    await ask_topic(cb.message, state)


@router.callback_query(Order.video, F.data.startswith("vid:"))
async def order_video(cb: CallbackQuery, state: FSMContext) -> None:
    v = cb.data.split(":", 1)[1]
    await state.update_data(video=v)
    await cb.message.edit_text(f"Ұзақтығы: <b>{'30 секунд' if v == '30' else '1 минут'}</b>")
    await cb.answer()
    await ask_topic(cb.message, state)


async def ask_topic(message: Message, state: FSMContext) -> None:
    await state.set_state(Order.topic)
    await message.answer("Тақырыбы мен талаптарын жазыңыз (пәні, тілі, оқу орны, т.б.):")


@router.message(Order.topic, F.text)
async def order_topic(message: Message, state: FSMContext) -> None:
    await state.update_data(topic=message.text.strip()[:1500])
    await state.set_state(Order.deadline)
    await message.answer("Мерзімі қашан? (мысалы: 25.11.2026 немесе «3 күнде»)")


@router.message(Order.deadline, F.text)
async def order_deadline(message: Message, state: FSMContext) -> None:
    await state.update_data(deadline=message.text.strip()[:100])
    await state.set_state(Order.name)
    await message.answer("Атыңыз кім?")


@router.message(Order.name, F.text)
async def order_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Атыңызды жазыңыз.")
        return
    await state.update_data(name=name[:100])
    await state.set_state(Order.phone)
    await message.answer(
        "Телефон нөміріңізді жазыңыз немесе төмендегі батырманы басыңыз:",
        reply_markup=ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="📱 Нөмірімді жіберу", request_contact=True)],
            [KeyboardButton(text=BTN_CANCEL)],
        ], resize_keyboard=True),
    )


@router.message(Order.phone)
async def order_phone(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number if message.contact else (message.text or "").strip()
    if sum(c.isdigit() for c in phone) < 10:
        await message.answer("Телефон нөмірін толық жазыңыз (кемінде 10 цифр).")
        return
    await state.update_data(phone=phone)
    await state.set_state(Order.confirm)
    data = await state.get_data()
    await message.answer("Тексеріңіз:", reply_markup=ReplyKeyboardRemove())
    await message.answer(summary(data), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Жіберу", callback_data="confirm:yes"),
        InlineKeyboardButton(text="❌ Бас тарту", callback_data="confirm:no"),
    ]]))


def summary(data: dict, user=None) -> str:
    s = SERVICES[data["service"]]
    e = html.escape
    lines = [
        "<b>🆕 Жаңа тапсырыс</b>" if user else "<b>Тапсырысыңыз:</b>",
        "",
        f"👤 Аты: {e(data['name'])}",
        f"📞 Телефон: {e(data['phone'])}",
        f"📌 Жұмыс түрі: {s['name']}",
    ]
    if "unit" in s:
        lines.append(f"🔢 {s['unit']}: {data['qty']}")
        if not s.get("no_plag"):
            lines.append(f"🛡️ Антиплагиат: {'иә' if data.get('plag', True) else 'жоқ'}")
    if "video" in s:
        lines.append(f"🎬 Ұзақтығы: {'30 секунд' if data.get('video') == '30' else '1 минут'}")
    lines.append(f"📝 Тақырыбы/талаптар: {e(data['topic'])}")
    lines.append(f"📅 Мерзімі: {e(data['deadline'])}")
    lines.append(f"💰 Болжамды баға: {estimate(data['service'], data.get('qty'), data.get('plag', True), data.get('video'))}")
    if s.get("note"):
        lines.append(f"<i>{s['note']}</i>")
    if user:
        who = f"@{user.username}" if user.username else e(user.full_name)
        lines.append(f'\n💬 Telegram: <a href="tg://user?id={user.id}">{who}</a>')
    return "\n".join(lines)


@router.callback_query(Order.confirm, F.data.startswith("confirm:"))
async def order_confirm(cb: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()
    await cb.answer()
    await cb.message.edit_reply_markup(reply_markup=None)
    if cb.data == "confirm:no":
        await cb.message.answer("Тапсырыс тоқтатылды.", reply_markup=MAIN_KB)
        return
    admin = os.getenv("ADMIN_CHAT_ID")
    sent = False
    if admin:
        try:
            await bot.send_message(int(admin), summary(data, cb.from_user))
            sent = True
        except Exception:
            logging.exception("Админге жіберу сәтсіз болды")
    if sent:
        await cb.message.answer(
            "Рақмет! ✅ Тапсырысыңыз қабылданды. Жақын арада сізбен хабарласамыз.",
            reply_markup=MAIN_KB,
        )
    else:
        await cb.message.answer(
            f'Кешіріңіз, тапсырысты жіберу мүмкін болмады. Бізге <a href="{WHATSAPP}">WhatsApp</a> '
            "арқылы жазыңыз: +7 700 233 95 20",
            reply_markup=MAIN_KB,
        )


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Төмендегі мәзірден таңдаңыз 👇", reply_markup=MAIN_KB)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("BOT_TOKEN айнымалысы қойылмаған")
    bot = Bot(token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
