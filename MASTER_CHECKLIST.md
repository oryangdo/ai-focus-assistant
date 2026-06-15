# AI Focus Assistant — Master Checklist

# Stage 0 — Environment & Setup

* [x] Python virtual environment
* [x] OpenCV installed
* [x] YOLOv8 installed
* [x] GitHub repository initialized
* [x] GitHub Desktop workflow setup
* [x] .gitignore configured

---

# Stage 1 — Real-Time Webcam Pipeline

* [x] Webcam feed working
* [x] YOLO object detection
* [x] Bounding box rendering
* [x] Confidence filtering
* [x] FPS counter
* [x] Person detection
* [x] Phone detection

---

# Stage 2 — Distraction Detection Logic

* [x] Phone-specific alerts
* [x] Continuous phone visibility tracking
* [x] Detection persistence logic
* [x] False positive reduction
* [x] Distraction event counting
* [x] Phone visible seconds tracking

---

# Stage 3 — Focus Session System

* [x] Pomodoro timer
* [x] Focus/break modes
* [x] Session countdown
* [x] Session completion overlay
* [x] Focus score calculation
* [x] Session summaries
* [x] Home screen (SPACE to start — timer does not auto-start)

---

# Stage 4 — Persistence & Data Storage

* [x] CSV session logging
* [x] Historical session persistence
* [x] Timestamped sessions
* [x] Session data accumulation between runs
* [x] Application Support user data paths (`src/paths.py`)

---

# Stage 5 — Analytics Engine

* [x] Historical analytics script
* [x] Aggregate metrics
* [x] Trend analysis
* [x] Rolling averages
* [x] Personal records
* [x] Time-of-day analysis
* [x] Chart generation
* [x] Analytics terminal output

---

# Stage 6 — Streamlit Dashboard

* [x] Streamlit dashboard
* [x] Session history table
* [x] Analytics charts
* [x] Aggregate dashboard metrics
* [x] Dashboard data loading
* [x] Historical visualization
* [x] Launch from session summary (Open Dashboard button)
* [x] Altair charts with readable axis labels
* [x] Non-interactive charts (no zoom/pan; page scroll preserved)

---

# Stage 7 — Behavioral Intelligence

* [x] Live distraction risk score
* [x] Risk trend analytics
* [x] Risk prediction heuristics
* [x] Predictive distraction warnings
* [x] Risk dashboard integration
* [x] Extensible ML-ready risk architecture

---

# Stage 8 — Attention & Gaze

## Stage 8.1 — Head Pose / Gaze-Away Detection

* [x] Gaze-away detection (MediaPipe Face Landmarker)
* [x] Continuous look-away tracking (5+ second threshold)
* [x] Gaze distraction counting (no repeat until forward again)
* [x] Live HUD gaze status
* [x] Session logging (gaze_distractions, gaze_away_seconds)
* [x] CSV schema migration for gaze/risk columns
* [x] Analytics and dashboard integration
* [x] Gaze factor in live risk estimator
* [x] Focus score includes gaze penalties
* [x] Historical gaze baselines in risk estimation
* [x] Persistent session summary overlay (ESC / X dismiss)
* [x] Session summary overlay on quit-with-q

### Stage 8.1 — Remaining polish

* [ ] Live HUD gaze_away_seconds total

## Stage 8.2+ — Future

* [ ] Posture tracking
* [ ] Eye gaze tracking (fine-grained)

---

# Stage 9 — Product Polish

* [ ] Config/settings system
* [x] Dashboard UI polish (Altair charts, readable labels, static graphs)
* [ ] Demo video
* [x] Professional README
* [ ] Screenshots/GIFs (placeholder section only)
* [x] App packaging (scripts + launchers)
* [x] Installer/build pipeline (`build_mac_app.sh`, `package_release.sh`)
* [x] PyInstaller build verification and release zip
* [x] Focus-only release zip workflow (`release_mac.sh`, `verify_release.sh`)
* [ ] Public GitHub release (upload zip to Releases)

---

# Stage 10 — Productivity Intelligence

Evolve from attention monitoring into personalized productivity insights using existing `sessions.csv` data.

## Stage 10.1 — Intelligence Foundation

* [ ] Derived session metrics (phone/gaze ratios, distraction density, risk spread)
* [ ] Personal baselines and “vs your average” comparisons
* [ ] Extended time-of-day analysis (hour, weekday, heatmap data)
* [ ] Study habit metrics (streaks, weekly volume, completion rate)
* [ ] Penalty decomposition (explain focus score breakdown)
* [ ] Phone vs gaze distraction profile

## Stage 10.2 — Recommendations + Dashboard

* [ ] Rule-based recommendation engine (`src/recommendations.py`)
* [ ] Dashboard insights panel (weekly summary, best time window)
* [ ] Productivity DNA / attention breakdown charts
* [ ] One-line insight on session summary (“+8 vs your avg”)

## Stage 10.3 — Predictive & ML-Ready (optional)

* [ ] Pre-session expected score briefing
* [ ] Focus quality tiers (Deep Work / Solid / Fragmented / At Risk)
* [ ] ML feature export from session history

---

# Future / Stretch Goals

* [ ] Multi-user support
* [ ] Cloud sync
* [ ] Mobile companion app
* [ ] Cross-device analytics
* [ ] Embedded ESP32 companion device
* [ ] Hardware focus indicator
* [ ] Posture tracking
* [ ] Fine-grained eye gaze tracking

---

# Engineering Goals

* Keep architecture modular
* Keep code readable
* Avoid giant monolithic files
* Maintain clean Git history
* Keep analytics reproducible
* Make future ML integration easy

---

# Current Immediate Goal

**Stage 10.1:** Build the productivity intelligence foundation — derived metrics, personal baselines, habit analytics, and extended time-of-day analysis on top of `sessions.csv`.

Remaining polish outside Stage 10: live HUD gaze-away seconds total, README screenshots/GIFs, demo video, PyInstaller build verification, public release.
