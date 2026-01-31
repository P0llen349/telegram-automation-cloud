"""
CLOUD AUTOMATION BOT V3 - Google Sheets Queue Version
======================================================

Telegram bot that uses Google SHEETS as a queue to trigger local automation.
This version avoids the Google Drive storage quota issue!

Architecture:
- Bot receives "RUNNIT" command from Telegram
- Writes command row to Google Sheets queue
- Polls Google Sheets for results
- Sends results back to Telegram

Work computer polls Google Sheets and runs local automation when command found.

Author: Mohammad Khair AbuShanab
Created: January 31, 2026
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

# Local imports - NOW USING SHEETS QUEUE!
from sheets_queue import GoogleSheetsQueue

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

# Google Sheets Queue - Use existing sheet or create new one
GOOGLE_QUEUE_SHEET_ID = os.getenv("GOOGLE_QUEUE_SHEET_ID", "1bfdWgSWpk25wt0tq5PPLuLySfJ-Vm4Ou7TVR2gVprag")

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
# GOOGLE SHEETS QUEUE
# =============================================================================

# Global queue instance
queue = None

def init_queue():
    """Initialize Google Sheets queue."""
    global queue
    try:
        logger.info("Initializing Google Sheets queue...")
        logger.info(f"GOOGLE_QUEUE_SHEET_ID: {GOOGLE_QUEUE_SHEET_ID}")
        import tempfile
        import base64

        credentials_source = None

        # Try base64 encoded credentials first (preferred for Railway)
        if GOOGLE_CREDENTIALS_BASE64:
            logger.info("Using base64 encoded credentials...")

            # Decode from base64
            creds_json = base64.b64decode(GOOGLE_CREDENTIALS_BASE64).decode('utf-8')
            credentials_source = creds_json  # Pass JSON string directly

        # Try regular JSON from environment variable
        elif GOOGLE_CREDENTIALS_JSON and not os.path.isfile(GOOGLE_CREDENTIALS_JSON):
            logger.info("Using JSON credentials from environment...")

            # Clean JSON
            creds_json = GOOGLE_CREDENTIALS_JSON.strip()

            # Remove any leading/trailing quotes if present
            if creds_json.startswith('"') and creds_json.endswith('"'):
                creds_json = creds_json[1:-1]
            if creds_json.startswith("'") and creds_json.endswith("'"):
                creds_json = creds_json[1:-1]

            credentials_source = creds_json

        # Use file path directly (for local testing)
        else:
            logger.info("Using credentials file path...")
            credentials_source = GOOGLE_CREDENTIALS_JSON or "google_credentials.json"

        # Initialize queue
        queue = GoogleSheetsQueue(
            credentials_json=credentials_source,
            sheet_id=GOOGLE_QUEUE_SHEET_ID
        )

        logger.info("Google Sheets queue ready")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets queue: {e}")
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
        await update.message.reply_text("Unauthorized access")
        return

    message = (
        "*Cloud Automation Bot V3*\n\n"
        "You are authorized!\n\n"
        f"Send `{TRIGGER_CODEWORD}` to trigger automation\n\n"
        "Commands:\n"
        f"* `{TRIGGER_CODEWORD}` - Run automation\n"
        "* `/status` - Check status\n"
        "* `/help` - Show help\n\n"
        "Using Google Sheets queue!\n"
        "Work computer will process your request"
    )

    await update.message.reply_text(message, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command"""
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("Unauthorized")
        return

    # Check queue status
    try:
        pending_commands = queue.check_commands()
        pending_results = queue.check_results()

        message = (
            "*Bot Status*\n\n"
            "Bot: Running\n"
            f"Queue: Connected (Sheets)\n"
            f"Pending commands: {len(pending_commands)}\n"
            f"Pending results: {len(pending_results)}\n"
            f"Authorized: {AUTHORIZED_USER_ID}\n"
            f"Trigger: `{TRIGGER_CODEWORD}`\n\n"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except:
        message = (
            "*Bot Status*\n\n"
            "Bot: Running\n"
            f"Queue: Error\n"
            f"Authorized: {AUTHORIZED_USER_ID}\n"
            f"Trigger: `{TRIGGER_CODEWORD}`\n\n"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    await update.message.reply_text(message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("Unauthorized")
        return

    message = (
        "*Help - Cloud Automation Bot V3*\n\n"
        f"*Trigger Automation:*\n"
        f"Send `{TRIGGER_CODEWORD}`\n\n"
        "*How it works:*\n"
        "1. You send command from anywhere\n"
        "2. Bot writes to Google Sheets queue\n"
        "3. Your work computer picks it up\n"
        "4. Automation runs on work computer\n"
        "5. Results sent back via Sheets\n"
        "6. Bot sends you confirmation!\n\n"
        "Duration: ~20-40 seconds\n"
        "Works from anywhere in the world!"
    )

    await update.message.reply_text(message, parse_mode='Markdown')

async def wait_for_result(command_id: str, update: Update) -> Optional[dict]:
    """
    Poll Google Sheets for result of a command.

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
            # Check for results matching our command_id
            results = queue.check_results(command_id)

            if results:
                # Found result!
                result = results[0]
                logger.info(f"Result received for {command_id}")

                # Mark result as processed using row_number
                queue.delete_result(row_number=result.get('row_number'))

                return result

            # Wait before next check
            await asyncio.sleep(RESULT_POLL_INTERVAL)

            elapsed = (datetime.now() - start_time).total_seconds()

            # Send progress update every 30 seconds
            if int(elapsed) % 30 == 0 and elapsed > 0:
                await update.message.reply_text(
                    f"Still waiting... ({int(elapsed)}s elapsed)",
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
        await update.message.reply_text("Unauthorized")
        return

    if message_text.upper() == TRIGGER_CODEWORD.upper():
        logger.info(f"Trigger detected from user {user_id}")

        # Send initial confirmation
        await update.message.reply_text(
            "*Automation Triggered!*\n\n"
            "Writing command to Google Sheets queue...\n"
            "Waiting for your work computer to pick it up...\n\n"
            "This may take 20-60 seconds depending on polling interval.",
            parse_mode='Markdown'
        )

        try:
            # Write command to Google Sheets queue
            command_id = queue.write_command("RUNNIT", {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })

            if not command_id:
                await update.message.reply_text(
                    "*Failed to write command*\n\n"
                    "Could not write to Google Sheets queue.",
                    parse_mode='Markdown'
                )
                return

            logger.info(f"Command written: {command_id}")

            # Send confirmation
            await update.message.reply_text(
                "*Command queued successfully!*\n\n"
                f"Command ID: `{command_id}`\n\n"
                "Waiting for work computer to process...\n"
                "I'll notify you when it's done!",
                parse_mode='Markdown'
            )

            # Wait for result
            result = await wait_for_result(command_id, update)

            if result:
                # Got result!
                if result.get('success'):
                    data = result.get('data', {})

                    # Build rich message with all details
                    message = "*AUTOMATION COMPLETED!*\n\n"

                    # Email info
                    if data.get('email_subject'):
                        message += f"*Email:* {data['email_subject'][:60]}\n"
                    if data.get('email_date'):
                        message += f"*Date:* {data['email_date']}\n"

                    message += "\n"

                    # Status indicators
                    if data.get('workflow_success'):
                        message += "* Download: Done\n"
                        message += "* Processing: Done\n"
                    if data.get('uploaded_to_sheets'):
                        message += "* Upload to Sheets: Done\n"

                    # Ticket Summary
                    ticket_summary = data.get('ticket_summary', {})
                    if ticket_summary:
                        message += "\n*--- TICKET SUMMARY ---*\n"

                        if ticket_summary.get('total_tickets'):
                            message += f"*Total Tickets:* {ticket_summary['total_tickets']}\n"

                        if ticket_summary.get('latest_date'):
                            message += f"*Latest Date:* {ticket_summary['latest_date']}\n"

                        if ticket_summary.get('latest_day_total'):
                            message += f"*Today's Tickets:* {ticket_summary['latest_day_total']}\n"

                        # Breakdown by connection type
                        by_type = ticket_summary.get('by_connection_type', {})
                        if by_type:
                            message += "\n*By Connection Type:*\n"
                            for conn_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]:
                                message += f"  {conn_type}: {count}\n"

                    # Duration
                    if data.get('duration'):
                        message += f"\n*Time:* {data['duration']:.1f} seconds\n"

                    # Link to sheets
                    if data.get('sheets_url'):
                        message += f"\n[Open Google Sheets]({data['sheets_url']})"

                    await update.message.reply_text(message, parse_mode='Markdown')
                else:
                    # Failed
                    await update.message.reply_text(
                        f"*Automation Failed*\n\n{result.get('message', 'Unknown error')}",
                        parse_mode='Markdown'
                    )
            else:
                # Timeout
                await update.message.reply_text(
                    "*Timeout*\n\n"
                    "Did not receive result within 5 minutes.\n\n"
                    "Possible issues:\n"
                    "* Work computer is offline\n"
                    "* Polling script not running\n"
                    "* Google Sheets access issue\n\n"
                    "Check work computer status.",
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Error handling trigger: {e}", exc_info=True)
            await update.message.reply_text(
                f"*Error*\n\n{str(e)}",
                parse_mode='Markdown'
            )

    else:
        await update.message.reply_text(
            f"Unknown command: `{message_text}`\n\n"
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
    logger.info("CLOUD AUTOMATION BOT V3 - GOOGLE SHEETS QUEUE")
    logger.info("="*70)
    logger.info(f"Authorized user: {AUTHORIZED_USER_ID}")
    logger.info(f"Trigger codeword: {TRIGGER_CODEWORD}")
    logger.info("="*70)

    # Initialize Google Sheets queue
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
        logger.info("Using Google SHEETS queue for work computer communication")
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
