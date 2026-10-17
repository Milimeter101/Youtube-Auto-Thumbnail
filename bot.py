import os
import re
from io import BytesIO
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_GEM_URL = os.getenv('GEMINI_GEM_URL')
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

@app.route('/')
def home():
    return "Thumbnail Bot with Webhook is running 24/7!"

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
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup(row_width=1)
    btn_yt = InlineKeyboardButton("🔗 YouTube Link ဖြင့် Thumbnail ယူမည်", callback_data="mode_youtube")
    btn_ref = InlineKeyboardButton("🖼️ ရှိပြီးသား Thumbnail ပုံကို Reference တင်မည်", callback_data="mode_reference")
    btn_gem = InlineKeyboardButton("🌐 Gemini Gem သို့ သွားရန်", url=GEMINI_GEM_URL)
    
    markup.add(btn_yt, btn_ref, btn_gem)
    
    bot.send_message(
        chat_id, 
        "မင်္ဂလာပါ! ကျေးဇူးပြု၍ အောက်ပါ Options များထဲမှ လိုအပ်သည်ကို ရွေးချယ်ပါ - 🎬", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    chat_id = call.message.chat.id
    
    if data == "mode_youtube":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "🔗 ကျေးဇူးပြု၍ YouTube Video Link တစ်ခု ပို့ပေးပါ။")
        
    elif data == "mode_reference":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "🖼️ ကျေးဇူးပြု၍ Thumbnail ပုံအသစ် ထုတ်ချင်သော Thumbnail ပုံကို (Photo ပုံစံဖြင့်) တိုက်ရိုက် တင်ပေးပါ။")
        
    elif data.startswith("dl_"):
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
                "Create a dramatically upgraded, high-converting 3D YouTube thumbnail with an ultra-detailed, highly relevant background. "
                "Make all texts clearly visible 3D texts. NO stroke around the text. "
                "COLOR PALETTE RESTRICTION: STRICTLY use only Red, Neon Green, Yellow, and White. Do NOT use Golden color. "
                "Ensure text colors do not blend into the background, avoid duplicated text colors, and make sure text size is large and readable."
            )

            # SDK အသစ်၏ မှန်ကန်သော Image Generation Syntax
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"]
                )
            )

            image_found = False
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    image_stream = BytesIO(image_bytes)
                    image_stream.name = "upgraded_thumbnail.jpg"
                    
                    bot.send_photo(
                        chat_id, 
                        image_stream, 
                        caption="✅ Bot ထဲတွင် ထုတ်ပေးထားသော 3D Thumbnail အသစ် ဖြစ်ပါသည်! 🎨🔥"
                    )
                    image_found = True
                    break
            
            if image_found:
                bot.delete_message(chat_id, msg.message_id)
            else:
                bot.edit_message_text("❌ ပုံထုတ်လုပ်၍ မရရှိပါ။ ကျေးဇူးပြု၍ ထပ်မံကြိုးစားပါ။", chat_id, msg.message_id)

        except Exception as e:
            bot.edit_message_text(f"❌ အမှားအယွင်း ဖြစ်ပွားသွားပါသည်: {str(e)}", chat_id, msg.message_id)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text
    video_id = extract_youtube_id(text)
    
    if video_id:
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        markup = InlineKeyboardMarkup(row_width=1)
        btn_download = InlineKeyboardButton("📥 Thumbnail Download လုပ်ရန်", callback_data=f"dl_{video_id}")
        btn_gem = InlineKeyboardButton("🌐 Gemini Gem သို့ သွားရန်", url=GEMINI_GEM_URL)
        btn_bot = InlineKeyboardButton("🎨 Bot ထဲမှာ Thumbnail ပုံ ဆက်ထုတ်ရန်", callback_data=f"bot_{video_id}")
        
        markup.add(btn_download, btn_gem, btn_bot)
        
        bot.send_photo(
            chat_id, 
            thumbnail_url, 
            caption="✅ YouTube Thumbnail အောင်မြင်စွာ ရရှိပါပြီ!\nအောက်ပါ Options များထဲမှ လိုအပ်တာကို ရွေးချယ်ပါ -", 
            reply_markup=markup
        )
    else:
        bot.reply_to(message, "❌ ကျေးဇူးပြု၍ မှန်ကန်သော YouTube Video Link တစ်ခု ပို့ပေးပါ သို့မဟုတ် /start ကို နှိပ်၍ Options ပြန်ရွေးပါ။")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "⏳ တင်လိုက်သော ပုံကို Reference အဖြစ်ယူ၍ 3D Thumbnail အသစ် ဖန်တီးနေပါပြီ...")
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        prompt = (
            "Make the texts to be more better than the original images (3d texts) clearly visible ,no stroke,be careful no to be as the same as background color and not golden color (use only red ,neon green, yellow,white),be careful not to be duplicated text color,not too small text size and change the background which is relevant to the content...
colors do not blend into the background, avoid duplicated text colors, and make sure text size is large and readable."
        )

        from PIL import Image
        import io
        img = Image.open(io.BytesIO(downloaded_file))

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        image_found = False
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                image_stream = BytesIO(image_bytes)
                image_stream.name = "upgraded_thumbnail.jpg"
                
                bot.send_photo(
                    chat_id, 
                    image_stream, 
                    caption="✅ Reference ပုံကို အခြေခံ၍ Bot ထဲတွင် ထုတ်ပေးထားသော 3D Thumbnail အသစ် ဖြစ်ပါသည်! 🎨🔥"
                )
                image_found = True
                break
        
        if image_found:
            bot.delete_message(chat_id, msg.message_id)
        else:
            bot.edit_message_text("❌ ပုံထုတ်လုပ်၍ မရရှိပါ။", chat_id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ လက်ရှိ function မရသေးပါ: {str(e)}", chat_id, msg.message_id)

if __name__ == '__main__':
    if RENDER_EXTERNAL_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/{TELEGRAM_TOKEN}")
        print(f"Webhook successfully set to: {RENDER_EXTERNAL_URL}/{TELEGRAM_TOKEN}")
    
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
