# -*- coding: utf-8 -*-
"""Pet behaviour state machine: awake → idle → sleep. No Qt dependency.

The widget drives the timers and visuals; this class is the single source of
truth for which state we are in and whether a transition is legal.
"""

from __future__ import annotations

from enum import Enum


class PetState(Enum):
    AWAKE = "awake"
    IDLE = "idle"
    SLEEP = "sleep"


class PetStateMachine:
    """Minimal transition rules.

    * awake → idle   (after no interaction for a while)
    * idle  → sleep  (after idling for a while)
    * any   → awake  (woken by interaction / wake())
    """

    def __init__(self) -> None:
        self.state: PetState = PetState.AWAKE

    def enter_idle(self) -> bool:
        """awake → idle. Returns True if the state actually changed."""
        if self.state is not PetState.AWAKE:
            return False
        self.state = PetState.IDLE
        return True

    def enter_sleep(self) -> bool:
        """(awake|idle) → sleep. Returns True if the state actually changed."""
        if self.state is PetState.SLEEP:
            return False
        self.state = PetState.SLEEP
        return True

    def wake(self) -> bool:
        """→ awake. Returns True if the state actually changed."""
        if self.state is PetState.AWAKE:
            return False
        self.state = PetState.AWAKE
        return True

    @property
    def is_awake(self) -> bool:
        return self.state is PetState.AWAKE
