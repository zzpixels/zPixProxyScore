"""
GUI Module

This module contains all the graphical user interface components
for the proxy checker application, including input forms and result displays.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from config import load_config, save_config, DEFAULT_API_KEY
from utils import sort_by_column
from export import export_to_csv, open_export_window


def get_user_input():
    """
    Display input form to collect proxies and API key from the user.

    Returns:
        dict: Dictionary with 'proxies' (list) and 'api_key' (str)
    """
    input_data = {}
    config = load_config()

    def submit():
        """Process form submission"""
        key = api_key_input.get().strip() or DEFAULT_API_KEY
        input_data['proxies'] = proxy_input.get("1.0", tk.END).strip().splitlines()
        input_data['api_key'] = key
        if save_api_key_var.get():
            save_config(key)
        window.destroy()

    # Create input window
    window = tk.Tk()
    window.title("Enter Proxies and API Key")

    # Proxy input area
    tk.Label(window, text="Enter Proxies (one per line, format IP:PORT:USER:PASS):").pack(pady=(10, 0))
    proxy_input = scrolledtext.ScrolledText(window, width=80, height=10)
    proxy_input.pack(padx=10, pady=5)

    # API key input
    tk.Label(window, text="Custom IPQualityScore API Key (optional):").pack(pady=(10, 0))
    api_key_input = tk.Entry(window, width=50)
    api_key_input.insert(0, config.get("api_key", DEFAULT_API_KEY))
    api_key_input.pack(pady=5)

    # Option to save API key
    save_api_key_var = tk.BooleanVar()
    tk.Checkbutton(window, text="Save API Key", variable=save_api_key_var).pack()

    # Submit button
    submit_btn = tk.Button(window, text="Start Check", command=submit)
    submit_btn.pack(pady=10)

    window.mainloop()
    return input_data


def display_gui_table(results, summary, failed_proxies):
    """
    Display the proxy check results in a sortable table GUI.

    Args:
        results (list): List of proxy check results
        summary (dict): Summary statistics of proxy checks
        failed_proxies (list): List of proxies that failed to check
    """
    # Create main window
    root = tk.Tk()
    root.title("zPix Proxy Score Checker Results")
    root.geometry("1300x600")

    # Configure styling
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview.Heading", font=('Helvetica', 11, 'bold'))
    style.configure("Treeview", font=('Helvetica', 10), rowheight=28)

    # Create main frame
    frame = ttk.Frame(root, padding=10)
    frame.pack(expand=True, fill='both')

    # Define table columns
    columns = ["Proxy IP", "Public IP", "Location", "ISP", "Fraud Score",
               "Proxy", "VPN", "Tor", "Mobile", "Recent Abuse", "Bot Status"]

    # Create Treeview widget for tabular display
    tree = ttk.Treeview(frame, columns=columns, show='headings')

    # Define column widths
    col_widths = {
        "Proxy IP": 150, "Public IP": 150, "Location": 180, "ISP": 180,
        "Fraud Score": 90, "Proxy": 60, "VPN": 60, "Tor": 60,
        "Mobile": 60, "Recent Abuse": 100, "Bot Status": 100
    }

    # Configure columns
    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: sort_by_column(tree, c, False))
        tree.column(col, anchor=tk.W, width=col_widths[col])

    # Add scrollbars
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side='right', fill='y')
    hsb.pack(side='bottom', fill='x')
    tree.pack(fill='both', expand=True)

    # Define double-click handler to show details
    def show_details(event):
        """Show detailed proxy information on double-click"""
        item = tree.identify_row(event.y)
        if item:
            idx = tree.index(item)
            details = results[idx][-1]
            messagebox.showinfo("Proxy Details", details)

    tree.bind("<Double-1>", show_details)

    # Insert data rows with color coding based on fraud score
    for row in results:
        fraud_score = row[4]
        tag = ""
        if fraud_score >= 75:
            tag = "high"
        elif fraud_score >= 30:
            tag = "medium"
        tree.insert('', tk.END, values=row[:-1], tags=(tag,))

    # Configure tag colors
    tree.tag_configure("high", background="#ffcccc")  # Light red for high risk
    tree.tag_configure("medium", background="#fff0b3")  # Light yellow for medium risk

    # Create footer with summary information
    footer_frame = ttk.Frame(root)
    footer_frame.pack(side='bottom', fill='x', pady=8)

    footer = ttk.Label(footer_frame, text=f"Proxies Checked: {summary['total']} | High Risk: {summary['high_risk']}",
                       font=('Helvetica', 10, 'italic'))
    footer.pack(side='left', padx=10)

    # Add export button
    export_btn = ttk.Button(footer_frame, text="Export…", command=lambda: open_export_window(tree, results))
    export_btn.pack(side='right', padx=10)

    # Show warning for failed proxies if any
    if failed_proxies:
        messagebox.showwarning("Some Proxies Failed",
                               f"The following proxies failed to check:\n\n" + "\n".join(failed_proxies))

    root.mainloop()