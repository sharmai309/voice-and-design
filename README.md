# 🎙️ Voice & Design — AI Sponsor Meeting Simulator

> Practice your Capstone sponsor meetings with AI personas, get real-time coaching, record your body language, and get certified meeting-ready — before the real thing.

**🌐 Live App:** https://voice-and-design-hejgggfxzekbldp5vxp6sh.streamlit.app

**📁 GitHub:** https://github.com/sharmai309/voice-and-design

---

## 🎯 What Is This?

Voice & Design is a Yoodli-inspired AI-powered simulator that helps UChicago Applied Data Science Capstone students practice sponsor meetings before the real thing.

Students interact with 5 different AI sponsor personas, receive live coaching hints after every message, record themselves on webcam, and get scored across 4 communication dimensions. Hit 80/100 to get certified meeting-ready.

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **Text Chat** | Type responses to your AI sponsor in a realistic meeting format |
| 🎙️ **Voice Input** | Speak to your sponsor — Whisper AI transcribes your speech |
| 🔊 **Sponsor Voice** | Sponsor responds out loud using OpenAI TTS |
| 📹 **Video Recording** | Record yourself during practice sessions and download the video |
| 😊 **Facial Analysis** | Claude Vision analyzes eye contact, confidence, engagement, professionalism |
| 💡 **Live Coaching** | Real-time coaching hint after every single message |
| 📊 **Score Report** | Full evaluation across 4 dimensions with strengths and improvements |
| 🏆 **Certification** | Hit 80/100 to be certified ready for your real sponsor meeting |

---

## 👥 Sponsor Personas

| Persona | Company | Difficulty | Description |
|---|---|---|---|
| 🌱 Mentor Sponsor | HealthTech Analytics | Beginner ⭐ | Warm and encouraging. Guides with questions. |
| 💡 Open Collaborator | TrendBox | Moderate ⭐⭐ | Loves ideas. Goes on tangents. Needs agenda management. |
| ⚡ Busy Executive | FastShip Logistics | Hard ⭐⭐⭐⭐ | Time-pressed. Get to the point or get cut off. |
| 💻 Technical Expert | BioSight Research | Hard ⭐⭐⭐⭐ | Deep dives into methodology and data fluency. |
| 🔍 Skeptical Sponsor | Verizon | Expert ⭐⭐⭐⭐⭐ | Questions everything. Demands evidence. |

---

## 📊 Scoring Dimensions

Each session is scored out of 100 across 4 dimensions (25 points each):

| Dimension | What It Measures |
|---|---|
| **Preparation** | Did you research the sponsor? Have an agenda? Ask informed questions? |
| **Communication** | Were you clear, concise, and professional? |
| **Meeting Management** | Did you introduce yourself, set an agenda, confirm next steps? |
| **Relationship Building** | Did you listen actively and build genuine rapport? |

**Score 80+ to get certified as meeting-ready!**

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Streamlit | Web interface and deployment |
| Claude API (claude-sonnet-4-6) | AI sponsor personas + scoring engine |
| Claude Vision API | Facial expression and body language analysis |
| OpenAI Whisper | Speech-to-text transcription |
| OpenAI TTS | Sponsor voice responses |
| Streamlit Cloud | Free public deployment |

---

## 🚀 Run Locally

### 1. Clone the repo
`bash
git clone https://github.com/sharmai309/voice-and-design.git
cd voice-and-design
`

### 2. Create virtual environment
`bash
# Windows
python -m venv venv
venv\Scripts\Activate.ps1

# Mac/Linux
python -m venv venv
source venv/bin/activate
`

### 3. Install dependencies
`bash
pip install -r requirements.txt
`

### 4. Add your API keys
Create .streamlit/secrets.toml:
`toml
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
OPENAI_API_KEY = "sk-your-openai-key-here"
`

Get your keys:
- Anthropic: https://console.anthropic.com
- OpenAI: https://platform.openai.com/api-keys

### 5. Run the app
`bash
streamlit run app.py
`

Open http://localhost:8501 in your browser.

---

## ☁️ Deployed On Streamlit Cloud

This app is deployed for free on Streamlit Cloud.

**Public URL:** https://voice-and-design-hejgggfxzekbldp5vxp6sh.streamlit.app

To deploy your own copy:
1. Fork this repo
2. Go to https://share.streamlit.io
3. Connect your GitHub repo
4. Set main file to pp.py
5. Add your API keys in Advanced Settings → Secrets
6. Click Deploy

---

## 📁 Project Structure

`
voice-and-design/
├── app.py                  # Full application — all pages in one file
├── requirements.txt        # Python dependencies
├── .gitignore              # Excludes secrets.toml and venv
├── README.md               # This file
└── .streamlit/
    └── secrets.toml        # API keys (never committed to GitHub)
`

---

## 🗺️ Roadmap

- [x] 5 AI sponsor personas with real company backgrounds
- [x] Live coaching hints after every message
- [x] Voice input via OpenAI Whisper
- [x] Sponsor voice output via OpenAI TTS
- [x] Video recording with webcam download
- [x] Facial expression and body language analysis via Claude Vision
- [x] Session scoring across 4 dimensions
- [x] Combined content + body language score
- [x] Yoodli-style design with gradient UI
- [ ] Persistent score database (Supabase)
- [ ] Multi-student team meeting simulation
- [ ] Instructor dashboard
- [ ] OpenAI Realtime API for live voice conversation

---

## 📸 How To Use

1. **Open the app** at https://voice-and-design-hejgggfxzekbldp5vxp6sh.streamlit.app
2. **Choose a sponsor** — start with 🌱 Mentor, work up to 🔍 Skeptic
3. **Practice** — type or click the mic to speak
4. **Watch live hints** appear after each message
5. **Go to Video Practice** to record yourself and get body language feedback
6. **End the meeting** after 3+ responses to see your full score report
7. **Hit 80/100** to get certified meeting-ready!

---

## 🎓 Built For

**University of Chicago**
Master of Applied Data Science — Capstone Program

AI Communication Practice Tool inspired by Yoodli.ai

---

## 📄 License

MIT License — free to use, fork, and modify.
