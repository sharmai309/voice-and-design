import streamlit as st
import os, json, base64, time
from anthropic import Anthropic

st.set_page_config(page_title="Voice & Design", page_icon="🎙️", layout="wide")

def get_client():
    try:
        key = st.secrets["ANTHROPIC_API_KEY"]
    except:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
    return Anthropic(api_key=key)

PERSONAS = {
    "mentor": {"name":"Mentor Sponsor","icon":"🌱","difficulty":1,"company":"HealthTech Analytics","desc":"Encouraging and supportive. Great for your first attempt.","prompt":"You are Dr. Sarah Chen, Senior Director of Analytics at HealthTech Analytics, a MENTOR SPONSOR for a UChicago Capstone team. Be warm, encouraging, patient. Ask guiding questions. Keep responses 2-4 sentences. START: Hi team, great to finally connect. Go ahead and introduce yourselves."},
    "executive": {"name":"Busy Executive","icon":"⚡","difficulty":4,"company":"FastShip Logistics","desc":"Time-pressed and terse. Get to the point fast.","prompt":"You are Marcus Webb, VP of Operations at FastShip Logistics, a BUSY EXECUTIVE SPONSOR. Always pressed for time. Short 1-3 sentence answers. Interrupt ramblers. START: Alright, you have got me for 10 minutes. What are we covering today?"},
    "skeptic": {"name":"Skeptical Sponsor","icon":"🔍","difficulty":5,"company":"Verizon","desc":"Challenges every assumption. Come with evidence.","prompt":"You are Dr. Raj Patel, CDO at Verizon, a SKEPTICAL SPONSOR. Question every assumption. Push back firmly. Challenge at least one thing per response. START: I reviewed your brief. Walk me through your problem statement, and be specific."},
    "technical": {"name":"Technical Expert","icon":"💻","difficulty":4,"company":"BioSight Research","desc":"Deep dives into methodology. Know your data.","prompt":"You are Dr. Aisha Okafor, Director of Data Science at BioSight Research, a TECHNICAL EXPERT SPONSOR. Ask about data sources, methodology, validation. At least one technical follow-up per response. START: Before deliverables, walk me through your technical approach."},
    "collaborator": {"name":"Open Collaborator","icon":"💡","difficulty":2,"company":"TrendBox","desc":"Loves ideas but needs you to manage the agenda.","prompt":"You are Jamie Torres, Director of Innovation at TrendBox, an OPEN COLLABORATOR SPONSOR. Love brainstorming. Go on tangents. START: So excited for this! Where do you want to start, I am totally open!"}
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
Look at this image carefully and evaluate their body language and presentation:

1. EYE CONTACT (0-25): Are they looking at the camera directly? Sustained eye contact shows confidence and engagement.
2. CONFIDENCE (0-25): Posture, facial expression, do they look confident or nervous/anxious?
3. ENGAGEMENT (0-25): Do they look interested and present, or distracted/bored/disengaged?
4. PROFESSIONALISM (0-25): Is their appearance, background, and setting appropriate for a professional sponsor meeting?

Be specific and constructive. Reference exactly what you see in the image.

Return ONLY this JSON, no other text:
{
  "eye_contact": 0,
  "confidence": 0,
  "engagement": 0,
  "professionalism": 0,
  "total": 0,
  "observations": ["specific observation 1", "specific observation 2", "specific observation 3"],
  "improvements": ["specific actionable improvement 1", "specific actionable improvement 2"],
  "quick_wins": ["quick win 1", "quick win 2"],
  "summary": "2-3 sentence overall body language assessment with specific details from the image"
}"""

VIDEO_HTML = """
<div style="font-family:sans-serif;padding:8px 0;">
  <video id="videoEl" autoplay muted playsinline style="width:100%;border-radius:12px;background:#000;max-height:400px;"></video>
  <div style="display:flex;gap:10px;margin-top:12px;flex-wrap:wrap;">
    <button id="startBtn" onclick="startRecording()" style="padding:10px 20px;border-radius:8px;border:none;background:#1D9E75;color:white;font-size:14px;font-weight:500;cursor:pointer;">▶️ Start Recording</button>
    <button id="stopBtn" onclick="stopRecording()" disabled style="padding:10px 20px;border-radius:8px;border:none;background:#D85A30;color:white;font-size:14px;font-weight:500;cursor:pointer;opacity:0.5;">⏹️ Stop Recording</button>
    <span id="timer" style="padding:10px;font-size:14px;color:#666;align-self:center;"></span>
  </div>
  <div id="status" style="margin-top:8px;font-size:13px;color:#666;"></div>
  <div id="previewDiv" style="margin-top:12px;display:none;">
    <p style="font-size:13px;font-weight:500;margin-bottom:6px;">📹 Your recorded video:</p>
    <video id="previewEl" controls style="width:100%;border-radius:8px;max-height:300px;"></video>
    <a id="downloadLink" download="interview-practice.webm" style="display:inline-block;margin-top:8px;padding:8px 16px;background:#185FA5;color:white;border-radius:6px;text-decoration:none;font-size:13px;">⬇️ Download Video</a>
  </div>
</div>
<script>
let mediaRecorder, stream, chunks=[], timerInterval, seconds=0;
async function startRecording(){
  try {
    stream = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
    document.getElementById("videoEl").srcObject = stream;
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    mediaRecorder.ondataavailable = e => { if(e.data.size>0) chunks.push(e.data); };
    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, {type:"video/webm"});
      const url = URL.createObjectURL(blob);
      document.getElementById("previewEl").src = url;
      document.getElementById("downloadLink").href = url;
      document.getElementById("previewDiv").style.display = "block";
      document.getElementById("status").textContent = "✅ Recording saved! Download it or take a snapshot below for AI analysis.";
    };
    mediaRecorder.start(1000);
    seconds = 0;
    timerInterval = setInterval(() => {
      seconds++;
      const m = Math.floor(seconds/60).toString().padStart(2,"0");
      const s = (seconds%60).toString().padStart(2,"0");
      document.getElementById("timer").textContent = "🔴 " + m + ":" + s;
    }, 1000);
    document.getElementById("startBtn").disabled = true;
    document.getElementById("startBtn").style.opacity = "0.5";
    document.getElementById("stopBtn").disabled = false;
    document.getElementById("stopBtn").style.opacity = "1";
    document.getElementById("status").textContent = "🔴 Recording in progress...";
  } catch(e) {
    document.getElementById("status").textContent = "❌ Camera access denied. Please allow camera permission.";
  }
}
function stopRecording(){
  if(mediaRecorder && mediaRecorder.state !== "inactive"){
    mediaRecorder.stop();
    stream.getTracks().forEach(t => t.stop());
    clearInterval(timerInterval);
    document.getElementById("timer").textContent = "";
    document.getElementById("startBtn").disabled = false;
    document.getElementById("startBtn").style.opacity = "1";
    document.getElementById("stopBtn").disabled = true;
    document.getElementById("stopBtn").style.opacity = "0.5";
  }
}
</script>
"""

VOICE_BTN_HTML = """
<div style="display:flex;align-items:center;gap:12px;padding:12px;background:#f8f9fa;border-radius:12px;margin-bottom:8px;border:1px solid #e9ecef;">
  <button id="micBtn" onclick="toggleMic()"
    style="width:52px;height:52px;border-radius:50%;border:2px solid #1D9E75;
    background:white;font-size:22px;cursor:pointer;flex-shrink:0;transition:all 0.2s;">🎙️</button>
  <div>
    <div id="micStatus" style="font-size:13px;font-weight:500;color:#333;">🎙️ Click to record your voice</div>
    <div id="micHint" style="font-size:11px;color:#888;margin-top:2px;">Speak clearly, then click stop — your voice will be sent to the sponsor</div>
  </div>
