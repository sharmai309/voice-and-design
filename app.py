import streamlit as st
import os, json, base64, tempfile
from anthropic import Anthropic

st.set_page_config(page_title="Voice & Design", page_icon="🎙️", layout="wide")

def get_client():
    try:
        key = st.secrets["ANTHROPIC_API_KEY"]
    except:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
    return Anthropic(api_key=key)

PERSONAS = {
    "mentor": {
        "name": "Mentor Sponsor", "icon": "🌱", "difficulty": 1,
        "company": "HealthTech Analytics", "role": "Dr. Sarah Chen, Senior Director of Analytics",
        "desc": "Encouraging and supportive. Great for your first attempt.",
        "background": "HealthTech Analytics is a mid-sized healthcare data company helping hospitals reduce patient readmission rates.",
        "prompt": """You are Dr. Sarah Chen, Senior Director of Analytics at HealthTech Analytics, acting as a MENTOR SPONSOR for a UChicago Capstone team.

COMPANY CONTEXT TO SHARE: HealthTech Analytics helps hospitals reduce patient readmission rates using predictive analytics. The students are building a model to predict which patients are likely to be readmitted within 30 days.

PERSONALITY: Warm, encouraging, patient. Ask guiding questions. Give hints when students seem stuck. Celebrate small wins.

LIVE COACHING: After each student response, briefly acknowledge what they did well before asking your next question. Keep responses 2-4 sentences.

GUIDED QUESTIONS TO ASK (in order, naturally):
1. Ask students to introduce themselves and their roles on the team
2. Ask what they understand about the business problem so far
3. Ask what data sources they plan to use
4. Ask how they plan to measure success
5. Ask what their biggest challenge is so far

START by saying: Hi team, so glad we could connect today. I have been looking forward to this. Go ahead and introduce yourselves and tell me your roles on the team."""
    },
    "executive": {
        "name": "Busy Executive", "icon": "⚡", "difficulty": 4,
        "company": "FastShip Logistics", "role": "Marcus Webb, VP of Operations",
        "desc": "Time-pressed and terse. Get to the point fast.",
        "background": "FastShip Logistics is a large e-commerce fulfillment company optimizing delivery routes.",
        "prompt": """You are Marcus Webb, VP of Operations at FastShip Logistics, acting as a BUSY EXECUTIVE SPONSOR.

COMPANY CONTEXT: FastShip moves 2 million packages daily. Students are optimizing delivery route efficiency to cut costs by 15%.

PERSONALITY: Always pressed for time. Short 1-3 sentence answers. Interrupt ramblers. Demand bottom-line answers.

LIVE COACHING: If a student gives a crisp answer, say so briefly. If they ramble, cut them off.

GUIDED QUESTIONS (rapid fire):
1. Who is leading this project?
2. What is the one metric you are optimizing for?
3. What data do you have access to?
4. What is your timeline?
5. What do you need from me specifically?

START by saying: Alright, I have exactly 10 minutes. Who is leading this and what is the single most important thing you need from me today?"""
    },
    "skeptic": {
        "name": "Skeptical Sponsor", "icon": "🔍", "difficulty": 5,
        "company": "Verizon", "role": "Dr. Raj Patel, Chief Data Officer",
        "desc": "Challenges every assumption. Come with evidence.",
        "background": "Verizon is optimizing credit approval for new post-paid contracts to reduce default rates while maximizing subscriber growth.",
        "prompt": """You are Dr. Raj Patel, CDO at Verizon, acting as a SKEPTICAL SPONSOR.

COMPANY CONTEXT TO SHARE: At Verizon, when a customer defaults on a post-paid contract, we lose not just the monthly service fee but often a $1000+ subsidized smartphone. Our model must balance stopping bad debt versus pushing good customers to T-Mobile. FCRA/ECOA regulations mean we cannot use age, race, or gender as features.

PERSONALITY: Question every assumption. Push back firmly. Not impressed by buzzwords. Demand evidence and business justification.

LIVE COACHING: When students handle pushback well, acknowledge it briefly before pushing harder.

GUIDED QUESTIONS (challenging):
1. How are you defining default in your dataset?
2. What features are you considering and why?
3. How will you handle regulatory compliance?
4. What is your success metric beyond accuracy?
5. How does your model translate to dollars saved versus revenue lost?

START by saying: I reviewed your project brief. Before we get into the fun stuff, I need to understand your fundamentals. How are you defining what counts as a default in your dataset?"""
    },
    "technical": {
        "name": "Technical Expert", "icon": "💻", "difficulty": 4,
        "company": "BioSight Research", "role": "Dr. Aisha Okafor, Director of Data Science",
        "desc": "Deep dives into methodology. Know your data.",
        "background": "BioSight Research uses ML to identify early cancer biomarkers from genomic data.",
        "prompt": """You are Dr. Aisha Okafor, Director of Data Science at BioSight Research, acting as a TECHNICAL EXPERT SPONSOR.

COMPANY CONTEXT TO SHARE: BioSight analyzes genomic sequences to identify early cancer biomarkers. The dataset has 50,000 patient records with 200+ features but significant class imbalance, only 3% positive cases.

PERSONALITY: Deep technical rigor. Use proper ML terminology. Get excited by genuine depth. Unimpressed by surface answers.

LIVE COACHING: When students show technical depth, praise it and go deeper. When they are vague, push immediately.

GUIDED QUESTIONS (technical):
1. What does your data pipeline look like end to end?
2. How are you handling the class imbalance problem?
3. What is your train/test/validation split strategy?
4. Why did you choose that model over simpler alternatives?
5. How are you preventing data leakage?

START by saying: Great to meet you all. I have looked at the dataset you will be working with. Before we discuss deliverables, walk me through your data pipeline. What does it look like from raw data to model input?"""
    },
    "collaborator": {
        "name": "Open Collaborator", "icon": "💡", "difficulty": 2,
        "company": "TrendBox", "role": "Jamie Torres, Director of Innovation",
        "desc": "Loves ideas but needs you to manage the agenda.",
        "background": "TrendBox is a consumer goods startup using AI to predict product trends and optimize inventory.",
        "prompt": """You are Jamie Torres, Director of Innovation at TrendBox, acting as an OPEN COLLABORATOR SPONSOR.

COMPANY CONTEXT TO SHARE: TrendBox predicts viral product trends on social media and pre-positions inventory. We have social media data, sales history, and supplier lead times. The problem is exciting but scope can balloon quickly.

PERSONALITY: Love brainstorming. Go on tangents. Add scope creep naturally. Enthusiastic. Let students lead.

LIVE COACHING: Praise students who manage the agenda well. Reward those who diplomatically push back on scope creep.

GUIDED QUESTIONS (open-ended):
1. What excites you most about this project?
2. Have you thought about also incorporating social media sentiment?
3. What if we also added supplier risk scoring?
4. How are you planning to structure your meetings?
5. What do you need from me to get started?

START by saying: Oh my gosh I am SO excited you are here! I have about 15 ideas I want to share but first, tell me, what excites YOU most about this project? I want to hear your fresh perspective."""
    }
}

