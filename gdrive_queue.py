"""
Google Drive Queue Manager
==========================

Uses Google Drive as a message queue between cloud bot and work computer.
- Cloud bot writes commands to Drive
- Work computer polls Drive for commands
- Work computer writes results back to Drive
- Cloud bot reads results and sends to Telegram

Author: Mohammad Khair AbuShanab
Created: January 28, 2026
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
import logging

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    import io
except ImportError:
    print("ERROR: Google API libraries not installed!")
    print("Install: pip install google-auth google-auth-oauthlib google-api-python-client")

logger = logging.getLogger(__name__)


class GoogleDriveQueue:
    """
    Simple queue system using Google Drive.
    """

    def __init__(self, credentials_json=None):
        """
        Initialize Google Drive queue.

        Args:
            credentials_json: Path to service account credentials JSON file
                             or JSON string of credentials
        """
        self.service = None
        self.queue_folder_id = None
        self.commands_folder_id = None
        self.results_folder_id = None

        # Initialize Google Drive service
        self._init_service(credentials_json)

        # Create queue folders
        self._init_folders()

    def _init_service(self, credentials_json):
        """Initialize Google Drive service with credentials."""
        try:
            # Handle credentials from environment variable or file
            if credentials_json and os.path.isfile(credentials_json):
                # Load from file
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_json,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            elif credentials_json:
                # Load from JSON string
                import json
                creds_dict = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
            else:
                # Try from environment variable
                creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
                if creds_json:
                    creds_dict = json.loads(creds_json)
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_dict,
                        scopes=['https://www.googleapis.com/auth/drive']
                    )
                else:
                    raise Exception("No Google credentials provided")

            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("✓ Google Drive service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Google Drive: {e}")
            raise

    def _init_folders(self):
        """Create queue folder structure in Google Drive."""
        try:
            # Create main queue folder
            self.queue_folder_id = self._get_or_create_folder("TelegramBotQueue")

            # Create subfolders
            self.commands_folder_id = self._get_or_create_folder(
                "commands",
                parent_id=self.queue_folder_id
            )
            self.results_folder_id = self._get_or_create_folder(
                "results",
                parent_id=self.queue_folder_id
            )

            logger.info(f"✓ Queue folders ready")
            logger.info(f"  - Commands: {self.commands_folder_id}")
            logger.info(f"  - Results: {self.results_folder_id}")

        except Exception as e:
            logger.error(f"Failed to create queue folders: {e}")
            raise

    def _get_or_create_folder(self, folder_name, parent_id=None):
        """
        Get existing folder or create new one.

        Args:
            folder_name: Name of folder
            parent_id: Parent folder ID (None for root)

        Returns:
            str: Folder ID
        """
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"

            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])

            if files:
                # Folder exists
                return files[0]['id']
            else:
                # Create folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if parent_id:
                    folder_metadata['parents'] = [parent_id]

                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()

                logger.info(f"✓ Created folder: {folder_name}")
                return folder.get('id')

        except Exception as e:
            logger.error(f"Error with folder {folder_name}: {e}")
            raise

    def write_command(self, command_type, data=None):
        """
        Write a command to the queue.

        Args:
            command_type: Type of command (e.g., "RUNNIT")
            data: Optional additional data

        Returns:
            str: Command ID (filename)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            command_id = f"{command_type}_{timestamp}"
            filename = f"{command_id}.json"

            command_data = {
                "command": command_type,
                "timestamp": timestamp,
                "data": data or {}
            }

            # Write to temp file
            temp_file = Path(f"/tmp/{filename}")
            with open(temp_file, 'w') as f:
                json.dump(command_data, f, indent=2)

            # Upload to Google Drive
            file_metadata = {
                'name': filename,
                'parents': [self.commands_folder_id]
            }

            media = MediaFileUpload(str(temp_file), mimetype='application/json')

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            # Clean up temp file
            temp_file.unlink()

            logger.info(f"✓ Command written: {command_id}")
            return command_id

        except Exception as e:
            logger.error(f"Failed to write command: {e}")
            return None

    def check_commands(self):
        """
        Check for pending commands in the queue.

        Returns:
            list: List of command dictionaries
        """
        try:
            # List files in commands folder
            query = f"'{self.commands_folder_id}' in parents and trashed=false"

            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                orderBy='createdTime'
            ).execute()

            files = results.get('files', [])

            if not files:
                return []

            commands = []
            for file in files:
                try:
                    # Download file content
                    request = self.service.files().get_media(fileId=file['id'])
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)

                    done = False
                    while not done:
                        status, done = downloader.next_chunk()

                    # Parse JSON
                    fh.seek(0)
                    command_data = json.loads(fh.read().decode('utf-8'))
                    command_data['file_id'] = file['id']
                    command_data['filename'] = file['name']

                    commands.append(command_data)

                except Exception as e:
                    logger.error(f"Error reading command file {file['name']}: {e}")

            return commands

        except Exception as e:
            logger.error(f"Failed to check commands: {e}")
            return []

    def delete_command(self, file_id):
        """
        Delete a command file after processing.

        Args:
            file_id: Google Drive file ID
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"✓ Command deleted: {file_id}")
        except Exception as e:
            logger.error(f"Failed to delete command {file_id}: {e}")

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
            filename = f"{result_id}.json"

            result_data = {
                "command_id": command_id,
                "success": success,
                "message": message,
                "timestamp": timestamp,
                "data": data or {}
            }

            # Write to temp file
            temp_file = Path(f"/tmp/{filename}")
            with open(temp_file, 'w') as f:
                json.dump(result_data, f, indent=2)

            # Upload to Google Drive
            file_metadata = {
                'name': filename,
                'parents': [self.results_folder_id]
            }

            media = MediaFileUpload(str(temp_file), mimetype='application/json')

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            # Clean up temp file
            temp_file.unlink()

            logger.info(f"✓ Result written: {result_id}")
            return result_id

        except Exception as e:
            logger.error(f"Failed to write result: {e}")
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
            # List files in results folder
            query = f"'{self.results_folder_id}' in parents and trashed=false"

            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                orderBy='createdTime'
            ).execute()

            files = results.get('files', [])

            if not files:
                return []

            results_list = []
            for file in files:
                try:
                    # Download file content
                    request = self.service.files().get_media(fileId=file['id'])
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)

                    done = False
                    while not done:
                        status, done = downloader.next_chunk()

                    # Parse JSON
                    fh.seek(0)
                    result_data = json.loads(fh.read().decode('utf-8'))
                    result_data['file_id'] = file['id']
                    result_data['filename'] = file['name']

                    # Filter by command_id if specified
                    if command_id and result_data.get('command_id') != command_id:
                        continue

                    results_list.append(result_data)

                except Exception as e:
                    logger.error(f"Error reading result file {file['name']}: {e}")

            return results_list

        except Exception as e:
            logger.error(f"Failed to check results: {e}")
            return []

    def delete_result(self, file_id):
        """
        Delete a result file after processing.

        Args:
            file_id: Google Drive file ID
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"✓ Result deleted: {file_id}")
        except Exception as e:
            logger.error(f"Failed to delete result {file_id}: {e}")


def main():
    """Test the Google Drive queue."""
    logging.basicConfig(level=logging.INFO)

    # Test with credentials file
    queue = GoogleDriveQueue("google_credentials.json")

    # Test writing a command
    command_id = queue.write_command("RUNNIT", {"test": True})
    print(f"Command ID: {command_id}")

    # Test checking commands
    commands = queue.check_commands()
    print(f"Commands found: {len(commands)}")
    for cmd in commands:
        print(f"  - {cmd['command']} at {cmd['timestamp']}")


if __name__ == "__main__":
    main()
