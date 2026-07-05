# TODO - Intelligent Batch Video File Renaming System

## Step 1: Create project scaffold
- [x] Create Python backend modules under `backend/`
- [x] Create frontend files under `frontend/`
- [ ] Add `main.py` to start the PyWebView app

## Step 2: Implement core logic (backend)
- [x] Implement filename parsing (topic number extraction)
- [x] Implement topic mapping loader from text file
- [x] Implement safe rename planning (detect duplicates/unmatched)
- [ ] Implement renaming executor with extension preservation (in renamer.py)
- [ ] Implement report generation (complete + persist)
- [ ] Implement undo for last operation

## Step 3: Implement frontend UI (web)
- [ ] Modern dashboard layout: sidebar + toolbar + cards
- [ ] Drag & drop for folder and topic text file
- [ ] Light/Dark mode
- [ ] Preview table with status badges and search/filter
- [ ] Progress indicator + toasts + completion summary
- [ ] Context menus + keyboard shortcuts

## Step 4: Bridge frontend ↔ backend
- [ ] Define JS API functions calling Python backend (via pywebview)
- [ ] Implement events: folder import, topic import, preview load, rename, undo

## Step 5: Add tooling & docs
- [x] Add `README.md` with setup/run instructions
- [ ] Add minimal sample `reports/` structure

## Step 6: Test flow
- [ ] Test with sample filenames
- [ ] Validate duplicate detection + safe renaming
- [ ] Validate report contents
- [ ] Validate undo

