import telebot
import google.generativeai as genai
import re
import time

# ---------- 🔑 अपनी API KEYS यहाँ डालें ----------
TELEGRAM_BOT_TOKEN = "8965822236:AAFZMaabmqiGFKiKSNtZVKpX3RrMX4XM-Uk"  # BotFather से लें
GEMINI_API_KEY = "AQ.Ab8RN6KCY9TL3bix9bATctLj_hii7qSCdwvsbRLTh_11fZc4Gw"  # Google AI Studio से लें
# -------------------------------------------------

# 1. Gemini सेट करें
genai.configure(api_key=GEMINI_API_KEY)

# मस्ती भरा Prompt (Gemini को ऐसे बोलना सिखाएं)
MASTI_PROMPT = """Tum ek masty bhari, sarcastic aur intelligent bot ho.
Har sawaal ka jawab Hinglish mein do, thoda attitude aur mazaak ke saath.
Hamesha apni baat ke end mein ek relevant emoji daalna mat bhoolo. 😎
Agar koi boring sawaal puche toh use bhi interesting bana ke jawab do.
Tumhara naam hai "Chatty" (लेकिन ये मत बताना अगर कोई पूछे तो बोलना "Main toh bas mazaak kar raha tha").
Kisi bhi cheez ka jawab do, lekin agar illegal ya harmful ho toh mana kar do.
Tumhe har baat ka jawab dena hai jaise Gemini deta hai, lekin apne andaaz mein.
"""

# Gemini model को configure करें
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",  # ya "gemini-pro"
    system_instruction=MASTI_PROMPT
)

# 2. Telegram Bot सेट करें
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# 3. /start और /help कमांड
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 **Namaste! Main hoon Chatty - aapka masti bhara AI dost!**\n\n"
        "Mujhe kuch bhi poochiye, main har baat ka jawab doonga apne style mein.\n"
        "Bas ek baat yaad rakhiyega: Main thoda sarcastic hoon! 😜\n\n"
        "Commands:\n"
        "/start - Meri shuruat karein\n"
        "/help - Yeh help dekhein\n"
        "/clear - Meri yaadash mitayein (baat-cheet bhool jaunga)\n\n"
        "Ab boliye, kya poochna hai? 🔥"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# 4. Chat History (Memory) - Takreeban 10 messages yaad rakhega
user_conversations = {}

@bot.message_handler(func=lambda message: True)
def chat_with_gemini(message):
    user_id = message.from_user.id
    user_text = message.text

    # Bot ko ignore karein agar khud ko mention kare
    if message.from_user.is_bot:
        return

    # Typing... indicator dikhayein
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # User ki purani baat-cheet history lo
        history = user_conversations.get(user_id, [])

        # Naya message history mein daalein
        history.append({"role": "user", "parts": [user_text]})

        # Sirf last 10 messages rakhein (taaki token zyada na lagein)
        if len(history) > 10:
            history = history[-10:]

        # Gemini se jawab lein
        response = model.generate_content(history)
        reply_text = response.text

        # Reply ko clean karein (thoda sa)
        reply_text = re.sub(r'\s+', ' ', reply_text).strip()

        # Agar jawab bohot lamba hai toh break kar dein (Telegram limit 4096 chars)
        if len(reply_text) > 4000:
            reply_text = reply_text[:4000] + "... (baaki ka jawab itna lamba tha ki maine kaat diya 😅)"

        # User ko jawab bhejein
        bot.reply_to(message, reply_text)

        # Gemini ka jawab history mein save karein (taaki context yaad rahe)
        history.append({"role": "model", "parts": [reply_text]})
        user_conversations[user_id] = history

    except Exception as e:
        error_msg = f"❌ Oops! Kuch gadbad ho gayi. Shayad main so raha tha. Thodi der baad try karo! 😴\nError: {e}"
        bot.reply_to(message, error_msg)
        print(f"Error for user {user_id}: {e}")

# 5. /clear command - Memory reset
@bot.message_handler(commands=['clear'])
def clear_memory(message):
    user_id = message.from_user.id
    if user_id in user_conversations:
        del user_conversations[user_id]
    bot.reply_to(message, "🧹 Meri yaadash saaf kar di gayi! Ab main tumhe nahi pehchanta. Naye dost ki tarah baat karo! 😂")

# 6. Bot ko start karein
if __name__ == "__main__":
    print("🤖 Chatty Bot chal raha hai... Ctrl+C se roken.")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Bot restart ho raha hai: {e}")
            time.sleep(5)