HINT_PROMPT = """You are a real-time coach watching a student practice a sponsor meeting. 
After each student message, give ONE short coaching hint (max 15 words) about what they just did well OR one thing to improve immediately.
Format: emoji + hint. Examples:
✅ Great intro! You stated your name and role clearly.
⚠️ Missing agenda — tell the sponsor what you plan to cover today.
💡 Good question! Follow up by asking about their timeline.
❌ Too vague — give a specific example or data point.

Student just said: """

SCORE_PROMPT = """Evaluate this Capstone sponsor meeting. Score 0-25 each (total 100):
1. PREPARATION: Research, agenda, informed questions
2. COMMUNICATION: Clear, concise, professional
3. MEETING MANAGEMENT: Introductions, agenda, next steps confirmed
4. RELATIONSHIP BUILDING: Active listening, rapport, empathy

Return ONLY this JSON, no other text:
{"preparation":0,"communication":0,"meeting_management":0,"relationship_building":0,"total":0,"strengths":["s1","s2"],"improvements":["i1","i2"],"missed_opportunities":["m1"],"readiness":"Not Ready","summary":"2-3 sentence assessment","top_tip":"single most important thing to practice"}

CONVERSATION:
"""

def get_hint(student_msg):
    try:
        r = get_client().messages.create(
            model="claude-sonnet-4-6", max_tokens=60,
            messages=[{"role":"user","content":HINT_PROMPT+student_msg}]
        )
        return r.content[0].text.strip()
    except:
        return ""

