import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from data import notebooks

# Define your bot token
BOT_TOKEN = "7926806994:AAFq8KFV41QDWKYPO2ui_HJxZII5KZgxINU"
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 6986899486

# Function to generate the laptop menu
def generate_laptop_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(notebook["name"], callback_data=f"laptop_{i}")
        for i, notebook in enumerate(notebooks)
    ]
    keyboard.add(*buttons)
    return keyboard

# Function to generate the main menu (persistent menu)
def generate_main_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Noutbuklar", callback_data="noutbuklar"),
        InlineKeyboardButton("Buyurtma", callback_data="buyurtma"),
        InlineKeyboardButton("Kredit", callback_data="kredit"),
        InlineKeyboardButton("Boshqa", callback_data="other")
    )
    return keyboard

# /start command handler
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Quyidagi noutbuklardan birini tanlang:",
        reply_markup=generate_laptop_menu(),
    )

# /menu command handler
@bot.message_handler(commands=["menu"])
def menu(message):
    bot.send_message(
        message.chat.id,
        "Quyidagi menyu orqali botning barcha imkoniyatlarini ko'rib chiqishingiz mumkin.",
        reply_markup=generate_main_menu(),
    )

# Callback query handler for selecting a laptop
@bot.callback_query_handler(func=lambda call: call.data.startswith("laptop_"))
def handle_choice(call):
    try:
        index = int(call.data.split("_")[1])
        selected_notebook = notebooks[index]
        bot.answer_callback_query(call.id)

        # Send the photo first
        bot.send_photo(call.message.chat.id, photo=selected_notebook["image"])

        # Then send the caption with options
        caption = (
            f"Tanlangan noutbuk:\n\n"
            f"{selected_notebook['info']}\n"
            f"Narx: {selected_notebook['price']}\n"
            f"Qolgan soni: {selected_notebook['stock_count']}\n"
        )

        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("Sotib olish", callback_data=f"buy_{index}"),
            InlineKeyboardButton("Kredit orqali to'lash", callback_data=f"credit_{index}"),
            InlineKeyboardButton("Bekor qilish", callback_data="cancel"),
        )
        bot.send_message(
            chat_id=call.message.chat.id,
            text=caption,
            reply_markup=keyboard
        )
    
    except Exception as e:
        bot.answer_callback_query(call.id, "Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

# Handle the "Buy" or "Credit" option
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_") or call.data.startswith("credit_"))
def handle_purchase_or_credit(call):
    try:
        parts = call.data.split("_")
        index = int(parts[1])
        selected_notebook = notebooks[index]

        # Ask for phone number
        bot.send_message(call.message.chat.id, "Iltimos, telefon raqamingizni kiriting.")
        bot.register_next_step_handler(call.message, ask_address, index)
    
    except Exception as e:
        print(f"Error in handle_purchase_or_credit: {e}")
        bot.answer_callback_query(call.id, "Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

# Ask for address after getting phone number
def ask_address(message, index):
    try:
        phone_number = message.text
        bot.send_message(message.chat.id, "Iltimos, manzilingizni kiriting.")
        bot.register_next_step_handler(message, finalize_purchase, phone_number, index)
    
    except Exception as e:
        print(f"Error in ask_address: {e}")
        bot.send_message(message.chat.id, "Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

# Finalize the purchase with address and payment method
def finalize_purchase(message, phone_number, index):
    try:
        address = message.text
        selected_notebook = notebooks[index]

        # Ask for payment method (cash or click)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("Naxt", callback_data=f"pay_naxt_{index}"),
            InlineKeyboardButton("Click", callback_data=f"pay_click_{index}")
        )

        bot.send_message(
            message.chat.id,
            f"Buyurtmangiz tasdiqlandi:\n\n"
            f"Noutbuk: {selected_notebook['name']}\n"
            f"Narx: {selected_notebook['price']}\n"
            f"Telefon raqami: {phone_number}\n"
            f"Manzil: {address}\n\n"
            f"To'lovni qanday amalga oshirasiz?",
            reply_markup=keyboard
        )
    
    except Exception as e:
        print(f"Error in finalize_purchase: {e}")
        bot.send_message(message.chat.id, "Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

# Handle the payment method selection (Naxt or Click)
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_payment(call):
    try:
        parts = call.data.split("_")
        payment_method = parts[1]
        index = int(parts[2])
        selected_notebook = notebooks[index]

        if payment_method == "naxt":
            action_text = "Naxt"
        elif payment_method == "click":
            action_text = "Click"

        bot.send_message(
            call.message.chat.id,
            f"Siz {action_text} to'lovini tanladingiz.\n\n"
            f"Buyurtmangiz tasdiqlandi:\n\n"
            f"Noutbuk: {selected_notebook['name']}\n"
            f"Narx: {selected_notebook['price']}\n"
            f"Siz bilan tez orada bog'lanamiz!"
        )

        # Notify the admin
        bot.send_message(
            ADMIN_ID,
            f"Yangi buyurtma:\n\n"
            f"Noutbuk: {selected_notebook['name']}\n"
            f"Narx: {selected_notebook['price']}\n"
            f"Telefon raqami: {call.message.chat.id}\n"
            f"Manzil: {call.message.text}\n"
            f"To'lov usuli: {action_text}"
        )
    
    except Exception as e:
        print(f"Error in handle_payment: {e}")
        bot.answer_callback_query(call.id, "Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")

# Handle the cancel action
@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Jarayon bekor qilindi.", reply_markup=ReplyKeyboardRemove())

# Default handler for unexpected or unhandled inputs
@bot.message_handler(func=lambda message: True)
def handle(message):
    bot.send_message(message.chat.id, "Iltimos, noto'g'ri buyruq kiritildi. Iltimos, tegishli variantni tanlang.",
                     reply_markup=generate_main_menu())

# Run the bot
bot.polling()
