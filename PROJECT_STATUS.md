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

## Focus Session System

* Pomodoro timer
* Focus/break modes
* Distraction tracking
* Phone visible time tracking
* Focus score calculation
* Session summary overlay

## Persistence

* CSV session logging
* Historical data persists between runs
* Session timestamps stored

## Analytics

* Historical analytics script
* Trend analysis
* Rolling averages
* Personal records
* Time-of-day analysis
* Charts generated in reports/

## Dashboard

* Streamlit dashboard
* Session table
* Historical charts
* Aggregate metrics

---

# Current Project Structure

## Main Files

* src/webcam_demo.py
* src/analytics.py
* src/dashboard.py

## Data

* data/sessions.csv

## Reports

* reports/

---

# Current Architecture

YOLO detection runs in real time using OpenCV webcam frames.

Phone detection events feed into:

* distraction tracking
* focus scoring
* Pomodoro session analytics

Session data is saved to CSV and later analyzed through:

* analytics.py
* Streamlit dashboard

---

# Current Focus Score Logic

Focus score is based on:

* distraction count
* total phone visible time
* session duration

(Current implementation may evolve later.)

---

# Current Goals

## Next Major Goal

Implement distraction risk prediction system.

Desired features:

* live distraction risk score
* behavioral trend analysis
* predictive heuristics
* future ML model integration

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

* Current trends are based on small dataset
* Focus score formula may need refinement
* UI could be cleaner
* YOLO model weights currently tracked in Git
* Need better dashboard polish

---