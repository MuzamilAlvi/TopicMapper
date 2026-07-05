# TopicMapper – Intelligent Batch Video File Renaming System

A modern desktop app (Python backend + web frontend) that batch-renames educational video files by matching extracted topic numbers from downloaded filenames to official topic titles provided via a text file.

## Features
- Select folder of video files
- Import topic list text file
- Extract topic numbers from filenames
- Match numbers to official titles
- Preview rename changes in a table
- Detect unmatched files and duplicates (safe rename)
- Animated progress + toasts
- Detailed report (success / skipped / duplicates / errors)
- Undo support for the most recent rename operation
- Light/Dark mode, search/filter, drag & drop

## Tech Stack
- **Desktop container:** `pywebview`
- **Backend:** Python
- **Frontend:** HTML/CSS/JS

## Setup
1. Create venv (recommended)
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies
   ```bat
   pip install pywebview
   ```

> Additional Python packages used by the backend are kept minimal.

## Run
```bat
py main.py
```

## Project Structure
```
project/
│
├── main.py
├── backend/
│   ├── renamer.py
│   ├── parser.py
│   ├── report.py
│   ├── undo.py
│   └── utils.py
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   ├── style.css
│   │   ├── theme.css
│   │   └── animations.css
│   ├── js/
│   │   ├── app.js
│   │   ├── ui.js
│   │   └── api.js
│   └── assets/
│       ├── icons/
│       └── images/
│
├── reports/
├── logs/
└── README.md
```

