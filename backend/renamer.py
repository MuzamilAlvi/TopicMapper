from __future__ import annotations

import json
import os
import re
import traceback
from typing import Any, Dict, List, Optional, Tuple

from backend.parser import parse_topics_txt, parse_video_folder
from backend.report import FilePlan, build_report
from backend.undo import RenameAction, UndoStack
from backend.utils import VIDEO_EXTENSIONS, extract_topic_number, normalize_topic_number


def _safe_title(title: str) -> str:
    # Windows reserved characters: <>:"/\\|?*
    banned = '<>:"/\\|?*'
    cleaned = "".join(ch if ch not in banned else "-" for ch in title)
    cleaned = cleaned.strip()
    return cleaned or "Untitled"


def _collapse_spaces(s: str) -> str:
    return re.sub(r"\s{2,}", " ", s).strip()


def _read_config() -> Dict[str, Any]:
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _get_naming_pattern(cfg: Dict[str, Any]) -> str:
    # Requirement: Naming Pattern with these options.
    # We'll store in config as `namingPattern`.
    # Defaults to `{number} - {title}`.
    return str(cfg.get("namingPattern", "{number} - {title}"))


class Renamer:
    def __init__(self) -> None:
        self.undo_stack = UndoStack()

    def _compute_padding_width(self, video_files: List[str]) -> int:
        nums: List[str] = []
        for path in video_files:
            name = os.path.basename(path)
            ext = os.path.splitext(name)[1]
            if ext.lower() not in VIDEO_EXTENSIONS:
                continue
            token = extract_topic_number(name)
            if token:
                nums.append(str(token).strip())
        return max((len(x) for x in nums), default=1)

    def _format_number(self, token: str, pad_width: int, keep_token: bool) -> str:
        # Requirement:
        # - Extracted number token from filename must be preserved for display.
        # - Numeric part must always be zero-padded to match largest sequence length.
        # - If keep_token=True, we use token's exact numeric value with zero-padding.
        n = str(token).strip()
        if not n:
            return "".zfill(pad_width)
        # normalize_topic_number drops leading zeros for matching, but we want numeric value.
        try:
            numeric_value = str(int(n))
        except Exception:
            numeric_value = n.lstrip("0") or "0"
        # Ensure padding to pad_width.
        return numeric_value.zfill(pad_width)

    def _render_filename(
        self,
        pattern: str,
        number_formatted: str,
        title: str,
        ext: str,
    ) -> str:
        safe = _safe_title(title)

        # Token replacement
        out = pattern
        out = out.replace("{number}", number_formatted)
        out = out.replace("{title}", safe)
        out = out.replace("{extension}", ext)
        # Some patterns may not use title/number. Ensure no double spaces.
        out = out.replace("  ", " ")
        out = _collapse_spaces(out)

        # Enforce extension preservation
        # If pattern already includes extension token, avoid double extension.
        if out.lower().endswith(ext.lower()):
            return out
        return f"{out}{ext}"

    def preview(self, folder: str, topics_txt: str) -> Dict:
        cfg = _read_config()
        naming_pattern = _get_naming_pattern(cfg)

        topics_raw = parse_topics_txt(topics_txt)  # {topic_number:int-like? -> title}
        topics: Dict[str, str] = {normalize_topic_number(k): v for k, v in topics_raw.items()}

        video_files = parse_video_folder(folder)
        pad_width = self._compute_padding_width(video_files)

        plans: List[FilePlan] = []
        intermediate: List[Tuple[FilePlan, str]] = []  # (plan, new_filename)

        for path in video_files:
            filename = os.path.basename(path)
            ext = os.path.splitext(filename)[1]
            if ext.lower() not in VIDEO_EXTENSIONS:
                continue

            token_raw = extract_topic_number(filename)
            if not token_raw:
                plans.append(
                    FilePlan(
                        original_path=path,
                        original_filename=filename,
                        topic_number=None,
                        official_title=None,
                        new_filename=None,
                        status="unmatched",
                        reason="No matching topic number/title found",
                    )
                )
                continue

            tnum_match = normalize_topic_number(token_raw)
            if not tnum_match or tnum_match not in topics:
                plans.append(
                    FilePlan(
                        original_path=path,
                        original_filename=filename,
                        topic_number=tnum_match,
                        official_title=None,
                        new_filename=None,
                        status="unmatched",
                        reason="No matching topic number/title found",
                    )
                )
                continue

            title = topics[tnum_match]
            number_formatted = self._format_number(str(token_raw), pad_width, keep_token=True)
            new_filename = self._render_filename(naming_pattern, number_formatted, title, ext)

            p = FilePlan(
                original_path=path,
                original_filename=filename,
                topic_number=tnum_match,
                official_title=title,
                new_filename=new_filename,
                status="matched",
                reason="",
            )
            intermediate.append((p, new_filename))

        # Duplicate detection by intended target filename
        intended: Dict[str, List[FilePlan]] = {}
        for p, new_fn in intermediate:
            intended.setdefault(new_fn, []).append(p)

        for new_fn, plist in intended.items():
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
            "paddingWidth": pad_width,
            "namingPattern": naming_pattern,
        }

    def rename_all(self, folder: str, topics_txt: str) -> Dict:
        preview_data = self.preview(folder, topics_txt)
        plans = preview_data["plans"]

        actions: List[RenameAction] = []
        errors: List[Dict[str, Any]] = []

        matched = [p for p in plans if p["status"] == "matched"]

        # Safe rename: rename only matched + not duplicates.
        for p in matched:
            old_path = p["original_path"]
            new_filename = p["new_filename"]
            if not new_filename:
                continue

            new_path = os.path.join(folder, new_filename)

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

        self.undo_stack.set_last(actions)

        report = preview_data["report"]
        report["counts"]["errors"] += len(errors)
        report["errors_extra"] = errors
        return report

    def undo_last(self) -> Dict:
        if not self.undo_stack.can_undo():
            return {"ok": False, "message": "Nothing to undo"}

        actions = self.undo_stack.get_last()
        reverted = 0
        undo_errors: List[Dict[str, Any]] = []

        for action in reversed(actions):
            try:
                if os.path.exists(action.new_path):
                    # Avoid overwriting if original path exists
                    if os.path.exists(action.original_path):
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

