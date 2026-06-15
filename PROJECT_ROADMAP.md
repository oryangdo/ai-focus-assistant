# AI Focus Assistant — Roadmap

High-level direction. Detailed checklist: [`MASTER_CHECKLIST.md`](MASTER_CHECKLIST.md). Current state: [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

---

## Completed (Stages 0–8.1)

- Real-time webcam pipeline (YOLO phone/person detection)
- Pomodoro focus sessions with focus scoring
- Gaze-away tracking (MediaPipe head pose)
- Live distraction risk estimation and warnings
- CSV session logging with schema migration
- CLI analytics and Streamlit dashboard
- macOS launchers and build scripts

---

## In Progress

### Stage 9 — Product Polish

- README screenshots/GIFs and demo video
- Config/settings system
- PyInstaller build verification and public release

### Stage 10 — Productivity Intelligence

Evolve from attention monitoring into personalized productivity insights.

**10.1 — Intelligence Foundation (current focus)**

- Derived metrics from `sessions.csv` (ratios, rates, risk spread)
- Personal baselines and “vs your average”
- Extended time-of-day and habit analytics
- Phone vs gaze distraction profile

**10.2 — Recommendations + Dashboard**

- Rule-based study recommendations
- Dashboard insights panel and weekly summary
- Session summary one-liner insights

**10.3 — Predictive & ML-Ready (optional)**

- Pre-session expected performance briefing
- Focus quality tiers and ML feature export

---

## Future / Stretch

- Multi-user support and cloud sync
- Mobile companion app
- Embedded ESP32 / hardware focus indicator
- Posture and fine-grained eye gaze tracking
