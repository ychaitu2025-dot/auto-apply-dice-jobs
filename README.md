# Dice Auto Apply Bot

A Python app that automates job applications on Dice.com. Uses Selenium for browser automation and a Tkinter GUI for control.

Maintained by **Chaithanya Yadlapalli**.

## Installation

### Step 1: Clone the repo
```bash
git clone https://github.com/ychaitu2025-dot/auto-apply-dice-jobs
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
# If Tkinter is missing: brew install python-tk
python3 run.py
```

**Linux**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# If Tkinter is missing: sudo apt-get install python3-tk
chmod +x run.py
./run.py
```

## How to Use the Bot

The app has 4 tabs: **Run Bot**, **Settings**, **Scheduler**, and **Logs**.

### Page 1: Run Bot
- **Job Titles to Apply:** comma-separated job titles (e.g. `AI Engineer, ML Engineer, Data Scientist`)
- **Exclude Keywords:** comma-separated (e.g. `Java, Director, Principal, Architect`)
- **Include Keywords:** comma-separated (e.g. `Python, RAG, LLM, Azure, AWS, NLP, PyTorch, TensorFlow, Agentic, LangGraph, LangChain`)
- Set **Workplace Type** and **Employment Type** as needed
- Click **Start Applying** once Settings (Page 2) is done

### Page 2: Settings
1. Enter your Dice login email and password
2. Click **Test Login** and confirm the "Login successful" popup
3. Click **Save Settings**

You're ready — go back to Page 1 and click **Start Applying**.

### Page 3: Scheduler
- Set a start time, end time, and gap between runs (e.g. every 3 hours)
- Choose which days it should run
- Click **Activate Scheduler** to let it run automatically without you starting it manually

### Page 4: Logs
- Shows what the bot is doing in real time
- Click **Load Latest Log File** to view the most recent run's log

## Tips
- On Page 2, **Run in headless mode** runs the bot in the background with no visible browser window.
- If you hit an error, paste it into an AI coding assistant (Claude, Copilot, Codex, etc.) and ask it to explain and fix the issue.

## Maintainer
**Chaithanya Yadlapalli**
Contact: ychaitu2025@gmail.com
