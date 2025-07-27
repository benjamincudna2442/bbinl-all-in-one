import aiohttp
import asyncio
import telebot
from flag_data import COUNTRY_FLAGS

def register(bot: telebot.TeleBot, custom_command_handler, command_prefixes_list): 
    @custom_command_handler("bin")
    def handle_bin_command(message):

        command_text = message.text.split(" ", 1)[0].lower() 
        actual_command = ""
        for prefix in command_prefixes_list: 
            if command_text.startswith(f"{prefix}bin"):
                actual_command = f"{prefix}bin"
                break

        # যদি কোনো আর্গুমেন্ট না থাকে (যেমন শুধু /bin বা .bin)
        if not message.text[len(actual_command):].strip(): 
            bot.reply_to(message, "❗ একটি BIN দিন যেমন: `/bin 426633`, `.bin 426633` অথবা `,bin 426633`", parse_mode="Markdown")
            return

        # BIN নাম্বার বের করার জন্য পরিবর্তিত লজিক
        bin_number_raw = message.text[len(actual_command):].strip().split()[0]
        bin_number = ''.join(filter(str.isdigit, bin_number_raw))


        try:
            bin_info = asyncio.run(lookup_bin(bin_number))

            if "error" in bin_info:
                bot.reply_to(message, f"❌ ত্রুটি: {bin_info['error']}")
                return

            user = message.from_user
            request_by = (
                f"@{user.username}" if user.username else
                f"{user.first_name or ''} {user.last_name or ''}".strip() if (user.first_name or user.last_name) else
                f"User ID: {user.id}"
            )

            formatted = (
                f"𝗕𝗜𝗡 ⇾ `{bin_number}`\n"
                f"𝗦𝗼𝘂𝗿𝗰𝗲: {bin_info.get('source', '❓ UNKNOWN')}\n\n"
                f"•──────────────────────•\n"
                f"𝗧𝘆𝗽𝗲: {(bin_info.get('type') or 'Error').upper()} ({(bin_info.get('scheme') or 'Error').upper()})\n"
                f"𝗕𝗿𝗮𝗻𝗱: {(bin_info.get('tier') or 'Error').upper()}\n"
                f"𝐈𝐬𝐬𝐲𝐮𝐞𝐫: {(bin_info.get('bank') or 'Error').upper()}\n"
                f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {(bin_info.get('country') or 'Error').upper()} {bin_info.get('flag', '🏳️')}\n"
                f"𝗖𝘂𝗿𝗿𝗲𝗻𝗰𝘆: {bin_info.get('currency', 'Error')} | 𝗖𝗼𝗱𝗲: {bin_info.get('country_code', 'N/A')}\n"
                f"•──────────────────────•\n\n"
                f"𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗯𝘆: {request_by}    |    𝗝𝗼𝗶𝗻: @bro_bin_lagbe"
            )

            bot.reply_to(message, formatted, parse_mode="Markdown")

        except Exception as e:
            bot.reply_to(message, f"❌ Internal error: {str(e)}")


async def lookup_bin(bin_number: str) -> dict:
    bin_to_use = ''.join(filter(str.isdigit, bin_number))[:6]
    headers = { "User-Agent": "Mozilla/5.0" }

    # 1️⃣ Your Own API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://cc-gen-test.vercel.app/bin/{bin_to_use}") as res:
                if res.status == 200:
                    data = await res.json()
                    country = (data.get("country") or "").upper()
                    return {
                        "type": data.get("type"),
                        "scheme": data.get("scheme"),
                        "tier": data.get("tier"),
                        "bank": data.get("bank"),
                        "country": country,
                        "currency": data.get("currency"),
                        "country_code": data.get("country_code"),
                        "flag": data.get("flag") or COUNTRY_FLAGS.get(country, "🏳️"),
                        "source": "1️⃣ CC-Gen API"
                    }
    except Exception as e:
        print("Your API fallback:", e)

    # 2️⃣ HandyAPI
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://data.handyapi.com/bin/{bin_to_use}",
                headers={**headers, "x-api-key": "handyapi-PUB-0YI0cklUYMv1njw6Q597r4C7KqB"}
            ) as res:
                if res.status == 200:
                    data = await res.json()
                    country = (data.get("Country", {}).get("Name") or "").upper()
                    return {
                        "type": data.get("Type"),
                        "scheme": data.get("Scheme"),
                        "tier": data.get("CardTier"),
                        "bank": data.get("Issuer"),
                        "country": country,
                        "currency": "N/A",
                        "country_code": data.get("Country", {}).get("Alpha2", "N/A"),
                        "flag": COUNTRY_FLAGS.get(country, "🏳️"),
                        "prepaid": False,
                        "luhn": True,
                        "source": "2️⃣ HandyAPI"
                    }
    except Exception as e:
        print("handyapi fallback:", e)

    # 3️⃣ Binlist.net
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://lookup.binlist.net/{bin_to_use}", headers=headers) as res:
                if res.status == 200:
                    data = await res.json()
                    country = (data.get("country", {}).get("name") or "").upper()
                    return {
                        "type": data.get("type"),
                        "scheme": data.get("scheme"),
                        "tier": data.get("brand"),
                        "bank": data.get("bank", {}).get("name"),
                        "country": country,
                        "currency": data.get("country", {}).get("currency"),
                        "country_code": data.get("country", {}).get("alpha2"),
                        "flag": data.get("country", {}).get("emoji", "🏳️"),
                        "prepaid": data.get("number", {}).get("prepaid", False),
                        "luhn": data.get("number", {}).get("luhn", True),
                        "source": "3️⃣ Binlist"
                    }
    except Exception as e:
        print("binlist fallback:", e)

    # 4️⃣ DrLab API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://drlabapis.onrender.com/api/bin?bin={bin_to_use}", headers=headers) as res:
                if res.status == 200:
                    data = await res.json()
                    if data.get("status") == "ok":
                        country = (data.get("country") or "").upper()
                        return {
                            "type": data.get("type"),
                            "scheme": data.get("scheme"),
                            "tier": data.get("tier"),
                            "bank": data.get("issuer"),
                            "country": country,
                            "currency": "N/A",
                            "country_code": "N/A",
                            "flag": COUNTRY_FLAGS.get(country, "🏳️"),
                            "prepaid": False,
                            "luhn": True,
                            "source": "4️⃣ DrLab API"
                        }
    except Exception as e:
        print("drlab fallback:", e)

    # 5️⃣ Bingen.vercel.app
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://bingen-rho.vercel.app/?bin={bin_to_use}", headers=headers) as res:
                if res.status == 200:
                    data = await res.json()
                    bin_info = data.get("bin_info", {})
                    country = (bin_info.get("country") or "").upper()
                    return {
                        "type": bin_info.get("type"),
                        "scheme": bin_info.get("scheme"),
                        "tier": bin_info.get("brand"),
                        "bank": bin_info.get("bank"),
                        "country": country,
                        "currency": "N/A",
                        "country_code": bin_info.get("country_code", "N/A"),
                        "flag": bin_info.get("flag", "🏳️"),
                        "prepaid": False,
                        "luhn": True,
                        "source": "5️⃣ Bingen"
                    }
    except Exception as e:
        print("bingen fallback:", e)

    return {"error": "BIN info not found in any source"}
