# SPYGLASS - SETUP GUIDE
==============================================

This guide walks you through setting up and running Spyglass

#### STEP 1: Install Python Dependencies
====================================

Open PowerShell or Command Prompt and run:

    pip install -r requirements.txt

This installs:
  - sqlalchemy (database ORM)
  - psutil (system info)
  - pynput (keyboard monitoring)
  - cryptography (encryption)
  - sqlcipher3-binary (database encryption)

If you get permission errors, try:
    pip install --user -r requirements.txt


#### STEP 2: Run the Spyglass App
==============================

In the same terminal, run:

   python spyglass.py

Optional launcher menu (starts Spyglass from `main.py`):

   python main.py


#### STEP 3: Follow the On-Screen Prompts
=====================================

A. ADMIN PRIVILEGES SCREEN
   - You'll see a UAC (User Account Control) prompt
   - Click "Yes" to grant administrator privileges
   - This is required for the monitoring processes of the app

B. CONSENT SCREEN
   - Read the monitoring disclosure
   - Choose monitoring level:
     [1] LOW  - Basic monitoring only
     [2] HIGH - Full monitoring including keystrokes
   - Type 1 or 2 and press ENTER
   - For device processes ONLY, select LOW (option 1)
   - For keylogger & device processes, select HIGH (option 2)


C. CONFIGURATION
   - Settings are automatically saved based on your choice
   - A confirmation screen shows your selection

D. DATABASE SETUP
   - Encrypted SQLCipher database is initialized
   - User table is created
   - Ready for testing

E. KEYSTROKE MENU (if you selected HIGH)
   - Select option 1 or 2 for 30 or 60-second test
   - Type freely on your keyboard
   - Test counts down automatically
   - Results show keystroke frequency analysis


#### STEP 4: View the Results
========================

After the test completes, you'll see:

KEYSTROKE LOGGING RESULTS
═══════════════════════════════════════════

Total keystrokes captured: [number]

Keystroke Frequency:
  'e'       42 ████████████████████████████████░░░░░░░
  't'       38 ███████████████████████████░░░░░░░░░░░░░
  'a'       35 ████████████████████░░░░░░░░░░░░░░░░░░
  ...

This shows which keys you pressed most frequently.


### FILES CREATED AFTER RUNNING TEST
==================================

spyglass.db
  - SQLCipher-encrypted database
  - Contains all monitoring data
  - Cannot be opened without encryption key

spyglass_settings.json
  - Configuration settings file
  - Stores monitoring level and feature toggles
  - Text file you can inspect

.spyglass_key (if using file-based encryption)
  - Encryption key file
  - Keep secure and secret

system_info.json
   - Full system/device information captured at startup
   - Saved in the Spyglass app folder
   - Used as a local record of initialization data


### TROUBLESHOOTING
===============

Issue: "ModuleNotFoundError: No module named 'X'"
Fix: Run 'pip install -r requirements.txt' again

Issue: "This application requires administrator privileges"
Fix: Run Command Prompt as Administrator, then run test

Issue: "Database is locked" or "no such table: main.event" error
Fix: 
  1. Close VS Code and all running instances
  2. Right-click PowerShell and select "Run as administrator"
  3. Run: `taskkill /IM python.exe /F`
  4. Run: `Remove-Item "spyglass.db" -Force`
  5. Restart the application to recreate the database

Issue: Keystroke test not capturing keystrokes
Fix: Make sure you selected HIGH monitoring level
    Restart test and select option 2

Issue: UAC prompt doesn't appear on elevation request
Fix: Try running Command Prompt as Administrator first,
    then run the test from that terminal


### TESTING RECOMMENDATIONS
=======================

1. First Test: Select LOW monitoring
   - Verifies consent and configuration work
   - No keystroke logging in this mode

2. Second Test: Select HIGH monitoring
   - Full keystroke logging enabled
   - Try the 30-second test first
   - Then try 60-second for more data

3. Check Configuration:
   - Select option 3 in the menu
   - View which monitoring is enabled
   - Check spyglass_settings.json file

4. Inspect Database:
   - File called spyglass.db is created
   - Encrypted with SQLCipher
   - Can view with SQLCipher tools (advanced)


### NEXT STEPS
==========

After testing keystroke logging:

1. Add more features:
   - Screenshot capture
   - Activity logging
   - Process tracking

2. Build full UI:
   - Dashboard for monitoring
   - Real-time statistics
   - Alert system


### IMPORTANT SECURITY NOTES
========================

- This monitoring captures ALL keyboard input
- Includes passwords, emails, sensitive data
- Ensure you only run this with proper authorization
- All data is encrypted at rest in SQLCipher
- Data stored locally on your device
- Keep encryption keys secure

This is for AUTHORIZED TESTING ONLY.


### QUESTIONS?
==========

Check the relevant file:
- Keystroke logging: keylogger.py
- App Monitoring: appMonitor.py
- Consent screen: consent.py
- Configuration: configSettings.py
- Database: database.py
- Admin privileges: adminHandler.py
