import os
import urllib.parse
import segno
from Info import * # Sabhi variables Info.py se load karne ke liye
from pyrogram import Client, filters, enums 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Note: Ensure karein ki Info.py mein UPI_ID, UPI_NAME, aur PRICES defined hain.

@Client.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    if query.data == 'activate_plan':
        btn = [[
            InlineKeyboardButton("💳 Pay via UPI (QR Code)", callback_data="upi_plans")
        ],[
            InlineKeyboardButton("Close", callback_data="close_data")
        ]]
        await query.message.edit("Aap premium kaise purchase karna chahte hain?", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data == "upi_plans":
        # Yahan variables Info.py se automatic pick honge
        btn = [
            [InlineKeyboardButton(f"⏳ 1 Week - ₹{ONE_WEEK_PRICE}", callback_data="pay_upi_1week")],
            [InlineKeyboardButton(f"📅 1 Month - ₹{ONE_MONTH_PRICE}", callback_data="pay_upi_1month")],
            [InlineKeyboardButton(f"🗓 3 Months - ₹{THREE_MONTHS_PRICE}", callback_data="pay_upi_3months")],
            [InlineKeyboardButton("🔙 Back", callback_data="activate_plan")]
        ]
        await query.message.edit_text("💎 Apna plan select karein:", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith('pay_upi_'):
        plan_type = query.data.split('_')[-1]
        
        amounts = {
            "1week": ONE_WEEK_PRICE,
            "1month": ONE_MONTH_PRICE,
            "3months": THREE_MONTHS_PRICE
        }
        amount = amounts.get(plan_type, 15)

        # UPI URL (UPI_ID aur UPI_NAME bhi Info.py se aayenge)
        encoded_name = urllib.parse.quote(UPI_NAME)
        upi_url = f"upi://pay?pa={UPI_ID}&pn={encoded_name}&am={amount}&cu=INR"
        qr_path = f"qr_{query.from_user.id}.png"
        
        try:
            qrcode = segno.make(upi_url)
            qrcode.save(qr_path, scale=10)

            await query.message.reply_photo(
                photo=qr_path,
                caption=(
                    f"✨ **Plan:** {plan_type.upper()}\n"
                    f"💰 **Amount:** ₹{amount}\n\n"
                    f"1️⃣ QR Code scan karein.\n"
                    f"2️⃣ Mobile users click: [Pay Now]({upi_url})\n\n"
                    f"Payment ke baad screenshot @{OWNER_USERNAME} ko bhejein."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Paid (Send Screenshot)", url=f"https://t.me/{OWNER_USERNAME}")]
                ])
            )
            await query.message.delete()

        except Exception as e:
            await query.message.reply_text(f"❌ Error: {e}")
        finally:
            if os.path.exists(qr_path):
                os.remove(qr_path)
