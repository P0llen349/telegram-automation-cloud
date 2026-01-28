"""
CLOUD AUTOMATION BOT V2 - Google Drive Queue Version
=====================================================

Telegram bot that uses Google Drive as a queue to trigger local automation.

Architecture:
- Bot receives "RUNNIT" command from Telegram
- Writes command to Google Drive queue
- Polls Google Drive for results
- Sends results back to Telegram

Work computer polls Google Drive and runs local automation when command found.

Author: Mohammad Khair AbuShanab
Created: January 28, 2026
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import Optional

# Telegram imports
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    print("ERROR: python-telegram-bot not installed!")
    sys.exit(1)

# Local imports
from gdrive_queue import GoogleDriveQueue

# =============================================================================
# CONFIGURATION - From Environment Variables
# =============================================================================

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "8401341002:AAHf4fB2bp4JATnaYo3RbK9EG_ziRHxz1f4")
AUTHORIZED_USER_ID = int(os.getenv("AUTHORIZED_USER_ID", "1003476862"))
TRIGGER_CODEWORD = os.getenv("TRIGGER_CODEWORD", "RUNNIT")

# Google credentials
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
GOOGLE_CREDENTIALS_BASE64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")  # Shared folder ID
GOOGLE_DRIVE_COMMANDS_FOLDER_ID = os.getenv("GOOGLE_DRIVE_COMMANDS_FOLDER_ID", "1KXAvAJu_-PCZiWMw-X3X8Alm4UBhR-3L")
GOOGLE_DRIVE_RESULTS_FOLDER_ID = os.getenv("GOOGLE_DRIVE_RESULTS_FOLDER_ID", "1q98oa_FMebqfkRwBCAxe78wUHjjVC64b")

# Polling settings
RESULT_POLL_INTERVAL = 10  # Check for results every 10 seconds
RESULT_TIMEOUT = 300  # Give up after 5 minutes

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# GOOGLE DRIVE QUEUE
# =============================================================================

# Global queue instance
queue = None

def init_queue():
    """Initialize Google Drive queue."""
    global queue
    try:
        logger.info("Initializing Google Drive queue...")
        logger.info(f"GOOGLE_DRIVE_FOLDER_ID: {GOOGLE_DRIVE_FOLDER_ID}")
        import tempfile
        import base64

        # Try base64 encoded credentials first (preferred for Railway)
        if GOOGLE_CREDENTIALS_BASE64:
            logger.info("Using base64 encoded credentials...")

            # Decode from base64
            creds_json = base64.b64decode(GOOGLE_CREDENTIALS_BASE64).decode('utf-8')

            # Create temp file
            temp_creds = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            temp_creds.write(creds_json)
            temp_creds.close()

            logger.info(f"Credentials written to: {temp_creds.name}")

            # Initialize queue with temp file and folder IDs
            queue = GoogleDriveQueue(
                temp_creds.name,
                parent_folder_id=GOOGLE_DRIVE_FOLDER_ID,
                commands_folder_id=GOOGLE_DRIVE_COMMANDS_FOLDER_ID,
                results_folder_id=GOOGLE_DRIVE_RESULTS_FOLDER_ID
            )

        # Try regular JSON from environment variable
        elif GOOGLE_CREDENTIALS_JSON and not os.path.isfile(GOOGLE_CREDENTIALS_JSON):
            logger.info("Using JSON credentials from environment...")

            # Create temp file
            temp_creds = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)

            # Clean and write JSON
            creds_json = GOOGLE_CREDENTIALS_JSON.strip()

            # Remove any leading/trailing quotes if present
            if creds_json.startswith('"') and creds_json.endswith('"'):
                creds_json = creds_json[1:-1]
            if creds_json.startswith("'") and creds_json.endswith("'"):
                creds_json = creds_json[1:-1]

            # Write to file
            temp_creds.write(creds_json)
            temp_creds.close()

            logger.info(f"Credentials written to: {temp_creds.name}")

            # Initialize queue with temp file and folder IDs
            queue = GoogleDriveQueue(
                temp_creds.name,
                parent_folder_id=GOOGLE_DRIVE_FOLDER_ID,
                commands_folder_id=GOOGLE_DRIVE_COMMANDS_FOLDER_ID,
                results_folder_id=GOOGLE_DRIVE_RESULTS_FOLDER_ID
            )

        # Use file path directly (for local testing)
        else:
            logger.info("Using credentials file path...")
            queue = GoogleDriveQueue(
                GOOGLE_CREDENTIALS_JSON,
                parent_folder_id=GOOGLE_DRIVE_FOLDER_ID,
                commands_folder_id=GOOGLE_DRIVE_COMMANDS_FOLDER_ID,
                results_folder_id=GOOGLE_DRIVE_RESULTS_FOLDER_ID
            )

        logger.info("✓ Google Drive queue ready")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Google Drive queue: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# =============================================================================
# TELEGRAM BOT HANDLERS
# =============================================================================

def is_authorized(user_id: int) -> bool:
    """Check if user is authorized"""
    return user_id == AUTHORIZED_USER_ID

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    logger.info(f"/start from user {user_id} ({username})")

    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Unauthorized access")
        return

    message = (
        "🤖 *Cloud Automation Bot V2*\n\n"
        "✅ You are authorized!\n\n"
        f"📝 Send `{TRIGGER_CODEWORD}` to trigger automation\n\n"
        "⚡ Commands:\n"
        f"• `{TRIGGER_CODEWORD}` - Run automation\n"
        "• `/status` - Check status\n"
        "• `/help` - Show help\n\n"
        "☁️ Using Google Drive queue!\n"
        "💻 Work computer will process your request"
    )

    await update.message.reply_text(message, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command"""
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Check queue status
    try:
        pending_commands = queue.check_commands()
        pending_results = queue.check_results()

        message = (
            "📊 *Bot Status*\n\n"
            "🤖 Bot: ✅ Running\n"
            f"☁️ Queue: ✅ Connected\n"
            f"📝 Pending commands: {len(pending_commands)}\n"
            f"📊 Pending results: {len(pending_results)}\n"
            f"👤 Authorized: {AUTHORIZED_USER_ID}\n"
            f"🔑 Trigger: `{TRIGGER_CODEWORD}`\n\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except:
        message = (
            "📊 *Bot Status*\n\n"
            "🤖 Bot: ✅ Running\n"
            f"☁️ Queue: ❌ Error\n"
            f"👤 Authorized: {AUTHORIZED_USER_ID}\n"
            f"🔑 Trigger: `{TRIGGER_CODEWORD}`\n\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    await update.message.reply_text(message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    message = (
        "📖 *Help - Cloud Automation Bot V2*\n\n"
        f"🚀 *Trigger Automation:*\n"
        f"Send `{TRIGGER_CODEWORD}`\n\n"
        "📋 *How it works:*\n"
        "1️⃣ You send command from anywhere\n"
        "2️⃣ Bot writes to Google Drive queue\n"
        "3️⃣ Your work computer picks it up\n"
        "4️⃣ Automation runs on work computer\n"
        "5️⃣ Results sent back via queue\n"
        "6️⃣ Bot sends you confirmation!\n\n"
        "⏱️ Duration: ~20-40 seconds\n"
        "💡 Works from anywhere in the world!"
    )

    await update.message.reply_text(message, parse_mode='Markdown')

async def wait_for_result(command_id: str, update: Update) -> Optional[dict]:
    """
    Poll Google Drive for result of a command.

    Args:
        command_id: Command ID to wait for
        update: Telegram update object (for status messages)

    Returns:
        dict: Result data or None if timeout
    """
    start_time = datetime.now()
    elapsed = 0

    while elapsed < RESULT_TIMEOUT:
        try:
            # Check for results
            results = queue.check_results(command_id)

            if results:
                # Found result!
                result = results[0]
                logger.info(f"✓ Result received for {command_id}")

                # Delete result file
                queue.delete_result(result['file_id'])

                return result

            # Wait before next check
            await asyncio.sleep(RESULT_POLL_INTERVAL)

            elapsed = (datetime.now() - start_time).total_seconds()

            # Send progress update every 30 seconds
            if int(elapsed) % 30 == 0 and elapsed > 0:
                await update.message.reply_text(
                    f"⏳ Still waiting... ({int(elapsed)}s elapsed)",
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Error checking results: {e}")
            await asyncio.sleep(RESULT_POLL_INTERVAL)
            elapsed = (datetime.now() - start_time).total_seconds()

    # Timeout
    logger.warning(f"Timeout waiting for result of {command_id}")
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages"""
    user_id = update.effective_user.id
    message_text = update.message.text.strip()

    logger.info(f"Message from {user_id}: {message_text}")

    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    if message_text.upper() == TRIGGER_CODEWORD.upper():
        logger.info(f"Trigger detected from user {user_id}")

        # Send initial confirmation
        await update.message.reply_text(
            "🚀 *Automation Triggered!*\n\n"
            "📝 Writing command to Google Drive queue...\n"
            "⏳ Waiting for your work computer to pick it up...\n\n"
            "This may take 20-60 seconds depending on polling interval.",
            parse_mode='Markdown'
        )

        try:
            # Write command to Google Drive queue
            command_id = queue.write_command("RUNNIT", {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })

            if not command_id:
                await update.message.reply_text(
                    "❌ *Failed to write command*\n\n"
                    "Could not write to Google Drive queue.",
                    parse_mode='Markdown'
                )
                return

            logger.info(f"✓ Command written: {command_id}")

            # Send confirmation
            await update.message.reply_text(
                "✅ *Command queued successfully!*\n\n"
                f"📋 Command ID: `{command_id}`\n\n"
                "⏳ Waiting for work computer to process...\n"
                "I'll notify you when it's done!",
                parse_mode='Markdown'
            )

            # Wait for result
            result = await wait_for_result(command_id, update)

            if result:
                # Got result!
                if result.get('success'):
                    message = (
                        "✅ *AUTOMATION COMPLETED!*\n\n"
                        f"📝 {result.get('message', 'Automation finished successfully')}\n\n"
                    )

                    # Add any additional data
                    data = result.get('data', {})
                    if data:
                        message += "📊 *Details:*\n"
                        if 'tickets_processed' in data:
                            message += f"• Tickets: {data['tickets_processed']}\n"
                        if 'duration' in data:
                            message += f"• Duration: {data['duration']:.1f}s\n"
                        if 'sheets_url' in data:
                            message += f"\n🔗 [View Google Sheets]({data['sheets_url']})"

                    await update.message.reply_text(message, parse_mode='Markdown')
                else:
                    # Failed
                    await update.message.reply_text(
                        f"❌ *Automation Failed*\n\n{result.get('message', 'Unknown error')}",
                        parse_mode='Markdown'
                    )
            else:
                # Timeout
                await update.message.reply_text(
                    "⏰ *Timeout*\n\n"
                    "Did not receive result within 5 minutes.\n\n"
                    "⚠️ Possible issues:\n"
                    "• Work computer is offline\n"
                    "• Polling script not running\n"
                    "• Google Drive access issue\n\n"
                    "Check work computer status.",
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Error handling trigger: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ *Error*\n\n{str(e)}",
                parse_mode='Markdown'
            )

    else:
        await update.message.reply_text(
            f"❓ Unknown command: `{message_text}`\n\n"
            f"Send `{TRIGGER_CODEWORD}` to trigger automation",
            parse_mode='Markdown'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Main function - start the bot"""

    logger.info("="*70)
    logger.info("CLOUD AUTOMATION BOT V2 - GOOGLE DRIVE QUEUE")
    logger.info("="*70)
    logger.info(f"Authorized user: {AUTHORIZED_USER_ID}")
    logger.info(f"Trigger codeword: {TRIGGER_CODEWORD}")
    logger.info("="*70)

    # Initialize Google Drive queue
    if not init_queue():
        logger.error("Failed to initialize queue. Exiting.")
        sys.exit(1)

    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_error_handler(error_handler)

        # Start polling
        logger.info("Bot is now running... Press Ctrl+C to stop")
        logger.info("Using Google Drive queue for work computer communication")
        application.run_polling(
            poll_interval=30,
            timeout=10,
            drop_pending_updates=True
        )

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
