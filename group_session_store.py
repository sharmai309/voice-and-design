"""
group_session_store.py
Shared, in-memory store for group practice call rooms.
Works because Streamlit Cloud runs a single process per deployed app,
so st.cache_resource gives us one shared object across all browser sessions.
NOTE: this does NOT survive app restarts/redeploys, and would need a real
database (e.g. Firestore, Supabase, Redis) if you ever scale to multiple
server instances.
"""

import threading
import time
import streamlit as st
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExpressionSample:
    timestamp: float
    dominant_emotion: str
    confidence: float
    notes: str = ""


@dataclass
class Student:
    name: str
    joined_at: float = field(default_factory=time.time)
    expression_log: list = field(default_factory=list)
    transcript: str = ""
    done: bool = False


@dataclass
class Room:
    code: str
    host_name: str
    students: dict = field(default_factory=dict)  # name -> Student
    turn_order: list = field(default_factory=list)  # list of names
    current_turn_index: int = 0
    started: bool = False
    finished: bool = False
    created_at: float = field(default_factory=time.time)
    zoom_join_url: str = ""
    zoom_start_url: str = ""
    zoom_meeting_id: str = ""
    zoom_passcode: str = ""

    @property
    def current_speaker(self) -> Optional[str]:
        if not self.turn_order or self.finished:
            return None
        if self.current_turn_index >= len(self.turn_order):
            return None
        return self.turn_order[self.current_turn_index]


class _GlobalStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.rooms: dict[str, Room] = {}


@st.cache_resource
def get_store() -> _GlobalStore:
    return _GlobalStore()


MAX_STUDENTS = 6
ROOM_TTL_SECONDS = 2 * 60 * 60


def _sweep_stale_rooms(store: "_GlobalStore"):
    """Drop rooms older than ROOM_TTL_SECONDS. Caller must hold store.lock."""
    cutoff = time.time() - ROOM_TTL_SECONDS
    stale = [code for code, room in store.rooms.items() if room.created_at < cutoff]
    for code in stale:
        del store.rooms[code]


def create_room(room_code: str, host_name: str, zoom_meeting: Optional[dict] = None) -> Room:
    store = get_store()
    with store.lock:
        _sweep_stale_rooms(store)
        room = Room(code=room_code, host_name=host_name)
        room.students[host_name] = Student(name=host_name)
        room.turn_order.append(host_name)
        if zoom_meeting:
            room.zoom_join_url = zoom_meeting.get("join_url", "")
            room.zoom_start_url = zoom_meeting.get("start_url", "")
            room.zoom_meeting_id = str(zoom_meeting.get("meeting_id", ""))
            room.zoom_passcode = zoom_meeting.get("passcode", "")
        store.rooms[room_code] = room
        return room


def join_room(room_code: str, student_name: str) -> tuple[bool, str]:
    store = get_store()
    with store.lock:
        room = store.rooms.get(room_code)
        if room is None:
            return False, "Room not found. Check the code with your host."
        if room.started:
            return False, "This session has already started."
        if len(room.students) >= MAX_STUDENTS:
            return False, f"Room is full (max {MAX_STUDENTS})."
        if student_name in room.students:
            return False, "That name is already taken in this room."
        room.students[student_name] = Student(name=student_name)
        room.turn_order.append(student_name)
        return True, "Joined!"


def get_room(room_code: str) -> Optional[Room]:
    store = get_store()
    with store.lock:
        return store.rooms.get(room_code)


def start_session(room_code: str):
    store = get_store()
    with store.lock:
        room = store.rooms.get(room_code)
        if room:
            room.started = True
            room.current_turn_index = 0


def log_expression(room_code: str, student_name: str, dominant_emotion: str,
                    confidence: float, notes: str = ""):
    store = get_store()
    with store.lock:
        room = store.rooms.get(room_code)
        if not room or student_name not in room.students:
            return
        room.students[student_name].expression_log.append(
            ExpressionSample(time.time(), dominant_emotion, confidence, notes)
        )


def append_transcript(room_code: str, student_name: str, text: str):
    store = get_store()
    with store.lock:
        room = store.rooms.get(room_code)
        if not room or student_name not in room.students:
            return
        room.students[student_name].transcript += (" " + text)


def advance_turn(room_code: str):
    store = get_store()
    with store.lock:
        room = store.rooms.get(room_code)
        if not room:
            return
        current = room.current_speaker
        if current:
            room.students[current].done = True
        room.current_turn_index += 1
        if room.current_turn_index >= len(room.turn_order):
            room.finished = True