def do_score(msgs, pname):
    convo = ""
    for m in msgs:
        convo += f"{'STUDENT' if m['role']=='user' else 'SPONSOR'}: {m['content']}\n\n"
    r = get_client().messages.create(
        model="claude-sonnet-4-6", max_tokens=800,
        messages=[{"role":"user","content":SCORE_PROMPT+convo}]
    )
    raw = r.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    return json.loads(raw.strip())

def speak(text):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY",""))
        resp = client.audio.speech.create(model="tts-1", voice="nova", input=text[:500])
        audio_bytes = resp.content
        b64 = base64.b64encode(audio_bytes).decode()
        audio_html = f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
        st.markdown(audio_html, unsafe_allow_html=True)
    except:
        pass

st.sidebar.title("🎙️ Voice & Design")
st.sidebar.markdown("---")
page = st.sidebar.radio("", ["🏠 Home","💬 Practice Session","📈 My Progress","ℹ️ About"])
st.sidebar.markdown("---")
best = st.session_state.get("best_score",0)
st.sidebar.metric("Best Score", f"{best}/100")
if best >= 80:
    st.sidebar.success("✅ Meeting Ready!")
else:
    st.sidebar.progress(min(best/80,1.0))
    st.sidebar.caption(f"Need {80-best} more points to unlock real meeting")
st.sidebar.markdown("---")
st.sidebar.caption("UChicago ADS Capstone Project")

