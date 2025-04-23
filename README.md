# 🛡️ Proxy Checker GUI

A Python GUI tool for checking proxy quality, fraud risk, geolocation, and network attributes using the IPQualityScore API and IP-API.

## ✨ Features

- 🧾 GUI Input for Proxies (IP:PORT:USER:PASS)
- 🔐 Optional and Persistent API Key Configuration
- 📍 IP Geolocation via IP-API
- 🚨 Fraud Risk Analysis via IPQualityScore
- 🧠 Color-coded risk visualizer (red for high risk, yellow for medium)
- 🖱️ Double-click any row to reveal proxy credentials (username, password, port)
- 💾 Export results to CSV
- 📊 PrettyTable CLI fallback (if GUI is disabled)
- ⚠️ List of failed proxies displayed after scan

---

## 🔑 Getting an IPQualityScore API Key

To use this tool, you need a free API key from IPQualityScore. Here's how:

1. Go to [https://www.ipqualityscore.com/create-account](https://www.ipqualityscore.com/create-account)
2. Create a free account using your email
3. Once logged in, navigate to the [Account Settings/API Keys page](https://www.ipqualityscore.com/user/settings)
4. Copy your **Default API Key**
5. Paste it into the tool when prompted or save it in `config.json` like this:

```json
{
  "api_key": "your_actual_ipqs_key_here"
}
```

🆓 The free plan should be fine — in testing, these queries don’t even drain your free token balance. This could change in the future, but for now it’s a bonus!

---

## 🪟 Windows Users – Precompiled `.exe` Version

If you don’t want to install Python or any dependencies, you can use the precompiled Windows `.exe` version:

1. Download the latest release from the [Releases](https://github.com/zzpixels/zPixProxyScore/releases) page.
2. Extract the ZIP archive (if applicable).
3. Double-click `zPixProxyScoreChecker.exe` to launch the app.

### 📝 Notes:
- No installation is required — just run and use.
- A `config.json` file will be created in the same folder to store your API key if you choose to save it.
- Double-click any proxy row to view credentials (port, username, password).
- You can export results to CSV using the **Export to CSV** button.

---

## 🐧 Linux / 🧪 Python Source Version

### 🧰 Requirements

Install Python 3 and then run:

```bash
pip install -r requirements.txt
```

If you are on Debian/Ubuntu and encounter issues with `tkinter`:

```bash
sudo apt install python3-tk
```

### 📦 Installation

```bash
git clone https://github.com/zzpixels/zPixProxyScore.git
cd zPixProxyScore
pip install -r requirements.txt
```

### 🚀 Usage

Just run:

```bash
python main.py
```

You'll be prompted to enter:

1. A list of proxies (one per line, format: `IP:PORT:USER:PASS`)
2. An IPQualityScore API Key (can be saved for future runs)

---

## 📝 Config Persistence

Your API key is saved in a `config.json` file in the current directory if you check the “Save API Key” box. This prevents you from needing to re-enter it each time.

---

## 📊 Output

A GUI table will display:

| Proxy IP | Public IP | Location | ISP | Fraud Score | Proxy | VPN | Tor | Mobile | Recent Abuse | Bot Status |
|----------|-----------|----------|-----|-------------|--------|------|-----|--------|---------------|-------------|

Rows are color-coded:
- 🔴 Red = Fraud score ≥ 75 (high risk)
- 🟡 Yellow = Fraud score ≥ 30 (medium risk)

Double-clicking a row opens a popup showing the proxy's credentials and port.

You can also export the results to a `.csv` file using the **Export to CSV** button.

---

## 📄 License

MIT — free to use and modify.