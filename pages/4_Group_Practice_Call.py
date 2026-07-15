import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from facial_analysis import analyze_facial_expression
from group_session_store import (
    create_room, join_room, get_room, start_session,
    advance_turn, log_expression, MAX_STUDENTS
)
from ui_theme import inject_theme, sidebar_brand

st.set_page_config(page_title="Group Practice Call", page_icon="👥", layout="wide")
inject_theme()
sidebar_brand()
st.sidebar.page_link("app.py", label="🏠 Home")
st.sidebar.markdown("---")

# ---------- helpers ----------

def new_room_code():
    import random, string
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))


# ---------- session state ----------

if "room_code" not in st.session_state:
    st.session_state.room_code = None
if "student_name" not in st.session_state:
    st.session_state.student_name = None
if "snapshot_counter" not in st.session_state:
    st.session_state.snapshot_counter = 0
if "last_snapshot_bytes" not in st.session_state:
    st.session_state.last_snapshot_bytes = None

st.markdown('<div class="hero-title fade-in" style="font-size:2.2rem;">👥 Group Practice Call</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub fade-in d1">Practice introducing yourself as a team, before the real sponsor meeting.</div>', unsafe_allow_html=True)

# ---------- lobby: create or join ----------

if st.session_state.room_code is None:
    tab_create, tab_join = st.tabs(["Create a room", "Join a room"])

    with tab_create:
        host_name = st.text_input("Your name", key="host_name_input")
        if st.button("Create Room", type="primary", disabled=not host_name):
            code = new_room_code()
            create_room(code, host_name)
            st.session_state.room_code = code
            st.session_state.student_name = host_name
            st.rerun()

    with tab_join:
        join_name = st.text_input("Your name", key="join_name_input")
        join_code = st.text_input("Room code", key="join_code_input").upper()
        if st.button("Join Room", disabled=not (join_name and join_code)):
            ok, msg = join_room(join_code, join_name)
            if ok:
                st.session_state.room_code = join_code
                st.session_state.student_name = join_name
                st.rerun()
            else:
                st.error(msg)

    st.stop()

# ---------- inside a room ----------

_room_peek = get_room(st.session_state.room_code)
if _room_peek is None or _room_peek.current_speaker != st.session_state.student_name:
    st_autorefresh(interval=3000, key="room_refresh")

room = get_room(st.session_state.room_code)
if room is None:
    st.error("This room no longer exists.")
    st.session_state.room_code = None
    st.stop()

me = st.session_state.student_name

st.markdown(f"""
<div class="room-banner fade-in">
  <span class="room-code-pill">{room.code}</span>
  <span style="font-size:0.9rem;color:#374151;">Share this code with your teammates · {len(room.students)}/{MAX_STUDENTS} joined</span>
</div>
""", unsafe_allow_html=True)

# roster grid
cols = st.columns(min(len(room.students), 6) or 1)
for i, (name, student) in enumerate(room.students.items()):
    with cols[i % len(cols)]:
        if student.done:
            st.markdown(f'<div class="student-chip done">✅ {name}</div>', unsafe_allow_html=True)
        elif name == room.current_speaker:
            st.markdown(f'<div class="student-chip speaking"><span class="live-dot"></span>&nbsp;{name} — speaking now</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="student-chip">{name}</div>', unsafe_allow_html=True)

if not room.started:
    if me == room.host_name:
        if st.button("Start Session", type="primary"):
            start_session(room.code)
            st.rerun()
    else:
        st.write("Waiting for the host to start the session...")
    st.stop()

if room.finished:
    st.header("📋 Meeting Summary")
    for name, student in room.students.items():
        with st.expander(f"{name}'s introduction", expanded=True):
            if student.expression_log:
                emotions = [e.dominant_emotion for e in student.expression_log]
                st.write(f"**Expression trend:** {' → '.join(emotions)}")
                avg_conf = sum(e.confidence for e in student.expression_log) / len(student.expression_log)
                st.write(f"**Avg confidence signal:** {avg_conf:.0%}")
                notes = [e.notes for e in student.expression_log if e.notes]
                if notes:
                    st.write(f"**Coaching note:** {notes[-1]}")
            else:
                st.write("No expression data captured.")
    st.stop()

# ---------- active turn ----------

st.subheader(f"Current speaker: {room.current_speaker}")

if me == room.current_speaker:
    st.write("You're on! Introduce yourself, then take a snapshot or two, "
             "then click **Done** when finished.")

    col1, col2 = st.columns([3, 2])

    with col1:
        cam_key = f"group_snapshot_{st.session_state.snapshot_counter}"
        img_file = st.camera_input("Take a snapshot while you talk", key=cam_key)

        if img_file is not None:
            new_bytes = img_file.getvalue()
            if new_bytes != st.session_state.last_snapshot_bytes:
                st.session_state.last_snapshot_bytes = new_bytes
                with st.spinner("Analyzing expression..."):
                    result = analyze_facial_expression(new_bytes)
                if result:
                    total = result.get("total", 0)
                    emotion = "confident" if total >= 80 else "engaged" if total >= 60 else "nervous"
                    log_expression(
                        room.code, me,
                        dominant_emotion=emotion,
                        confidence=total / 100.0,
                        notes=result.get("summary", "")
                    )
                    st.success(f"Snapshot analyzed — score {total}/100")
                st.session_state.snapshot_counter += 1
                st.rerun()

    with col2:
        st.markdown("#### Snapshots so far")
        me_student = room.students[me]
        if me_student.expression_log:
            for e in me_student.expression_log:
                st.write(f"- {e.dominant_emotion} ({e.confidence:.0%})")
        else:
            st.caption("None yet — take a snapshot to the left.")

    st.markdown("---")
    if st.button("✅ Done, next person", type="primary"):
        advance_turn(room.code)
        st.rerun()
else:
    st.write("Watching this teammate's introduction. Your turn is coming up.")
