# AI Focus Assistant

An AI-powered productivity assistant that uses **YOLOv8** and **OpenCV** to detect phone distractions during **Pomodoro** focus sessions, log session history, and visualize productivity trends with analytics and a **Streamlit** dashboard.

## Features

- **Real-time webcam detection** — YOLOv8 object detection with bounding boxes and confidence filtering
- **Phone distraction tracking** — streak-based detection to reduce false positives
- **Pomodoro timer** — 25-minute focus / 5-minute break cycles with on-screen HUD
- **Focus scoring** — score based on distractions and phone visible time
- **Distraction risk estimation** — live LOW / MEDIUM / HIGH risk during focus sessions
- **Predictive warnings** — on-screen alerts before a phone distraction is logged
- **Risk trend analytics** — historical peak/avg risk trends in CLI and dashboard
- **Session logging** — append-only CSV history in `data/sessions.csv`
- **Analytics CLI** — trends, rolling averages, personal records, time-of-day stats, charts in `reports/`
- **Streamlit dashboard** — session history, metrics, and charts

## Requirements

- **Python 3.10+** (recommended)
- **Webcam** (for the live demo)
- macOS, Linux, or Windows

## Quick start

### 1. Clone and set up the environment

```bash
git clone <your-repo-url>
cd summer_project

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Run the live focus session (webcam)

```bash
python webcam_demo.py
```

Or use the helper script:

```bash
./run.sh
```

On first run, **Ultralytics downloads** `yolov8s.pt` automatically (~22MB). Weights are not stored in Git.

**Controls**

| Key | Action |
|-----|--------|
| `q` | Quit (saves the current focus session if one is active) |

The HUD shows timer mode, phone hits, risk level, FPS, and object count.

### 3. View analytics (terminal + charts)

```bash
python -m src.analytics
```

Charts are written to `reports/` (gitignored). Run this after completing one or more focus sessions.

### 4. Open the dashboard

```bash
python -m streamlit run src/dashboard.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## Project structure

```
summer_project/
├── webcam_demo.py      # Main app: webcam + YOLO + Pomodoro + risk HUD
├── run.sh              # Shortcut to run webcam_demo.py
├── requirements.txt
├── src/
│   ├── pomodoro.py         # Timer and session scoring
│   ├── risk_estimator.py   # Heuristic distraction risk (ML-ready interface)
│   ├── session_logger.py   # CSV persistence
│   ├── analytics.py        # Historical stats and chart generation
│   └── dashboard.py        # Streamlit UI
├── data/               # Created at runtime (sessions.csv)
└── reports/            # Created by analytics (PNG charts)
```

## Data and generated files

These paths are **not** committed to Git:

| Path | Purpose |
|------|---------|
| `data/sessions.csv` | Session history (timestamp, duration, distractions, phone time, focus score, risk scores) |
| `reports/*.png` | Charts from `src/analytics.py` |
| `*.pt` | YOLO weights (downloaded on first run) |
| `Ultralytics/` | Ultralytics config cache |

A fresh clone starts with no session data. The dashboard and analytics scripts show an empty state until you complete at least one focus session.

## How it works

1. **Detection** — Each frame is processed by YOLOv8; phone detections use a confidence threshold and a consecutive-frame streak before counting as a distraction.
2. **Sessions** — `PomodoroTimer` tracks focus/break modes, distractions, phone visible time, and risk samples.
3. **Persistence** — Completed sessions are appended to `data/sessions.csv`.
4. **Analytics** — `src/analytics.py` and `src/dashboard.py` read the same CSV for summaries and charts.

## Configuration

Tunable constants (thresholds, model path, timer lengths) live in:

- `webcam_demo.py` — detection and HUD settings
- `src/pomodoro.py` — focus/break durations (default 25 / 5 minutes)
- `src/risk_estimator.py` — risk weights and level thresholds

## Troubleshooting

| Issue | Suggestion |
|-------|------------|
| Webcam won't open | Close other apps using the camera; check permissions |
| Slow FPS | Use `yolov8n.pt` in `webcam_demo.py` for a lighter model |
| No data in dashboard | Run `webcam_demo.py` and finish or quit (`q`) a focus session first |
| `ModuleNotFoundError` | Activate `.venv` and run `pip install -r requirements.txt` |

## Roadmap

See `MASTER_CHECKLIST.md` for feature stages. Stage 7 (behavioral intelligence) is complete. Next focus:

- Product polish: screenshots, config system, UI improvements (Stage 9)
- ML personalization (Stage 8)

## License

Add a license file if you plan to publish this repository publicly.
