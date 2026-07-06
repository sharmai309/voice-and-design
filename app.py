import streamlit as st
import os, json, base64, cv2, tempfile, time
from anthropic import Anthropic
from PIL import Image
import numpy as np

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

FACIAL_PROMPT = """You are an expert communication coach analyzing a student during a sponsor meeting practice.
Look at this image carefully and evaluate:

1. EYE CONTACT (0-25): Are they looking at the camera/screen? Sustained eye contact shows engagement.
2. CONFIDENCE (0-25): Posture, facial expression, does the person look confident or nervous?
3. ENGAGEMENT (0-25): Do they look interested and present, or distracted/disengaged?
4. PROFESSIONALISM (0-25): Is their appearance and setting appropriate for a sponsor meeting?

Return ONLY this JSON:
{
  "eye_contact": 0,
  "confidence": 0,
  "engagement": 0,
  "professionalism": 0,
  "total": 0,
  "observations": ["observation 1", "observation 2", "observation 3"],
  "improvements": ["improvement 1", "improvement 2"],
  "summary": "2-3 sentence overall body language assessment"
}"""

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

def analyze_facial_expression(image_bytes):
    try:
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        r = get_client().messages.create(
            model="claude-sonnet-4-6", max_tokens=600,
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
        return None

def speak_text(text):
    try:
        from openai import OpenAI
        oai = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY",""))
        resp = oai.audio.speech.create(model="tts-1", voice="nova", input=text[:500])
        b64 = base64.b64encode(resp.content).decode()
        st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    except: pass

VOICE_HTML = """
<div style="background:var(--surface-1,#f8f9fa);border:1px solid #dee2e6;border-radius:12px;padding:16px;margin-bottom:8px;">
  <div style="display:flex;align-items:center;gap:12px;">
    <button id="micBtn" onclick="toggleRecording()" style="width:48px;height:48px;border-radius:50%;border:none;background:#1D9E75;color:white;font-size:20px;cursor:pointer;">🎙️</button>
    <div>
      <div style="font-weight:500;font-size:14px;" id="micStatus">Click mic to speak</div>
      <div style="font-size:12px;color:gray;" id="transcript"></div>
    </div>
  </div>
</div>
<script>
let mediaRecorder, audioChunks=[], isRecording=false;
async function toggleRecording(){
  if(!isRecording){
    const stream=await navigator.mediaDevices.getUserMedia({audio:true});
    mediaRecorder=new MediaRecorder(stream);
    audioChunks=[];
    mediaRecorder.ondataavailable=e=>audioChunks.push(e.data);
    mediaRecorder.onstop=async()=>{
      const blob=new Blob(audioChunks,{type:"audio/webm"});
      const reader=new FileReader();
      reader.onloadend=()=>{
        const b64=reader.result.split(",")[1];
        window.parent.postMessage({type:"audio",data:b64},"*");
        document.getElementById("transcript").textContent="Processing...";
      };
      reader.readAsDataURL(blob);
    };
    mediaRecorder.start();
    isRecording=true;
    document.getElementById("micBtn").style.background="#D85A30";
    document.getElementById("micBtn").textContent="⏹️";
    document.getElementById("micStatus").textContent="Recording... click to stop";
  } else {
    mediaRecorder.stop();
    isRecording=false;
    document.getElementById("micBtn").style.background="#1D9E75";
    document.getElementById("micBtn").textContent="🎙️";
    document.getElementById("micStatus").textContent="Click mic to speak";
  }
}
</script>
"""

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
            st.markdown("**Speak or type** — sponsor responds in character")
    with c3:
        with st.container(border=True):
            st.markdown("### 3️⃣")
            st.markdown("**Record video** — AI analyzes your facial expressions")
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
    st.markdown("Record yourself during practice and get AI feedback on your body language.")
    st.markdown("---")

    names = {v["name"]:k for k,v in PERSONAS.items()}
    default = st.session_state.get("pid","mentor")
    sel = st.selectbox("Choose your sponsor",list(names.keys()),
        index=list(names.keys()).index(PERSONAS[default]["name"]))
    pid = names[sel]
    p = PERSONAS[pid]

    st.markdown("---")
    st.markdown("### 📸 Step 1 — Take a snapshot for analysis")
    st.info("💡 Tip: Sit upright, look at your camera, good lighting. Then click the button below.")

    img_file = st.camera_input("📷 Take a photo to analyze your body language")

    if img_file:
        col1, col2 = st.columns([1,1])
        with col1:
            st.image(img_file, caption="Your snapshot", use_container_width=True)

        with col2:
            if st.button("🤖 Analyze My Body Language", type="primary", use_container_width=True):
                with st.spinner("Claude is analyzing your facial expressions and body language..."):
                    image_bytes = img_file.getvalue()
                    result = analyze_facial_expression(image_bytes)

                if result:
                    st.session_state["facial_result"] = result
                    st.success("Analysis complete!")
                else:
                    st.error("Analysis failed — check your API key.")

    if st.session_state.get("facial_result"):
        result = st.session_state["facial_result"]
        st.markdown("---")
        st.markdown("## 😊 Body Language Report")

        total = result.get("total", 0)
        color = "green" if total>=80 else "orange" if total>=60 else "red"
        st.markdown(f"### Body Language Score: :{color}[{total}/100]")
        st.progress(total/100)

        st.markdown("---")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("👁️ Eye Contact", f"{result.get('eye_contact',0)}/25")
        c2.metric("💪 Confidence", f"{result.get('confidence',0)}/25")
        c3.metric("🎯 Engagement", f"{result.get('engagement',0)}/25")
        c4.metric("👔 Professionalism", f"{result.get('professionalism',0)}/25")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### ✅ What You Did Well")
            for obs in result.get("observations", []):
                st.success(obs)
        with col2:
            st.markdown("#### ⚠️ What To Improve")
            for imp in result.get("improvements", []):
                st.warning(imp)

        st.markdown("---")
        st.info(f"**Overall:** {result.get('summary','')}")

        st.markdown("---")
        st.markdown("### 💡 Quick Tips Based On Your Analysis")
        tips = {
            "eye_contact": ("👁️ Eye Contact","Look directly at your webcam — not at your own face on screen. Put a sticky note arrow pointing at the camera lens."),
            "confidence": ("💪 Confidence","Sit up straight, shoulders back. Take a deep breath before speaking. Speak slowly and pause between points."),
            "engagement": ("🎯 Engagement","Nod occasionally when the sponsor speaks. Lean slightly forward to show interest. Smile naturally."),
            "professionalism": ("👔 Professionalism","Use a clean, simple background. Good lighting from the front. Dress as you would for the real meeting.")
        }
        for key,(title,tip) in tips.items():
            score = result.get(key,0)
            if score < 20:
                with st.expander(f"🔴 Improve: {title} ({score}/25)"):
                    st.markdown(tip)
            elif score < 22:
                with st.expander(f"🟡 Refine: {title} ({score}/25)"):
                    st.markdown(tip)

        st.markdown("---")
        st.markdown("### 📥 Save Your Results")
        if "video_history" not in st.session_state:
            st.session_state["video_history"] = []
        if st.button("💾 Save This Analysis To My Progress"):
            st.session_state["video_history"].append({
                "persona": p["name"],
                "score": total,
                "summary": result.get("summary",""),
                "timestamp": time.strftime("%Y-%m-%d %H:%M")
            })
            st.success("Saved! Check My Progress page.")

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
    msgs = st.session_state[mkey]
    hints = st.session_state[hkey]

    c1,c2 = st.columns([1,4])
    with c1:
        if st.button("🔄 New Session"):
            st.session_state[mkey]=[]
            st.session_state[hkey]=[]
            st.session_state["scored"]=False
            st.session_state["result"]=None
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
        st.markdown("---")
        st.markdown("### 📹 Body Language")
        if st.button("📸 Analyze Me Now", use_container_width=True):
            st.session_state["go_to_video"] = True
            st.info("Go to 📹 Video Practice page!")

    if not st.session_state["scored"]:
        st.markdown("---")
        st.markdown("#### 🎙️ Voice Input")
        st.components.v1.html(VOICE_HTML, height=100)
        st.markdown("#### ✍️ Or type your response")
        if prompt := st.chat_input("Type your message..."):
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
            st.markdown("### 😊 Combined Score (Content + Body Language)")
            content_score = total
            body_score = st.session_state["facial_result"].get("total",0)
            combined = round((content_score + body_score) / 2)
            color2 = "green" if combined>=80 else "orange" if combined>=60 else "red"
            st.markdown(f"### Combined: :{color2}[{combined}/100]")
            c1,c2 = st.columns(2)
            c1.metric("Content Score", f"{content_score}/100")
            c2.metric("Body Language", f"{body_score}/100")

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
            st.markdown("### 🎯 Readiness")
            st.progress(min(best/80,1.0))
            if best>=80: st.success("✅ CERTIFIED — Ready for your real sponsor meeting!")
            else: st.warning(f"Need {80-best} more points. Best: {best}/100")
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
                    c1,c2,c3 = st.columns([2,2,3])
                    c1.write(f"**{v['timestamp']}**")
                    c2.write(f"Body language: **{v['score']}/100**")
                    c3.write(v['summary'])

elif page == "ℹ️ About":
    st.title("ℹ️ About Voice & Design")
    st.markdown("---")
    st.markdown("""
## 🎙️ Voice & Design
AI-powered Yoodli-style sponsor meeting simulator for UChicago ADS Capstone students.

### Features
- 🎙️ Speak to your sponsor — Whisper transcribes your voice
- 🔊 Hear sponsor respond — OpenAI TTS voice
- 📹 Video practice — AI analyzes facial expressions
- 👁️ Eye contact + confidence + engagement scores
- 💡 Live coaching hints after every message
- 📊 Combined content + body language score
- 🏆 Get certified meeting-ready at 80+

### Tech Stack
- Streamlit · Claude API · OpenAI Whisper · OpenAI TTS · Claude Vision

### Built For
UChicago Master of Applied Data Science — Capstone Program
""")
