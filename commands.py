"""
commands.py
A central registry of "commands" -- named actions with a title, optional
shortcut hint, and a callback. Both the Omarchy-style launcher and the
VS Code-style command palette read from this same registry, and future
plugins can register their own commands here too.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Command:
    id: str
    title: str
    callback: Callable[[], None]
    category: str = "General"
    shortcut: str = ""
    keywords: list[str] = field(default_factory=list)

    def matches(self, query: str) -> bool:
        q = query.lower().strip()
        if not q:
            return True
        haystack = " ".join([self.title, self.category, self.id, *self.keywords]).lower()
        # simple fuzzy-ish substring match on each whitespace-separated token
        return all(token in haystack for token in q.split())


class CommandRegistry:
    """Holds every command available in the browser, keyed by id."""

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        self._commands[command.id] = command

    def register_many(self, commands: list[Command]) -> None:
        for c in commands:
            self.register(c)

    def unregister(self, command_id: str) -> None:
        self._commands.pop(command_id, None)

    def get(self, command_id: str) -> Command | None:
        return self._commands.get(command_id)

    def all(self) -> list[Command]:
        return list(self._commands.values())

    def search(self, query: str) -> list[Command]:
        return [c for c in self._commands.values() if c.matches(query)]

    def run(self, command_id: str) -> None:
        cmd = self.get(command_id)
        if cmd:
            cmd.callback()
