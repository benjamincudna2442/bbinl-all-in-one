import requests
import re
import base64
from telebot import types
from telebot.types import Message, CallbackQuery
import io

def encode_data(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).decode()

def decode_data(encoded: str) -> str:
    return base64.urlsafe_b64decode(encoded.encode()).decode()

def generate_cards_via_api(bin_input, count, month=None, year=None, cvv=None):
    params = {
        "bin": bin_input,
        "limit": count
    }
    if month:
        params["month"] = month
    if year:
        params["year"] = year
    if cvv:
        params["cvv"] = cvv

    try:
        url = "https://cc-gen-test.vercel.app/generate"
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            cards = []
            for card in data.get("cards", []):
                card_number = card.get("number")
                expiry = card.get("expiry")
                cvv_code = card.get("cvv")
                cards.append(f"{card_number}|{expiry.replace('/', '|')}|{cvv_code}")

            bin_info = data.get("bin_info", None)
            return {
                "cards": cards,
                "info": {
                    "brand": bin_info.get("scheme", "N/A").upper() if bin_info else "N/A",
                    "type": bin_info.get("type", "N/A").upper() if bin_info else "N/A",
                    "level": bin_info.get("tier", "N/A").upper() if bin_info else "N/A",
                    "bank": bin_info.get("bank", "N/A") if bin_info else "N/A",
                    "country": bin_info.get("country", "N/A") if bin_info else "N/A",
                    "flag": bin_info.get("flag", "") if bin_info else "",
                }
            }
        elif response.status_code == 400: 
            error_data = response.json()
            print(f"API Error (400): {error_data.get('message', 'Unknown error')}")
            return {"error": error_data.get("message", "Invalid BIN or parameters.")}
        else:
            print(f"API request failed with status code: {response.status_code}")
            return {"error": f"API request failed with status code: {response.status_code}"}

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return {"error": f"Network error or API is down: {e}"}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": f"An unexpected error occurred: {e}"}

# Function to create a text file from a list of cards
def create_text_file(cards):
    file_content = "\n".join(cards)
    file_obj = io.BytesIO(file_content.encode())
    file_obj.name = "generated_cards.txt"
    return file_obj

# Function to extract BIN, Month, Year, CVV from a given text
def extract_bin_from_text(text: str):
    bin_part = None
    month = None
    year = None
    cvv = None

    full_format_match = re.search(
        r'(\d{6,16}(?:x{0,10}|X{0,10})?)\s*[|/]?\s*(\d{1,2})?\s*[|/]?\s*(\d{2,4})?\s*[|/]?\s*(\d{3,4}|rnd)?',
        text, re.IGNORECASE
    )
    if full_format_match:
        extracted_bin = full_format_match.group(1)
        bin_part = re.match(r'^\d+', extracted_bin).group(0) if re.match(r'^\d+', extracted_bin) else None

        month = full_format_match.group(2)
        year = full_format_match.group(3)
        cvv = full_format_match.group(4)

        if month and len(month) == 1:
            month = '0' + month
        if year and len(year) == 2:
            current_year_prefix = 20 if int(year) < 50 else 19 
            year = str(current_year_prefix) + year
        if cvv and cvv.lower() == 'rnd':
            cvv = None 

        if bin_part: 
            return bin_part, month, year, cvv

    bin_patterns = [
        r'\b(?:BIN|Bin|𝗕𝗶𝗻|💳|B\s?I\s?N)\s*[:]?\s*(\d{6,16}(?:x{0,10}|X{0,10})?)\b',
        r'\b(\d{15,16}(?:x{0,10}|X{0,10})?)\b', 
        r'\b(\d{6,10}(?:x{0,10}|X{0,10})?)\s*\|\d{1,2}\|\d{2,4}\b' 
    ]
    for pattern in bin_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_bin = match.group(1)
            bin_part = re.match(r'^\d+', extracted_bin).group(0) 
            break

    # Month/Year patterns
    month_year_patterns = [
        r'\b(?:Fecha|🗓|𝗙𝗲𝗰𝗵𝗮|Date|Exp|Expiry)\s*[:]?\s*(\d{1,2})[/\s|-](\d{2,4})\b',
        r'\b(\d{1,2})[/\s|-](\d{2,4})\b' 
    ]
    for pattern in month_year_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            month = match.group(1)
            year = match.group(2)
            if len(month) == 1:
                month = '0' + month
            if len(year) == 2:
                current_year_prefix = 20 if int(year) < 50 else 19
                year = str(current_year_prefix) + year
            break

    # CVV patterns
    cvv_patterns = [
        r'\b(?:CVV|Cvv|𝗖𝘃𝘃)\s*[:]?\s*(\d{3,4}|rnd)\b',
        r'\b(\d{3,4}|rnd)\b(?=\s*$|\s*[.,;])' 
    ]
    for pattern in cvv_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            cvv_val = match.group(1)
            if cvv_val.lower() != 'rnd':
                cvv = cvv_val
            break

    return bin_part, month, year, cvv


