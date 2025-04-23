import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from concurrent.futures import ThreadPoolExecutor, as_completed
from prettytable import PrettyTable
import csv
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
failed_proxies = []
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
        geo_resp = requests.get(GEO_API_URL, proxies=proxies, timeout=10)
        geo_data = geo_resp.json()
        if geo_data.get('status') != 'success':
            failed_proxies.append(proxy)
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
                fraud_data.get('bot_status', 'N/A'),
                f"Username: {user}\nPassword: {password}\nPort: {port}"
            ]
            results.append(row)
            summary["total"] += 1
        else:
            failed_proxies.append(proxy)

    except Exception as e:
        failed_proxies.append(proxy)

def export_to_csv():
    if not results:
        messagebox.showinfo("Export", "No data to export.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return

    headers = ["Proxy IP", "Public IP", "Location", "ISP", "Fraud Score",
               "Proxy", "VPN", "Tor", "Mobile", "Recent Abuse", "Bot Status"]

    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for row in results:
            writer.writerow(row[:-1])  # exclude details

    messagebox.showinfo("Export Complete", f"Data successfully exported to\n{file_path}")

def display_gui_table():
    root = tk.Tk()
    root.title("zPix Proxy Score Checker Results")
    root.geometry("1300x600")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview.Heading", font=('Helvetica', 11, 'bold'))
    style.configure("Treeview", font=('Helvetica', 10), rowheight=28)

    frame = ttk.Frame(root, padding=10)
    frame.pack(expand=True, fill='both')

    columns = ["Proxy IP", "Public IP", "Location", "ISP", "Fraud Score",
               "Proxy", "VPN", "Tor", "Mobile", "Recent Abuse", "Bot Status"]

    tree = ttk.Treeview(frame, columns=columns, show='headings')
    col_widths = {
        "Proxy IP": 150, "Public IP": 150, "Location": 180, "ISP": 180,
        "Fraud Score": 90, "Proxy": 60, "VPN": 60, "Tor": 60,
        "Mobile": 60, "Recent Abuse": 100, "Bot Status": 100
    }
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor=tk.W, width=col_widths[col])

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side='right', fill='y')
    hsb.pack(side='bottom', fill='x')
    tree.pack(fill='both', expand=True)

    def show_details(event):
        item = tree.identify_row(event.y)
        if item:
            idx = tree.index(item)
            details = results[idx][-1]
            messagebox.showinfo("Proxy Details", details)

    tree.bind("<Double-1>", show_details)

    for row in results:
        fraud_score = row[4]
        tag = ""
        if fraud_score >= 75:
            tag = "high"
        elif fraud_score >= 30:
            tag = "medium"
        tree.insert('', tk.END, values=row[:-1], tags=(tag,))

    tree.tag_configure("high", background="#ffcccc")
    tree.tag_configure("medium", background="#fff0b3")

    footer_frame = ttk.Frame(root)
    footer_frame.pack(side='bottom', fill='x', pady=8)

    footer = ttk.Label(footer_frame, text=f"Proxies Checked: {summary['total']} | High Risk: {summary['high_risk']}", font=('Helvetica', 10, 'italic'))
    footer.pack(side='left', padx=10)

    export_btn = ttk.Button(footer_frame, text="Export to CSV", command=export_to_csv)
    export_btn.pack(side='right', padx=10)

    if failed_proxies:
        messagebox.showwarning("Some Proxies Failed", f"The following proxies failed to check:\n\n" + "\n".join(failed_proxies))

    root.mainloop()

def display_terminal_table():
    table = PrettyTable()
    table.field_names = ["Proxy IP", "Public IP", "Location", "ISP", "Fraud Score",
                         "Proxy", "VPN", "Tor", "Mobile", "Recent Abuse", "Bot Status"]
    for row in results:
        table.add_row(row[:-1])
    print(table)

def show_loading_window():
    load = tk.Tk()
    load.title("Checking Proxies")
    tk.Label(load, text="Checking proxies... This may take a moment.", font=("Helvetica", 12)).pack(padx=20, pady=20)
    load.update()
    return load

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

    loading = show_loading_window()
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        list(executor.map(check_proxy, proxies))
    loading.destroy()

    display_gui_table() if USE_GUI else display_terminal_table()

if __name__ == '__main__':
    main()
