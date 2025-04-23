import requests
import tkinter as tk
from tkinter import ttk, scrolledtext
from concurrent.futures import ThreadPoolExecutor
from prettytable import PrettyTable
import os
import json

# === Configuration ===
DEFAULT_API_KEY = ''
CONFIG_FILE = "config.json"
IPQ_API_URL = 'https://ipqualityscore.com/api/json/ip'
GEO_API_URL = 'http://ip-api.com/json/'
THREADS = 10
USE_GUI = True

results = []
summary = {"total": 0, "high_risk": 0}
api_key = DEFAULT_API_KEY

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"api_key": DEFAULT_API_KEY}

def save_config(api_key):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"api_key": api_key}, f)

def check_proxy(proxy):
    ip, port, user, password = proxy.split(':')
    proxy_ip = ip
    proxies = {
        'http': f'http://{user}:{password}@{ip}:{port}',
        'https': f'http://{user}:{password}@{ip}:{port}',
    }

    try:
        geo_resp = requests.get(GEO_API_URL, proxies=proxies, timeout=10)
        geo_data = geo_resp.json()
        if geo_data.get('status') != 'success':
            return

        public_ip = geo_data['query']
        location = f"{geo_data['city']}, {geo_data['regionName']}"

        fraud_url = f"{IPQ_API_URL}/{api_key}/{public_ip}?strictness=1"
        fraud_resp = requests.get(fraud_url, timeout=10)
        fraud_data = fraud_resp.json()

        if fraud_data.get('success'):
            fraud_score = fraud_data.get('fraud_score', 0)
            if fraud_score >= 75:
                summary["high_risk"] += 1

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
                fraud_data.get('bot_status', 'N/A')
            ]
            results.append(row)
            summary["total"] += 1

    except Exception as e:
        print(f"{proxy} => Error: {e}")

def display_gui_table():
    root = tk.Tk()
    root.title("zPix Proxy Score Checker Results")
    root.geometry("1250x600")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview.Heading", font=('Helvetica', 11, 'bold'))
    style.configure("Treeview", font=('Helvetica', 10), rowheight=28)

    frame = ttk.Frame(root, padding=10)
    frame.pack(expand=True, fill='both')

    columns = ["Proxy IP", "Public IP", "Location", "ISP", "Fraud Score",
               "Proxy", "VPN", "Tor", "Mobile", "Recent Abuse", "Bot Status"]

    tree = ttk.Treeview(frame, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor=tk.W, width=110)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side='right', fill='y')
    hsb.pack(side='bottom', fill='x')
    tree.pack(fill='both', expand=True)

    for row in results:
        fraud_score = row[4]
        tag = ""
        if fraud_score >= 75:
            tag = "high"
        elif fraud_score >= 30:
            tag = "medium"
        tree.insert('', tk.END, values=row, tags=(tag,))

    tree.tag_configure("high", background="#ffcccc")
    tree.tag_configure("medium", background="#fff0b3")

    footer = ttk.Label(root, text=f"Proxies Checked: {summary['total']} | High Risk: {summary['high_risk']}",
                       font=('Helvetica', 10, 'italic'))
    footer.pack(side='bottom', pady=8)

    root.mainloop()

def display_terminal_table():
    table = PrettyTable()
    table.field_names = ["Proxy IP", "Public IP", "Location", "ISP", "Fraud Score",
                         "Proxy", "VPN", "Tor", "Mobile", "Recent Abuse", "Bot Status"]
    for row in results:
        table.add_row(row)
    print(table)

def get_user_input():
    input_data = {}
    config = load_config()

    def submit():
        key = api_key_input.get().strip() or DEFAULT_API_KEY
        input_data['proxies'] = proxy_input.get("1.0", tk.END).strip().splitlines()
        input_data['api_key'] = key
        if save_api_key_var.get():
            save_config(key)
        window.destroy()

    window = tk.Tk()
    window.title("Enter Proxies and API Key")

    tk.Label(window, text="Enter Proxies (one per line, format IP:PORT:USER:PASS):").pack(pady=(10, 0))
    proxy_input = scrolledtext.ScrolledText(window, width=80, height=10)
    proxy_input.pack(padx=10, pady=5)

    tk.Label(window, text="Custom IPQualityScore API Key (optional):").pack(pady=(10, 0))
    api_key_input = tk.Entry(window, width=50)
    api_key_input.insert(0, config.get("api_key", DEFAULT_API_KEY))
    api_key_input.pack(pady=5)

    save_api_key_var = tk.BooleanVar()
    tk.Checkbutton(window, text="Save API Key", variable=save_api_key_var).pack()

    submit_btn = tk.Button(window, text="Start Check", command=submit)
    submit_btn.pack(pady=10)

    window.mainloop()
    return input_data

def main():
    global api_key
    if USE_GUI:
        user_input = get_user_input()
        proxies = user_input['proxies']
        api_key = user_input['api_key']
    else:
        print("GUI disabled. Please modify the script to support CLI input if needed.")
        return

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        executor.map(check_proxy, proxies)

    display_gui_table() if USE_GUI else display_terminal_table()

if __name__ == '__main__':
    main()