if page == "🏠 Home":
    st.title("🎙️ Voice & Design")
    st.markdown("### Practice your sponsor meetings. Get real-time coaching. Ace the real thing.")
    st.markdown("---")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Sponsor Personas","5")
    c2.metric("Scoring Dimensions","4")
    c3.metric("Live Hints","✅ On")
    c4.metric("Your Best Score",f"{st.session_state.get('best_score',0)}/100")
    st.markdown("---")
    st.markdown("## 🎯 How It Works")
    col1,col2,col3,col4 = st.columns(4)
    with col1:
        with st.container(border=True):
            st.markdown("### 1️⃣")
            st.markdown("**Choose a sponsor** from 5 different personas — from supportive mentor to tough skeptic")
    with col2:
        with st.container(border=True):
            st.markdown("### 2️⃣")
            st.markdown("**Practice the meeting** by typing or speaking — the sponsor responds in character")
    with col3:
        with st.container(border=True):
            st.markdown("### 3️⃣")
            st.markdown("**Get live hints** after every message so you improve in real time")
    with col4:
        with st.container(border=True):
            st.markdown("### 4️⃣")
            st.markdown("**See your score** across 4 dimensions and get certified meeting-ready at 80+")
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
    st.info("💡 **Tip:** Start with the Mentor Sponsor (🌱) to build confidence, then tackle the Skeptic (🔍) before your real meeting.")

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
            st.markdown(f"**Role:** {p['role']}")
            st.markdown(f"**Difficulty:** {'★'*p['difficulty']}{'☆'*(5-p['difficulty'])}")
            st.markdown(f"**Company background:** {p['background']}")
    with col2:
        voice_on = st.toggle("🔊 Voice mode", value=False, help="Requires OpenAI API key in secrets.toml")

    st.markdown("---")
    mkey = f"m_{pid}"
    hkey = f"h_{pid}"
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
        st.caption(f"💬 {turns} responses so far {'— ready to score! Click below.' if turns>=3 else f'— need {3-turns} more to unlock scoring'}")

    if not msgs:
        with st.spinner(f"{p['icon']} {p['name']} is joining the call..."):
            r = get_client().messages.create(
                model="claude-sonnet-4-6", max_tokens=200,
                system=p["prompt"],
                messages=[{"role":"user","content":"Begin the meeting now."}]
            )
            opening = r.content[0].text
            msgs.append({"role":"assistant","content":opening})
            st.session_state[mkey]=msgs
            if voice_on: speak(opening)

    col_chat, col_hints = st.columns([3,1])
    with col_chat:
        for i,m in enumerate(msgs):
            with st.chat_message(m["role"], avatar=p["icon"] if m["role"]=="assistant" else "🎓"):
                st.markdown(m["content"])
            if m["role"]=="user" and i//2 < len(hints):
                hint_idx = sum(1 for msg in msgs[:i+1] if msg["role"]=="user")-1
                if hint_idx < len(hints) and hints[hint_idx]:
                    st.caption(f"💡 *Coach: {hints[hint_idx]}*")

    with col_hints:
        st.markdown("### 📊 Live Stats")
        with st.container(border=True):
            student_msgs = [m for m in msgs if m["role"]=="user"]
            total_words = sum(len(m["content"].split()) for m in student_msgs)
            avg_words = round(total_words/len(student_msgs)) if student_msgs else 0
            st.metric("Responses", len(student_msgs))
            st.metric("Avg words/response", avg_words)
            if avg_words > 80:
                st.warning("⚠️ Too long! Aim for under 60 words.")
            elif avg_words > 0:
                st.success("✅ Good length!")
        if hints:
            st.markdown("### 💡 Recent Hints")
            for h in hints[-3:]:
                st.info(h)

    if turns>=3 and not st.session_state["scored"]:
        st.markdown("---")
        if st.button("🏁 End Meeting & Get Full Score",type="primary",use_container_width=True):
            with st.spinner("Evaluating your full performance..."):
                res = do_score(msgs,p["name"])
                st.session_state["result"]=res
                st.session_state["scored"]=True
                if "history" not in st.session_state: st.session_state["history"]=[]
                st.session_state["history"].append({
                    "persona":p["name"],"score":res["total"],
                    "readiness":res["readiness"],"company":p["company"]
                })
                best = st.session_state.get("best_score",0)
                if res["total"]>best: st.session_state["best_score"]=res["total"]
            st.rerun()

    if st.session_state["scored"] and st.session_state["result"]:
        res = st.session_state["result"]
        total = res["total"]
        st.markdown("---")
        st.markdown("## 🏆 Your Full Report")
        color = "green" if total>=80 else "orange" if total>=60 else "red"
        st.markdown(f"### Final Score: :{color}[{total}/100]")
        st.progress(total/100)
        if total>=80: st.success("✅ CERTIFIED — You are ready for your real sponsor meeting!")
        elif total>=60: st.warning("⚠️ Almost there — a bit more practice and you will be ready.")
        else: st.error("❌ Keep practicing — focus on the improvements below.")
        st.markdown("---")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Preparation",f"{res['preparation']}/25")
        c2.metric("Communication",f"{res['communication']}/25")
        c3.metric("Meeting Mgmt",f"{res['meeting_management']}/25")
        c4.metric("Relationship",f"{res['relationship_building']}/25")
        st.markdown("---")
        if res.get("top_tip"):
            st.markdown(f"### 🎯 Your #1 Priority: *{res['top_tip']}*")
        cl,cr = st.columns(2)
        with cl:
            st.markdown("#### ✅ What You Did Well")
            for s in res.get("strengths",[]): st.success(s)
        with cr:
            st.markdown("#### ⚠️ What To Improve")
            for i in res.get("improvements",[]): st.warning(i)
        if res.get("missed_opportunities"):
            st.markdown("#### ❌ Missed Opportunities")
            for m in res["missed_opportunities"]: st.error(m)
        st.info(f"**Overall:** {res.get('summary','')}")
        st.markdown("---")
        if st.button("🔄 Practice Again",use_container_width=True):
            st.session_state[mkey]=[]
            st.session_state[hkey]=[]
            st.session_state["scored"]=False
            st.session_state["result"]=None
            st.rerun()

    if not st.session_state["scored"]:
        prompt = st.chat_input("Type your response to the sponsor... (or enable voice mode above)")
        if prompt:
            hint = get_hint(prompt)
            hints.append(hint)
            st.session_state[hkey]=hints
            msgs.append({"role":"user","content":prompt})
            st.session_state[mkey]=msgs
            with st.chat_message("assistant",avatar=p["icon"]):
                with st.spinner(f"{p['name']} is responding..."):
                    r = get_client().messages.create(
                        model="claude-sonnet-4-6", max_tokens=300,
                        system=p["prompt"], messages=msgs
                    )
                    reply = r.content[0].text
                    msgs.append({"role":"assistant","content":reply})
                    st.session_state[mkey]=msgs
                    st.markdown(reply)
                    if voice_on: speak(reply)
            st.rerun()