def register(bot, custom_command_handler, command_prefixes_list): 
    @custom_command_handler("gen")
    def handle_gen(message: Message):
        try:
            bin_part = None
            month = None
            year = None
            cvv = None
            count = 10  

            command_text_full = message.text.split(" ", 1)[0].lower() 
            actual_command_len = 0
            for prefix in command_prefixes_list:
                if command_text_full.startswith(f"{prefix}gen"):
                    actual_command_len = len(f"{prefix}gen")
                    break

            full_input_after_command = message.text[actual_command_len:].strip()

            if message.reply_to_message:
                replied_text = message.reply_to_message.text or message.reply_to_message.caption
                if replied_text:
                    bin_part, month, year, cvv = extract_bin_from_text(replied_text)

                    if full_input_after_command and full_input_after_command.isdigit():
                        count = int(full_input_after_command)
                        count = min(count, 1000)
                    elif not bin_part:  
                        bot.reply_to(message, "❌ দুঃখিত! উত্তর দেওয়া মেসেজ থেকে কোনো বৈধ BIN খুঁজে পাওয়া যায়নি।", parse_mode="Markdown") 
                        return
                else:
                    bot.reply_to(message, "❌ উত্তর দেওয়া মেসেজে কোনো টেক্সট বা ক্যাপশন নেই যা থেকে BIN এক্সট্র্যাক্ট করা যায়।", parse_mode="Markdown") 
                    return
            else: 
                if not full_input_after_command: 
                    bot.reply_to(message, f"❌ BIN অনুপস্থিত। উদাহরণ: `{command_prefixes_list[0]}gen 515462xxxxxx|02|28|573 5` অথবা `{command_prefixes_list[1]}gen 515462xxxxxx|02|28|573 5`", parse_mode="Markdown") 
                    return

                full_input = full_input_after_command
                parts = full_input.split()

                # Check if the last part is a number (for count)
                if len(parts) > 1 and parts[-1].isdigit():
                    count = int(parts[-1])
                    count = min(count, 1000)
                    base_input = " ".join(parts[:-1]).strip()
                else:
                    base_input = full_input
                   
                input_parts_cc = re.split(r"[|/]", base_input)
                bin_part = input_parts_cc[0]
                month = input_parts_cc[1] if len(input_parts_cc) > 1 else None
                year = input_parts_cc[2] if len(input_parts_cc) > 2 else None
                cvv = input_parts_cc[3] if len(input_parts_cc) > 3 else None

                # Normalize month if single digit
                if month and len(month) == 1:
                    month = '0' + month
                # Normalize year to 4 digits if 2 digits are found
                if year and len(year) == 2:
                    current_year_prefix = 20 if int(year) < 50 else 19
                    year = str(current_year_prefix) + year

            if not bin_part: 
                bot.reply_to(message, "❌ BIN খুঁজে পাওয়া যায়নি। দয়া করে আপনার ইনপুট বা উত্তর দেওয়া মেসেজ চেক করুন।", parse_mode="Markdown") # Changed parse_mode
                return

            # Call API to generate cards
            result = generate_cards_via_api(bin_part, count, month, year, cvv)

            if result and "error" in result:
                bot.reply_to(message, f"❌ কার্ড জেনারেট করা যায়নি: {result['error']}")
                return
            elif not result or not result.get("cards"):
                bot.reply_to(message, "❌ কার্ড জেনারেট করতে ব্যর্থ। API ডাউন থাকতে পারে অথবা ইনপুট অবৈধ।")
                return

            cards = result["cards"]
            info = result.get("info")
            username = message.from_user.first_name or "User"

            if count > 10:
                file = create_text_file(cards)
                caption = (
                    f"𝗕𝗜𝗡 ⇾ <code>{bin_part}</code>\n"
                    f"𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ {count}\n\n"
                    f"𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗯𝘆: {username}    |    𝗝𝗼𝗶𝗻: @bro_bin_lagbe"
                )
                bot.send_document(
                    chat_id=message.chat.id,
                    document=file,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                msg = (
                    f"𝗕𝗜𝗡 ⇾ <code>{bin_part}</code>\n"
                    f"𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ {count}\n\n"
                    f"•──────────────────────•\n"
                    + "\n".join([f"<code>{card}</code>" for card in cards]) +
                    f"\n•──────────────────────•\n\n"
                )
                if info:
                    msg += (
                        f"𝗜𝗻𝗳𝗼: {info['brand']} - {info['type']} - {info['level']}\n"
                        f"𝗕𝗮𝗻𝗸: {info['bank']}\n"
                        f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {info['country']} {info['flag']}\n\n"
                    )
                
                regen_input_data = f"{bin_part}"
                if month:
                    regen_input_data += f"|{month}"
                if year:
                    regen_input_data += f"|{year}"
                if cvv:
                    regen_input_data += f"|{cvv}"
                regen_input_data += f" {count}"  

                msg += f"𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗯𝘆: {username}    |    𝗝𝗼𝗶𝗻: @bro_bin_lagbe"
                encoded_input = encode_data(regen_input_data)
                cb_data = f"regen|{encoded_input}"
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("♻️ Regenerate", callback_data=cb_data))
                bot.reply_to(message, msg, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {str(e)}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("regen|"))
    def handle_regen(call: CallbackQuery):
        try:
            _, encoded_input = call.data.split('|', 1)
            decoded_input = decode_data(encoded_input)

            parts_with_count = decoded_input.split()
            count = 10  
            base_input = decoded_input

            if len(parts_with_count) > 1 and parts_with_count[-1].isdigit():
                count = int(parts_with_count[-1])
                count = min(count, 1000)
                base_input = " ".join(parts_with_count[:-1]).strip()

            parts = re.split(r"[|/]", base_input)
            bin_part = parts[0]
            month = parts[1] if len(parts) > 1 else None
            year = parts[2] if len(parts) > 2 else None
            cvv = parts[3] if len(parts) > 3 else None

            if month and len(month) == 1:
                month = '0' + month
            if year and len(year) == 2:
                current_year_prefix = 20 if int(year) < 50 else 19
                year = str(current_year_prefix) + year

            result = generate_cards_via_api(bin_part, count, month, year, cvv)

            if result and "error" in result:
                bot.answer_callback_query(call.id, f"❌ রি-জেনারেট করা যায়নি: {result['error']}")
                return
            elif not result or not result.get("cards"):
                bot.answer_callback_query(call.id, "❌ কার্ড রি-জেনারেট করতে ব্যর্থ।")
                return

            cards = result["cards"]
            info = result.get("info")
            username = call.from_user.first_name or "User"

            msg = (
                f"𝗕𝗜𝗡 ⇾ <code>{bin_part}</code>\n"
                f"𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ {count}\n\n"
                f"•──────────────────────•\n"
                + "\n".join([f"<code>{card}</code>" for card in cards]) +
                f"\n•──────────────────────•\n\n"
            )
            if info:
                msg += (
                    f"𝗜𝗻𝗳𝗼: {info['brand']} - {info['type']} - {info['level']}\n"
                    f"𝗕𝗮𝗻𝗸: {info['bank']}\n"
                    f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {info['country']} {info['flag']}\n\n"
                )
            msg += f"𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗯𝘆: {username}    |    𝗝𝗼𝗶𝗻: @bro_bin_lagbe"

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("♻️ Regenerate", callback_data=call.data))

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=msg,
                parse_mode="HTML",
                reply_markup=markup
            )
            bot.answer_callback_query(call.id, "✅ কার্ড রি-জেনারেট করা হয়েছে।")

        except Exception as e:
            bot.answer_callback_query(call.id, f"⚠️ Error: {str(e)}")
