"""
WORK COMPUTER POLLER
====================

Runs on your work computer and polls Google Sheets for automation commands.
When a command is found, runs the local automation and writes results back.

Author: Mohammad Khair AbuShanab
Created: January 28, 2026
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sheets_queue import GoogleSheetsQueue

# =============================================================================
# CONFIGURATION
# =============================================================================

# Google Sheets credentials
GOOGLE_CREDENTIALS_FILE = Path(__file__).parent / "google_credentials.json"
GOOGLE_SHEET_QUEUE_ID = "1bfdWgSWpk25wt0tq5PPLuLySfJ-Vm4Ou7TVR2gVprag"  # Queue sheet ID (same as cloud bot)

# Local automation script
AUTOMATION_SCRIPT = Path("C:/Users/mshanab/AAA-Mohammad Khair AbuShanab/ULTIMATE_BACKUP_FOLDER/Project_Organization/RUN_COMPLETE_AUTOMATION_AUTO.bat")

# Polling settings
POLL_INTERVAL = 15  # Check every 15 seconds

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Create logs directory
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"work_poller_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# AUTOMATION RUNNER
# =============================================================================

def run_local_automation():
    """
    Run the local automation script.

    Returns:
        tuple: (success, message, data)
    """
    try:
        logger.info("="*70)
        logger.info("RUNNING LOCAL AUTOMATION")
        logger.info("="*70)

        if not AUTOMATION_SCRIPT.exists():
            error_msg = f"Automation script not found: {AUTOMATION_SCRIPT}"
            logger.error(error_msg)
            return False, error_msg, {}

        start_time = datetime.now()

        # Run the batch file
        logger.info(f"Executing: {AUTOMATION_SCRIPT}")

        result = subprocess.run(
            [str(AUTOMATION_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=AUTOMATION_SCRIPT.parent,
            shell=True
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Automation completed in {duration:.1f} seconds")
        logger.info(f"Return code: {result.returncode}")

        # DEBUG: Log the actual output (full)
        if result.stdout:
            logger.info(f"STDOUT (length={len(result.stdout)}):\n{result.stdout}")
        if result.stderr:
            logger.info(f"STDERR:\n{result.stderr}")

        if result.returncode == 0:
            # Success! Parse details from output
            import re
            output = result.stdout

            # Extract details from output
            email_subject = ""
            email_date = ""
            files_downloaded = 0
            workflow_success = False
            uploaded_to_sheets = False

            # Parse email subject
            subject_match = re.search(r'Subject\s*:\s*(.+)', output)
            if subject_match:
                email_subject = subject_match.group(1).strip()

            # Parse email date
            date_match = re.search(r'Date Received\s*:\s*(.+)', output)
            if date_match:
                email_date = date_match.group(1).strip()

            # Parse files downloaded
            files_match = re.search(r'Downloaded (\d+) new file', output)
            if files_match:
                files_downloaded = int(files_match.group(1))

            # Check for success markers
            if '[SUCCESS] COMPLETE WORKFLOW FINISHED SUCCESSFULLY' in output:
                workflow_success = True

            if 'Data uploaded to Google Sheets' in output:
                uploaded_to_sheets = True

            # Build detailed message
            if workflow_success:
                success_msg = f"Workflow completed in {duration:.1f}s"
                if email_subject:
                    success_msg = f"Processed: {email_subject[:50]}"
            else:
                success_msg = f"Automation ran in {duration:.1f}s (check logs)"

            logger.info(success_msg)

            data = {
                "duration": duration,
                "email_subject": email_subject,
                "email_date": email_date,
                "files_downloaded": files_downloaded,
                "workflow_success": workflow_success,
                "uploaded_to_sheets": uploaded_to_sheets,
                "sheets_url": "https://docs.google.com/spreadsheets/d/13x58yfkrvA9_7bo-Wtzw6EwcPVCjE8x2IUmkF8c6Aro/edit"
            }

            return True, success_msg, data

        else:
            # Failed
            error_msg = f"Automation failed with exit code {result.returncode}"
            logger.error(error_msg)

            # Log stderr if available
            if result.stderr:
                logger.error(f"Error output:\n{result.stderr[:500]}")

            return False, error_msg, {"exit_code": result.returncode}

    except Exception as e:
        error_msg = f"Error running automation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg, {}

# =============================================================================
# POLLING LOOP
# =============================================================================

def process_command(queue, command):
    """
    Process a command from the queue.

    Args:
        queue: GoogleDriveQueue instance
        command: Command dictionary

    Returns:
        bool: True if processed successfully
    """
    try:
        command_type = command.get('command')
        command_id = command.get('filename', '').replace('.json', '')
        file_id = command.get('file_id')

        logger.info("="*70)
        logger.info(f"PROCESSING COMMAND: {command_type}")
        logger.info(f"Command ID: {command_id}")
        logger.info("="*70)

        if command_type == "RUNNIT":
            # Run the automation
            success, message, data = run_local_automation()

            # Write result to queue
            logger.info("Writing result to Google Sheets...")
            result_id = queue.write_result(command_id, success, message, data)

            if result_id:
                logger.info(f"✓ Result written: {result_id}")
            else:
                logger.error("Failed to write result")

            # Delete command file
            logger.info("Deleting command file...")
            queue.delete_command(row_number=command.get('row_number'))

            return True

        else:
            logger.warning(f"Unknown command type: {command_type}")
            # Delete unknown command
            queue.delete_command(row_number=command.get('row_number'))
            return False

    except Exception as e:
        logger.error(f"Error processing command: {e}", exc_info=True)
        return False

def polling_loop(queue):
    """
    Main polling loop.

    Args:
        queue: GoogleDriveQueue instance
    """
    logger.info("="*70)
    logger.info("WORK COMPUTER POLLER - STARTED")
    logger.info("="*70)
    logger.info(f"Polling interval: {POLL_INTERVAL} seconds")
    logger.info(f"Automation script: {AUTOMATION_SCRIPT}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("="*70)
    logger.info("Waiting for commands...")

    consecutive_errors = 0
    max_consecutive_errors = 10

    while True:
        try:
            # Check for commands
            commands = queue.check_commands()

            if commands:
                logger.info(f"Found {len(commands)} command(s) in queue")

                for command in commands:
                    process_command(queue, command)

                logger.info("All commands processed. Waiting for next poll...")
            else:
                # No commands - just log every 10 polls
                if int(time.time()) % (POLL_INTERVAL * 10) == 0:
                    logger.info(f"Still polling... ({datetime.now().strftime('%H:%M:%S')})")

            # Reset error counter on success
            consecutive_errors = 0

            # Wait before next poll
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Poller stopped by user")
            break

        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error in polling loop: {e}", exc_info=True)

            if consecutive_errors >= max_consecutive_errors:
                logger.error(f"Too many consecutive errors ({consecutive_errors}). Exiting.")
                break

            # Wait before retrying
            logger.info(f"Waiting {POLL_INTERVAL} seconds before retry...")
            time.sleep(POLL_INTERVAL)

# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Main function"""

    # Check if automation script exists
    if not AUTOMATION_SCRIPT.exists():
        logger.error(f"Automation script not found: {AUTOMATION_SCRIPT}")
        logger.error("Please update AUTOMATION_SCRIPT path in this file")
        return

    # Initialize Google Sheets queue
    try:
        logger.info("Initializing Google Sheets queue...")
        queue = GoogleSheetsQueue(
            str(GOOGLE_CREDENTIALS_FILE),
            sheet_id=GOOGLE_SHEET_QUEUE_ID
        )
        logger.info("✓ Google Sheets queue initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets queue: {e}")
        logger.error("Make sure google_credentials.json exists in the same folder")
        return

    # Start polling
    try:
        polling_loop(queue)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
