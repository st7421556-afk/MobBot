import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from products import products
from config import TOKEN, ADMIN_IDS
from datetime import datetime

bot = telebot.TeleBot(TOKEN)

orders = []
feedbacks = []
new_item = {}

# =========================
# ADMIN CHECK
# =========================
def is_admin(user_id):
    return user_id in ADMIN_IDS


# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "👋 <b>Вітаю!</b> Це бот для замовлення мобільних пристроїв 📱\n\n"
        "Оберіть дію нижче 👇"
    )

    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(
        InlineKeyboardButton("📱 Каталог", callback_data="open_catalog"),
        InlineKeyboardButton("ℹ️ Інфо", callback_data="open_info"),
        InlineKeyboardButton("❓ Допомога", callback_data="open_help"),
        InlineKeyboardButton("💬 Відгук", callback_data="open_feedback")
    )

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)


# =========================
# ADMIN PANEL
# =========================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ У вас немає доступу")
        return

    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton("🛒 Замовлення", callback_data="admin_orders"),
        InlineKeyboardButton("📬 Відгуки", callback_data="admin_feedback")
    )

    markup.add(
        InlineKeyboardButton("➕ Додати товар", callback_data="admin_add_item"),
        InlineKeyboardButton("🗑 Видалити товар", callback_data="admin_remove_item")
    )

    text = (
        "⚙️ <b>Адмін-панель:</b>\n\n"
    )

    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)


# =========================
# CATALOG
# =========================
@bot.message_handler(commands=['catalog'])
def catalog(message):
    markup = InlineKeyboardMarkup()

    for key, item in products.items():
        markup.add(
            InlineKeyboardButton(
                text=f"{item['name']} - {item['price']} грн",
                callback_data=key
            )
        )

    bot.send_message(message.chat.id, "📱 Новинки смартфонів:", reply_markup=markup)


# =========================
# CALLBACK
# =========================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    global orders

    data = call.data

    # =========================
    # 🔥 ГОЛОВНЕ INLINE МЕНЮ (/start кнопки)
    # =========================
    if data == "open_catalog":
        catalog(call.message)
        return

    if data == "open_info":
        info_command(call.message)
        return

    if data == "open_help":
        help_command(call.message)
        return

    if data == "open_feedback":
        feedback(call.message)
        return

    # =========================
    # 🔥 АДМІН ПАНЕЛЬ
    # =========================
    if data == "admin_orders":
        if is_admin(call.from_user.id):
            bot.send_message(
                call.message.chat.id,
                "\n\n".join(orders) if orders else "📭 Немає замовлень"
            )
        return

    if data == "admin_feedback":
        if is_admin(call.from_user.id):
            bot.send_message(
                call.message.chat.id,
                "\n\n".join(feedbacks) if feedbacks else "📭 Немає відгуків"
            )
        return

    # =========================
    # 🔥 ЗАМОВЛЕННЯ
    # =========================
    if data.startswith("order_"):
        product_key = data.split("_")[1]
        product = products.get(product_key)

        order_text = (
            f"🛒 НОВЕ ЗАМОВЛЕННЯ!\n\n"
            f"👤 {call.from_user.first_name}\n"
            f"🆔 {call.from_user.id}\n\n"
            f"📱 {product['name']}\n"
            f"💰 {product['price']} грн"
        )

        orders.append(order_text)

        for admin_id in ADMIN_IDS:
            bot.send_message(admin_id, order_text)

        bot.send_message(call.message.chat.id, "✅ Замовлення оформлено!")
        return

    # =========================
    # 🔥 АДМІН ДОДАВАННЯ ТОВАРУ
    # =========================
    if data == "admin_add_item":
        if is_admin(call.from_user.id):
            bot.send_message(
                call.message.chat.id,
                "✏️ Введи товар у форматі:\n\n"
                "назва;ціна;дисплей;пам'ять;кольори;опис\n\n"
                "📌 Приклад:\n"
                "iPhone 15;45000;6.1 OLED;128GB,256GB;Black,White;Новий флагман Apple"
            )
            bot.register_next_step_handler(call.message, process_new_item)
        return

    # =========================
    # 🔥 АДМІН ВИДАЛЕННЯ
    # =========================
    if data == "admin_remove_item":
        if is_admin(call.from_user.id):
            bot.send_message(call.message.chat.id, "🗑 Введи ключ товару")
            bot.register_next_step_handler(call.message, delete_item)
        return

    # =========================
    # 🔥 КАТАЛОГ ТОВАРІВ
    # =========================
    product = products.get(data)

    if product:
        text = (
            f"📱 <b>{product['name']}</b>\n\n"
            f"💰 {product['price']} грн\n"
            f"📱 Дисплей: {product['display']}\n"
            f"💾 Пам'ять: {', '.join(product['memory'])}\n"
            f"🎨 Кольори: {', '.join(product['colors'])}\n\n"
            f"📋 Опис:\n{product['description']}"
        )

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🛒 Замовити", callback_data=f"order_{data}")
        )

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=markup
        )
        return