</div>
<script>
let recorder, audioChunks=[], recording=false;
async function toggleMic(){
  if(!recording){
    try{
      const stream = await navigator.mediaDevices.getUserMedia({audio:true});
      recorder = new MediaRecorder(stream);
      audioChunks = [];
      recorder.ondataavailable = e => audioChunks.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(audioChunks,{type:"audio/webm"});
        const reader = new FileReader();
        reader.onloadend = () => {
          window.parent.postMessage({type:"voice",data:reader.result.split(",")[1]},"*");
          document.getElementById("micStatus").textContent = "⏳ Processing your voice...";
          document.getElementById("micHint").textContent = "Please wait...";
        };
        reader.readAsDataURL(blob);
        stream.getTracks().forEach(t=>t.stop());
      };
      recorder.start();
      recording=true;
      document.getElementById("micBtn").style.background="#D85A30";
      document.getElementById("micBtn").style.borderColor="#D85A30";
      document.getElementById("micBtn").textContent="⏹️";
      document.getElementById("micStatus").textContent="🔴 Recording... click to stop";
      document.getElementById("micHint").textContent="Speak clearly to the sponsor";
    } catch(e) {
      document.getElementById("micStatus").textContent="❌ Microphone access denied — check browser permissions";
    }
  } else {
    recorder.stop();
    recording=false;
    document.getElementById("micBtn").style.background="white";
    document.getElementById("micBtn").style.borderColor="#1D9E75";
    document.getElementById("micBtn").textContent="🎙️";
    document.getElementById("micStatus").textContent="🎙️ Click to record your voice";
    document.getElementById("micHint").textContent="Speak clearly, then click stop";
  }
}
</script>
"""

def transcribe_audio(audio_b64):
    try:
        from openai import OpenAI
        import tempfile
        oai = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY",""))
        audio_bytes = base64.b64decode(audio_b64)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_bytes)
            fname = f.name
        with open(fname, "rb") as f:
            result = oai.audio.transcriptions.create(model="whisper-1", file=f)
        return result.text
    except Exception as e:
        return None

def analyze_facial_expression(image_bytes):
    try:
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        r = get_client().messages.create(
            model="claude-sonnet-4-6", max_tokens=800,
            messages=[{"role":"user","content":[
                {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":b64}},
                {"type":"text","text":FACIAL_PROMPT}
            ]}]
        )
        raw = r.content[0].text.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        st.error(f"Analysis error: {e}")
        return None

def speak_text(text):
    try:
        from openai import OpenAI
        oai = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY",""))
        resp = oai.audio.speech.create(model="tts-1", voice="nova", input=text[:500])
        b64 = base64.b64encode(resp.content).decode()
        st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    except: pass

def get_hint(msg):
    try:
        r = get_client().messages.create(model="claude-sonnet-4-6", max_tokens=60,
            messages=[{"role":"user","content":HINT_PROMPT+msg}])
        return r.content[0].text.strip()
    except: return ""

def do_score(msgs, pname):
    convo = "".join(f"{'STUDENT' if m['role']=='user' else 'SPONSOR'}: {m['content']}\n\n" for m in msgs)
    r = get_client().messages.create(model="claude-sonnet-4-6", max_tokens=800,
        messages=[{"role":"user","content":SCORE_PROMPT+convo}])
    raw = r.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    return json.loads(raw.strip())

st.sidebar.title("🎙️ Voice & Design")
st.sidebar.markdown("---")
page = st.sidebar.radio("", ["🏠 Home","💬 Practice Session","📹 Video Practice","📈 My Progress","ℹ️ About"])
st.sidebar.markdown("---")
best = st.session_state.get("best_score",0)
st.sidebar.metric("Best Score", f"{best}/100")
if best>=80: st.sidebar.success("✅ Meeting Ready!")
else:
    st.sidebar.progress(min(best/80,1.0))
    st.sidebar.caption(f"Need {80-best} more points")
st.sidebar.markdown("---")
st.sidebar.caption("UChicago ADS Capstone Project")

if page == "🏠 Home":
    st.title("🎙️ Voice & Design")
    st.markdown("### Practice your sponsor meetings. Get real-time coaching. Ace the real thing.")
    st.markdown("---")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Sponsor Personas","5")
    c2.metric("Scoring Dimensions","4")
    c3.metric("Voice + Video","🎙️📹")
    c4.metric("Your Best Score",f"{best}/100")
    st.markdown("---")
    st.markdown("## 🎯 How It Works")
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.markdown("### 1️⃣")
            st.markdown("**Choose a sponsor** from 5 different personas")
    with c2:
        with st.container(border=True):
            st.markdown("### 2️⃣")
            st.markdown("**Practice** — type or speak to your sponsor")
    with c3:
        with st.container(border=True):
            st.markdown("### 3️⃣")
            st.markdown("**Record video** — AI analyzes your body language")
    with c4:
        with st.container(border=True):
            st.markdown("### 4️⃣")
            st.markdown("**Full report** — content + body language score")
    st.markdown("---")
    st.markdown("## 👥 Choose Your Sponsor")
    cols = st.columns(5)
    for col,(pid,p) in zip(cols,PERSONAS.items()):
        with col:
            with st.container(border=True):
                st.markdown(f"## {p['icon']}")
                st.markdown(f"**{p['name']}**")
                st.caption("★"*p["difficulty"]+"☆"*(5-p["difficulty"]))
                st.caption(f"🏢 {p['company']}")
                st.write(p["desc"])
                if st.button("Practice →",key=f"h_{pid}",use_container_width=True):
                    st.session_state["pid"]=pid
                    st.rerun()
    st.markdown("---")
    st.info("💡 Start with 🌱 Mentor Sponsor, then work up to 🔍 Skeptic before your real meeting.")

elif page == "📹 Video Practice":
    st.title("📹 Video Practice")
    st.markdown("Record your interview practice session, then get AI feedback on your body language.")
    st.markdown("---")
    names = {v["name"]:k for k,v in PERSONAS.items()}
    default = st.session_state.get("pid","mentor")
    sel = st.selectbox("Choose your sponsor",list(names.keys()),
        index=list(names.keys()).index(PERSONAS[default]["name"]))
    pid = names[sel]
    p = PERSONAS[pid]
    st.markdown("---")
    col1, col2 = st.columns([3,2])
    with col1:
        st.markdown("### 🎬 Step 1 — Record Your Session")
        st.info("💡 Tips: Look at camera, good lighting, sit upright, professional background")
        st.components.v1.html(VIDEO_HTML, height=520)
    with col2:
        st.markdown("### 📸 Step 2 — Take Snapshot for Analysis")
        st.markdown("Take a photo during or after recording for AI facial expression analysis:")
        img_file = st.camera_input("📷 Snapshot")
        if img_file:
            st.image(img_file, caption="Your snapshot", use_container_width=True)
            st.session_state["snapshot"] = img_file.getvalue()
    st.markdown("---")
    if st.session_state.get("snapshot"):
        if st.button("🤖 Give Analysis for Facial Expression", type="primary", use_container_width=True):
            with st.spinner("🔍 Claude is analyzing your facial expressions, eye contact, and body language..."):
                result = analyze_facial_expression(st.session_state["snapshot"])
            if result:
                st.session_state["facial_result"] = result
                st.session_state["facial_timestamp"] = time.strftime("%Y-%m-%d %H:%M")
                st.rerun()
            else:
                st.error("Analysis failed — make sure your Anthropic API key is set correctly.")
    else:
        st.info("👆 Take a snapshot above to enable the facial expression analysis button.")
    if st.session_state.get("facial_result"):
        result = st.session_state["facial_result"]
        st.markdown("---")
        st.markdown("## 😊 Facial Expression & Body Language Report")
        st.caption(f"Analyzed at: {st.session_state.get('facial_timestamp','')}")
        total = result.get("total", 0)
        color = "green" if total>=80 else "orange" if total>=60 else "red"
        st.markdown(f"### Body Language Score: :{color}[{total}/100]")
        st.progress(total/100)
        if total >= 80: st.success("✅ Excellent body language! You look confident and professional.")
        elif total >= 60: st.warning("⚠️ Good effort! A few tweaks will make you look more confident.")
        else: st.error("❌ Your body language needs work before the real meeting.")
        st.markdown("---")
        c1,c2,c3,c4 = st.columns(4)
        ec = result.get("eye_contact",0)
        cf = result.get("confidence",0)
        en = result.get("engagement",0)
        pr = result.get("professionalism",0)
        c1.metric("👁️ Eye Contact", f"{ec}/25", delta="Good" if ec>=20 else "Needs work")
        c2.metric("💪 Confidence", f"{cf}/25", delta="Good" if cf>=20 else "Needs work")
        c3.metric("🎯 Engagement", f"{en}/25", delta="Good" if en>=20 else "Needs work")
        c4.metric("👔 Professionalism", f"{pr}/25", delta="Good" if pr>=20 else "Needs work")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### ✅ What You Did Well")
            for obs in result.get("observations", []): st.success(obs)
            st.markdown("#### ⚡ Quick Wins")
            for qw in result.get("quick_wins", []): st.info(qw)
        with col2:
            st.markdown("#### ⚠️ What To Improve")
            for imp in result.get("improvements", []): st.warning(imp)
            st.markdown("#### 💡 Specific Tips")
            if ec < 20: st.markdown("**👁️ Eye contact:** Look directly at your camera lens, not at your own face on screen.")
            if cf < 20: st.markdown("**💪 Confidence:** Sit up straight, shoulders back. Take a slow breath before speaking.")
            if en < 20: st.markdown("**🎯 Engagement:** Nod occasionally, lean slightly forward, smile naturally.")
            if pr < 20: st.markdown("**👔 Professionalism:** Use a clean background, good front lighting, dress professionally.")
        st.markdown("---")
        st.info(f"**Overall Assessment:** {result.get('summary','')}")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Analysis To My Progress", use_container_width=True):
                if "video_history" not in st.session_state: st.session_state["video_history"] = []
                st.session_state["video_history"].append({
                    "persona": p["name"], "score": total, "eye_contact": ec,
                    "confidence": cf, "engagement": en, "professionalism": pr,
                    "summary": result.get("summary",""),
                    "timestamp": st.session_state.get("facial_timestamp","")
                })
                st.success("✅ Saved to My Progress!")
        with col2:
            if st.button("🔄 Analyze Again", use_container_width=True):
                st.session_state["facial_result"] = None
                st.session_state["snapshot"] = None
                st.rerun()

elif page == "💬 Practice Session":
    st.title("💬 Practice Session")
    names = {v["name"]:k for k,v in PERSONAS.items()}
    default = st.session_state.get("pid","mentor")
    sel = st.selectbox("Choose your sponsor",list(names.keys()),
        index=list(names.keys()).index(PERSONAS[default]["name"]))
    pid = names[sel]
    p = PERSONAS[pid]
    col1,col2 = st.columns([3,1])
    with col1:
        with st.expander(f"{p['icon']} About {p['name']} — {p['company']}"):
            st.write(f"**Difficulty:** {'★'*p['difficulty']}{'☆'*(5-p['difficulty'])}")
            st.write(p["desc"])
    with col2:
        voice_on = st.toggle("🔊 Sponsor voice", value=False)
    st.markdown("---")
    mkey,hkey = f"m_{pid}",f"h_{pid}"
    if mkey not in st.session_state: st.session_state[mkey]=[]
    if hkey not in st.session_state: st.session_state[hkey]=[]
    if "scored" not in st.session_state: st.session_state["scored"]=False
    if "result" not in st.session_state: st.session_state["result"]=None
    if "pending_voice" not in st.session_state: st.session_state["pending_voice"]=None
    msgs = st.session_state[mkey]
    hints = st.session_state[hkey]
    c1,c2 = st.columns([1,4])
    with c1:
        if st.button("🔄 New Session"):
            st.session_state[mkey]=[]
            st.session_state[hkey]=[]
            st.session_state["scored"]=False
            st.session_state["result"]=None
            st.session_state["pending_voice"]=None
            st.rerun()
    with c2:
        turns = sum(1 for m in msgs if m["role"]=="user")
        st.caption(f"💬 {turns} responses — {'ready to score!' if turns>=3 else f'need {3-turns} more to unlock scoring'}")
    if not msgs:
        with st.spinner(f"{p['icon']} Joining the call..."):
            r = get_client().messages.create(model="claude-sonnet-4-6",max_tokens=200,
                system=p["prompt"],messages=[{"role":"user","content":"Begin the meeting now."}])
            opening = r.content[0].text
            msgs.append({"role":"assistant","content":opening})
            st.session_state[mkey]=msgs
            if voice_on: speak_text(opening)
    col_chat,col_side = st.columns([3,1])
    with col_chat:
        for i,m in enumerate(msgs):
            with st.chat_message(m["role"],avatar=p["icon"] if m["role"]=="assistant" else "🎓"):
                st.markdown(m["content"])
            if m["role"]=="user":
                hidx = sum(1 for msg in msgs[:i+1] if msg["role"]=="user")-1
                if hidx < len(hints) and hints[hidx]:
                    st.caption(f"💡 *{hints[hidx]}*")
    with col_side:
        st.markdown("### 📊 Live Stats")
        with st.container(border=True):
            student_msgs = [m for m in msgs if m["role"]=="user"]
            avg_w = round(sum(len(m["content"].split()) for m in student_msgs)/len(student_msgs)) if student_msgs else 0
            st.metric("Responses", len(student_msgs))
            st.metric("Avg words", avg_w)
            if avg_w>80: st.warning("⚠️ Too long!")
            elif avg_w>0: st.success("✅ Good length")
        if hints:
            st.markdown("### 💡 Recent Hints")
            for h in hints[-3:]: st.info(h)

    if not st.session_state["scored"]:
        st.markdown("---")
        st.markdown("#### 🎙️ Record Your Voice")
        st.components.v1.html(VOICE_BTN_HTML, height=90)

        if st.session_state.get("pending_voice"):
            audio_b64 = st.session_state["pending_voice"]
            st.session_state["pending_voice"] = None
            with st.spinner("🎙️ Transcribing your voice..."):
                transcript = transcribe_audio(audio_b64)
            if transcript:
                st.info(f"🎙️ You said: *{transcript}*")
                hint = get_hint(transcript)
                hints.append(hint)
                st.session_state[hkey]=hints
                msgs.append({"role":"user","content":transcript})
                st.session_state[mkey]=msgs
                with st.chat_message("assistant",avatar=p["icon"]):
                    with st.spinner("Responding..."):
                        r = get_client().messages.create(model="claude-sonnet-4-6",max_tokens=300,
                            system=p["prompt"],messages=msgs)
                        reply = r.content[0].text
                        msgs.append({"role":"assistant","content":reply})
                        st.session_state[mkey]=msgs
                        if voice_on: speak_text(reply)
                st.rerun()
            else:
                st.warning("Could not transcribe — check your OpenAI API key or try again.")

        st.markdown("#### ✍️ Or type your message")
        if prompt := st.chat_input("Type your message to the sponsor..."):
            hint = get_hint(prompt)
            hints.append(hint)
            st.session_state[hkey]=hints
            msgs.append({"role":"user","content":prompt})
            st.session_state[mkey]=msgs
            with st.chat_message("assistant",avatar=p["icon"]):
                with st.spinner("Responding..."):
                    r = get_client().messages.create(model="claude-sonnet-4-6",max_tokens=300,
                        system=p["prompt"],messages=msgs)
                    reply = r.content[0].text
                    msgs.append({"role":"assistant","content":reply})
                    st.session_state[mkey]=msgs
                    if voice_on: speak_text(reply)
            st.rerun()

    turns = sum(1 for m in msgs if m["role"]=="user")
    if turns>=3 and not st.session_state["scored"]:
        st.markdown("---")
        if st.button("🏁 End Meeting & Get Score",type="primary",use_container_width=True):
            with st.spinner("Evaluating..."):
                res = do_score(msgs,p["name"])
                st.session_state["result"]=res
                st.session_state["scored"]=True
                if "history" not in st.session_state: st.session_state["history"]=[]
                st.session_state["history"].append({"persona":p["name"],"score":res["total"],"readiness":res["readiness"],"company":p["company"]})
                if res["total"]>best: st.session_state["best_score"]=res["total"]
            st.rerun()

    if st.session_state["scored"] and st.session_state["result"]:
        res = st.session_state["result"]
        total = res["total"]
        st.markdown("---")
        st.markdown("## 🏆 Your Results")
        color = "green" if total>=80 else "orange" if total>=60 else "red"
        st.markdown(f"### Score: :{color}[{total}/100]")
        st.progress(total/100)
        if total>=80: st.success("✅ CERTIFIED — Ready for your real sponsor meeting!")
        elif total>=60: st.warning("⚠️ Almost there — keep practicing.")
        else: st.error("❌ Keep practicing.")
        if res.get("top_tip"): st.markdown(f"### 🎯 Top Priority: *{res['top_tip']}*")
        st.markdown("---")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Preparation",f"{res['preparation']}/25")
        c2.metric("Communication",f"{res['communication']}/25")
        c3.metric("Meeting Mgmt",f"{res['meeting_management']}/25")
        c4.metric("Relationship",f"{res['relationship_building']}/25")
        if st.session_state.get("facial_result"):
            st.markdown("---")
            st.markdown("### 🎯 Combined Score")
            body = st.session_state["facial_result"].get("total",0)
            combined = round((total+body)/2)
            color2 = "green" if combined>=80 else "orange" if combined>=60 else "red"
            st.markdown(f"**Content:** {total}/100 | **Body Language:** {body}/100 | **Combined: :{color2}[{combined}/100]**")
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
            st.session_state[mkey]=[]
            st.session_state[hkey]=[]
            st.session_state["scored"]=False
            st.session_state["result"]=None
            st.rerun()

elif page == "📈 My Progress":
    st.title("📈 My Progress")
    st.markdown("---")
    history = st.session_state.get("history",[])
    video_history = st.session_state.get("video_history",[])
    if not history and not video_history:
        st.info("No sessions yet! Go to Practice Session or Video Practice to get started.")
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
            st.markdown("### 🎯 Readiness")
            st.progress(min(best/80,1.0))
            if best>=80: st.success("✅ CERTIFIED — Ready for your real sponsor meeting!")
            else: st.warning(f"Need {80-best} more points. Best: {best}/100")
            st.markdown("---")
            st.markdown("### 📋 Practice Session History")
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
                    st.caption(v.get('summary',''))

elif page == "ℹ️ About":
    st.title("ℹ️ About Voice & Design")
    st.markdown("---")
    st.markdown("""
## 🎙️ Voice & Design
AI-powered Yoodli-style sponsor meeting simulator for UChicago ADS Capstone students.

### Features
- 💬 Text chat with 5 AI sponsor personas
- 🎙️ Voice record button — speak to your sponsor
- 🔊 Sponsor speaks back with OpenAI TTS
- 📹 Record your interview practice session
- 😊 AI analyzes facial expressions and body language
- 💡 Live coaching hints after every message
- 📊 Combined content + body language score report
- 🏆 Get certified meeting-ready at 80+

### Tech Stack
- Streamlit · Claude API · OpenAI Whisper · OpenAI TTS · Claude Vision API

### Built For
UChicago Master of Applied Data Science — Capstone Program
""")
