# Dice Auto Apply Bot

A Python-based desktop application that helps automate job searching and application workflows on Dice.com using Selenium and a simple Tkinter GUI.

The application provides configurable job filters, automated application runs, scheduling, browser control, and real-time logging from a single desktop interface.

> Maintained by: Chaithanya Yadlapalli

---

## Features

* Search jobs using multiple job titles
* Include specific technical keywords
* Exclude unwanted roles or technologies
* Filter by workplace type
* Filter by employment type
* Automate supported Dice application workflows using Selenium
* Tkinter-based desktop GUI
* Schedule automated application runs
* Optional headless browser mode
* Real-time application logs
* Persistent application log files
* Configurable Dice account settings
* Built-in login testing

---

## Application

The application contains four main sections: Run Bot, Settings, Scheduler, and Logs.

### 1. Run Bot

Configure your job search and start the application process.

**Job Titles:** comma-separated job titles

```text
AI Engineer, ML Engineer, Generative AI Engineer, Data Scientist
```

**Exclude Keywords:** comma-separated, to skip unwanted positions

```text
Java, Director, Principal, Architect
```

**Include Keywords:** comma-separated, technologies or skills that should appear in relevant jobs

```text
Python, RAG, LLM, Azure, AWS, NLP, PyTorch, TensorFlow, Agentic AI, LangGraph, LangChain
```

You can also configure:

* Workplace type
* Employment type
* Other available application filters

Once the settings are configured, click Start Applying.

---

### 2. Settings

Configure the Dice account and browser settings.

1. Enter your Dice login email and password.
2. Click Test Login.
3. Confirm that the login test succeeds.
4. Click Save Settings.
5. Return to the Run Bot tab.

**Headless Mode:** an optional setting on this page. When enabled, Selenium runs without displaying the browser window, which is useful for scheduled/background runs.

---

### 3. Scheduler

Lets the bot run automatically on a schedule.

You can configure:

* Start time
* End time
* Run interval
* Days of the week

Example: start 9:00 AM, end 6:00 PM, every 3 hours, Monday to Friday.

Click Activate Scheduler to enable automatic runs.

---

### 4. Logs

Shows what the bot is doing in real time: jobs discovered, jobs evaluated, applications attempted, successful actions, skipped jobs, errors, and browser events.

Click Load Latest Log File to load the most recent log file.

---
## Installation

### Prerequisites

* Python 3.10+
* Git
* An active Dice account
* A supported browser for Selenium (Brave, Chrome, Firefox, Edge, or Safari)

### Step 1: Clone the repo

```bash
git clone https://github.com/ychaitu2025-dot/auto-apply-dice-jobs.git
cd auto-apply-dice-jobs
```

### Step 2: Set up based on your OS

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**macOS**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

If Tkinter is missing on macOS: `brew install python-tk`

**Linux**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x run.py
./run.py
```

If Tkinter is missing on Linux: `sudo apt-get install python3-tk`

---

## Credential Security

Your Dice credentials are required for the automated login workflow.

Never commit credentials to Git. Do not add passwords, API keys, cookies, session tokens, or other secrets to `.py` files, config files, `.env` files, log files, or Git commits.

Make sure local config/credential files are listed in `.gitignore`, for example:

```gitignore
venv/
__pycache__/
*.pyc
.env
.env.*
config.json
credentials.json
logs/
*.log
```

If you accidentally commit a credential, rotate it immediately and remove it from the repository history.

---

## Technology Stack

| Technology | Purpose |
| ---------- | ------- |
| Python | Application development |
| Tkinter | Desktop GUI |
| Selenium | Browser automation |
| WebDriver | Browser control |
| Logging | Application monitoring |
| Virtualenv | Dependency isolation |

---

## Troubleshooting

**Application does not start**

```bash
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**Tkinter error**

Ubuntu/Debian: `sudo apt-get install python3-tk`
macOS: `brew install python-tk`

**Selenium/browser problems**

Verify your browser is installed and compatible with the Selenium configuration. Try running without headless mode so you can watch what the browser is doing.

**Login failure**

Check your Dice email, password, internet connection, browser compatibility, and whether Dice is asking for extra verification. Use Test Login before starting a run.

**Application errors**

Check the Logs tab first, or the latest log file. When reporting an issue, include your OS, Python version, browser, the error message, the relevant log, and steps to reproduce. Never include passwords, cookies, or tokens.

---

## Contributing

Contributions, bug reports, and improvements are welcome.

```bash
git checkout -b feature/my-feature
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
```

Then open a Pull Request. Keep pull requests focused and include enough information to reproduce and test the change.

---

## Responsible Use

This project is intended as a personal automation and productivity tool. Automated interaction with websites may be subject to the site's terms of service, rate limits, and bot-detection systems.

You are responsible for reviewing Dice's terms and policies, using the software responsibly, avoiding excessive request rates, protecting your account credentials, reviewing applications before submission where appropriate, and complying with applicable laws and website policies.

The maintainer does not guarantee the automation will keep working if Dice changes its website, authentication, application flow, or anti-automation mechanisms.

---

## Maintainer

Chaithanya Yadlapalli

Email: ychaitu2025@gmail.com

GitHub: ychaitu2025-dot
