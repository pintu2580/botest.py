from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import speedtest
import requests
import logging
import os
import asyncio

# Bot token and admin ID
TOKEN = '7543854356:AAEGsi9keaw5yGkIw6Af-N6hx2BenST881Y'
ADMIN_ID = 5218430002

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with interactive buttons."""
    keyboard = [
        [InlineKeyboardButton("Run Speed Test", callback_data='speedtest')],
        [InlineKeyboardButton("Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Welcome to the Speed Test Bot! 🎉\n'
        'Click the button below to start a speed test or get help.',
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()

    if query.data == 'speedtest':
        await perform_speedtest(query.message, context)
    elif query.data == 'help':
        await show_help(query.message)
    else:
        await query.message.reply_text("Unknown action.")

async def perform_speedtest(message: Update.message, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Perform a speed test, send progress updates, and send results to the user."""
    user = message.from_user
    username = user.username if user.username else user.first_name

    # Send initial message
    sent_message = await message.reply_text("Starting the speed test... Please wait ⏳")

    # Simulate different stages of the test with distinct messages
    stages = [
        "Performing download test 🚀",
        "Performing upload test 📤",
        "Calculating results 🧮"
    ]

    for stage in stages:
        await asyncio.sleep(2)  # Simulate waiting time for each stage
        await sent_message.edit_text(stage)

    # Perform the speed test
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        ping = st.results.ping
    except Exception as e:
        logger.error(f"Error during speed test: {e}")
        await sent_message.edit_text("An error occurred during the speed test. Please try again later.")
        return

    # Collect additional details
    try:
        ip_info = requests.get('https://api.ipify.org?format=json').json()
        ip_address = ip_info.get('ip')
        
        isp_info = requests.get(f'https://ipinfo.io/{ip_address}/json').json()
        isp = isp_info.get('org', 'Unknown')
        city = isp_info.get('city', 'Unknown')
        region = isp_info.get('region', 'Unknown')
        country = isp_info.get('country', 'Unknown')
        district = isp_info.get('district', 'Unknown')

        location = f"{city}, {region}, {district}, {country}" if district != 'Unknown' else f"{city}, {region}, {country}"
    except Exception as e:
        logger.error(f"Error retrieving IP info: {e}")
        ip_address, isp, location = 'Unknown', 'Unknown', 'Unknown'

    # Final result message
    result_message = (
        f"*Speed Test Results:* 🏎️\n\n"
        f"👤 *Username:* `{username}`\n"
        f"📥 *Download Speed:* `{download_speed:.2f} Mbps`\n"
        f"📤 *Upload Speed:* `{upload_speed:.2f} Mbps`\n"
        f"⏱️ *Ping:* `{ping} ms`\n\n"
        f"🌐 *IP Address:* `{ip_address}`\n"
        f"🌍 *ISP:* `{isp}`\n"
        f"📍 *Location:* `{location}`\n"
    )

    # Edit the message with the final result
    await sent_message.edit_text("Speed test completed! 🎉\n\n" + result_message, parse_mode=ParseMode.MARKDOWN)

    # Create a file with the results
    file_path = 'speedtest_results.txt'
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(result_message)

        # Send results to admin as a file
        await context.bot.send_document(chat_id=ADMIN_ID, document=open(file_path, 'rb'), caption="Speed Test Results")
    except Exception as e:
        logger.error(f"Failed to send file to admin: {e}")
        await message.reply_text("Failed to send results to the admin. Please try again later.")

    # Clean up the file
    if os.path.exists(file_path):
        os.remove(file_path)

async def show_help(message: Update.message) -> None:
    """Provide help information."""
    help_message = (
        "*Help - Speed Test Bot* 📚\n\n"
        "Welcome to the Speed Test Bot! Here are some things you can do:\n\n"
        "- Click 'Run Speed Test' to check your internet speed.\n"
        "- Click 'Help' to see this message.\n\n"
        "If you have any questions, feel free to ask!"
    )
    await message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Use asyncio.run to handle the event loop
    try:
        import asyncio
        asyncio.run(application.run_polling())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")

if __name__ == '__main__':
    main()
