"""
Main Module - Proxy Checker Application

This is the entry point for the proxy checker application.
It handles the program flow from user input to displaying results.

The application checks proxies against IP quality services to determine
their risk level and characteristics.
"""
from config import USE_GUI, THREADS
from proxy_checker import check_proxies_with_threading, results, summary, failed_proxies
from gui import get_user_input, display_gui_table
from utils import display_terminal_table, show_loading_window


def main():
    """
    Main function that orchestrates the application flow.

    1. Gets user input (proxies and API key)
    2. Checks the proxies with a loading screen
    3. Displays the results in either GUI or terminal
    """
    if USE_GUI:
        # Get input through GUI mode
        user_input = get_user_input()
        proxies = user_input['proxies']
        api_key = user_input['api_key']
    else:
        # CLI mode (not fully implemented)
        print("GUI disabled. Please modify the script to support CLI input if needed.")
        return

    # Show loading window and check proxies
    loading = show_loading_window()
    check_proxies_with_threading(proxies, api_key, THREADS)
    loading.destroy()

    # Display results based on GUI mode setting
    display_gui_table(results, summary, failed_proxies)if USE_GUI else display_terminal_table(results)


if __name__ == '__main__':
    main()