# AI Focus Assistant

An AI-powered productivity system that detects phone and gaze distractions during Pomodoro focus sessions, estimates real-time distraction risk, and turns session history into actionable analytics.

Built with **YOLOv8**, **MediaPipe**, **OpenCV**, and **Streamlit**.

---

## Demo

<a href="https://youtu.be/pXaMNblhLVE">
  <img src="https://img.youtube.com/vi/pXaMNblhLVE/maxresdefault.jpg" alt="AI Focus Assistant — demo video (click to play on YouTube)" width="720">
</a>

*Click the thumbnail to watch the full walkthrough on YouTube.*

Home screen → focus session → detection → session summary → Streamlit dashboard.

### Focus session app

**Home screen** — press **SPACE** to start a Pomodoro focus session.

![Home screen](docs/images/home-screen.png)

**Live HUD** — timer, gaze status, and distraction risk while focusing.

![Live focus session HUD](docs/images/live-hud.png)

**Detection in action**

| Phone detection | Gaze-away detection |
| :---: | :---: |
| ![YOLO phone detection with MEDIUM risk](docs/images/phone-detection.png) | ![Head turned away with gaze status AWAY](docs/images/gaze-away.png) |

**Session summary** — focus score, distraction breakdown, and **Open Dashboard** button.

![Session complete overlay](docs/images/session-summary.png)

### Streamlit dashboard

**Overview** — aggregate metrics and focus score trend across sessions.

![Dashboard overview with focus score chart](docs/images/dashboard-overview.png)

**Session analytics** — phone time, distractions, and risk charts.

![Dashboard analytics charts](docs/images/dashboard-analytics.png)

**Risk & gaze analysis**

| Risk analysis | Gaze analysis |
| :---: | :---: |
| ![Risk distribution and session trends](docs/images/dashboard-risk.png) | ![Gaze away time and distraction events](docs/images/dashboard-gaze.png) |

**Session history** — full table with focus scores, risk, and gaze metrics.

![Session history table](docs/images/dashboard-history.png)

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
        CSV[("CSV Storage<br/><i>Application Support</i>")]
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

First run auto-downloads YOLO weights and the MediaPipe face model into your user cache if they are not bundled with the app.

### Download for macOS (no Python required)

**End users:** download the latest **`AI-Focus-Assistant-mac.zip`** from [GitHub Releases](https://github.com/oryangdo/summer_project/releases).

The release zip contains:

| Item | Description |
|------|-------------|
| `AI Focus Assistant.app` | Standalone focus sessions only (~1 GB) |
| `README.txt` | Unzip instructions, Gatekeeper workaround, camera permission, session data path |

It does **not** include the Streamlit dashboard. The dashboard requires cloning the repo and a one-time Python setup (see [Analytics & dashboard](#analytics--dashboard)).

```
Unzip → open AI-Focus-Assistant-mac → double-click AI Focus Assistant.app
→ allow camera → press SPACE to start → session saves automatically → summary appears
```

**First launch (Gatekeeper):** macOS may block the unsigned app. Right-click **AI Focus Assistant.app** → **Open** → confirm **Open**. After that, double-click works normally. Full steps are in the zip’s `README.txt`.

No Terminal or Python setup is required for focus sessions in the release zip.

### Desktop use (macOS, from source)

**Option A — repo launchers (one-time Python setup)**

```bash
./scripts/setup_mac_apps.sh
```

Then double-click:

| App | What it does |
|-----|----------------|
| `macos/AI Focus Assistant.app` | Opens the live webcam focus session |
| `macos/Open Dashboard.app` | Opens the Streamlit dashboard in your browser |

**Option B — build a release zip (maintainers)**

On macOS, build and verify a GitHub Release artifact:

```bash
./scripts/release_mac.sh
```

This runs PyInstaller, packages `release/AI-Focus-Assistant-mac.zip` (focus app + `README.txt` only), and smoke-tests launch + session save. Upload the zip to [GitHub Releases](https://github.com/oryangdo/summer_project/releases). The zip is gitignored and is not committed to the repository.

Individual steps:

```bash
./scripts/build_mac_app.sh      # PyInstaller build → dist/AI Focus Assistant.app
./scripts/package_release.sh    # → release/AI-Focus-Assistant-mac.zip
./scripts/verify_release.sh     # unzip, launch, and CSV smoke test
```

| Topic | Detail |
|-------|--------|
| Start session | Home screen → press **SPACE** |
| End session | Natural timer end or **Q** during focus → persistent summary overlay |
| Dismiss summary | **ESC** or click **X** |
| Open dashboard | **Source/Python setup only** — clone repo, install requirements, then use **D** / **Open Dashboard** on summary, `Open Dashboard.app`, or `streamlit run`. Not available in the standalone release app. |
| Camera | Allow access when macOS prompts on first launch |
| Session data | `~/Library/Application Support/AI Focus Assistant/data/sessions.csv` |
| Charts | `~/Library/Application Support/AI Focus Assistant/reports/` (CLI analytics; dashboard requires Python setup) |
| Dashboard UI | Opens in **Safari/Chrome** — not embedded in the focus app window |

The **GitHub Release zip** is focus-only: `AI Focus Assistant.app` + `README.txt`. The repo `macos/` launchers run from source after `./scripts/setup_mac_apps.sh` and can open both the focus session and the dashboard.

---

## Usage

**Live focus session**

```bash
python webcam_demo.py    # or ./run.sh
```

| Key / action | Behavior |
|--------------|----------|
| **SPACE** | Start focus session from home screen |
| **Q** | Save and show summary if in focus; quit from home/summary |
| **ESC** / **X** | Dismiss session summary |
| **D** / **Open Dashboard** | Open stats in browser (when summary is visible) |

**Analytics & dashboard**

```bash
python -m src.analytics
python -m streamlit run src/dashboard.py
```

Or double-click `macos/Open Dashboard.app` after running `./scripts/setup_mac_apps.sh`.

---

## Analytics

Sessions append to `~/Library/Application Support/AI Focus Assistant/data/sessions.csv` (focus score, distractions, phone/gaze time, risk scores). The CLI prints trends and writes charts to `~/Library/Application Support/AI Focus Assistant/reports/`; the Streamlit dashboard reads the same CSV.

---

## Roadmap

- **In progress:** Stage 10.1 productivity intelligence (derived metrics, personal baselines, habit insights)
- **Next:** Stage 10.2 recommendations + dashboard insights panel
- **Also pending:** config system, public GitHub release

Details: [`MASTER_CHECKLIST.md`](MASTER_CHECKLIST.md) · [`PROJECT_STATUS.md`](PROJECT_STATUS.md)

---

## Troubleshooting

Webcam issues → check camera permissions. Slow FPS → use `yolov8n.pt`. Empty dashboard → complete at least one session first. Import errors → activate `.venv` and reinstall requirements.

---

## License

MIT License — see [LICENSE](LICENSE). Copyright (c) 2026 Orlando Yang.
