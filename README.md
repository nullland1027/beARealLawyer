# beARealLawyer ⚖️

A lightweight, local-first case/project management board for lawyers. Built with Streamlit and stored as a simple JSON file, it helps you track matters, link local files/folders, and visualize status at a glance. ✅

## Features ✨

- Kanban-style board with three status columns (Waiting, Processing, Closed). 📌
- Quick project creation with client/opponent/lawyer fields. ⚡
- Edit full details: stage, completion %, notes, and attachments. 🧾
- Attach local files and folders, then open them directly from the UI. 📎
- Metrics panel for total counts and status distribution. 📊
- Safe “Danger Zone” flow to delete all projects with multi-step confirmation. 🚨

## Tech Stack 🧰

- Python 3.11+
- Streamlit
- Local JSON storage (`data/projects.json`)

## Project Structure 🧩

- `app.py`: Streamlit entrypoint.
- `ui/`: UI layout and components.
- `core/`: Models, repository, storage, and file-link helpers.
- `data/`: Local data file (created automatically).

## Getting Started (Local) 🚀

1) Create a virtual environment (optional but recommended).
2) Install dependencies.
3) Run the app.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL shown in the terminal (default is `http://localhost:8501`).

## Run with Docker 🐳

```bash
docker compose up --build
```

- App runs on `http://localhost:8501`.
- Data persists in `./data` via a volume mapping.

## Data & Persistence 💾

All projects are stored in `data/projects.json`. You can reset data by:

- Using the “Danger Zone” delete-all flow in the sidebar, or
- Deleting `data/projects.json` manually.

## Platform Notes 🖥️

- File and folder pickers use macOS AppleScript (`osascript`) and open files via `open`.
- On non-macOS environments (including most Docker containers), file selection/opening may not work. In that case, you can still paste paths manually.

## License 📄

MIT License. See `LICENSE`.
