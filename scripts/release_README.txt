AI Focus Assistant — macOS Release
====================================

Thank you for downloading AI Focus Assistant.

This zip contains a standalone focus session app. You do not need Python
or Terminal to run it.


QUICK START
-----------

1. Unzip
   - Double-click AI-Focus-Assistant-mac.zip
   - macOS creates a folder named AI-Focus-Assistant-mac

2. Open the app
   - Open that folder
   - Double-click "AI Focus Assistant.app"

3. Start a focus session
   - On the home screen, press SPACE
   - A 25-minute Pomodoro focus session begins

4. When the session ends
   - A summary overlay appears with your focus score and distractions
   - Press ESC or click X to dismiss the summary


FIRST LAUNCH ON macOS (GATEKEEPER)
----------------------------------

Because this app is not signed with an Apple Developer ID, macOS may block
it the first time.

If you see "can't be opened because Apple cannot check it for malicious
software":

1. Do NOT double-click the app again immediately
2. Right-click (or Control-click) "AI Focus Assistant.app"
3. Choose "Open"
4. Click "Open" in the dialog
5. After this one-time step, you can double-click normally in the future

Alternative: System Settings → Privacy & Security → scroll down → click
"Open Anyway" next to the blocked app message.


CAMERA PERMISSION
-----------------

AI Focus Assistant needs your webcam to detect phone distractions and
track gaze during focus sessions.

When macOS asks for camera access:
- Click OK / Allow

If you previously denied access:
System Settings → Privacy & Security → Camera → enable
"AI Focus Assistant"


SESSION DATA
------------

Your session history is saved automatically to:

  ~/Library/Application Support/AI Focus Assistant/data/sessions.csv

(Full path example:
 /Users/YOUR_USERNAME/Library/Application Support/AI Focus Assistant/data/sessions.csv)

Each completed focus session appends a row with focus score, distractions,
phone time, gaze metrics, and risk scores.


CONTROLS
--------

SPACE  — Start focus session (from home screen)
Q      — End session early and show summary (during focus), or quit
ESC / X — Dismiss session summary


VIEWING ANALYTICS (OPTIONAL)
----------------------------

This release zip contains the focus session app only.

To view charts and full session history in the Streamlit dashboard,
clone the project from GitHub, set up Python once, and run:

  python -m streamlit run src/dashboard.py

See the project README for details.


TROUBLESHOOTING
---------------

Camera will not open
  → Check System Settings → Privacy & Security → Camera

App will not open
  → Use the Gatekeeper right-click → Open workaround above

Need help
  → https://github.com/oryangdo/summer_project