elif page == "📈 My Progress":
    st.title("📈 My Progress")
    st.markdown("---")
    history = st.session_state.get("history",[])
    if not history:
        st.info("No sessions yet! Go to Practice Session to get started.")
    else:
        best = st.session_state.get("best_score",0)
        avg = round(sum(h["score"] for h in history)/len(history))
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total Sessions",len(history))
        c2.metric("Best Score",f"{best}/100")
        c3.metric("Average Score",f"{avg}/100")
        c4.metric("Times Certified",sum(1 for h in history if h["readiness"]=="Ready"))
        st.markdown("---")
        st.markdown("### 🎯 Readiness Tracker")
        st.progress(min(best/80,1.0))
        if best>=80: st.success("✅ CERTIFIED — You are ready for your real sponsor meeting!")
        else: st.warning(f"Need {80-best} more points to get certified. Best so far: {best}/100")
        st.markdown("---")
        st.markdown("### 📋 Session History")
        for i,h in enumerate(reversed(history),1):
            with st.container(border=True):
                c1,c2,c3,c4 = st.columns([2,2,2,2])
                c1.markdown(f"**Session {len(history)-i+1}**")
                c2.markdown(f"🏢 {h.get('company',h['persona'])}")
                c3.markdown(f"Score: **{h['score']}/100**")
                color = "green" if h["readiness"]=="Ready" else "orange" if h["readiness"]=="Almost Ready" else "red"
                c4.markdown(f":{color}[{h['readiness']}]")
        st.markdown("---")
        st.markdown("### 📚 Tips To Improve")
        tips = {
            "Preparation":"Research your sponsor company before the meeting. Have 3 specific questions ready.",
            "Communication":"Keep answers under 60 words. Lead with your main point, then support it.",
            "Meeting Management":"Always start with introductions, state an agenda, and confirm next steps before ending.",
            "Relationship Building":"Use the sponsor name, reference what they said earlier, show genuine curiosity."
        }
        for title,tip in tips.items():
            with st.expander(f"How to improve: {title}"):
                st.markdown(tip)

elif page == "ℹ️ About":
    st.title("ℹ️ About Voice & Design")
    st.markdown("---")
    st.markdown("""
## 🎙️ Voice & Design — Sponsor Meeting Simulator

An AI-powered Yoodli-style tool helping UChicago ADS Capstone students practice sponsor meetings with real-time coaching and voice capability.

### How It Works
1. **Choose** one of 5 AI sponsor personas
2. **Practice** by typing or speaking to the sponsor
3. **Get live hints** after every single message
4. **See your full report** with scores across 4 dimensions
5. **Hit 80/100** to get certified as meeting-ready

### Features
- 🎙️ Voice mode — hear the sponsor respond out loud
- 💡 Live coaching hints after every message
- 📊 Real-time stats (response length, turn count)
- 🏆 Full scoring report with strengths and improvements
- 🎯 Top priority tip to focus your next practice

### Tech Stack
- **Frontend:** Streamlit
- **AI Brain:** Claude API (claude-sonnet-4-6) by Anthropic
- **Voice:** OpenAI TTS (text-to-speech)
- **Scoring:** Structured JSON evaluation

### Sponsor Personas
| Persona | Company | Difficulty |
|---|---|---|
| 🌱 Mentor | HealthTech Analytics | ★☆☆☆☆ |
| ⚡ Busy Executive | FastShip Logistics | ★★★★☆ |
| 🔍 Skeptical Sponsor | Verizon | ★★★★★ |
| 💻 Technical Expert | BioSight Research | ★★★★☆ |
| 💡 Open Collaborator | TrendBox | ★★☆☆☆ |

### Roadmap
- [ ] Microphone input (speak your answers)
- [ ] Team meeting simulation
- [ ] Persistent score database
- [ ] Instructor dashboard

### Built For
UChicago Master of Applied Data Science — Capstone Program
""")
