import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# 📌 TOKEN va ADMIN ID-larini shu yerda yozamiz
TOKEN = "8301978711:AAGOF5F29XMyg8DAgan3VLePeizZCFfG4mU"  
ADMINS = [7752032178, 7919326758]  

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 📂 Fayllar
try:
    with open("movies.json", "r") as f:
        movies = json.load(f)
except FileNotFoundError:
    movies = []

try:
    with open("settings.json", "r") as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {"channels": []}

users = set()
temp_data = {}

# 📌 Saqlash funksiyalari
def save_movies():
    with open("movies.json", "w") as f:
        json.dump(movies, f, indent=2)

def save_settings():
    with open("settings.json", "w") as f:
        json.dump(settings, f, indent=2)

# 📋 Admin panel klaviaturasi
def admin_keyboard():
    kb = [
        [KeyboardButton(text="🎞 Kinolar ro'yxati")],
        [KeyboardButton(text="📢 Reklama yuborish")],
        [KeyboardButton(text="👥 Foydalanuvchilar soni")],
        [KeyboardButton(text="➕ Kanal ulash"), KeyboardButton(text="➖ Kanal uzish")],
        [KeyboardButton(text="❌ Chiqish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ---------------- START ----------------
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    users.add(message.from_user.id)

    if settings["channels"]:
        links = "\n".join([f"➡️ {c}" for c in settings["channels"]])
        await message.answer(
            f"👋 Salom!\n🎬 Kino olish uchun kod yuboring.\n\n📢 Avval quyidagi kanallarga a'zo bo‘ling:\n{links}\n\n✅ Keyin kod yuboring."
        )
    else:
        await message.answer("👋 Salom!\n🎬 Kino olish uchun kod yuboring.")

# ---------------- ADMIN PANEL ----------------
@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("⛔ Siz admin emassiz!")

    await message.answer("📋 Admin panel:", reply_markup=admin_keyboard())

# ---------------- VIDEO QABUL ----------------
@dp.message(lambda m: m.video and m.from_user.id in ADMINS)
async def handle_video(message: types.Message):
    temp_data[message.chat.id] = {"file_id": message.video.file_id}
    await message.answer("✅ Kino qabul qilindi.\nEndi unga kod yuboring 🔑")

# ---------------- MATN QABUL ----------------
@dp.message(lambda m: m.text)
async def handle_text(message: types.Message):
    chat_id = message.chat.id
    text = message.text
    user_id = message.from_user.id

    is_admin = user_id in ADMINS

    # ADMIN PANEL
    if is_admin:
        if text == "🎞 Kinolar ro'yxati":
            if not movies:
                return await message.answer("📂 Hozircha kino yo‘q.")
            lst = "\n".join([f"{i+1}. Kod: {m['code']}" for i, m in enumerate(movies)])
            return await message.answer("🎬 Kinolar ro'yxati:\n\n" + lst)

        if text == "📢 Reklama yuborish":
            temp_data["reklama"] = True
            return await message.answer("✍️ Reklama matnini yuboring:")

        if temp_data.get("reklama") and not text.startswith("/"):
            for uid in users:
                try:
                    await bot.send_message(uid, "📢 Reklama:\n\n" + text)
                except:
                    pass
            del temp_data["reklama"]
            return await message.answer("✅ Reklama yuborildi!")

        if text == "👥 Foydalanuvchilar soni":
            return await message.answer(f"👥 Foydalanuvchilar soni: {len(users)}")

        if text == "➕ Kanal ulash":
            temp_data["add_channel"] = True
            return await message.answer("🔗 Kanal linkini yuboring (masalan: @kanal):")

        if temp_data.get("add_channel") and text.startswith("@"):
            settings["channels"].append(text)
            save_settings()
            del temp_data["add_channel"]
            return await message.answer(f"✅ Kanal ulandi:\n{text}")

        if text == "➖ Kanal uzish":
            if not settings["channels"]:
                return await message.answer("📂 Hozircha kanal ulanmagan.")
            lst = "\n".join([f"{i+1}. {c}" for i, c in enumerate(settings["channels"])])
            temp_data["remove_channel"] = True
            return await message.answer(f"❌ Qaysi kanalni uzmoqchisiz? Raqamini yuboring:\n\n{lst}")

        if temp_data.get("remove_channel") and text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(settings["channels"]):
                removed = settings["channels"].pop(idx)
                save_settings()
                await message.answer(f"❌ Kanal uzildi:\n{removed}")
            else:
                await message.answer("⚠️ Noto‘g‘ri raqam!")
            del temp_data["remove_channel"]
            return

        if text == "❌ Chiqish":
            return await message.answer("✅ Admin panel yopildi", reply_markup=types.ReplyKeyboardRemove())

    # ADMIN KINO KOD QO‘SHYAPTI
    if temp_data.get(chat_id) and temp_data[chat_id].get("file_id"):
        movies.append({"file_id": temp_data[chat_id]["file_id"], "code": text})
        save_movies()
        await message.answer(f"🎉 Kino saqlandi!\n🔑 Kod: {text}")
        del temp_data[chat_id]
        return

    # USER KOD YUBORADI
    movie = next((m for m in movies if m["code"] == text), None)
    if movie:
        return await bot.send_video(chat_id, movie["file_id"], caption="🎬 Marhamat, siz so‘ragan kino!")
    else:
        return await message.answer("⚠️ Siz yuborgan kod bo‘yicha kino topilmadi.")

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
