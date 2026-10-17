import os
import re
from io import BytesIO
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai

# Environment Variables မှ ယူခြင်း
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_GEM_URL = os.getenv('GEMINI_GEM_URL')
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL') # Render က သူ့အလိုအလျောက် ပေးသော URL

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

@app.route('/')
def home():
    return "Thumbnail Bot with Webhook is running 24/7!"

# Telegram Webhook Endpoint (Telegram မှ Message များ တိုက်ရိုက်ဝင်လာမည့်နေရာ)
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return '', 403

def extract_youtube_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|v\/|watch\?v=|youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "မင်္ဂလာပါ! YouTube Link တစ်ခု ပို့ပေးပါ။ အောက်ပါ Options များကို အသုံးပြုနိုင်ပါမည်။ 🎬")

@bot.message_handler(func=lambda message: True)
def handle_youtube_link(message):
    text = message.text
    video_id = extract_youtube_id(text)
    
    if not video_id:
        bot.reply_to(message, "❌ ကျေးဇူးပြု၍ မှန်ကန်သော YouTube Video Link တစ်ခု ပို့ပေးပါခင်ဗျာ။")
        return

    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    
    markup = InlineKeyboardMarkup(row_width=1)
    btn_download = InlineKeyboardButton("📥 Thumbnail Download လုပ်ရန်", callback_data=f"dl_{video_id}")
    btn_gem = InlineKeyboardButton("🌐 Gemini Gem သို့ သွားရန်", url=GEMINI_GEM_URL)
    btn_bot = InlineKeyboardButton("🎨 Bot ထဲမှာ 3D ပုံ ဆက်ထုတ်ရန်", callback_data=f"bot_{video_id}")
    
    markup.add(btn_download, btn_gem, btn_bot)
    
    bot.send_photo(
        message.chat.id, 
        thumbnail_url, 
        caption="✅ YouTube Thumbnail အောင်မြင်စွာ ရရှိပါပြီ!\nအောက်ပါ Options များထဲမှ လိုအပ်တာကို ရွေးချယ်ပါ -", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    chat_id = call.message.chat.id
    
    if data.startswith("dl_"):
        video_id = data.split("_")[1]
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        bot.answer_callback_query(call.id, "Thumbnail ပုံကို ပို့ပေးနေပါပြီ...")
        bot.send_document(chat_id, thumbnail_url, caption="📥 ဤနေရာတွင် Download ဆွဲနိုင်ပါသည်။")
        
    elif data.startswith("bot_"):
        video_id = data.split("_")[1]
        bot.answer_callback_query(call.id, "Gemini AI ဖြင့် 3D Thumbnail တည်ဆောက်နေပါပြီ...")
        msg = bot.send_message(chat_id, "⏳ Gemini AI ဖြင့် 3D Thumbnail အသစ် ဖန်တီးနေပါပြီ... ခေတ္တစောင့်ဆိုင်းပေးပါ။")
        
        try:
            prompt = (
                "change and create a dramatically upgraded, high-converting 3D YouTube thumbnail which is relevant to the content with an ultra-detailed, highly relevant background. "
                "Make all texts clearly visible 3D texts. NO stroke around the text. "
                "COLOR PALETTE RESTRICTION: STRICTLY use only Red, Neon Green, Yellow, and White. Do NOT use Golden color. "
                "Ensure text colors do not blend into the background, avoid duplicated text colors, and make sure text size is large and readable."
            )

            response = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=prompt,
                config=dict(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="16:9",
                )
            )

            for generated_image in response.generated_images:
                image_stream = BytesIO(generated_image.image.image_bytes)
                image_stream.name = "upgraded_thumbnail.jpg"
                
                bot.send_photo(
                    chat_id, 
                    image_stream, 
                    caption="✅ Bot ထဲတွင် ထုတ်ပေးထားသော 3D Thumbnail အသစ် ဖြစ်ပါသည်! 🎨🔥"
                )
                bot.delete_message(chat_id, msg.message_id)

        except Exception as e:
            bot.edit_message_text(f"❌ အမှားအယွင်း ဖြစ်ပွားသွားပါသည်: {str(e)}", chat_id, msg.message_id)

if __name__ == '__main__':
    # Webhook ကို အလိုအလျောက် ချိတ်ဆက်ပေးခြင်း
    if RENDER_EXTERNAL_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/{TELEGRAM_TOKEN}")
        print(f"Webhook successfully set to: {RENDER_EXTERNAL_URL}/{TELEGRAM_TOKEN}")
    
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
