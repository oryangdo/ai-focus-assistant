# AI Focus Assistant

An AI-powered productivity system that detects phone and gaze distractions during Pomodoro focus sessions, estimates real-time distraction risk, and turns session history into actionable analytics.

Built with **YOLOv8**, **MediaPipe**, **OpenCV**, and **Streamlit**.

---

## Demo

**[▶ Watch demo video](https://youtu.be/PLACEHOLDER)** *(add link when ready)*

A 60–90 second walkthrough: live focus session → phone/gaze detection → session summary → dashboard.

---

## Screenshots

| Live focus HUD | Session summary |
|:---:|:---:|
| ![Live focus session HUD](docs/images/live-hud.png) | ![Session summary overlay](docs/images/session-summary.png) |
| Pomodoro timer, gaze status, live risk, phone detection | Focus score, phone time, gaze metrics, peak risk |

| Streamlit dashboard | Analytics charts |
|:---:|:---:|
| ![Streamlit dashboard](docs/images/dashboard.png) | ![Analytics charts](docs/images/analytics-charts.png) |
| Session history, aggregate metrics, trend lines | CLI-generated focus, phone, risk, and gaze charts |

> Add PNGs to `docs/images/` before publishing. Paths above are ready to use once assets exist.

---

## GIFs

| Phone detection | Gaze tracking | Risk warning |
|:---:|:---:|:---:|
| ![Phone detection demo](docs/images/phone-detection.gif) | ![Gaze tracking demo](docs/images/gaze-tracking.gif) | ![Risk warning demo](docs/images/risk-warning.gif) |
| YOLO streak-based phone alert | Head-pose look-away detection | Predictive on-screen warning |

> Short screen recordings (5–15 s each) work well here. Export as GIF or use GitHub-supported formats.

---

## Project Overview

Most Pomodoro timers measure time — not *attention*. **AI Focus Assistant** runs a real-time webcam pipeline that detects phone use and look-away behavior, scores each focus session, estimates live distraction risk, and logs history for analytics.

Modular design: detection, gaze tracking, Pomodoro, risk estimation, persistence, and analytics are separate modules orchestrated by `webcam_demo.py`.

---

## Features

- **Real-time CV** — YOLOv8 phone/person detection + MediaPipe head-pose gaze tracking
- **Pomodoro sessions** — 25/5 focus/break cycles with live HUD and session summaries
- **Behavioral intelligence** — live LOW / MEDIUM / HIGH risk with predictive warnings
- **Analytics** — CSV logging, CLI trends, and a Streamlit dashboard

---

## Architecture

```mermaid
flowchart TB
    subgraph Input["Input Layer"]
        WC["Webcam Input<br/><i>OpenCV capture</i>"]
    end

    subgraph RealTime["Real-Time Processing Pipeline"]
        direction TB
        YOLO["YOLO Detection<br/><i>YOLOv8 — phone & person</i>"]
        GAZE["Gaze Tracker<br/><i>MediaPipe Face Landmarker</i>"]
    end

    subgraph Session["Focus Session System"]
        POM["Pomodoro System<br/><i>Timer · focus/break · scoring</i>"]
    end

    subgraph Intelligence["Behavioral Intelligence"]
        RISK["Risk Estimator<br/><i>Live LOW / MEDIUM / HIGH</i>"]
    end

    subgraph Persistence["Persistence Layer"]
        LOG["Session Logger<br/><i>Schema migration · timestamps</i>"]
        CSV[("CSV Storage<br/><i>data/sessions.csv</i>")]
    end

    subgraph Offline["Offline Analytics & Visualization"]
        ANALYTICS["Analytics Engine<br/><i>Trends · charts · reports/</i>"]
        DASH["Streamlit Dashboard<br/><i>Session table · historical charts</i>"]
    end

    ORCH["webcam_demo.py<br/><i>Main orchestrator</i>"]

    WC --> ORCH
    ORCH --> YOLO
    ORCH --> GAZE

    YOLO -->|"Phone streak · visible time<br/>Distraction events"| POM
    GAZE -->|"Look-away seconds<br/>Gaze distraction events"| POM

    POM -->|"Session state · metrics"| RISK
    GAZE -->|"Head pose · gaze status"| RISK
    YOLO -->|"Phone activity"| RISK

    CSV -.->|"Historical phone & gaze baselines"| RISK

    POM -->|"Focus score · session summary"| LOG
    RISK -->|"Peak risk score"| LOG
    LOG --> CSV

    CSV --> ANALYTICS
    CSV --> DASH

    classDef input fill:#e8f4fd,stroke:#1a73e8,stroke-width:2px
    classDef realtime fill:#fef7e0,stroke:#f9ab00,stroke-width:2px
    classDef session fill:#e6f4ea,stroke:#34a853,stroke-width:2px
    classDef intel fill:#fce8e6,stroke:#ea4335,stroke-width:2px
    classDef persist fill:#f3e8fd,stroke:#9334e6,stroke-width:2px
    classDef offline fill:#e8eaf6,stroke:#5c6bc0,stroke-width:2px
    classDef orch fill:#fff,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5

    class WC input
    class YOLO,GAZE realtime
    class POM session
    class RISK intel
    class LOG,CSV persist
    class ANALYTICS,DASH offline
    class ORCH orch
```

**Stack:** OpenCV · YOLOv8 · MediaPipe · Python · CSV · Matplotlib · Streamlit

---

## Installation

**Requirements:** Python 3.10+, webcam, macOS / Linux / Windows

```bash
git clone https://github.com/oryangdo/summer_project.git
cd summer_project

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

First run auto-downloads YOLO weights (`yolov8s.pt`) and the MediaPipe face model (`models/face_landmarker.task`).

---

## Usage

**Live focus session**

```bash
python webcam_demo.py    # or ./run.sh
```

Press `q` to quit — saves the current session if active.

**Analytics & dashboard**

```bash
python -m src.analytics
python -m streamlit run src/dashboard.py
```

---

## Analytics

Sessions append to `data/sessions.csv` (focus score, distractions, phone/gaze time, risk scores). The CLI prints trends and writes charts to `reports/`; the Streamlit dashboard shows session history and aggregate metrics.

---

## Roadmap

- **Next:** UI polish, config system, screenshots/GIFs, demo video, public release (Stage 9)
- **Future:** ML-based distraction prediction, desktop packaging, study recommendations

Details: [`MASTER_CHECKLIST.md`](MASTER_CHECKLIST.md) · [`PROJECT_STATUS.md`](PROJECT_STATUS.md)

---

## Troubleshooting

Webcam issues → check camera permissions. Slow FPS → use `yolov8n.pt`. Empty dashboard → complete at least one session first. Import errors → activate `.venv` and reinstall requirements.

---

## License

Add a license file before publishing this repository publicly.
