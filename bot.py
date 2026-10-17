import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re

# Render Environment Variables ထဲကနေ Token ကို ယူသုံးခြင်း (လုံခြုံရေးအတွက်)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_GEM_URL = os.getenv('GEMINI_GEM_URL')

bot = telebot.TeleBot(TOKEN)

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
    bot.reply_to(message, "မင်္ဂလာပါ! YouTube Link တစ်ခု ပို့ပေးပါ။ Thumbnail ပုံကို ထုတ်ပေးပြီး Gemini Gem ဆီ ချိတ်ဆက်ပေးပါမယ်။ 🎬")

@bot.message_handler(func=lambda message: True)
def handle_youtube_link(message):
    text = message.text
    video_id = extract_youtube_id(text)
    
    if video_id:
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        markup = InlineKeyboardMarkup()
        btn = InlineKeyboardButton("🎨 Gemini Gem ဖြင့် Thumbnail အသစ်ထုတ်မည်", url=GEMINI_GEM_URL)
        markup.add(btn)
        
        bot.send_photo(
            message.chat.id, 
            thumbnail_url, 
            caption="✅ YouTube Thumbnail အောင်မြင်စွာ Extract လုပ်ပြီးပါပြီ!\nအောက်ပါ Button ကိုနှိပ်ပြီး သင့်ရဲ့ Custom Gem ထဲမှာ ပုံအသစ် ဆက်ထုတ်နိုင်ပါပြီ။", 
            reply_markup=markup
        )
    else:
        bot.reply_to(message, "❌ ကျေးဇူးပြု၍ မှန်ကန်သော YouTube Video Link တစ်ခု ပို့ပေးပါခင်ဗျာ။")

if __name__ == '__main__':
    print("Bot is running 24/7 on Render...")
    bot.infinity_polling()