# =========================
# HELP
# =========================
@bot.message_handler(commands=['help'])
def help_command(message):
    text = (
        "📖 <b>Команди:</b>\n"
        "/start\n/help\n/info\n/catalog\n/feedback"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")


# =========================
# INFO
# =========================
@bot.message_handler(commands=['info'])
def info_command(message):
    bot.send_message(
        message.chat.id,
        "🤖 Бот для замовлення смартфонів 📱",
        parse_mode="HTML"
    )


# =========================
# ORDERS (TEXT)
# =========================
@bot.message_handler(commands=['orders'])
def show_orders(message):
    if not is_admin(message.from_user.id):
        return

    bot.send_message(message.chat.id, "\n\n".join(orders) or "📭 Немає замовлень")


# =========================
# FEEDBACK
# =========================
@bot.message_handler(commands=['feedback'])
def feedback(message):
    bot.send_message(message.chat.id, "✍️ Напиши відгук:")
    bot.register_next_step_handler(message, send_feedback)


def send_feedback(message):
    user = message.from_user

    text = (
        f"💬 ВІДГУК\n\n"
        f"👤 {user.first_name}\n"
        f"🆔 {user.id}\n\n"
        f"{message.text}"
    )

    feedbacks.append(text)

    for admin_id in ADMIN_IDS:
        bot.send_message(admin_id, text)

    bot.send_message(message.chat.id, "✅ Дякуємо!")

    # =========================
    # ADD ITEM SAVE FUNCTION
    # =========================

@bot.message_handler(commands=['add_item'])
def add_item(message):
    if not is_admin(message.from_user.id):
        return

    bot.send_message(
        message.chat.id,
        "📱 Введи дані товару:\n"
        "назва;ціна;дисплей;пам'ять;кольори;опис"
    )

    bot.register_next_step_handler(message, process_new_item)

def process_new_item(message):
    try:
        name, price, display, memory, colors, description = message.text.split(";")

        key = name.lower().replace(" ", "_")

        products[key] = {
            "name": name.strip(),
            "price": int(price),
            "display": display.strip(),
            "memory": [x.strip() for x in memory.split(",")],
            "colors": [x.strip() for x in colors.split(",")],
            "description": description.strip()
        }

        bot.send_message(message.chat.id, "✅ Товар додано!")

    except:
        bot.send_message(message.chat.id, "❌ Неправильний формат")

def delete_item(message):
    key = message.text.strip().lower().replace(" ", "_")

    if key in products:
        del products[key]
        bot.send_message(message.chat.id, "✅ Товар видалено")
    else:
        bot.send_message(message.chat.id, "❌ Товар не знайдено")

@bot.message_handler(commands=['hello'])
def hello(message):
    bot.send_message(
        message.chat.id,
        f"👋 Привіт, {message.from_user.first_name}!\n\n"
        "Я бот для замовлення смартфонів 📱\n"
        "Можу допомогти з вибором, замовленням і інформацією про товари."
    )

@bot.message_handler(content_types=['text'])
def auto_reply(message):
    text = message.text.lower()

    # =========================
    # 📱 РЕАЛЬНИЙ КАТАЛОГ З products
    # =========================
    if "які товари" in text or "каталог" in text:

        if not products:
            bot.send_message(message.chat.id, "📭 Наразі товарів немає")
            return

        catalog_text = "📱 <b>Доступні товари:</b>\n\n"

        for key, item in products.items():
            catalog_text += (
                f"📌 {item['name']}\n"
                f"💰 {item['price']} грн\n\n"
            )

        catalog_text += "👉 Натисни /catalog щоб переглянути детально"

        bot.send_message(message.chat.id, catalog_text, parse_mode="HTML")
        return

    # =========================
    # 🛒 ЯК ЗАМОВИТИ
    # =========================
    if "як замовити" in text:
        bot.send_message(
            message.chat.id,
            "🛒 Як зробити замовлення:\n\n"
            "1️⃣ Відкрий /catalog\n"
            "2️⃣ Обери товар\n"
            "3️⃣ Натисни «Замовити»\n\n"
            "📦 Ми зв'яжемось з тобою після замовлення"
        )
        return

    # =========================
    # 💰 ЦІНИ
    # =========================
    if "ціна" in text:
        bot.send_message(
            message.chat.id,
            "💰 Ціни залежать від моделі.\n"
            "Використай /catalog щоб побачити всі актуальні ціни 📱"
        )
        return

    # =========================
    # ❓ НЕВІДОМЕ ПИТАННЯ
    # =========================
    bot.send_message(
        message.chat.id,
        "❓ Я не зовсім зрозумів запит.\n"
        "Спробуй:\n"
        "/catalog — товари\n"
        "/help — команди"
    )

# =========================
# RUN BOT
# =========================
bot.infinity_polling()