import streamlit as st
import os, json, base64, time, re
from concurrent.futures import ThreadPoolExecutor
from anthropic import Anthropic

st.set_page_config(page_title="Capstone Coach", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

from ui_theme import inject_theme, sidebar_brand
inject_theme()

def get_client():
    try:
        key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        st.error("⚠️ ANTHROPIC_API_KEY is not set. Add it to .streamlit/secrets.toml or your environment.")
    return Anthropic(api_key=key)

def get_openai_client():
    from openai import OpenAI
    try:
        key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        st.error("⚠️ OPENAI_API_KEY is not set. Add it to .streamlit/secrets.toml or your environment.")
    return OpenAI(api_key=key)

def extract_json(raw):
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))

def truncate_at_sentence(text, limit):
    if len(text) <= limit:
        return text
    snippet = text[:limit]
    ends = list(re.finditer(r"[.!?](?:\s|$)", snippet))
    if ends:
        return snippet[:ends[-1].end()].strip()
    spaces = list(re.finditer(r"\s", snippet))
    if spaces:
        return snippet[:spaces[-1].start()].strip()
    return snippet

PERSONAS = {
    "mentor": {"name":"Mentor Sponsor","icon":"🌱","difficulty":1,"diff_label":"Beginner","company":"HealthTech Analytics","role":"Dr. Sarah Chen · Sr. Director of Analytics","desc":"Warm and encouraging. Guides you with questions rather than answers.","prompt":"You are Dr. Sarah Chen, Senior Director of Analytics at HealthTech Analytics, a MENTOR SPONSOR for a UChicago Capstone team. Be warm, encouraging, patient. Ask guiding questions. Keep responses 2-4 sentences. START: Hi team, great to finally connect. Go ahead and introduce yourselves."},
    "executive": {"name":"Busy Executive","icon":"⚡","difficulty":4,"diff_label":"Hard","company":"FastShip Logistics","role":"Marcus Webb · VP of Operations","desc":"Time-pressed and terse. Get to the point or get cut off.","prompt":"You are Marcus Webb, VP of Operations at FastShip Logistics, a BUSY EXECUTIVE SPONSOR. Always pressed for time. Short 1-3 sentence answers. Interrupt ramblers. START: Alright, you have got me for 10 minutes. What are we covering today?"},
    "skeptic": {"name":"Skeptical Sponsor","icon":"🔍","difficulty":5,"diff_label":"Expert","company":"Verizon","role":"Dr. Raj Patel · Chief Data Officer","desc":"Questions everything. Demands evidence. Pushes back on every claim.","prompt":"You are Dr. Raj Patel, CDO at Verizon, a SKEPTICAL SPONSOR. Question every assumption. Push back firmly. Challenge at least one thing per response. START: I reviewed your brief. Walk me through your problem statement, and be specific."},
    "technical": {"name":"Technical Expert","icon":"💻","difficulty":4,"diff_label":"Hard","company":"BioSight Research","role":"Dr. Aisha Okafor · Director of Data Science","desc":"Deep dives into methodology. Expects technical rigor and data fluency.","prompt":"You are Dr. Aisha Okafor, Director of Data Science at BioSight Research, a TECHNICAL EXPERT SPONSOR. Ask about data sources, methodology, validation. At least one technical follow-up per response. START: Before deliverables, walk me through your technical approach."},
    "collaborator": {"name":"Open Collaborator","icon":"💡","difficulty":2,"diff_label":"Moderate","company":"TrendBox","role":"Jamie Torres · Director of Innovation","desc":"Loves every idea. Goes on tangents. Needs you to manage the agenda.","prompt":"You are Jamie Torres, Director of Innovation at TrendBox, an OPEN COLLABORATOR SPONSOR. Love brainstorming. Go on tangents. START: So excited for this! Where do you want to start, I am totally open!"}
}

DIFF_CLASS = {1:"diff-1",2:"diff-2",3:"diff-3",4:"diff-4",5:"diff-5"}

