def register(bot, custom_command_handler, command_prefixes_list): 
    @custom_command_handler("start")
    @custom_command_handler("arise")
    def start_command(message):
        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name

        welcome_text = (
            f"👋 <b>Welcome {username}!</b>\n\n"
            "🛠 <b>Available Commands:</b>\n\n"

            "<code>/arise</code> or <code>.arise</code> — Start the bot\n"
            "<code>/gen</code> or <code>.gen</code> — Generate random cards with BIN info\n"
            "<code>/chk</code> or <code>.chk</code> — Check a single card's status\n"
            "<code>/mas</code> or <code>.mas</code> — Check all generated cards at once (reply to a list)\n"
            "<code>/fake</code> or <code>.fake</code> — Get fake address\n"
            "<code>/country</code> or <code>.country</code> — Check available countries\n"
            "<code>/imagine</code> or <code>.imagine</code> — Generate AI images\n"
            "<code>/bgremove</code> or <code>.bgremove</code> — Remove image background\n"
            "<code>/download</code> or <code>.download</code> — Download videos from YT, FB & Insta\n"
            "<code>/gemini</code> or <code>.gemini</code> — Talk to Gemini\n"
            "<code>/gpt</code> or <code>.gpt</code> — Talk to GPT\n"
            "<code>/say</code> or <code>.say</code> — Text to speech\n"
            "<code>/spam</code> or <code>.spam</code> — spam text or imprase ut gf using /spmtxt i love u 1000\n"
            "<code>/translate</code> or <code>.translate</code> — Translate texts\n"
            "<code>/info</code> or <code>.info</code> — Get Telegram user/bot/group/channel info\n"
            "<code>/iban</code> or <code>.iban</code> — generate Iban using 1. germeny - de 2. united kingdom - gb 3. netherlands - nl \n"
            "<code>/reveal</code> or <code>.reveal</code> — Show all commands\n\n"

            "🔸 <b>বিশেষ দ্রষ্টব্য:</b> আপনি !, #, ', বা অন্য কোনো চিহ্ন দিয়েও কমান্ড চালাতে পারবেন।\n\n"
            "📢 <b>Join our Telegram Channel:</b>\n"
            "<a href='https://t.me/bro_bin_lagbe'>https://t.me/bro_bin_lagbe</a>"
        )

        bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")
