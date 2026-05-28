# dice_auto_apply/app_tkinter.py

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
import pyautogui
import subprocess
import json

# Try both absolute and relative imports for compatibility
try:
    from core.browser_detector import get_browser_path
    from core.dice_login import login_to_dice, update_dice_credentials, validate_dice_credentials
    from core.main_script import get_web_driver, fetch_jobs_with_requests, apply_to_job_url
except ImportError:
    try:
        from core.browser_detector import get_browser_path
        from core.dice_login import login_to_dice, update_dice_credentials, validate_dice_credentials
        from core.main_script import get_web_driver, fetch_jobs_with_requests, apply_to_job_url
    except ImportError:
        from core.browser_detector import get_browser_path
        from core.dice_login import login_to_dice, update_dice_credentials, validate_dice_credentials
        from core.main_script import get_web_driver, fetch_jobs_with_requests, apply_to_job_url



def fix_imports():
    """Fix imports for both development and packaged environments"""
    import os
    import sys
    
    # Add the parent directory to the path if not already there
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Call this at the beginning of your script
fix_imports()

class DiceAutoBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dice Auto Apply Bot")
        self.root.geometry("900x700")
        
        # Set app icon if available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "resources", "app_icon.png")
            if os.path.exists(icon_path):
                # For Windows
                if sys.platform == 'win32':
                    self.root.iconbitmap(icon_path)
                # For macOS and others that support .png icons
                else:
                    img = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, img)
        except Exception as e:
            pass
        
        # Disable PyAutoGUI failsafe
        pyautogui.FAILSAFE = False
        
        # Configure logging
        self.setup_logging()
        
        # Initialize variables
        self.driver = None
        self.job_thread = None
        self.running = False

        # Scheduler state
        self.scheduler_enabled = False
        self.scheduler_thread = None
        self.next_run_time = None
        self.scheduler_history = []
        
        # Load configuration if exists
        self.load_config()
        
        # Create the tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tab frames
        self.main_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.logs_tab = ttk.Frame(self.notebook)
        self.scheduler_tab = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.main_tab, text="Run Bot")
        self.notebook.add(self.settings_tab, text="Settings")
        self.notebook.add(self.logs_tab, text="Logs")
        self.notebook.add(self.scheduler_tab, text="⏰ Scheduler")
        
        # Set up UI for each tab
        self.setup_main_tab()
        self.setup_settings_tab()
        self.setup_logs_tab()
        self.setup_scheduler_tab()
        
        # Log that app is started
        self.logger.info("Application started")
        
    def setup_logging(self):
        """Set up logging for the application"""
        # Create logs directory if needed
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        # Create log filename with timestamp
        log_file = os.path.join(logs_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self):
        """Load configuration from config file"""
        self.config_dir = os.path.join(os.path.dirname(__file__), "config")
        self.config_file = os.path.join(self.config_dir, "settings.json")
        
        # Default values
        self.search_queries = ["AI ML", "Gen AI", "Agentic AI", "Data Engineer", "Data Analyst", "Machine Learning"]
        self.exclude_keywords = ["Manager", "Director",".net", "SAP","java","w2 only","only w2","no c2c",
        "only on w2","w2 profiles only","tester","f2f"]
        self.include_keywords = ["AI", "Artificial","Inteligence","Machine","Learning", "ML", "Data", "NLP", "ETL",
        "Natural Language Processing","analyst","scientist","senior","cloud", 
        "aws","gcp","Azure","agentic","python","rag","llm"]
        self.headless_mode = False
        self.job_limit = 1500
        
        # Try to load from file if it exists
        import json
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.search_queries = config.get('search_queries', self.search_queries)
                    self.exclude_keywords = config.get('exclude_keywords', self.exclude_keywords)
                    self.include_keywords = config.get('include_keywords', self.include_keywords)
                    self.headless_mode = config.get('headless_mode', self.headless_mode)
                    self.job_limit = config.get('job_application_limit', self.job_limit)
                    self.logger.info("Configuration loaded successfully")
            except Exception as e:
                self.logger.error(f"Error loading configuration: {e}")
        
    def save_config(self):
        """Save configuration to config file"""
        # Ensure config directory exists
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        import json
        try:
            config = {
                'search_queries': [q.strip() for q in self.search_query_entry.get().split(',') if q.strip()],
                'exclude_keywords': [k.strip() for k in self.exclude_keywords_entry.get().split(',') if k.strip()],
                'include_keywords': [k.strip() for k in self.include_keywords_entry.get().split(',') if k.strip()],
                'headless_mode': self.headless_var.get(),
                'job_application_limit': self.job_limit_var.get()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
            # Update credentials in .env file
            username = self.username_entry.get()
            password = self.password_entry.get()
            
            if username and password:
                update_dice_credentials(username, password)
                
            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")
            self.logger.info("Settings saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Could not save settings: {str(e)}")
        
    def calculate_time_estimate(self, jobs_count):
        """Calculate and display estimated completion time based on job count"""
        # Calculate based on historical data or defaults
        # Average time per job is around 10 seconds, but can vary
        avg_job_time = 10  # seconds
        total_seconds = jobs_count * avg_job_time
        
        # Add overhead time for initialization, etc.
        overhead_seconds = 60  # 1 minute overhead
        
        total_seconds += overhead_seconds
        
        # Calculate hours, minutes, seconds
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Create time string
        time_str = ""
        if hours > 0:
            time_str += f"{int(hours)} hours "
        if minutes > 0 or hours > 0:
            time_str += f"{int(minutes)} minutes "
        time_str += f"{int(seconds)} seconds"
        
        # Update UI with estimate
        self.update_status(f"Estimated completion time: {time_str}")
        return time_str

    def setup_main_tab(self):
        """Set up the main tab UI"""
        # Job queries section
        query_frame = ttk.LabelFrame(self.main_tab, text="Job Titles to Apply:")
        query_frame.pack(fill="x", padx=10, pady=10)
        
        # Search queries field
        self.search_query_entry = ttk.Entry(query_frame, width=70)
        self.search_query_entry.pack(fill="x", padx=10, pady=10)
        self.search_query_entry.insert(0, ", ".join(self.search_queries))
        
        # Keywords section
        keywords_frame = ttk.LabelFrame(self.main_tab, text="Optional Keywords for Better Job Filtering:")
        keywords_frame.pack(fill="x", padx=10, pady=10)
        
        # Exclude keywords
        ttk.Label(keywords_frame, text="Exclude Keywords:").pack(anchor="w", padx=10, pady=5)
        self.exclude_keywords_entry = ttk.Entry(keywords_frame, width=70)
        self.exclude_keywords_entry.pack(fill="x", padx=10, pady=5)
        self.exclude_keywords_entry.insert(0, ", ".join(self.exclude_keywords))
        
        # Include keywords
        ttk.Label(keywords_frame, text="Include Keywords:").pack(anchor="w", padx=10, pady=5)
        self.include_keywords_entry = ttk.Entry(keywords_frame, width=70)
        self.include_keywords_entry.pack(fill="x", padx=10, pady=5)
        self.include_keywords_entry.insert(0, ", ".join(self.include_keywords))
        
        # Start button with custom style
        style = ttk.Style()
        style.configure("Green.TButton", background="gray", font=("Helvetica", 12))
        
        self.start_button = ttk.Button(self.main_tab, text="Start Applying", command=self.start_applying, style="Green.TButton")
        self.start_button.pack(fill="x", padx=10, pady=10)
        
        # Stop button
        self.stop_button = ttk.Button(self.main_tab, text="Stop", command=self.stop_applying, state="disabled")
        self.stop_button.pack(fill="x", padx=10, pady=5)
        
        # Progress section
        progress_frame = ttk.LabelFrame(self.main_tab, text="Progress")
        progress_frame.pack(fill="x", padx=10, pady=10)
        
        # Status label
        self.status_label = ttk.Label(progress_frame, text="Ready to start.")
        self.status_label.pack(padx=10, pady=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        
        # Statistics frame
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        # Add estimated time label
        estimated_time_frame = ttk.Frame(progress_frame)
        estimated_time_frame.pack(fill="x", padx=10, pady=2)
        ttk.Label(estimated_time_frame, text="Estimated Time:").grid(row=0, column=0, padx=5, pady=2)
        self.estimated_time_label = ttk.Label(estimated_time_frame, text="Calculating...")
        self.estimated_time_label.grid(row=0, column=1, padx=5, pady=2)

        # Total Jobs
        ttk.Label(stats_frame, text="Total Jobs:").grid(row=0, column=0, padx=5, pady=5)
        self.jobs_found_label = ttk.Label(stats_frame, text="0")
        self.jobs_found_label.grid(row=0, column=1, padx=5, pady=5)
        
        # Jobs applied
        ttk.Label(stats_frame, text="Jobs Applied:").grid(row=0, column=2, padx=5, pady=5)
        self.jobs_applied_label = ttk.Label(stats_frame, text="0")
        self.jobs_applied_label.grid(row=0, column=3, padx=5, pady=5)
        
        # Failed jobs
        ttk.Label(stats_frame, text="Failed Applications:").grid(row=0, column=4, padx=5, pady=5)
        self.jobs_failed_label = ttk.Label(stats_frame, text="0")
        self.jobs_failed_label.grid(row=0, column=5, padx=5, pady=5)
        
        # Excel Files section
        excel_frame = ttk.LabelFrame(self.main_tab, text="Excel Files")
        excel_frame.pack(fill="x", padx=10, pady=5)
        
        excel_buttons_frame = ttk.Frame(excel_frame)
        excel_buttons_frame.pack(fill="x", padx=5, pady=5)
        
        # Open Applied Jobs Excel
        applied_button = ttk.Button(excel_buttons_frame, text="Open Applied Jobs Excel", command=lambda: self.open_excel_file("applied_jobs.xlsx"))
        applied_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Open Not Applied Jobs Excel
        not_applied_button = ttk.Button(excel_buttons_frame, text="Open Not Applied Jobs Excel", command=lambda: self.open_excel_file("not_applied_jobs.xlsx"))
        not_applied_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Open Excluded Jobs Excel
        excluded_button = ttk.Button(excel_buttons_frame, text="Open Excluded Jobs Excel", command=lambda: self.open_excel_file("excluded_jobs.xlsx"))
        excluded_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Log section
        log_frame = ttk.LabelFrame(self.main_tab, text="Logs")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create text widget with scrollbar
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.config(state="disabled")  # Make it read-only
        
        # Add a handler that redirects logs to this widget
        self.log_handler = LogTextHandler(self.log_text)
        self.log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        self.logger.addHandler(self.log_handler)
        
    def open_excel_file(self, filename):
        """Open an Excel file using the system default application"""
        try:
            if not os.path.exists(filename):
                if filename == "excluded_jobs.xlsx":
                    # Create the file if it doesn't exist
                    df = pd.DataFrame(columns=["Job Title", "Job URL", "Company", "Location", "Employment Type", "Posted Date", "Exclusion Reason"])
                    df.to_excel(filename, index=False)
                    self.logger.info(f"Created new {filename} file")
                else:
                    messagebox.showinfo("File Not Found", f"The file {filename} does not exist yet.")
                    return
                    
            # Open the file with the default system application
            if sys.platform == "win32":
                os.startfile(filename)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", filename])
            else:  # Linux
                subprocess.run(["xdg-open", filename])
                
            self.logger.info(f"Opened {filename}")
        except Exception as e:
            self.logger.error(f"Error opening {filename}: {e}")
            messagebox.showerror("Error", f"Could not open {filename}: {str(e)}")

    def setup_settings_tab(self):
        """Set up the settings tab UI"""
        # Login settings
        login_frame = ttk.LabelFrame(self.settings_tab, text="Dice Login")
        login_frame.pack(fill="x", padx=10, pady=10)
        
        # Username field
        username_frame = ttk.Frame(login_frame)
        username_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(username_frame, text="Username:", width=15).pack(side="left")
        self.username_entry = ttk.Entry(username_frame, width=50)
        self.username_entry.pack(side="left", fill="x", expand=True)
        
        # Password field
        password_frame = ttk.Frame(login_frame)
        password_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(password_frame, text="Password:", width=15).pack(side="left")
        self.password_entry = ttk.Entry(password_frame, show="*", width=50)
        self.password_entry.pack(side="left", fill="x", expand=True)
        
        # Test login button
        self.test_login_button = ttk.Button(login_frame, text="Test Login", command=self.test_login)
        self.test_login_button.pack(pady=10)
        
        # Application settings
        settings_frame = ttk.LabelFrame(self.settings_tab, text="Application Settings")
        settings_frame.pack(fill="x", padx=10, pady=10)
        
        # Headless mode checkbox
        self.headless_var = tk.BooleanVar(value=self.headless_mode)
        headless_check = ttk.Checkbutton(
            settings_frame, 
            text="Run in headless mode (no visible browser)",
            variable=self.headless_var
        )
        headless_check.pack(anchor="w", padx=10, pady=5)
        
        # Job limit
        limit_frame = ttk.Frame(settings_frame)
        limit_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(limit_frame, text="Maximum jobs to apply for:").pack(side="left")
        self.job_limit_var = tk.IntVar(value=self.job_limit)
        job_limit_spin = ttk.Spinbox(
            limit_frame, 
            from_=1, 
            to=1000, 
            width=5, 
            textvariable=self.job_limit_var
        )
        job_limit_spin.pack(side="left", padx=5)
        
        # Save settings button
        self.save_settings_button = ttk.Button(
            settings_frame, 
            text="Save Settings",
            command=self.save_config
        )
        self.save_settings_button.pack(pady=10)
        
        # User guide
        guide_frame = ttk.LabelFrame(self.settings_tab, text="User Guide")
        guide_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.guide_text = scrolledtext.ScrolledText(guide_frame, wrap=tk.WORD)
        self.guide_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add user guide content
        guide_content = """
How to Use This Application
--------------------------

1. Enter your Dice.com login credentials in the Settings tab and test them
2. Enter job titles to search for (separated by commas)
3. Optionally specify include/exclude keywords to filter results
4. Click "Start Applying" to begin the automated job application process

Understanding Keywords
--------------------

Include Keywords: Jobs must contain at least one of these words in the title
Exclude Keywords: Jobs containing any of these words will be skipped

Finding Results
-------------

After the process completes, you can find:
- applied_jobs.xlsx - List of jobs successfully applied to
- not_applied_jobs.xlsx - List of jobs that couldn't be applied to
        """
        self.guide_text.insert("1.0", guide_content)
        self.guide_text.config(state="disabled")  # Make it read-only
        
        # Get login details from environment (if available)
        from dotenv import load_dotenv
        load_dotenv()
        import os
        username = os.getenv("DICE_USERNAME", "")
        password = os.getenv("DICE_PASSWORD", "")
        
        if username:
            self.username_entry.insert(0, username)
        if password:
            self.password_entry.insert(0, password)
        
    def setup_logs_tab(self):
        """Set up the logs tab UI"""
        # Create full log view
        log_frame = ttk.Frame(self.logs_tab)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create text widget with scrollbar
        self.full_log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.full_log_text.pack(fill="both", expand=True)
        self.full_log_text.config(state="disabled")  # Make it read-only
        
        # Add button to load latest log file
        ttk.Button(self.logs_tab, text="Load Latest Log File", command=self.load_log_file).pack(pady=10)
        
    def load_log_file(self):
        """Load and display the latest log file"""
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        if not os.path.exists(logs_dir):
            messagebox.showinfo("No Logs", "No log files found.")
            return
            
        # Find all log files
        log_files = [os.path.join(logs_dir, f) for f in os.listdir(logs_dir) if f.startswith("app_")]
        
        if not log_files:
            messagebox.showinfo("No Logs", "No log files found.")
            return
            
        # Get the most recent log file
        latest_log = max(log_files, key=os.path.getmtime)
        
        try:
            # Read and display log content
            with open(latest_log, 'r') as f:
                content = f.read()
                
            # Update the text widget
            self.full_log_text.config(state="normal")
            self.full_log_text.delete("1.0", tk.END)
            self.full_log_text.insert("1.0", content)
            self.full_log_text.config(state="disabled")
            
            self.logger.info(f"Loaded log file: {os.path.basename(latest_log)}")
            
        except Exception as e:
            self.logger.error(f"Error loading log file: {e}")
            messagebox.showerror("Error", f"Failed to load log file: {str(e)}")
            
    def test_login(self):
        """Test Dice login credentials"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Missing Credentials", "Please enter both username and password.")
            return
            
        # Disable button during testing
        self.test_login_button.config(state="disabled", text="Testing...")
        self.root.update_idletasks()
        
        def test_login_thread():
            try:
                # Import the validation function
                
                success = validate_dice_credentials(username, password)
                
                # Update UI from the main thread
                self.root.after(0, lambda: self.test_login_complete(success))
                
            except Exception as e:
                self.logger.error(f"Login test error: {str(e)}")
                # Update UI from the main thread
                self.root.after(0, lambda: self.test_login_complete(False, str(e)))
                
        # Run the test in a separate thread
        threading.Thread(target=test_login_thread, daemon=True).start()
        
    def test_login_complete(self, success, error_msg=None):
        """Handle login test completion"""
        # Re-enable the button
        self.test_login_button.config(state="normal", text="Test Login")
        
        if success:
            self.logger.info("Login test successful")
            messagebox.showinfo("Login Test", "Login successful!")
        else:
            error = error_msg if error_msg else "Login failed. Please check your credentials."
            self.logger.error(f"Login test failed: {error}")
            messagebox.showerror("Login Test", error)
            
    def start_applying(self):
        """Start the job application process"""
        # Validate inputs
        search_queries = [q.strip() for q in self.search_query_entry.get().split(",") if q.strip()]
        if not search_queries:
            messagebox.showwarning("Missing Input", "Please enter at least one job title to search for.")
            return
            
        # Check for login credentials
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing Credentials", "Please enter Dice login credentials in the Settings tab.")
            self.notebook.select(1)  # Switch to settings tab
            return
            
        # Get keywords
        exclude_keywords = [k.strip() for k in self.exclude_keywords_entry.get().split(",") if k.strip()]
        include_keywords = [k.strip() for k in self.include_keywords_entry.get().split(",") if k.strip()]
        
        # Update UI
        self.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_bar["value"] = 0
        self.status_label.config(text="Starting...")
        
        # Reset counters
        self.jobs_found_label.config(text="0")
        self.jobs_applied_label.config(text="0")
        self.jobs_failed_label.config(text="0")
        
        # Clear log text
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")
        
        # Run job application process in a separate thread
        self.job_thread = threading.Thread(
            target=self.run_job_application,
            args=(search_queries, include_keywords, exclude_keywords, username, password),
            daemon=True
        )
        self.job_thread.start()
        
    def run_job_application(self, search_queries, include_keywords, exclude_keywords, username, password):
        """Run the job application process in a background thread"""
        try:
            # Record start time
            start_time = time.time()
            self.logger.info(f"Starting job applications with queries: {search_queries}")
            
            # Initialize web driver
            self.update_status("Initializing web driver...")
            headless = self.headless_var.get()
            driver = get_web_driver()
            
            # Login to Dice
            self.update_status("Logging in to Dice...")
            login_success = login_to_dice(driver, (username, password))
            if not login_success:
                self.update_status("Login failed. Please check your credentials.")
                self.root.after(0, lambda: messagebox.showerror(
                    "Login Failed", 
                    "Could not log in to Dice. Please check your credentials."
                ))
                driver.quit()
                self.reset_ui()
                return
                    
            self.update_status("Login successful. Fetching jobs...")
            
            # Find jobs matching the search queries
            all_jobs = {}
            excluded_jobs = []  # Track excluded jobs
            total_queries = len(search_queries)
            
            for i, query in enumerate(search_queries):
                if not self.running:
                    self.update_status("Stopped by user.")
                    driver.quit()
                    self.reset_ui()
                    return
                    
                self.update_status(f"Searching for '{query}' ({i+1}/{total_queries})...")
                
                # Use the fetch_jobs_with_requests function
                jobs, excluded = fetch_jobs_with_requests(driver, query, include_keywords, exclude_keywords)
                
                # Track counts before adding new jobs
                jobs_before = len(all_jobs)
                
                # Add unique jobs to dictionary
                for job in jobs:
                    if job["Job URL"] not in all_jobs:
                        all_jobs[job["Job URL"]] = job
                
                # Add excluded jobs
                excluded_jobs.extend(excluded)
                
                # Calculate current count
                current_count = len(all_jobs)
                
                # Update the counter after each query, capturing the current count
                count_to_display = current_count
                self.root.after(0, lambda c=count_to_display: self.jobs_found_label.config(text=str(c)))
                
                # Print debug info
                print(f"Query '{query}': Found {len(jobs)} total jobs, added {current_count - jobs_before} unique jobs")
                
                # Move mouse to prevent sleeping
                pyautogui.moveRel(1, 1, duration=0.1)
                pyautogui.moveRel(-1, -1, duration=0.1)
                        
            # Make sure the final count is displayed
            final_count = len(all_jobs)
            self.update_status(f"Found {final_count} unique jobs matching criteria")
            self.root.after(0, lambda c=final_count: self.jobs_found_label.config(text=str(c)))
            
            # Save excluded jobs to Excel
            if excluded_jobs:
                try:
                    excluded_file = "excluded_jobs.xlsx"
                    df_excluded = pd.DataFrame(excluded_jobs)
                    df_excluded.to_excel(excluded_file, index=False)
                    self.logger.info(f"Saved {len(excluded_jobs)} excluded jobs to {excluded_file}")
                except Exception as e:
                    self.logger.error(f"Error saving excluded jobs: {e}")
            
            # Check for already applied jobs
            self.update_status("Checking for already applied jobs...")
            applied_jobs_file = "applied_jobs.xlsx"
            already_applied = set()
            
            if os.path.exists(applied_jobs_file):
                try:
                    df_applied = pd.read_excel(applied_jobs_file)
                    already_applied = set(df_applied["Job URL"].dropna())
                    self.update_status(f"Found {len(already_applied)} previously applied jobs to skip")
                except Exception as e:
                    self.logger.error(f"Error reading applied jobs file: {e}")
            
            # Filter out already applied jobs
            jobs_to_apply = [job for job in all_jobs.values() if job["Job URL"] not in already_applied]
            self.update_status(f"Applying to {len(jobs_to_apply)} jobs...")

            # Update the Total Jobs count to show the jobs that will be processed
            jobs_to_process_count = len(jobs_to_apply)
            self.root.after(0, lambda c=jobs_to_process_count: self.jobs_found_label.config(text=str(c)))

            # Apply job limit if set
            job_limit = self.job_limit_var.get()
            if job_limit > 0 and len(jobs_to_apply) > job_limit:
                limited_count = job_limit
                self.update_status(f"Limiting to {job_limit} jobs as per settings")
                jobs_to_apply = jobs_to_apply[:job_limit]
                self.root.after(0, lambda c=limited_count: self.jobs_found_label.config(text=str(c)))

            # Calculate initial estimated time (assuming 10 jobs per minute)
            jobs_per_minute = 10.0
            total_jobs = len(jobs_to_apply)
            
            if total_jobs > 0:
                estimated_minutes = total_jobs / jobs_per_minute
                hours = int(estimated_minutes // 60)
                minutes = int(estimated_minutes % 60)

                # Format time string
                initial_estimate = ""
                if hours > 0:
                    initial_estimate += f"{hours} hours "
                if minutes > 0 or hours > 0:
                    initial_estimate += f"{minutes} minutes"
                else:
                    initial_estimate += "less than 1 minute"

                # Update both status and dedicated time label
                self.update_status(f"Estimated completion time: {initial_estimate}")
                self.root.after(0, lambda t=initial_estimate: self.estimated_time_label.config(text=t))
            
            # Start applying to jobs
            applied_count = 0
            failed_count = 0
            
            # Variables for dynamic time estimation
            job_start_times = []
            job_processing_times = []
            
            for i, job in enumerate(jobs_to_apply):
                if not self.running:
                    self.update_status("Stopped by user.")
                    driver.quit()
                    self.reset_ui()
                    return
                
                # Record job start time for this specific job
                job_start_time = time.time()
                
                # Update progress
                progress = int((i / len(jobs_to_apply)) * 100) if jobs_to_apply else 0
                self.root.after(0, lambda p=progress: self.progress_bar.config(value=p))
                
                # Show job details in status
                job_title = job.get("Job Title", "Unknown")
                self.update_status(f"Applying to: {job_title} ({i+1}/{len(jobs_to_apply)})")

                # Apply to job using your existing function
                try:
                    result = apply_to_job_url(driver, job["Job URL"])
                    
                    # Record job completion time and calculate processing time for this job
                    job_end_time = time.time()
                    processing_time = job_end_time - job_start_time
                    
                    # Keep track of job times for estimation
                    job_start_times.append(job_start_time)
                    job_processing_times.append(processing_time)
                    
                    # Calculate dynamic time estimate after a few jobs
                    if i >= 2 and len(jobs_to_apply) > i+1:
                        # Calculate average time per job based on the last few jobs
                        recent_times = job_processing_times[-min(10, len(job_processing_times)):]
                        avg_time_per_job = sum(recent_times) / len(recent_times)
                        
                        # Calculate remaining time
                        remaining_jobs = len(jobs_to_apply) - (i + 1)
                        remaining_seconds = avg_time_per_job * remaining_jobs
                        
                        # Format remaining time string
                        remaining_hours = int(remaining_seconds // 3600)
                        remaining_minutes = int((remaining_seconds % 3600) // 60)
                        remaining_seconds = int(remaining_seconds % 60)
                        
                        time_remaining = ""
                        if remaining_hours > 0:
                            time_remaining += f"{remaining_hours} hours "
                        if remaining_minutes > 0 or remaining_hours > 0:
                            time_remaining += f"{remaining_minutes} minutes "
                        time_remaining += f"{remaining_seconds} seconds"
                        
                        # Update the estimated time label
                        self.root.after(0, lambda t=time_remaining: self.estimated_time_label.config(text=t))
                    
                    if result:
                        applied_count += 1
                        # Update applied count
                        count_to_display = applied_count
                        self.root.after(0, lambda c=count_to_display: 
                            self.jobs_applied_label.config(text=str(c)))
                        
                        # Save to applied jobs Excel file
                        try:
                            job["Applied"] = True
                            if os.path.exists(applied_jobs_file):
                                df_existing = pd.read_excel(applied_jobs_file)
                            else:
                                df_existing = pd.DataFrame(columns=[
                                    "Job Title", "Job URL", "Company", "Location", 
                                    "Employment Type", "Posted Date", "Applied"
                                ])
                            
                            df_new = pd.DataFrame([job])
                            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                            df_combined.to_excel(applied_jobs_file, index=False)
                        except Exception as e:
                            self.logger.error(f"Error updating Excel file: {e}")
                    else:
                        failed_count += 1
                        # Update failed count
                        count_to_display = failed_count
                        self.root.after(0, lambda c=count_to_display: 
                            self.jobs_failed_label.config(text=str(c)))
                        
                        # Save to not applied jobs Excel file
                        not_applied_file = "not_applied_jobs.xlsx"
                        try:
                            if os.path.exists(not_applied_file):
                                df_existing = pd.read_excel(not_applied_file)
                            else:
                                df_existing = pd.DataFrame(columns=[
                                    "Job Title", "Job URL", "Company", "Location", 
                                    "Employment Type", "Posted Date", "Applied"
                                ])
                            
                            job["Applied"] = False
                            df_new = pd.DataFrame([job])
                            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                            df_combined.to_excel(not_applied_file, index=False)
                        except Exception as e:
                            self.logger.error(f"Error updating not_applied Excel file: {e}")
                    
                except Exception as e:
                    self.logger.error(f"Error applying to {job_title}: {e}")
                    failed_count += 1
                    # Update failed count
                    count_to_display = failed_count
                    self.root.after(0, lambda c=count_to_display: 
                        self.jobs_failed_label.config(text=str(c)))
                
                # Move mouse to prevent sleeping
                pyautogui.moveRel(1, 1, duration=0.1)
                pyautogui.moveRel(-1, -1, duration=0.1)
            
            # Compute execution time
            end_time = time.time()
            execution_time = end_time - start_time
            hours, remainder = divmod(execution_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_str = f"{int(hours)}h {int(minutes)}m {seconds:.2f}s"
            self.update_status(f"Completed! Applied: {applied_count}, Failed: {failed_count}, Time: {time_str}")
            
            # Final progress update
            self.root.after(0, lambda: self.progress_bar.config(value=100))
            # Clear estimated time as we're done
            self.root.after(0, lambda: self.estimated_time_label.config(text="Completed"))
            
            # Save job data to JSON file
            import json
            try:
                job_data = {
                    "Total Jobs Found": len(all_jobs),
                    "Jobs Applied": applied_count,
                    "Jobs Failed": failed_count,
                    "Execution Time": time_str,
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with open("job_application_summary.json", "w") as f:
                    json.dump(job_data, f, indent=4)
            except Exception as e:
                self.logger.error(f"Error saving job data: {e}")
                
            # Show completion message
            self.root.after(0, lambda: messagebox.showinfo(
                "Process Complete", 
                f"Application process completed!\n\n"
                f"Applied to {applied_count} jobs\n"
                f"Failed for {failed_count} jobs\n\n"
                f"Total execution time: {time_str}"
            ))
            
            # Clean up
            driver.quit()
                
        except Exception as e:
            self.logger.error(f"Error in job application process: {e}")
            self.update_status(f"Error: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror(
                "Error", 
                f"An error occurred: {str(e)}"
            ))
        finally:
            # Reset UI
            self.reset_ui()


            
    def stop_applying(self):
        """Stop the job application process"""
        if not self.running:
            return
            
        self.running = False
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Stopping... Please wait.")
        self.logger.info("User requested to stop the application process")
        
    def reset_ui(self):
        """Reset UI after job completion or stop"""
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="normal", text="Stop")
        
    def update_status(self, message):
        """Update status message and log it"""
        self.logger.info(message)
        self.root.after(0, lambda msg=message: self.status_label.config(text=msg))

    # ───────────────────────────── SCHEDULER ─────────────────────────────

    def setup_scheduler_tab(self):
        """Build the Scheduler tab UI."""
        # ── Status bar at the top ──
        status_frame = ttk.LabelFrame(self.scheduler_tab, text="Scheduler Status")
        status_frame.pack(fill="x", padx=10, pady=(10, 5))

        row1 = ttk.Frame(status_frame)
        row1.pack(fill="x", padx=10, pady=5)
        ttk.Label(row1, text="Status:", width=14, anchor="w").pack(side="left")
        self.sched_status_label = ttk.Label(row1, text="Disabled", foreground="gray")
        self.sched_status_label.pack(side="left")

        row2 = ttk.Frame(status_frame)
        row2.pack(fill="x", padx=10, pady=2)
        ttk.Label(row2, text="Next Run:", width=14, anchor="w").pack(side="left")
        self.sched_next_label = ttk.Label(row2, text="—")
        self.sched_next_label.pack(side="left")

        row3 = ttk.Frame(status_frame)
        row3.pack(fill="x", padx=10, pady=2)
        ttk.Label(row3, text="Countdown:", width=14, anchor="w").pack(side="left")
        self.sched_countdown_label = ttk.Label(row3, text="—")
        self.sched_countdown_label.pack(side="left")

        # ── Mode selection ──
        mode_frame = ttk.LabelFrame(self.scheduler_tab, text="Schedule Mode")
        mode_frame.pack(fill="x", padx=10, pady=5)

        self.sched_mode_var = tk.StringVar(value="window")
        ttk.Radiobutton(mode_frame, text="Run every 10-15 min inside a time window  (e.g. 09:00 – 18:00)",
                        variable=self.sched_mode_var, value="window",
                        command=self._toggle_sched_mode).pack(anchor="w", padx=10, pady=3)
        ttk.Radiobutton(mode_frame, text="Run at specific time(s) every day",
                        variable=self.sched_mode_var, value="daily",
                        command=self._toggle_sched_mode).pack(anchor="w", padx=10, pady=3)
        ttk.Radiobutton(mode_frame, text="Run every N hours (interval)",
                        variable=self.sched_mode_var, value="interval",
                        command=self._toggle_sched_mode).pack(anchor="w", padx=10, pady=3)

        # ── Time-window panel (NEW - shown by default) ──
        self.window_frame = ttk.Frame(mode_frame)
        self.window_frame.pack(fill="x", padx=20, pady=5)

        wrow1 = ttk.Frame(self.window_frame)
        wrow1.pack(anchor="w", pady=3)
        ttk.Label(wrow1, text="Start time:").pack(side="left")
        self.window_start_var = tk.StringVar(value="09:00")
        ttk.Entry(wrow1, textvariable=self.window_start_var, width=8).pack(side="left", padx=5)
        ttk.Label(wrow1, text="End time:").pack(side="left", padx=(10, 0))
        self.window_end_var = tk.StringVar(value="18:00")
        ttk.Entry(wrow1, textvariable=self.window_end_var, width=8).pack(side="left", padx=5)

        wrow2 = ttk.Frame(self.window_frame)
        wrow2.pack(anchor="w", pady=3)
        ttk.Label(wrow2, text="Run every").pack(side="left")
        self.window_min_var = tk.IntVar(value=10)
        ttk.Spinbox(wrow2, from_=1, to=60, width=4,
                    textvariable=self.window_min_var).pack(side="left", padx=4)
        ttk.Label(wrow2, text="to").pack(side="left")
        self.window_max_var = tk.IntVar(value=15)
        ttk.Spinbox(wrow2, from_=1, to=60, width=4,
                    textvariable=self.window_max_var).pack(side="left", padx=4)
        ttk.Label(wrow2, text="minutes (random)").pack(side="left")

        ttk.Label(self.window_frame,
                  text="Bot will run every 10-15 min while inside the window, then pause until next day.",
                  foreground="gray").pack(anchor="w")

        # ── Daily times panel ──
        self.daily_frame = ttk.Frame(mode_frame)
        # not packed by default (window is selected)

        ttk.Label(self.daily_frame, text="Run times (HH:MM, comma-separated):").pack(anchor="w")
        self.sched_times_entry = ttk.Entry(self.daily_frame, width=40)
        self.sched_times_entry.insert(0, "09:00, 13:00, 18:00")
        self.sched_times_entry.pack(anchor="w", pady=3)
        ttk.Label(self.daily_frame,
                  text="Example: 09:00, 13:00, 18:00  (24-hour format)",
                  foreground="gray").pack(anchor="w")

        # ── Interval panel ──
        self.interval_frame = ttk.Frame(mode_frame)
        # not packed by default (window is selected)

        int_row = ttk.Frame(self.interval_frame)
        int_row.pack(anchor="w", pady=3)
        ttk.Label(int_row, text="Repeat every").pack(side="left")
        self.sched_interval_var = tk.IntVar(value=4)
        ttk.Spinbox(int_row, from_=1, to=24, width=5,
                    textvariable=self.sched_interval_var).pack(side="left", padx=5)
        ttk.Label(int_row, text="hour(s)").pack(side="left")

        ttk.Label(self.interval_frame,
                  text="First run starts immediately when you enable the scheduler.",
                  foreground="gray").pack(anchor="w")

        # ── Days of week ──
        days_frame = ttk.LabelFrame(self.scheduler_tab, text="Active Days")
        days_frame.pack(fill="x", padx=10, pady=5)

        days_row = ttk.Frame(days_frame)
        days_row.pack(padx=10, pady=5)
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.day_vars = []
        for i, d in enumerate(day_names):
            v = tk.BooleanVar(value=(i < 5))  # Mon-Fri on by default
            self.day_vars.append(v)
            ttk.Checkbutton(days_row, text=d, variable=v).pack(side="left", padx=6)

        # ── Control buttons ──
        btn_frame = ttk.Frame(self.scheduler_tab)
        btn_frame.pack(fill="x", padx=10, pady=8)

        self.sched_enable_btn = ttk.Button(
            btn_frame, text="▶  Enable Scheduler",
            command=self.enable_scheduler)
        self.sched_enable_btn.pack(side="left", padx=5)

        self.sched_disable_btn = ttk.Button(
            btn_frame, text="⏹  Disable Scheduler",
            command=self.disable_scheduler, state="disabled")
        self.sched_disable_btn.pack(side="left", padx=5)

        ttk.Button(btn_frame, text="▶  Run Now",
                   command=self._scheduler_trigger_now).pack(side="left", padx=5)

        # ── Run history ──
        hist_frame = ttk.LabelFrame(self.scheduler_tab, text="Run History")
        hist_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.sched_history_text = scrolledtext.ScrolledText(
            hist_frame, height=8, wrap=tk.WORD, state="disabled")
        self.sched_history_text.pack(fill="both", expand=True, padx=5, pady=5)

    def _toggle_sched_mode(self):
        """Show/hide the correct options panel."""
        mode = self.sched_mode_var.get()
        self.window_frame.pack_forget()
        self.daily_frame.pack_forget()
        self.interval_frame.pack_forget()
        if mode == "window":
            self.window_frame.pack(fill="x", padx=20, pady=5)
        elif mode == "daily":
            self.daily_frame.pack(fill="x", padx=20, pady=5)
        else:
            self.interval_frame.pack(fill="x", padx=20, pady=5)

    # ── enable / disable ──

    def enable_scheduler(self):
        """Validate inputs and start the background scheduler thread."""
        if self.scheduler_enabled:
            return

        # Validate inputs based on mode
        mode = self.sched_mode_var.get()
        if mode == "window":
            for label, var in [("Start time", self.window_start_var), ("End time", self.window_end_var)]:
                try:
                    datetime.strptime(var.get().strip(), "%H:%M")
                except ValueError:
                    messagebox.showwarning("Scheduler",
                        f"Invalid {label}: '{var.get()}'\nUse HH:MM (24-hour).")
                    return
            if self.window_min_var.get() > self.window_max_var.get():
                messagebox.showwarning("Scheduler", "Min interval must be ≤ Max interval.")
                return
        elif mode == "daily":
            raw = self.sched_times_entry.get()
            times = [t.strip() for t in raw.split(",") if t.strip()]
            if not times:
                messagebox.showwarning("Scheduler", "Please enter at least one run time.")
                return
            for t in times:
                try:
                    datetime.strptime(t, "%H:%M")
                except ValueError:
                    messagebox.showwarning("Scheduler",
                        f"Invalid time format: '{t}'\nUse HH:MM (24-hour).")
                    return

        self.scheduler_enabled = True
        self.sched_enable_btn.config(state="disabled")
        self.sched_disable_btn.config(state="normal")
        self.sched_status_label.config(text="Active", foreground="green")
        self._log_sched_history("Scheduler enabled.")
        self.logger.info("Scheduler enabled")

        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        # Start countdown ticker
        self._update_countdown()

    def disable_scheduler(self):
        """Stop the scheduler."""
        self.scheduler_enabled = False
        self.next_run_time = None
        self.sched_enable_btn.config(state="normal")
        self.sched_disable_btn.config(state="disabled")
        self.sched_status_label.config(text="Disabled", foreground="gray")
        self.sched_next_label.config(text="—")
        self.sched_countdown_label.config(text="—")
        self._log_sched_history("Scheduler disabled.")
        self.logger.info("Scheduler disabled")

    # ── background loop ──

    def _scheduler_loop(self):
        """Runs in a daemon thread; fires the bot at the right times."""
        import random
        mode = self.sched_mode_var.get()

        if mode == "window":
            # Parse window bounds
            sh, sm = map(int, self.window_start_var.get().strip().split(":"))
            eh, em = map(int, self.window_end_var.get().strip().split(":"))
            min_interval = self.window_min_var.get()
            max_interval = self.window_max_var.get()

            while self.scheduler_enabled:
                now = datetime.now()
                start_today = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
                end_today   = now.replace(hour=eh, minute=em, second=0, microsecond=0)

                if self._is_active_day(now) and start_today <= now <= end_today:
                    # Inside window — fire
                    self.root.after(0, self._scheduler_trigger_now)
                    # Wait a random interval before next attempt
                    wait_mins = random.randint(min_interval, max_interval)
                    self.next_run_time = datetime.now() + timedelta(minutes=wait_mins)
                    self.root.after(0, lambda t=self.next_run_time:
                        self.sched_next_label.config(text=t.strftime("%H:%M:%S")))
                    # Sleep in 30-second chunks so we can be cancelled quickly
                    for _ in range(wait_mins * 2):  # wait_mins * 60s / 30s
                        if not self.scheduler_enabled:
                            break
                        time.sleep(30)
                else:
                    # Outside window — figure out when the next window opens
                    if now < start_today:
                        next_window = start_today
                    else:
                        # Window already ended today; open tomorrow
                        next_window = start_today + timedelta(days=1)
                    # Skip to the next active day
                    for _ in range(7):
                        if self._is_active_day(next_window):
                            break
                        next_window += timedelta(days=1)

                    self.next_run_time = next_window
                    self.root.after(0, lambda t=next_window:
                        self.sched_next_label.config(text=t.strftime("%Y-%m-%d %H:%M")))
                    time.sleep(30)

        elif mode == "interval":
            hours = self.sched_interval_var.get()
            self.next_run_time = datetime.now()
            while self.scheduler_enabled:
                now = datetime.now()
                if now >= self.next_run_time:
                    if self._is_active_day(now):
                        self.root.after(0, self._scheduler_trigger_now)
                    self.next_run_time = datetime.now() + timedelta(hours=hours)
                    self.root.after(0, lambda t=self.next_run_time:
                        self.sched_next_label.config(text=t.strftime("%Y-%m-%d %H:%M")))
                time.sleep(30)
        else:
            # daily mode
            while self.scheduler_enabled:
                self.next_run_time = self._next_daily_run()
                if self.next_run_time:
                    self.root.after(0, lambda t=self.next_run_time:
                        self.sched_next_label.config(text=t.strftime("%Y-%m-%d %H:%M")))
                time.sleep(30)
                now = datetime.now()
                if self.next_run_time and now >= self.next_run_time:
                    if self._is_active_day(now):
                        self.root.after(0, self._scheduler_trigger_now)
                    self.next_run_time = self.next_run_time + timedelta(minutes=1)

    def _next_daily_run(self):
        """Return the next datetime matching a configured time slot."""
        raw = self.sched_times_entry.get()
        times = [t.strip() for t in raw.split(",") if t.strip()]
        now = datetime.now()
        candidates = []
        for t in times:
            try:
                h, m = map(int, t.split(":"))
                candidate = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if candidate <= now:
                    candidate += timedelta(days=1)
                candidates.append(candidate)
            except Exception:
                pass
        return min(candidates) if candidates else None

    def _is_active_day(self, dt):
        """Return True if dt falls on a checked weekday (0=Mon … 6=Sun)."""
        return self.day_vars[dt.weekday()].get()

    def _scheduler_trigger_now(self):
        """Trigger a bot run immediately (called from scheduler or 'Run Now' button)."""
        if self.running:
            self._log_sched_history("Skipped (bot already running).")
            return
        self._log_sched_history(f"Triggered run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.start_applying()

    def _update_countdown(self):
        """Tick the countdown label every second."""
        if not self.scheduler_enabled:
            return
        if self.next_run_time:
            remaining = self.next_run_time - datetime.now()
            total_sec = int(remaining.total_seconds())
            if total_sec < 0:
                total_sec = 0
            h, r = divmod(total_sec, 3600)
            m, s = divmod(r, 60)
            self.sched_countdown_label.config(text=f"{h:02d}h {m:02d}m {s:02d}s")
        self.root.after(1000, self._update_countdown)

    def _log_sched_history(self, msg):
        """Append a timestamped line to the history text box."""
        entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
        self.scheduler_history.append(entry)
        self.sched_history_text.config(state="normal")
        self.sched_history_text.insert("end", entry)
        self.sched_history_text.see("end")
        self.sched_history_text.config(state="disabled")
        

class LogTextHandler(logging.Handler):
    """Custom log handler that redirects logs to a tk Text widget"""
    
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        
    def emit(self, record):
        msg = self.format(record)
        
        def append_log():
            self.text_widget.config(state="normal")
            self.text_widget.insert("end", msg + "\n")
            self.text_widget.see("end")  # Scroll to the bottom
            self.text_widget.config(state="disabled")
            
        # Schedule the update in the main thread
        self.text_widget.after(0, append_log)


def main():
    root = tk.Tk()
    app = DiceAutoBotApp(root)
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

if __name__ == "__main__":
    main()