SCENARIOS = {
    "initial": {"name":"Initial Meeting / Problem Definition","icon":"🧭",
        "desc":"First meeting with your sponsor — introduce the team and nail down the problem you're solving.",
        "context":"MEETING SCENARIO — INITIAL MEETING / PROBLEM DEFINITION: This is the team's first meeting with you. Steer the conversation toward understanding the problem statement, business context, and what success looks like. Ask why this problem matters now and who is affected."},
    "scope": {"name":"Scope","icon":"📐",
        "desc":"Define what's in and out of scope for the project, deliverables, and constraints.",
        "context":"MEETING SCENARIO — SCOPE: This meeting is about defining scope. Steer the conversation toward what is and isn't included in the project, deliverables, timeline, and constraints. Push back if the team's scope sounds too broad, too vague, or unbounded."},
    "data": {"name":"Data","icon":"🗄️",
        "desc":"Discuss data sources, access, quality, and privacy/security constraints.",
        "context":"MEETING SCENARIO — DATA: This meeting is about data. Steer the conversation toward what data sources are available, how the team will access them, data quality concerns, and any privacy/security constraints. Ask pointed questions about data readiness."},
    "progress": {"name":"Progress Summary","icon":"📈",
        "desc":"Give a progress update — what's done, what's blocked, what's next.",
        "context":"MEETING SCENARIO — PROGRESS SUMMARY: This meeting is a status update. Expect the team to report what they've completed, what's blocked, and next steps. Ask about timeline risk and whether the project is on track."},
}

SCORE_PROMPT = """Evaluate this Capstone sponsor meeting. Score 0-25 each (total 100):
1. PREPARATION: Research, agenda, informed questions
2. COMMUNICATION: Clear, concise, professional
3. MEETING MANAGEMENT: Introductions, agenda, next steps
4. RELATIONSHIP BUILDING: Listening, rapport, empathy
Return ONLY this JSON:
{"preparation":0,"communication":0,"meeting_management":0,"relationship_building":0,"total":0,"strengths":["s1","s2"],"improvements":["i1","i2"],"missed_opportunities":["m1"],"readiness":"Not Ready","summary":"assessment","top_tip":"top priority"}
CONVERSATION:
"""

HINT_PROMPT = "You are a real-time coach. Give ONE short hint (max 15 words) about what the student just said. Format: emoji + hint. Student said: "

FACIAL_PROMPT = """You are an expert communication coach analyzing a student during a sponsor meeting practice session.
Evaluate their body language and presentation:
1. EYE CONTACT (0-25): Looking at camera directly?
2. CONFIDENCE (0-25): Posture, facial expression?
3. ENGAGEMENT (0-25): Look interested and present?
4. PROFESSIONALISM (0-25): Appearance and setting appropriate?
Return ONLY this JSON:
{"eye_contact":0,"confidence":0,"engagement":0,"professionalism":0,"total":0,"observations":["o1","o2","o3"],"improvements":["i1","i2"],"quick_wins":["q1","q2"],"summary":"2-3 sentence assessment"}"""

VIDEO_HTML = """
<div style="font-family:sans-serif;">
  <video id="videoEl" autoplay muted playsinline style="width:100%;border-radius:12px;background:#000;max-height:380px;"></video>
  <div style="display:flex;gap:10px;margin-top:12px;flex-wrap:wrap;">
    <button id="startBtn" onclick="startRecording()" style="padding:10px 20px;border-radius:8px;border:none;background:linear-gradient(135deg,#7A1F2E,#B3273A);color:white;font-size:14px;font-weight:600;cursor:pointer;">▶️ Start Recording</button>
    <button id="stopBtn" onclick="stopRecording()" disabled style="padding:10px 20px;border-radius:8px;border:none;background:#EF4444;color:white;font-size:14px;font-weight:600;cursor:pointer;opacity:0.4;">⏹️ Stop</button>
    <span id="timer" style="padding:10px;font-size:14px;color:#EF4444;font-weight:600;align-self:center;"></span>
  </div>
  <div id="status" style="margin-top:8px;font-size:13px;color:#6B7280;"></div>
  <div id="previewDiv" style="margin-top:12px;display:none;">
    <p style="font-size:13px;font-weight:600;margin-bottom:6px;">📹 Your recording:</p>
    <video id="previewEl" controls style="width:100%;border-radius:8px;max-height:280px;"></video>
    <a id="downloadLink" download="interview-practice.webm" style="display:inline-block;margin-top:8px;padding:8px 16px;background:#9F2B3F;color:white;border-radius:8px;text-decoration:none;font-size:13px;font-weight:600;">⬇️ Download Video</a>
  </div>
</div>
<script>
let mediaRecorder, stream, chunks=[], timerInterval, seconds=0;
async function startRecording(){
  try {
    stream = await navigator.mediaDevices.getUserMedia({video:true,audio:true});
    document.getElementById("videoEl").srcObject=stream;
    mediaRecorder=new MediaRecorder(stream);
    chunks=[];
    mediaRecorder.ondataavailable=e=>{if(e.data.size>0)chunks.push(e.data);};
    mediaRecorder.onstop=()=>{
      const blob=new Blob(chunks,{type:"video/webm"});
      const url=URL.createObjectURL(blob);
      document.getElementById("previewEl").src=url;
      document.getElementById("downloadLink").href=url;
      document.getElementById("previewDiv").style.display="block";
      document.getElementById("status").textContent="✅ Done! Download or take a snapshot for AI analysis.";
    };
    mediaRecorder.start(1000);
    seconds=0;
    timerInterval=setInterval(()=>{
      seconds++;
      const m=Math.floor(seconds/60).toString().padStart(2,"0");
      const s=(seconds%60).toString().padStart(2,"0");
      document.getElementById("timer").textContent="🔴 "+m+":"+s;
    },1000);
    document.getElementById("startBtn").disabled=true;
    document.getElementById("startBtn").style.opacity="0.5";
    document.getElementById("stopBtn").disabled=false;
    document.getElementById("stopBtn").style.opacity="1";
    document.getElementById("status").textContent="🔴 Recording...";
  } catch(e){
    document.getElementById("status").textContent="❌ Camera access denied.";
  }
}
function stopRecording(){
  if(mediaRecorder&&mediaRecorder.state!=="inactive"){
    mediaRecorder.stop();
    stream.getTracks().forEach(t=>t.stop());
    clearInterval(timerInterval);
    document.getElementById("timer").textContent="";
    document.getElementById("startBtn").disabled=false;
    document.getElementById("startBtn").style.opacity="1";
    document.getElementById("stopBtn").disabled=true;
    document.getElementById("stopBtn").style.opacity="0.4";
  }
}
</script>
"""

