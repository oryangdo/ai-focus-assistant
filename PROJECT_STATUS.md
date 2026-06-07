# AI Focus Assistant — Project Status

## Overview

AI-powered productivity assistant using YOLOv8, OpenCV, analytics, and Streamlit.

The application detects phone distractions during Pomodoro focus sessions, tracks behavioral data, stores session history, and generates productivity analytics.

---

# Current Features

## Real-Time Detection

* Webcam feed using OpenCV
* YOLOv8 object detection
* Phone-specific detection
* Person detection
* Confidence threshold filtering
* MediaPipe Face Landmarker head-pose / gaze-away detection
* Personal baseline calibration (~3s) with deviation-based look-away detection

## Focus Session System

* Pomodoro timer
* Focus/break modes
* Distraction tracking (phone + gaze)
* Phone visible time tracking
* Gaze away time and gaze distraction events (5+ sec continuous look-away)
* Focus score calculation (phone + gaze penalties)
* Live HUD with gaze status (CAL / FWD / AWAY / NO FACE)
* Session summary overlay with gaze metrics

## Behavioral Intelligence

* Live distraction risk score (LOW / MEDIUM / HIGH)
* Gaze-weighted live risk factor (30%)
* Historical risk baselines from CSV (phone + gaze history)
* Predictive on-screen warnings (phone streak, gaze look-away, rising risk)

## Persistence

* CSV session logging (9-column schema)
* Automatic CSV header migration with `.bak` backup
* Historical data persists between runs
* Session timestamps stored

## Analytics

* Historical analytics script
* Trend analysis (focus, phone, risk, gaze)
* Rolling averages
* Personal records
* Time-of-day analysis
* Charts generated in reports/ (including gaze_metrics.png)

## Dashboard

* Streamlit dashboard
* Session table with gaze and risk columns
* Historical charts (focus, phone, risk, gaze)
* Aggregate metrics with formula help text

---

# Current Project Structure

## Main Files

* webcam_demo.py — main webcam entry point
* src/gaze_tracker.py — MediaPipe head-pose / gaze-away tracking
* src/hud.py — OpenCV HUD overlays
* src/pomodoro.py — Pomodoro timer and session data
* src/risk_estimator.py — heuristic risk model
* src/session_logger.py — CSV persistence and schema migration
* src/analytics.py
* src/dashboard.py

## Data

* data/sessions.csv

## Reports

* reports/

---

# Current Architecture

YOLO detection runs in real time using OpenCV webcam frames.

Phone and gaze detection events feed into:

* distraction tracking
* focus scoring
* live risk estimation
* Pomodoro session analytics

Session data is saved to CSV and later analyzed through:

* analytics.py
* Streamlit dashboard

Modular layout: gaze tracking, HUD, risk, and persistence are separate modules consumed by webcam_demo.py.

---

# Current Focus Score Logic

Score starts at 100 and subtracts penalties (clamped to 0–100):

* **Phone time share** — `(phone_visible_seconds / duration) × 50` (major)
* **Phone distractions** — `distractions × 5` (major)
* **Gaze distractions** — `gaze_distraction_count × 2` (minor)
* **Gaze away share** — `(gaze_away_seconds / duration) × 25` (minor)

---

# Current Risk Logic

Live risk combines five weighted factors: session fatigue, recent phone activity, current distractions, historical CSV baselines (phone 60% / gaze 40%), and live gaze head pose (30% weight). Historical gaze averages from sessions.csv raise baseline risk for users who frequently look away.

---

# Current Goals

## Completed

* **Stage 7** — Behavioral intelligence (live risk, warnings, risk analytics, dashboard)
* **Stage 8.1** — Gaze-away detection, HUD, logging, analytics, risk integration
* **Stage 8.1 polish** — CSV schema migration, gaze in focus score, historical gaze risk baselines

## Next Major Goal

**Stage 9 — Product polish:**

* Config/settings system
* HUD polish (live gaze-away time total, summary on quit)
* Dashboard redesign and screenshots
* Demo video and public GitHub release

---

# Future Ideas

* ML-based distraction prediction
* User settings/config system
* Desktop app packaging
* Better UI/UX polish
* Multi-user support
* Study recommendations
* Focus streak tracking

---

# Known Issues / Improvements

* Trends based on a small session dataset
* Live HUD shows gaze event count but not running gaze-away seconds total
* Quit-with-q saves session but skips the 5-second summary overlay
* Face landmarker model downloads on first run to `models/face_landmarker.task`
* UI and dashboard could use further polish

---