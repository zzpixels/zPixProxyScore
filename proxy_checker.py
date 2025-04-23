"""
Proxy Checker Module

This module contains the core functionality for checking proxies against
various APIs to determine their quality, risk level, and other attributes.
"""
import requests
from concurrent.futures import ThreadPoolExecutor

from config import IPQ_API_URL, GEO_API_URL

# Globals
results = []
summary = {"total": 0, "high_risk": 0}
failed_proxies = []


def check_proxy(proxy, api_key):
    """
    Check a single proxy against geolocation and fraud detection APIs.

    Args:
        proxy (str): Proxy string in format IP:PORT:USER:PASS
        api_key (str): API key for the IP Quality Score service

    Note:
        Results are stored in the global 'results', 'summary', and 'failed_proxies' lists.
    """
    # Parse proxy components
    try:
        ip, port, user, password = proxy.split(':')
    except ValueError:
        failed_proxies.append(f"Malformed: {proxy}")
        return

    proxy_ip = ip
    proxies = {
        'http': f'http://{user}:{password}@{ip}:{port}',
        'https': f'http://{user}:{password}@{ip}:{port}',
    }

    try:
        # Step 1: Check if proxy works by querying geo-location API
        geo_resp = requests.get(GEO_API_URL, proxies=proxies, timeout=10)
        geo_data = geo_resp.json()
        if geo_data.get('status') != 'success':
            failed_proxies.append(proxy)
            return

        # Extract geo information
        public_ip = geo_data['query']
        location = f"{geo_data['city']}, {geo_data['regionName']}"

        # Step 2: Check the proxy's IP against fraud detection API
        fraud_url = f"{IPQ_API_URL}/{api_key}/{public_ip}?strictness=1"
        fraud_resp = requests.get(fraud_url, timeout=10)
        fraud_data = fraud_resp.json()

        if fraud_data.get('success'):
            # Process successful fraud check results
            fraud_score = fraud_data.get('fraud_score', 0)
            if fraud_score >= 75:
                summary["high_risk"] += 1

            # Create result row with all collected data
            row = [
                proxy_ip,
                public_ip,
                location,
                fraud_data.get('ISP', 'N/A'),
                fraud_score,
                fraud_data.get('proxy', 'N/A'),
                fraud_data.get('vpn', 'N/A'),
                fraud_data.get('tor', 'N/A'),
                fraud_data.get('mobile', 'N/A'),
                fraud_data.get('recent_abuse', 'N/A'),
                fraud_data.get('bot_status', 'N/A'),
                f"Username: {user}\nPassword: {password}\nPort: {port}"
            ]
            results.append(row)
            summary["total"] += 1
        else:
            failed_proxies.append(proxy)
    except Exception:
        failed_proxies.append(proxy)


def check_proxies_with_threading(proxies, api_key, threads=10):
    """
    Check multiple proxies concurrently using a thread pool.

    Args:
        proxies (list): List of proxy strings to check
        api_key (str): API key for the IP Quality Score service
        threads (int): Number of concurrent threads to use
    """
    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Pass the api_key parameter to each check_proxy call
        futures = [executor.submit(check_proxy, proxy, api_key) for proxy in proxies]
        for future in futures:
            future.result()