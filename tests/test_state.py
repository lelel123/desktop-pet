# -*- coding: utf-8 -*-
from pet.state import PetState, PetStateMachine


def test_initial_state_is_awake():
    assert PetStateMachine().state is PetState.AWAKE


def test_awake_to_idle():
    m = PetStateMachine()
    assert m.enter_idle() is True
    assert m.state is PetState.IDLE


def test_idle_only_from_awake():
    m = PetStateMachine()
    m.enter_idle()
    assert m.enter_idle() is False


def test_idle_to_sleep():
    m = PetStateMachine()
    m.enter_idle()
    assert m.enter_sleep() is True
    assert m.state is PetState.SLEEP


def test_sleep_from_awake_is_allowed():
    m = PetStateMachine()
    assert m.enter_sleep() is True
    assert m.state is PetState.SLEEP


def test_sleep_is_idempotent():
    m = PetStateMachine()
    m.enter_sleep()
    assert m.enter_sleep() is False


def test_wake_from_any_state():
    m = PetStateMachine()
    m.enter_idle()
    assert m.wake() is True
    m.enter_sleep()
    assert m.wake() is True
    assert m.state is PetState.AWAKE


def test_wake_when_already_awake():
    m = PetStateMachine()
    assert m.wake() is False
