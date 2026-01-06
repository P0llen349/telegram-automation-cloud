"""
Test Email Downloader
======================

Quick test to verify IMAP email download works.
Run this before deploying to cloud.
"""

from email_downloader import OutlookIMAPDownloader
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    logger.info("="*70)
    logger.info("TESTING EMAIL DOWNLOADER")
    logger.info("="*70)

    # Your credentials
    EMAIL = "mkhair.abushanab@jepco.com.jo"
    PASSWORD = "Z%275067870790us"

    # Create downloader
    downloader = OutlookIMAPDownloader(EMAIL, PASSWORD)

    # Test connection
    logger.info("\n[TEST 1] Testing IMAP connection...")
    if downloader.connect():
        logger.info("✅ Connection successful!")

        try:
            # Test email search
            logger.info("\n[TEST 2] Searching for ticket emails...")
            csv_file = downloader.get_latest_ticket_email(
                sender="mohammad.jarrar@jepco.com.jo",
                subject_contains="Open tickets Summary",
                output_dir="test_downloads"
            )

            if csv_file:
                logger.info(f"\n✅ SUCCESS! Downloaded: {csv_file}")
                logger.info("="*70)
                logger.info("Email downloader is working correctly!")
                logger.info("You can now deploy to Railway.")
                logger.info("="*70)
            else:
                logger.warning("\n⚠️ No email found. This might be normal if:")
                logger.warning("  - No emails received today")
                logger.warning("  - Email already processed")
                logger.warning("  - Subject/sender doesn't match")

        finally:
            downloader.disconnect()

    else:
        logger.error("❌ Connection failed!")
        logger.error("Check:")
        logger.error("  1. Email and password are correct")
        logger.error("  2. IMAP is enabled on your Outlook account")
        logger.error("  3. Network connection is working")

if __name__ == "__main__":
    main()
