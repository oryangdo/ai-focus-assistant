# AI Focus Assistant — Roadmap

High-level direction. Detailed checklist: [`MASTER_CHECKLIST.md`](MASTER_CHECKLIST.md). Current state: [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

---

## Completed (Stages 0–9.1 core)

- Real-time webcam pipeline (YOLO phone/person detection)
- Pomodoro focus sessions with focus scoring
- Gaze-away tracking (MediaPipe head pose)
- Live distraction risk estimation and warnings
- CSV session logging with schema migration
- CLI analytics and Streamlit dashboard
- macOS launchers and build scripts
- PyInstaller focus-app packaging (`release_mac.sh`, verified release zip workflow)

---

## In Progress

### Stage 9 — Product Polish

- README screenshots/GIFs and demo video
- Config/settings system
- Public GitHub release (upload focus-app zip)

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