def transcribe_audio(audio_bytes):
    try:
        import tempfile
        oai = get_openai_client()
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_bytes)
            fname = f.name
        with open(fname, "rb") as f:
            result = oai.audio.transcriptions.create(model="whisper-1", file=f)
        return result.text
    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return None

def analyze_facial_expression(image_bytes):
    try:
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        r = get_client().messages.create(
            model="claude-sonnet-4-6", max_tokens=800,
            messages=[{"role":"user","content":[
                {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":b64}},
                {"type":"text","text":FACIAL_PROMPT}
            ]}])
        return extract_json(r.content[0].text.strip())
    except Exception as e:
        st.error(f"Analysis error: {e}")
        return None

def speak_text(text):
    try:
        oai = get_openai_client()
        snippet = truncate_at_sentence(text, 500)
        resp = oai.audio.speech.create(model="tts-1", voice="nova", input=snippet)
        b64 = base64.b64encode(resp.content).decode()
        st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Sponsor voice unavailable: {e}")

def get_hint(client, msg):
    try:
        r = client.messages.create(model="claude-sonnet-4-6", max_tokens=60,
            messages=[{"role":"user","content":HINT_PROMPT+msg}])
        return r.content[0].text.strip(), None
    except Exception as e:
        return "", e

def do_score(msgs, pname):
    convo = "".join(f"{'STUDENT' if m['role']=='user' else 'SPONSOR'}: {m['content']}\n\n" for m in msgs)
    try:
        r = get_client().messages.create(model="claude-sonnet-4-6", max_tokens=800,
            messages=[{"role":"user","content":SCORE_PROMPT+convo}])
        return extract_json(r.content[0].text.strip())
    except Exception as e:
        st.error(f"Scoring failed: {e}")
        return None

def handle_user_message(user_text, msgs, hints, mkey, hkey, system_prompt, voice_on):
    msgs.append({"role": "user", "content": user_text})
    client = get_client()

    def _reply_task():
        return client.messages.create(model="claude-sonnet-4-6", max_tokens=500,
            system=system_prompt, messages=msgs)

    with ThreadPoolExecutor(max_workers=2) as ex:
        hint_future = ex.submit(get_hint, client, user_text)
        reply_future = ex.submit(_reply_task)
        hint, hint_err = hint_future.result()
        try:
            reply = reply_future.result().content[0].text
        except Exception as e:
            reply = None
            reply_err = e
        else:
            reply_err = None

    if hint_err:
        st.warning(f"Hint unavailable: {hint_err}")
    hints.append(hint)
    st.session_state[hkey] = hints

    if reply_err:
        st.error(f"Sponsor reply failed: {reply_err}")
    else:
        msgs.append({"role": "assistant", "content": reply})
        st.session_state[mkey] = msgs
        if voice_on:
            st.session_state["pending_tts"] = reply
    st.rerun()

# Play any sponsor TTS queued by the previous turn, now that the rerun has
# completed — rendering it before the rerun would wipe the <audio> element.
if st.session_state.get("pending_tts"):
    speak_text(st.session_state.pop("pending_tts"))

# ── SIDEBAR ──────────────────────────────────────
sidebar_brand()
st.sidebar.markdown("---")

# ── KEY FIX: Navigation with session state ────────
PAGE_OPTIONS = ["🏠 Home","💬 Practice Session","📹 Video Practice","📈 My Progress","ℹ️ About"]
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "🏠 Home"

page = st.sidebar.radio("", PAGE_OPTIONS,
    index=PAGE_OPTIONS.index(st.session_state["current_page"]))
st.session_state["current_page"] = page

st.sidebar.markdown("---")
best = st.session_state.get("best_score",0)
st.sidebar.markdown(f"""
<div style="padding:12px;background:#1a1a2e;border-radius:10px;margin-bottom:8px;">
  <div style="font-size:0.75rem;color:#9CA3AF;margin-bottom:4px;">YOUR BEST SCORE</div>
  <div style="font-size:1.8rem;font-weight:800;color:{'#10B981' if best>=80 else '#F59E0B' if best>=60 else 'white'};">{best}/100</div>
  {'<div style="font-size:0.75rem;color:#10B981;margin-top:2px;">✅ Meeting Ready!</div>' if best>=80 else f'<div style="font-size:0.75rem;color:#9CA3AF;margin-top:2px;">Need {80-best} more points</div>'}
</div>
""", unsafe_allow_html=True)
if best < 80:
    st.sidebar.progress(min(best/80,1.0))

st.sidebar.markdown("---")
st.sidebar.page_link("pages/4_Group_Practice_Call.py", label="👥 Group Practice Call")

def go_to(page_name, persona_id=None):
    st.session_state["current_page"] = page_name
    if persona_id:
        st.session_state["pid"] = persona_id
    st.rerun()

# ── HOME ─────────────────────────────────────────
if page == "🏠 Home":
    col1, col2 = st.columns([3,2])
    with col1:
        st.markdown('<div class="hero-label fade-in">AI-Powered Practice for UChicago Capstone</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title fade-in d1">Practice that feels real.<br>Results that are.</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub fade-in d2">Practice your sponsor meetings with AI personas, get live coaching after every message, record your body language, and get certified meeting-ready — before the real thing.</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1:
            if st.button("💬 Start Practicing", use_container_width=True, type="primary"):
                go_to("💬 Practice Session", "mentor")
        with c2:
            if st.button("📹 Video Practice", use_container_width=True):
                go_to("📹 Video Practice")
    with col2:
        st.markdown("""
<div style="background:linear-gradient(135deg,#FBEAEC,#F7DEE1);border-radius:20px;padding:24px;margin-top:16px;">
  <div style="font-size:0.7rem;font-weight:600;color:#6B7280;letter-spacing:0.1em;margin-bottom:12px;">LIVE PRACTICE SESSION</div>
  <div style="background:white;border-radius:12px;padding:14px;margin-bottom:10px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
      <div style="width:36px;height:36px;background:#9F2B3F;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;">🔍</div>
      <div>
        <div style="font-size:0.85rem;font-weight:600;color:#111827;">Dr. Raj Patel</div>
        <div style="font-size:0.75rem;color:#9CA3AF;">CDO at Verizon · Skeptical</div>
      </div>
    </div>
    <div style="font-size:0.85rem;color:#374151;line-height:1.5;">"You're solving before diagnosing the problem. What data supports that assumption?"</div>
  </div>
  <div style="background:#FBEAEC;border-radius:10px;padding:10px 12px;font-size:0.8rem;color:#7A1F2E;">
    💡 <strong>Hint:</strong> Back up your claim with a specific data point or source.
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-header">How it works</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Four steps from practice to certified meeting-ready.</div>', unsafe_allow_html=True)

    steps = [
        ("1","Choose a persona","Pick from 5 AI sponsor types — from supportive mentor to tough skeptic. Each has a real company, real constraints, real pushback."),
        ("2","Practice the meeting","Type or speak your responses. The sponsor stays in character and challenges you like a real meeting would."),
        ("3","Get live coaching","After every single message, an AI coach gives you a one-line hint on what to improve immediately."),
        ("4","Record & analyze","Film yourself during practice. AI analyzes your eye contact, confidence, engagement, and professionalism.")
    ]
    cols = st.columns(4)
    for idx,(num,title,desc) in enumerate(steps):
        with cols[idx]:
            st.markdown(f"""
<div class="step-card fade-in d{idx+1}">
  <div style="width:44px;height:44px;background:linear-gradient(135deg,#7A1F2E,#B3273A);border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:800;font-size:1.1rem;margin:0 auto 14px;">{num}</div>
  <div style="font-size:1rem;font-weight:700;color:#111827;margin-bottom:8px;">{title}</div>
  <div style="font-size:0.85rem;color:#6B7280;line-height:1.5;">{desc}</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-header">Choose Your Sponsor</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Five AI personas, each with unique behavior, industry context, and difficulty level.</div>', unsafe_allow_html=True)

    cols = st.columns(5)
    for idx,(pid,p) in enumerate(PERSONAS.items()):
        with cols[idx]:
            st.markdown(f"""
<div class="persona-card fade-in d{(idx % 6) + 1}">
  <div class="persona-icon">{p['icon']}</div>
  <div class="persona-name">{p['name']}</div>
  <div class="persona-company">🏢 {p['company']}</div>
  <div class="persona-desc">{p['desc']}</div>
  <span class="difficulty-badge {DIFF_CLASS[p['difficulty']]}">{p['diff_label']}</span>
</div>
""", unsafe_allow_html=True)
            if st.button("Practice →", key=f"h_{pid}", use_container_width=True):
                go_to("💬 Practice Session", pid)

    st.markdown("---")
    with st.container(key="cta_banner"):
        st.markdown("""
<div class="cta-card">
  <div style="font-size:2rem;font-weight:800;margin-bottom:12px;">Ready to practice?</div>
  <div style="font-size:1rem;opacity:0.9;">Hit 80/100 to get certified meeting-ready. Start with the Mentor Sponsor.</div>
</div>
""", unsafe_allow_html=True)
        if st.button("🌱 Start with Mentor Sponsor", use_container_width=True, type="primary"):
            go_to("💬 Practice Session", "mentor")

# ── VIDEO PRACTICE ────────────────────────────────
elif page == "📹 Video Practice":
    st.markdown('<div class="hero-title" style="font-size:2rem;">📹 Video Practice</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Record yourself, take a snapshot, and get AI feedback on your body language.</div>', unsafe_allow_html=True)
    st.markdown("---")
    names = {v["name"]:k for k,v in PERSONAS.items()}
    default = st.session_state.get("pid","mentor")
    sel = st.selectbox("Choose your sponsor", list(names.keys()),
        index=list(names.keys()).index(PERSONAS[default]["name"]))
    pid = names[sel]
    p = PERSONAS[pid]
    st.markdown("---")
    col1, col2 = st.columns([3,2])
    with col1:
        st.markdown("#### 🎬 Step 1 — Record Your Session")
        st.info("💡 Look at camera · Good lighting · Sit upright · Professional background")
        st.components.v1.html(VIDEO_HTML, height=500)
    with col2:
        st.markdown("#### 📸 Step 2 — Take Snapshot for Analysis")
        img_file = st.camera_input("Take a photo now")
        if img_file:
            st.session_state["snapshot"] = img_file.getvalue()
    st.markdown("---")
    if st.session_state.get("snapshot"):
        if st.button("🤖 Give Analysis for Facial Expression", type="primary", use_container_width=True):
            with st.spinner("🔍 Analyzing your facial expressions, eye contact, and body language..."):
                result = analyze_facial_expression(st.session_state["snapshot"])
            if result:
                st.session_state["facial_result"] = result
                st.session_state["facial_timestamp"] = time.strftime("%Y-%m-%d %H:%M")
                st.rerun()
            else:
                st.error("Analysis failed — check your API key.")
    else:
        st.info("👆 Take a snapshot above to unlock the AI analysis button.")
    if st.session_state.get("facial_result"):
        result = st.session_state["facial_result"]
        total = result.get("total",0)
        st.markdown("---")
        st.markdown("## 😊 Body Language Report")
        color = "green" if total>=80 else "orange" if total>=60 else "red"
        st.markdown(f"### Score: :{color}[{total}/100]")
        st.progress(total/100)
        if total>=80: st.success("✅ Excellent! You look confident and professional.")
        elif total>=60: st.warning("⚠️ Good effort — a few tweaks will help a lot.")
        else: st.error("❌ Needs work before the real meeting.")
        st.markdown("---")
        ec,cf,en,pr = result.get("eye_contact",0),result.get("confidence",0),result.get("engagement",0),result.get("professionalism",0)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("👁️ Eye Contact",f"{ec}/25",delta="Good" if ec>=20 else "Needs work")
        c2.metric("💪 Confidence",f"{cf}/25",delta="Good" if cf>=20 else "Needs work")
        c3.metric("🎯 Engagement",f"{en}/25",delta="Good" if en>=20 else "Needs work")
        c4.metric("👔 Professionalism",f"{pr}/25",delta="Good" if pr>=20 else "Needs work")
        st.markdown("---")
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("#### ✅ What You Did Well")
            for o in result.get("observations",[]): st.success(o)
            st.markdown("#### ⚡ Quick Wins")
            for q in result.get("quick_wins",[]): st.info(q)
        with col2:
            st.markdown("#### ⚠️ Improve")
            for i in result.get("improvements",[]): st.warning(i)
            st.markdown("#### 💡 Tips")
            if ec<20: st.markdown("**👁️** Look at your camera lens, not your own face on screen.")
            if cf<20: st.markdown("**💪** Sit up straight, take a breath, speak at a steady pace.")
            if en<20: st.markdown("**🎯** Nod occasionally, lean slightly forward, smile naturally.")
            if pr<20: st.markdown("**👔** Clean background, front lighting, dress professionally.")
        st.markdown("---")
        st.info(f"**Overall:** {result.get('summary','')}")
        col1,col2 = st.columns(2)
        with col1:
            if st.button("💾 Save to My Progress", use_container_width=True):
                if "video_history" not in st.session_state: st.session_state["video_history"]=[]
                st.session_state["video_history"].append({"persona":p["name"],"score":total,"eye_contact":ec,"confidence":cf,"engagement":en,"professionalism":pr,"summary":result.get("summary",""),"timestamp":st.session_state.get("facial_timestamp","")})
                st.success("✅ Saved!")
        with col2:
            if st.button("🔄 Analyze Again", use_container_width=True):
                st.session_state["facial_result"]=None
                st.session_state["snapshot"]=None
                st.rerun()

# ── PRACTICE SESSION ─────────────────────────────
elif page == "💬 Practice Session":
    st.markdown('<div class="hero-title" style="font-size:2rem;">💬 Practice Session</div>', unsafe_allow_html=True)
    names = {v["name"]:k for k,v in PERSONAS.items()}
    default = st.session_state.get("pid","mentor")
    scenario_names = {v["name"]:k for k,v in SCENARIOS.items()}
    default_scenario = st.session_state.get("scenario_id","initial")
    sc1,sc2 = st.columns(2)
    with sc1:
        sel = st.selectbox("Choose your sponsor",list(names.keys()),
            index=list(names.keys()).index(PERSONAS[default]["name"]))
    with sc2:
        scen_sel = st.selectbox("Choose your meeting scenario",list(scenario_names.keys()),
            index=list(scenario_names.keys()).index(SCENARIOS[default_scenario]["name"]))
    pid = names[sel]
    p = PERSONAS[pid]
    scenario_id = scenario_names[scen_sel]
    scenario = SCENARIOS[scenario_id]
    st.session_state["scenario_id"] = scenario_id
    system_prompt = p["prompt"] + "\n\n" + scenario["context"]
    col1,col2 = st.columns([3,1])
    with col1:
        with st.expander(f"{p['icon']} About {p['name']} — {p['company']}  ·  {scenario['icon']} {scenario['name']}"):
            st.markdown(f"**Role:** {p['role']}")
            st.markdown(f"**Difficulty:** {'★'*p['difficulty']}{'☆'*(5-p['difficulty'])} {p['diff_label']}")
            st.markdown(p["desc"])
            st.markdown(f"**Scenario:** {scenario['desc']}")
    with col2:
        voice_on = st.toggle("🔊 Sponsor voice",value=False)
    st.markdown("---")
    mkey,hkey = f"m_{pid}_{scenario_id}",f"h_{pid}_{scenario_id}"
    scored_key,result_key = f"scored_{pid}_{scenario_id}",f"result_{pid}_{scenario_id}"
    if mkey not in st.session_state: st.session_state[mkey]=[]
    if hkey not in st.session_state: st.session_state[hkey]=[]
    if scored_key not in st.session_state: st.session_state[scored_key]=False
    if result_key not in st.session_state: st.session_state[result_key]=None
    msgs = st.session_state[mkey]
    hints = st.session_state[hkey]
    c1,c2 = st.columns([1,4])
    with c1:
        if st.button("🔄 New Session"):
            st.session_state[mkey]=[]; st.session_state[hkey]=[]
            st.session_state[scored_key]=False; st.session_state[result_key]=None
            st.rerun()
    with c2:
        turns = sum(1 for m in msgs if m["role"]=="user")
        st.caption(f"💬 {turns} responses — {'🎯 Ready to score!' if turns>=3 else f'Need {3-turns} more to unlock scoring'}")
    if not msgs:
        try:
            with st.spinner(f"{p['icon']} {p['name']} is joining..."):
                r = get_client().messages.create(model="claude-sonnet-4-6",max_tokens=200,
                    system=system_prompt,messages=[{"role":"user","content":"Begin the meeting now."}])
                opening = r.content[0].text
                msgs.append({"role":"assistant","content":opening})
                st.session_state[mkey]=msgs
                if voice_on: speak_text(opening)
        except Exception as e:
            st.error(f"Could not start the meeting: {e}")
            st.stop()
    col_chat,col_side = st.columns([3,1])
    with col_chat:
        for i,m in enumerate(msgs):
            with st.chat_message(m["role"],avatar=p["icon"] if m["role"]=="assistant" else "🎓"):
                st.markdown(m["content"])
            if m["role"]=="user":
                hidx = sum(1 for msg in msgs[:i+1] if msg["role"]=="user")-1
                if hidx < len(hints) and hints[hidx]:
                    st.markdown(f'<div class="hint-bubble">💡 {hints[hidx]}</div>', unsafe_allow_html=True)
    with col_side:
        st.markdown("### 📊 Live Stats")
        with st.container(border=True):
            sm = [m for m in msgs if m["role"]=="user"]
            avg_w = round(sum(len(m["content"].split()) for m in sm)/len(sm)) if sm else 0
            st.metric("Responses",len(sm))
            st.metric("Avg words",avg_w)
            if avg_w>80: st.warning("⚠️ Too long!")
            elif avg_w>0: st.success("✅ Good length")
        if hints:
            st.markdown("### 💡 Recent Hints")
            for h in hints[-3:]:
                st.markdown(f'<div class="hint-bubble">{h}</div>', unsafe_allow_html=True)

    if not st.session_state[scored_key]:
        st.markdown("---")
        st.markdown("#### 🎙️ Record your voice")
        voice_key = f"voice_{pid}_{scenario_id}_{turns}"
        audio_file = st.audio_input("Record your voice", key=voice_key, label_visibility="collapsed")
        if audio_file is not None:
            with st.spinner("🎙️ Transcribing..."):
                transcript = transcribe_audio(audio_file.getvalue())
            if transcript:
                st.info(f"🎙️ You said: *{transcript}*")
                handle_user_message(transcript, msgs, hints, mkey, hkey, system_prompt, voice_on)
            else:
                st.warning("Could not transcribe — check your OpenAI API key.")
        st.markdown("#### ✍️ Or type your message")
        if prompt := st.chat_input("Type your message to the sponsor..."):
            handle_user_message(prompt, msgs, hints, mkey, hkey, system_prompt, voice_on)

    turns = sum(1 for m in msgs if m["role"]=="user")
    if turns>=3 and not st.session_state[scored_key]:
        st.markdown("---")
        if st.button("🏁 End Meeting & Get Score",type="primary",use_container_width=True):
            with st.spinner("Evaluating your performance..."):
                res = do_score(msgs,p["name"])
            if res:
                st.session_state[result_key]=res; st.session_state[scored_key]=True
                if "history" not in st.session_state: st.session_state["history"]=[]
                st.session_state["history"].append({"persona":p["name"],"score":res["total"],"readiness":res["readiness"],"company":p["company"]})
                if res["total"]>best: st.session_state["best_score"]=res["total"]
                st.rerun()

    if st.session_state[scored_key] and st.session_state[result_key]:
        res = st.session_state[result_key]
        total = res["total"]
        st.markdown("---")
        st.markdown("## 🏆 Your Results")
        color = "green" if total>=80 else "orange" if total>=60 else "red"
        st.markdown(f"### Score: :{color}[{total}/100]")
        st.progress(total/100)
        if total>=80: st.success("✅ CERTIFIED — You are ready for your real sponsor meeting!")
        elif total>=60: st.warning("⚠️ Almost there — keep practicing.")
        else: st.error("❌ Keep practicing — focus on improvements below.")
        if res.get("top_tip"): st.markdown(f"### 🎯 Top Priority: *{res['top_tip']}*")
        st.markdown("---")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Preparation",f"{res['preparation']}/25")
        c2.metric("Communication",f"{res['communication']}/25")
        c3.metric("Meeting Mgmt",f"{res['meeting_management']}/25")
        c4.metric("Relationship",f"{res['relationship_building']}/25")
        if st.session_state.get("facial_result"):
            body = st.session_state["facial_result"].get("total",0)
            combined = round((total+body)/2)
            color2 = "green" if combined>=80 else "orange" if combined>=60 else "red"
            st.markdown("---")
            st.markdown(f"### 🎯 Combined Score: :{color2}[{combined}/100]")
            c1,c2 = st.columns(2)
            c1.metric("Content Score",f"{total}/100")
            c2.metric("Body Language",f"{body}/100")
        cl,cr = st.columns(2)
        with cl:
            st.markdown("#### ✅ Strengths")
            for s in res.get("strengths",[]): st.success(s)
        with cr:
            st.markdown("#### ⚠️ Improve")
            for i in res.get("improvements",[]): st.warning(i)
        if res.get("missed_opportunities"):
            st.markdown("#### ❌ Missed")
            for m in res["missed_opportunities"]: st.error(m)
        st.info(res.get("summary",""))
        if st.button("🔄 Practice Again",use_container_width=True):
            st.session_state[mkey]=[]; st.session_state[hkey]=[]
            st.session_state[scored_key]=False; st.session_state[result_key]=None
            st.rerun()

# ── PROGRESS ─────────────────────────────────────
elif page == "📈 My Progress":
    st.markdown('<div class="hero-title" style="font-size:2rem;">📈 My Progress</div>', unsafe_allow_html=True)
    st.markdown("---")
    history = st.session_state.get("history",[])
    video_history = st.session_state.get("video_history",[])
    if not history and not video_history:
        st.info("No sessions yet! Go to Practice Session to get started.")
    else:
        if history:
            best = st.session_state.get("best_score",0)
            avg = round(sum(h["score"] for h in history)/len(history))
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Sessions",len(history))
            c2.metric("Best Score",f"{best}/100")
            c3.metric("Average",f"{avg}/100")
            c4.metric("Certified",sum(1 for h in history if h["readiness"]=="Ready"))
            st.markdown("---")
            st.markdown("### 🎯 Readiness Tracker")
            st.progress(min(best/80,1.0))
            if best>=80: st.success("✅ CERTIFIED — Ready for your real sponsor meeting!")
            else: st.warning(f"Need {80-best} more points to get certified. Best: {best}/100")
            st.markdown("---")
            st.markdown("### 📋 Session History")
            for i,h in enumerate(reversed(history),1):
                with st.container(border=True):
                    c1,c2,c3,c4 = st.columns([2,2,2,2])
                    c1.write(f"**Session {len(history)-i+1}**")
                    c2.write(f"🏢 {h.get('company',h['persona'])}")
                    c3.write(f"**{h['score']}/100**")
                    color = "green" if h["readiness"]=="Ready" else "orange" if h["readiness"]=="Almost Ready" else "red"
                    c4.markdown(f":{color}[{h['readiness']}]")
        if video_history:
            st.markdown("---")
            st.markdown("### 📹 Video Analysis History")
            for v in reversed(video_history):
                with st.container(border=True):
                    c1,c2,c3,c4,c5 = st.columns([2,1,1,1,1])
                    c1.write(f"**{v['timestamp']}**")
                    c2.metric("Total",f"{v['score']}/100")
                    c3.metric("👁️",f"{v.get('eye_contact',0)}/25")
                    c4.metric("💪",f"{v.get('confidence',0)}/25")
                    c5.metric("🎯",f"{v.get('engagement',0)}/25")
                    st.caption(v.get("summary",""))
    if history or video_history:
        st.markdown("---")
        export = {
            "history": history,
            "video_history": video_history,
            "best_score": st.session_state.get("best_score",0),
        }
        st.download_button(
            "⬇️ Export My Progress (JSON)",
            data=json.dumps(export, indent=2),
            file_name="capstone_coach_progress.json",
            mime="application/json",
            use_container_width=True,
        )
        st.caption("⚠️ Session data resets when you refresh the page — export it if you want to keep it.")

# ── ABOUT ─────────────────────────────────────────
elif page == "ℹ️ About":
    st.markdown('<div class="hero-title" style="font-size:2rem;">🎓 About Capstone Coach</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
## 🎓 Capstone Coach
AI-powered sponsor meeting simulator for UChicago ADS Capstone students — practice with AI personas, live coaching, and full team assessment before the real thing.

### Features
- 🗂️ Meeting scenario picker — Initial Meeting, Scope, Data, Progress Summary
- 💬 Text chat with AI sponsor personas
- 🎙️ Voice record button — speak to your sponsor
- 🔊 Sponsor speaks back with OpenAI TTS
- 📹 Record your interview practice session
- 😊 AI analyzes facial expressions and body language
- 💡 Live coaching hints after every message
- 📊 Combined content + body language score
- 👥 Zoom-integrated Group Practice Call — assess every team member
- 🏆 Get certified meeting-ready at 80+

### Tech Stack
Streamlit · Claude API · OpenAI Whisper · OpenAI TTS · Claude Vision · Zoom API

### Built For
UChicago Master of Applied Data Science — Capstone Program
""")
