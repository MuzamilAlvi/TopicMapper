from __future__ import annotations

import os
import traceback
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from backend.parser import parse_topics_txt, parse_video_folder
from backend.report import FilePlan, build_report
from backend.undo import RenameAction, UndoStack
from backend.utils import VIDEO_EXTENSIONS, extract_topic_number


def _safe_new_name(title: str) -> str:
    # Windows reserved characters: <>:"/\\|?*
    banned = '<>:\"/\\|?*'
    cleaned = "".join(ch if ch not in banned else "-" for ch in title)
    cleaned = cleaned.strip()
    # avoid empty
    return cleaned or "Untitled"


class Renamer:
    def __init__(self) -> None:
        self.undo_stack = UndoStack()

    def preview(self, folder: str, topics_txt: str) -> Dict:
        topics = parse_topics_txt(topics_txt)  # topic_number -> title
        video_files = parse_video_folder(folder)

        plans: List[FilePlan] = []
        # First pass: create matched/unmatched plans, but hold new_filename unset until duplicate detection
        intermediate: List[Tuple[FilePlan, str]] = []  # (plan, intended_new_filename)

        for path in video_files:
            filename = os.path.basename(path)
            ext = os.path.splitext(filename)[1]
            if ext.lower() not in VIDEO_EXTENSIONS:
                continue

            tnum = extract_topic_number(filename)
            if not tnum or tnum not in topics:
                plans.append(
                    FilePlan(
                        original_path=path,
                        original_filename=filename,
                        topic_number=tnum,
                        official_title=None,
                        new_filename=None,
                        status="unmatched",
                        reason="No matching topic number/title found",
                    )
                )
                continue

            title = topics[tnum]
            safe_title = _safe_new_name(title)
            new_filename = f"{safe_title}{ext}"
            p = FilePlan(
                original_path=path,
                original_filename=filename,
                topic_number=tnum,
                official_title=title,
                new_filename=new_filename,
                status="matched",
                reason="",
            )
            intermediate.append((p, new_filename))

        # Duplicate detection: intended new filenames mapping
        intended_to_plans: Dict[str, List[FilePlan]] = {}
        for p, new_fn in intermediate:
            intended_to_plans.setdefault(new_fn, []).append(p)

        for new_fn, plist in intended_to_plans.items():
            if len(plist) > 1:
                for p in plist:
                    p.status = "duplicate"  # type: ignore
                    p.reason = "Duplicate target filename detected; will not rename"
                    plans.append(p)
            else:
                plans.append(plist[0])

        return {
            "plans": [
                {
                    "original_path": p.original_path,
                    "original_filename": p.original_filename,
                    "topic_number": p.topic_number,
                    "official_title": p.official_title,
                    "new_filename": p.new_filename,
                    "status": p.status,
                    "reason": p.reason,
                }
                for p in plans
            ],
            "report": build_report(plans),
        }

    def rename_all(self, folder: str, topics_txt: str) -> Dict:
        preview_data = self.preview(folder, topics_txt)
        plans = preview_data["plans"]

        actions: List[RenameAction] = []
        errors: List[Dict] = []

        # Create actions only for matched plans
        # Only rename items that were matched AND are not duplicates.
        matched = [p for p in plans if p["status"] == "matched"]

        for p in matched:
            old_path = p["original_path"]
            new_filename = p["new_filename"]
            if not new_filename:
                continue
            new_path = os.path.join(folder, new_filename)


            # If already exists for safety, skip
            if os.path.exists(new_path):
                errors.append(
                    {
                        "original_filename": p["original_filename"],
                        "new_filename": new_filename,
                        "error": "Target file already exists",
                    }
                )
                continue

            try:
                os.rename(old_path, new_path)
                actions.append(
                    RenameAction(
                        original_path=old_path,
                        original_filename=p["original_filename"],
                        new_path=new_path,
                        new_filename=new_filename,
                    )
                )
            except Exception as e:
                errors.append(
                    {
                        "original_filename": p["original_filename"],
                        "new_filename": new_filename,
                        "error": str(e),
                        "trace": traceback.format_exc(),
                    }
                )

        # Store undo actions
        self.undo_stack.set_last(actions)

        # Build final report with statuses based on preview + errors
        # For simplicity, we keep preview statuses and add error count.
        report = preview_data["report"]
        report["counts"]["errors"] += len(errors)
        report["errors_extra"] = errors

        return report

    def undo_last(self) -> Dict:
        if not self.undo_stack.can_undo():
            return {"ok": False, "message": "Nothing to undo"}

        actions = self.undo_stack.get_last()
        reverted = 0
        undo_errors: List[Dict] = []

        # Reverse order to be safer
        for action in reversed(actions):
            try:
                if os.path.exists(action.new_path):
                    if os.path.exists(action.original_path):
                        # Avoid overwriting
                        undo_errors.append(
                            {
                                "new_filename": action.new_filename,
                                "error": "Original file already exists; cannot restore safely",
                            }
                        )
                        continue
                    os.rename(action.new_path, action.original_path)
                    reverted += 1
            except Exception as e:
                undo_errors.append({"new_filename": action.new_filename, "error": str(e)})

        # Clear after undo attempt
        self.undo_stack.clear()

        return {
            "ok": True,
            "reverted": reverted,
            "errors": undo_errors,
        }


class RenamerAPI:
    """Exposed to JavaScript via pywebview."""

    def __init__(self) -> None:
        self.renamer = Renamer()

    def api_pick_folder(self) -> Dict:
        from backend.dialogs import pick_directory

        path = pick_directory()
        if not path:
            return {"ok": False, "message": "Folder not selected"}
        return {"ok": True, "folder": path}

    def api_pick_topics_file(self) -> Dict:
        from backend.dialogs import pick_topics_txt

        path = pick_topics_txt()
        if not path:
            return {"ok": False, "message": "Topics file not selected"}
        return {"ok": True, "topics_txt": path}

    def api_preview(self, folder: str, topics_txt: str) -> Dict:
        return self.renamer.preview(folder, topics_txt)

    def api_rename_all(self, folder: str, topics_txt: str) -> Dict:
        return self.renamer.rename_all(folder, topics_txt)

    def api_undo_last(self) -> Dict:
        return self.renamer.undo_last()

