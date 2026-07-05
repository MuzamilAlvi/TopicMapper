from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class RenameAction:
    original_path: str
    original_filename: str
    new_path: str
    new_filename: str


class UndoStack:
    """Stores rename actions for the most recent operation."""

    def __init__(self) -> None:
        self._last_actions: List[RenameAction] = []
        self._active: bool = False

    def set_last(self, actions: List[RenameAction]) -> None:
        self._last_actions = actions
        self._active = True if actions else False

    def can_undo(self) -> bool:
        return self._active and len(self._last_actions) > 0

    def get_last(self) -> List[RenameAction]:
        return list(self._last_actions)

    def clear(self) -> None:
        self._last_actions = []
        self._active = False

