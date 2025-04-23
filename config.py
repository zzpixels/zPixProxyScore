"""
Configuration module for the proxy checker application.

This module manages application-wide configuration constants and
provides functions for loading and saving user configurations.
"""
import os
import json

# === Configuration ===
DEFAULT_API_KEY = ''
CONFIG_FILE = "config.json"
IPQ_API_URL = 'https://ipqualityscore.com/api/json/ip'
GEO_API_URL = 'http://ip-api.com/json/'
THREADS = 10
USE_GUI = True


def load_config():
    """
    Load configuration from the config file.

    Returns:
        dict: Configuration dictionary containing at minimum the API key
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"api_key": DEFAULT_API_KEY}


def save_config(api_key):
    """
    Save configuration to the config file.

    Args:
        api_key (str): The API key to save
    """
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"api_key": api_key}, f)