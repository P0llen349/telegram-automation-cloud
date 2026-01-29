"""
Google Sheets Queue Manager
============================

Uses Google Sheets as a message queue between cloud bot and work computer.
- Cloud bot writes commands to Sheets (appends rows)
- Work computer polls Sheets for commands (reads rows)
- Work computer writes results back to Sheets (appends rows)
- Cloud bot reads results and sends to Telegram

This avoids the Google Drive storage quota issue entirely!

Author: Mohammad Khair AbuShanab
Created: January 29, 2026
"""

import json
import time
from datetime import datetime
import logging

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: Google API libraries not installed!")
    print("Install: pip install google-auth google-auth-oauthlib google-api-python-client")

logger = logging.getLogger(__name__)


class GoogleSheetsQueue:
    """
    Simple queue system using Google Sheets.

    Sheet structure:
    - Tab "commands": command_id | command | timestamp | data | status
    - Tab "results": result_id | command_id | success | message | timestamp | data | status
    """

    def __init__(self, credentials_json, sheet_id=None):
        """
        Initialize Google Sheets queue.

        Args:
            credentials_json: Path to service account credentials JSON file
            sheet_id: Google Sheets ID (will create new if not provided)
        """
        self.service = None
        self.sheet_id = sheet_id

        # Initialize Google Sheets service
        self._init_service(credentials_json)

        # Setup sheet tabs
        self._init_sheets()

    def _init_service(self, credentials_json):
        """Initialize Google Sheets service with credentials."""
        try:
            import os

            # Handle credentials from environment variable or file
            if credentials_json and os.path.isfile(credentials_json):
                # Load from file
                logger.info("Loading credentials from file...")
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_json,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            elif credentials_json:
                # Load from JSON string
                logger.info("Loading credentials from string...")
                creds_dict = json.loads(credentials_json.strip())
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                raise Exception("No Google credentials provided")

            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("✓ Google Sheets service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            raise

    def _init_sheets(self):
        """Create/verify queue tabs in Google Sheets."""
        try:
            if not self.sheet_id:
                # Create new spreadsheet
                spreadsheet = {
                    'properties': {
                        'title': 'TelegramBotQueue'
                    },
                    'sheets': [
                        {'properties': {'title': 'commands'}},
                        {'properties': {'title': 'results'}}
                    ]
                }

                spreadsheet = self.service.spreadsheets().create(
                    body=spreadsheet,
                    fields='spreadsheetId'
                ).execute()

                self.sheet_id = spreadsheet.get('spreadsheetId')
                logger.info(f"✓ Created new queue sheet: {self.sheet_id}")

                # Add headers
                self._add_headers()
            else:
                logger.info(f"Using existing queue sheet: {self.sheet_id}")

                # Verify tabs exist
                spreadsheet = self.service.spreadsheets().get(
                    spreadsheetId=self.sheet_id
                ).execute()

                sheet_titles = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]

                # Create missing tabs
                requests = []
                if 'commands' not in sheet_titles:
                    requests.append({
                        'addSheet': {
                            'properties': {'title': 'commands'}
                        }
                    })
                if 'results' not in sheet_titles:
                    requests.append({
                        'addSheet': {
                            'properties': {'title': 'results'}
                        }
                    })

                if requests:
                    self.service.spreadsheets().batchUpdate(
                        spreadsheetId=self.sheet_id,
                        body={'requests': requests}
                    ).execute()
                    logger.info("✓ Created missing tabs")
                    self._add_headers()

            logger.info("✓ Queue sheets ready")
            logger.info(f"  - Sheet ID: {self.sheet_id}")
            logger.info(f"  - URL: https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit")

        except Exception as e:
            logger.error(f"Failed to setup queue sheets: {e}")
            raise

    def _add_headers(self):
        """Add headers to command and result tabs."""
        try:
            # Commands header
            commands_header = [['command_id', 'command', 'timestamp', 'data', 'status']]
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range='commands!A1:E1',
                valueInputOption='RAW',
                body={'values': commands_header}
            ).execute()

            # Results header
            results_header = [['result_id', 'command_id', 'success', 'message', 'timestamp', 'data', 'status']]
            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range='results!A1:G1',
                valueInputOption='RAW',
                body={'values': results_header}
            ).execute()

            logger.info("✓ Headers added to sheets")

        except Exception as e:
            logger.error(f"Failed to add headers: {e}")

    def write_command(self, command_type, data=None):
        """
        Write a command to the queue.

        Args:
            command_type: Type of command (e.g., "RUNNIT")
            data: Optional additional data

        Returns:
            str: Command ID
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            command_id = f"{command_type}_{timestamp}"

            # Prepare row data
            data_json = json.dumps(data or {})
            row = [
                command_id,
                command_type,
                timestamp,
                data_json,
                'pending'
            ]

            # Append to commands sheet
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range='commands!A:E',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [row]}
            ).execute()

            logger.info(f"✓ Command written: {command_id}")
            return command_id

        except Exception as e:
            logger.error(f"Failed to write command: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def check_commands(self):
        """
        Check for pending commands in the queue.

        Returns:
            list: List of command dictionaries
        """
        try:
            # Read all commands
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='commands!A2:E'  # Skip header
            ).execute()

            rows = result.get('values', [])

            if not rows:
                return []

            commands = []
            for i, row in enumerate(rows, start=2):  # Start from row 2 (after header)
                # Skip if not enough columns or already processed
                if len(row) < 5:
                    continue

                if row[4] != 'pending':  # status column
                    continue

                try:
                    command_data = {
                        'command_id': row[0],
                        'command': row[1],
                        'timestamp': row[2],
                        'data': json.loads(row[3]) if row[3] else {},
                        'status': row[4],
                        'row_number': i  # Store row number for deletion
                    }
                    commands.append(command_data)
                except Exception as e:
                    logger.error(f"Error parsing command row {i}: {e}")

            return commands

        except Exception as e:
            logger.error(f"Failed to check commands: {e}")
            return []

    def delete_command(self, command_id=None, row_number=None):
        """
        Mark a command as processed (delete from queue).

        Args:
            command_id: Command ID (used if row_number not provided)
            row_number: Row number in sheet (preferred)
        """
        try:
            if row_number:
                # Mark as processed in the status column
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=f'commands!E{row_number}',
                    valueInputOption='RAW',
                    body={'values': [['processed']]}
                ).execute()
                logger.info(f"✓ Command marked as processed (row {row_number})")
            else:
                # Find row by command_id and mark as processed
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.sheet_id,
                    range='commands!A2:E'
                ).execute()

                rows = result.get('values', [])
                for i, row in enumerate(rows, start=2):
                    if len(row) > 0 and row[0] == command_id:
                        self.service.spreadsheets().values().update(
                            spreadsheetId=self.sheet_id,
                            range=f'commands!E{i}',
                            valueInputOption='RAW',
                            body={'values': [['processed']]}
                        ).execute()
                        logger.info(f"✓ Command {command_id} marked as processed")
                        return

                logger.warning(f"Command {command_id} not found")

        except Exception as e:
            logger.error(f"Failed to delete command: {e}")

    def write_result(self, command_id, success, message, data=None):
        """
        Write a result to the queue.

        Args:
            command_id: ID of command this is a result for
            success: Boolean indicating success/failure
            message: Result message
            data: Optional additional data

        Returns:
            str: Result ID
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_id = f"RESULT_{command_id}_{timestamp}"

            # Prepare row data
            data_json = json.dumps(data or {})
            row = [
                result_id,
                command_id,
                str(success),  # Convert boolean to string
                message,
                timestamp,
                data_json,
                'pending'
            ]

            # Append to results sheet
            self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range='results!A:G',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [row]}
            ).execute()

            logger.info(f"✓ Result written: {result_id}")
            return result_id

        except Exception as e:
            logger.error(f"Failed to write result: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def check_results(self, command_id=None):
        """
        Check for results in the queue.

        Args:
            command_id: Optional - filter for specific command

        Returns:
            list: List of result dictionaries
        """
        try:
            # Read all results
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='results!A2:G'  # Skip header
            ).execute()

            rows = result.get('values', [])

            if not rows:
                return []

            results_list = []
            for i, row in enumerate(rows, start=2):  # Start from row 2
                # Skip if not enough columns or already processed
                if len(row) < 7:
                    continue

                if row[6] != 'pending':  # status column
                    continue

                # Filter by command_id if specified
                if command_id and row[1] != command_id:
                    continue

                try:
                    result_data = {
                        'result_id': row[0],
                        'command_id': row[1],
                        'success': row[2].lower() == 'true',  # Convert string back to boolean
                        'message': row[3],
                        'timestamp': row[4],
                        'data': json.loads(row[5]) if row[5] else {},
                        'status': row[6],
                        'row_number': i  # Store row number for deletion
                    }
                    results_list.append(result_data)
                except Exception as e:
                    logger.error(f"Error parsing result row {i}: {e}")

            return results_list

        except Exception as e:
            logger.error(f"Failed to check results: {e}")
            return []

    def delete_result(self, result_id=None, row_number=None):
        """
        Mark a result as processed (delete from queue).

        Args:
            result_id: Result ID (used if row_number not provided)
            row_number: Row number in sheet (preferred)
        """
        try:
            if row_number:
                # Mark as processed in the status column
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=f'results!G{row_number}',
                    valueInputOption='RAW',
                    body={'values': [['processed']]}
                ).execute()
                logger.info(f"✓ Result marked as processed (row {row_number})")
            else:
                # Find row by result_id and mark as processed
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.sheet_id,
                    range='results!A2:G'
                ).execute()

                rows = result.get('values', [])
                for i, row in enumerate(rows, start=2):
                    if len(row) > 0 and row[0] == result_id:
                        self.service.spreadsheets().values().update(
                            spreadsheetId=self.sheet_id,
                            range=f'results!G{i}',
                            valueInputOption='RAW',
                            body={'values': [['processed']]}
                        ).execute()
                        logger.info(f"✓ Result {result_id} marked as processed")
                        return

                logger.warning(f"Result {result_id} not found")

        except Exception as e:
            logger.error(f"Failed to delete result: {e}")


def main():
    """Test the Google Sheets queue."""
    logging.basicConfig(level=logging.INFO)

    # Test with credentials file
    queue = GoogleSheetsQueue("google_credentials.json")

    # Test writing a command
    command_id = queue.write_command("RUNNIT", {"test": True})
    print(f"Command ID: {command_id}")

    time.sleep(2)

    # Test checking commands
    commands = queue.check_commands()
    print(f"Commands found: {len(commands)}")
    for cmd in commands:
        print(f"  - {cmd['command']} at {cmd['timestamp']}")


if __name__ == "__main__":
    main()
