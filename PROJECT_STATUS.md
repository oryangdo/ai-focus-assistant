# AI Focus Assistant — Project Status

## Overview

AI-powered productivity assistant using YOLOv8, OpenCV, MediaPipe, analytics, and Streamlit.

The application detects phone and gaze distractions during Pomodoro focus sessions, tracks behavioral data, stores session history, and generates productivity analytics.

---

# Current Features

## Real-Time Detection

* Webcam feed using OpenCV
* YOLOv8 object detection (yolov8s)
* Phone-specific detection with streak-based false-positive reduction
* Person detection
* Confidence threshold filtering
* MediaPipe Face Landmarker head-pose / gaze-away detection
* Personal baseline calibration (~3s) with deviation-based look-away detection

## Focus Session System

* Home screen on launch — press **SPACE** to start a focus session
* Pomodoro timer (25 min focus / 5 min break)
* Focus/break modes; timer does not auto-start on app open
* Distraction tracking (phone + gaze)
* Phone visible time tracking
* Gaze away time and gaze distraction events (5+ sec continuous look-away)
* Focus score calculation (phone + gaze penalties)
* Live HUD with gaze status (CAL / FWD / AWAY / NO FACE)
* Persistent session summary overlay (ESC / X to dismiss)
* **Open Dashboard** button on session summary (+ D key) — opens browser stats

## Behavioral Intelligence

* Live distraction risk score (LOW / MEDIUM / HIGH)
* Gaze-weighted live risk factor (30%)
* Historical risk baselines from CSV (phone + gaze history)
* Predictive on-screen warnings (phone streak, gaze look-away, rising risk)

## Persistence

* CSV session logging (9-column schema)
* Automatic CSV header migration with `.bak` backup
* User data in `~/Library/Application Support/AI Focus Assistant/`
* Session timestamps stored

## Analytics

* Historical analytics script
* Trend analysis (focus, phone, risk, gaze)
* Rolling averages, personal records, time-of-day analysis
* Charts saved to Application Support `reports/`

## Dashboard

* Streamlit dashboard (opens in web browser)
* Session table with gaze and risk columns
* Historical charts (focus, phone, risk, gaze)
* Aggregate metrics with formula help text
* Launch via `Open Dashboard.app`, session summary button, or CLI

## Desktop Packaging (Stage 9.1)

* macOS repo launchers in `macos/` (double-click after setup)
* PyInstaller build script: `scripts/build_mac_app.sh`
* Release zip script: `scripts/package_release.sh`
* Standalone focus `.app` (~1 GB) + separate dashboard launcher in release bundle

---

# Current Project Structure

## Main Files

* webcam_demo.py — main webcam entry point
* src/gaze_tracker.py — MediaPipe head-pose / gaze-away tracking
* src/hud.py — OpenCV HUD overlays, home screen, session summary
* src/pomodoro.py — Pomodoro timer and session data
* src/risk_estimator.py — heuristic risk model
* src/session_logger.py — CSV persistence and schema migration
* src/paths.py — Application Support paths and model resolution
* src/dashboard_launcher.py — start Streamlit + open browser
* src/ui_utils.py — GUI error dialogs for packaged launches
* src/analytics.py
* src/dashboard.py

## Scripts

* scripts/setup_mac_apps.sh — one-time dev launcher setup
* scripts/build_mac_app.sh — PyInstaller standalone build
* scripts/package_release.sh — zip focus app + dashboard launcher

## User Data (runtime)

* `~/Library/Application Support/AI Focus Assistant/data/sessions.csv`
* `~/Library/Application Support/AI Focus Assistant/reports/`
* `~/Library/Application Support/AI Focus Assistant/cache/` (model downloads)

---

# Current Architecture

YOLO detection and gaze tracking run in real time on OpenCV webcam frames during active focus sessions.

Phone and gaze events feed distraction tracking, focus scoring, live risk estimation, and Pomodoro analytics.

Session data saves to Application Support CSV and is consumed by analytics.py and the Streamlit dashboard.

Modular layout: gaze, HUD, risk, paths, persistence, and analytics are separate modules consumed by webcam_demo.py.

---

# Current Focus Score Logic

Score starts at 100 and subtracts penalties (clamped to 0–100):

* **Phone time share** — `(phone_visible_seconds / duration) × 50` (major)
* **Phone distractions** — `distractions × 5` (major)
* **Gaze distractions** — `gaze_distraction_count × 2` (minor)
* **Gaze away share** — `(gaze_away_seconds / duration) × 25` (minor)

---

# Current Risk Logic

Live risk combines five weighted factors: session fatigue, recent phone activity, current distractions, historical CSV baselines (phone 60% / gaze 40%), and live gaze head pose (30% weight).

---

# Current Goals

## Completed

* **Stages 0–8.1** — Full CV pipeline, gaze, risk, analytics, dashboard
* **Stage 9.1 (partial)** — paths module, macOS launchers, build scripts, home screen, persistent summary, dashboard button, quit-with-q summary

## In Progress

* **Stage 9.1** — Complete PyInstaller build verification and release zip
* **Stage 9** — Screenshots, demo video, config system, public release

## Remaining Polish

* Live HUD running gaze-away seconds total (not just event count)
* Screenshot/GIF assets for README
* Demo video

---

# Known Issues / Improvements

* Trends based on a small session dataset
* Live HUD shows gaze event count but not running gaze-away seconds total
* Standalone focus app excludes Streamlit — dashboard requires separate launcher + Python setup
* UI and dashboard could use further polish
* README screenshot placeholders until assets are added
