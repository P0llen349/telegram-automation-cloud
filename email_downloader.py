"""
Cloud Email Downloader - IMAP Version
======================================

Downloads emails from Outlook/Office 365 using IMAP protocol.
Searches for ticket summary emails and downloads CSV attachments.

Author: Mohammad Khair AbuShanab
Created: January 6, 2026
Purpose: Cloud-based replacement for PowerShell email downloader
"""

import imaplib
import email
from email.header import decode_header
import os
import re
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class OutlookIMAPDownloader:
    """
    Downloads emails from Outlook using IMAP protocol.
    """

    def __init__(self, email_address, password, imap_server="outlook.office365.com", imap_port=993):
        """
        Initialize the IMAP downloader.

        Args:
            email_address: Outlook email address
            password: Email password
            imap_server: IMAP server address (default: outlook.office365.com)
            imap_port: IMAP port (default: 993 for SSL)
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.mail = None

    def connect(self):
        """
        Connect to the IMAP server.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to {self.imap_server}:{self.imap_port}...")
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)

            logger.info(f"Logging in as {self.email_address}...")
            self.mail.login(self.email_address, self.password)

            logger.info("✓ Connected successfully!")
            return True

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """
        Disconnect from the IMAP server.
        """
        if self.mail:
            try:
                self.mail.logout()
                logger.info("✓ Disconnected from IMAP server")
            except:
                pass

    def search_emails(self, sender=None, subject_contains=None, folder="INBOX"):
        """
        Search for emails matching criteria.

        Args:
            sender: Filter by sender email address
            subject_contains: Filter by subject text
            folder: Email folder to search (default: INBOX)

        Returns:
            list: List of email IDs matching criteria
        """
        try:
            # Select the folder
            logger.info(f"Selecting folder: {folder}")
            status, messages = self.mail.select(folder)

            if status != "OK":
                logger.error(f"Failed to select folder {folder}")
                return []

            # Build search criteria
            search_criteria = []

            if sender:
                search_criteria.append(f'FROM "{sender}"')

            if subject_contains:
                search_criteria.append(f'SUBJECT "{subject_contains}"')

            # If no criteria, search all
            if not search_criteria:
                search_query = "ALL"
            else:
                search_query = " ".join(search_criteria)

            logger.info(f"Searching with criteria: {search_query}")

            # Search emails
            status, email_ids = self.mail.search(None, search_query)

            if status != "OK":
                logger.error("Search failed")
                return []

            # Get list of email IDs
            email_id_list = email_ids[0].split()

            logger.info(f"Found {len(email_id_list)} matching emails")

            return email_id_list

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_email_data(self, email_id):
        """
        Fetch email data by ID.

        Args:
            email_id: Email ID to fetch

        Returns:
            email.message.Message: Email message object or None
        """
        try:
            status, msg_data = self.mail.fetch(email_id, "(RFC822)")

            if status != "OK":
                logger.error(f"Failed to fetch email {email_id}")
                return None

            # Parse email
            msg = email.message_from_bytes(msg_data[0][1])
            return msg

        except Exception as e:
            logger.error(f"Error fetching email {email_id}: {e}")
            return None

    def decode_subject(self, subject):
        """
        Decode email subject (handles encoding).

        Args:
            subject: Encoded subject string

        Returns:
            str: Decoded subject
        """
        if subject is None:
            return ""

        decoded_parts = decode_header(subject)
        decoded_subject = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_subject += part.decode(encoding or 'utf-8')
                except:
                    decoded_subject += part.decode('utf-8', errors='ignore')
            else:
                decoded_subject += part

        return decoded_subject

    def download_attachments(self, msg, output_dir=".", filename_pattern=None):
        """
        Download attachments from an email message.

        Args:
            msg: Email message object
            output_dir: Directory to save attachments
            filename_pattern: Regex pattern to match filename (optional)

        Returns:
            list: List of downloaded file paths
        """
        downloaded_files = []

        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Iterate through email parts
            for part in msg.walk():
                # Check if part is an attachment
                if part.get_content_maintype() == 'multipart':
                    continue

                if part.get('Content-Disposition') is None:
                    continue

                # Get filename
                filename = part.get_filename()

                if not filename:
                    continue

                # Decode filename
                filename = self.decode_subject(filename)

                # Check if filename matches pattern (if provided)
                if filename_pattern:
                    if not re.search(filename_pattern, filename, re.IGNORECASE):
                        logger.debug(f"Skipping {filename} (doesn't match pattern)")
                        continue

                # Save attachment
                filepath = os.path.join(output_dir, filename)

                logger.info(f"Downloading attachment: {filename}")

                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))

                downloaded_files.append(filepath)
                logger.info(f"✓ Saved: {filepath}")

            return downloaded_files

        except Exception as e:
            logger.error(f"Error downloading attachments: {e}")
            return downloaded_files

    def get_latest_ticket_email(self, sender="mohammad.jarrar@jepco.com.jo",
                                subject_contains="Open tickets Summary",
                                output_dir="downloads"):
        """
        Get the latest ticket summary email and download its CSV attachment.

        Args:
            sender: Email address of sender
            subject_contains: Text that should be in subject
            output_dir: Directory to save CSV file

        Returns:
            str: Path to downloaded CSV file, or None if not found
        """
        try:
            # Search for matching emails
            email_ids = self.search_emails(sender=sender, subject_contains=subject_contains)

            if not email_ids:
                logger.warning("No matching emails found")
                return None

            # Get the most recent email (last ID in list)
            latest_email_id = email_ids[-1]
            logger.info(f"Processing most recent email (ID: {latest_email_id.decode()})")

            # Fetch email
            msg = self.get_email_data(latest_email_id)

            if not msg:
                logger.error("Failed to fetch email")
                return None

            # Get subject and date
            subject = self.decode_subject(msg['Subject'])
            date = msg['Date']

            logger.info(f"Email subject: {subject}")
            logger.info(f"Email date: {date}")

            # Download CSV attachments
            csv_files = self.download_attachments(
                msg,
                output_dir=output_dir,
                filename_pattern=r'\.csv$'  # Only CSV files
            )

            if not csv_files:
                logger.warning("No CSV attachments found in email")
                return None

            # Return the first CSV file found
            return csv_files[0]

        except Exception as e:
            logger.error(f"Error getting latest ticket email: {e}")
            return None


def main():
    """
    Test the email downloader.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Configuration (will be replaced with environment variables in cloud)
    EMAIL_ADDRESS = os.getenv("OUTLOOK_EMAIL", "mkhair.abushanab@jepco.com.jo")
    EMAIL_PASSWORD = os.getenv("OUTLOOK_PASSWORD", "Z%275067870790us")

    logger.info("="*70)
    logger.info("OUTLOOK EMAIL DOWNLOADER - IMAP VERSION")
    logger.info("="*70)

    # Create downloader
    downloader = OutlookIMAPDownloader(EMAIL_ADDRESS, EMAIL_PASSWORD)

    # Connect
    if not downloader.connect():
        logger.error("Failed to connect to IMAP server")
        return

    try:
        # Download latest ticket email
        csv_file = downloader.get_latest_ticket_email(
            sender="mohammad.jarrar@jepco.com.jo",
            subject_contains="Open tickets Summary",
            output_dir="downloads"
        )

        if csv_file:
            logger.info("="*70)
            logger.info(f"SUCCESS! Downloaded: {csv_file}")
            logger.info("="*70)
        else:
            logger.warning("No CSV file downloaded")

    finally:
        # Disconnect
        downloader.disconnect()


if __name__ == "__main__":
    main()
