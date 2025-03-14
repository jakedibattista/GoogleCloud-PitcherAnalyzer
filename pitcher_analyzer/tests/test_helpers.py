"""Helper functions for tests."""
import os
import sys
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_test_credentials():
    """Get credentials for testing, or None if not available."""
    try:
        from google.oauth2 import service_account
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path or not os.path.exists(creds_path):
            logger.warning("No credentials available for testing")
            return None
            
        with open(creds_path) as f:
            creds_dict = json.load(f)
        return service_account.Credentials.from_service_account_info(creds_dict)
    except ImportError:
        logger.warning("Google Cloud libraries not available")
        return None
    except Exception as e:
        logger.warning(f"Error loading credentials: {e}")
        return None

def skip_if_no_credentials():
    """Skip the test if no credentials are available."""
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path or not os.path.exists(creds_path):
        logger.warning("Skipping test: No credentials available")
        return True
    return False 