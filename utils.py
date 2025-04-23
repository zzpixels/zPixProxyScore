"""
Utility Module

This module contains utility functions used across the application
for various tasks like sorting, displaying tables, and UI helpers.
"""
import tkinter as tk
from prettytable import PrettyTable


def sort_by_column(tv, col, reverse):
    """
    Sort a Treeview by a specific column.

    Args:
        tv (ttk.Treeview): The Treeview widget to sort
        col (str): Column identifier to sort by
        reverse (bool): Whether to sort in reverse order
    """
    # Get all values from the specified column and their corresponding item IDs
    data = [(tv.set(k, col), k) for k in tv.get_children("")]

    # Try to sort numerically first, fallback to string sort if not possible
    try:
        data.sort(key=lambda t: float(t[0]), reverse=reverse)
    except ValueError:
        data.sort(key=lambda t: t[0], reverse=reverse)

    # Reorder the items in the Treeview
    for index, (_, k) in enumerate(data):
        tv.move(k, "", index)

    # Configure column heading to toggle sort direction on next click
    tv.heading(col, command=lambda: sort_by_column(tv, col, not reverse))


def display_terminal_table(results):
    """
    Display proxy check results in a formatted ASCII table in the terminal.

    Args:
        results (list): List of proxy check results
    """
    table = PrettyTable()
    table.field_names = ["Proxy IP", "Public IP", "Location", "ISP", "Fraud Score",
                         "Proxy", "VPN", "Tor", "Mobile", "Recent Abuse", "Bot Status"]
    for row in results:
        table.add_row(row[:-1])  # Exclude the details column
    print(table)


def show_loading_window():
    """
    Display a simple loading window while proxies are being checked.

    Returns:
        tk.Tk: The loading window object (to be destroyed later)
    """
    load = tk.Tk()
    load.title("Checking Proxies")
    tk.Label(load, text="Checking proxies... This may take a moment.", font=("Helvetica", 12)).pack(padx=20, pady=20)
    load.update()
    return load