import os
import urllib.parse
import segno
from info import * # Ensure UPI_ID, UPI_NAME, PRICES, and OWNER_USERNAME are here
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

@Client.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    data = query.data

    if data == 'activate_plan':
        btn = [
            [InlineKeyboardButton("💳 Pay via UPI (QR Code)", callback_data="upi_plans")],
            [InlineKeyboardButton("❌ Close", callback_data="close_data")]
        ]
        await query.message.edit_text(
            "**Aap premium kaise purchase karna chahte hain?**", 
            reply_markup=InlineKeyboardMarkup(btn)
        )

    elif data == "upi_plans":
        # Using variables directly from info.py
        btn = [
            [InlineKeyboardButton(f"⏳ 1 Week - ₹{ONE_WEEK_PRICE}", callback_data="pay_upi_1week")],
            [InlineKeyboardButton(f"📅 1 Month - ₹{ONE_MONTH_PRICE}", callback_data="pay_upi_1month")],
            [InlineKeyboardButton(f"🗓 3 Months - ₹{THREE_MONTHS_PRICE}", callback_data="pay_upi_3months")],
            [InlineKeyboardButton("🔙 Back", callback_data="activate_plan")]
        ]
        await query.message.edit_text("💎 **Apna plan select karein:**", reply_markup=InlineKeyboardMarkup(btn))

    elif data.startswith('pay_upi_'):
        plan_type = data.split('_')[-1]
        
        amounts = {
            "1week": ONE_WEEK_PRICE,
            "1month": ONE_MONTH_PRICE,
            "3months": THREE_MONTHS_PRICE
        }
        amount = amounts.get(plan_type)

        # UPI URL Construction
        encoded_name = urllib.parse.quote(UPI_NAME)
        # Added a note (tn) to the UPI URL so you know what the payment is for
        upi_url = f"upi://pay?pa={UPI_ID}&pn={encoded_name}&am={amount}&cu=INR&tn=Premium_{plan_type}"
        
        qr_path = f"qr_{query.from_user.id}.png"
        
        try:
            # Generate QR Code
            qrcode = segno.make(upi_url)
            qrcode.save(qr_path, scale=10, border=2)

            caption = (
                f"✨ **Plan Selected:** `{plan_type.upper()}`\n"
                f"💰 **Amount to Pay:** `₹{amount}`\n\n"
                f"1️⃣ **QR Code scan karein** kisi bhi UPI App se.\n"
                f"2️⃣ **Mobile Users:** Aap niche diye gaye button se direct pay kar sakte hain.\n\n"
                f"⚠️ **Payment ke baad screenshot** @{OWNER_USERNAME} ko bhejein."
            )

            await query.message.reply_photo(
                photo=qr_path,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Open UPI App (Pay Now)", url=upi_url)],
                    [InlineKeyboardButton("✅ Paid (Send Screenshot)", url=f"https://t.me/{OWNER_USERNAME}")],
                    [InlineKeyboardButton("❌ Close", callback_data="close_data")]
                ])
            )
            # Delete the previous menu message to keep the chat clean
            await query.message.delete()

        except Exception as e:
            await query.answer(f"Error: {e}", show_alert=True)
        finally:
            if os.path.exists(qr_path):
                os.remove(qr_path)

    elif data == "close_data":
        try:
            await query.message.delete()
            if query.message.reply_to_message:
                await query.message.reply_to_message.delete()
        except Exception:
            await query.answer("Message deleted!", show_alert=False)
