# 🎓 AI Language Tutor

An intelligent, AI-powered language learning desktop application built with Python. Features real-time grammar correction, speech recognition, vocabulary tracking, and a gamified XP progression system.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![AI](https://img.shields.io/badge/AI-Groq%20%7C%20Gemini-FF6F61?style=for-the-badge)

---

## ✨ Key Features

### 🤖 AI-Powered Conversation
- Real-time chat with AI tutor using **Groq** (primary) and **Google Gemini** (fallback)
- Multiple conversation personas (Friendly, Formal, Coach, Comedian)
- Topic-based learning scenarios (Restaurant, Travel, Job Interview, etc.)
- Context-aware responses with learning memory

### 📝 Real-Time Grammar Correction
- Instant grammar error detection with inline highlighting
- Wavy underline indicators for mistakes
- Hover tooltips showing correct suggestions
- Grammar category analysis (verb tense, articles, prepositions, etc.)

### 🎤 Speech Recognition
- Azure Speech-to-Text integration
- Multi-language support (English, Turkish)
- Pronunciation assessment with scoring
- Live transcription feedback

### 📚 Vocabulary System
- Interactive vocabulary highlighting in chat
- Personal word list with AI-generated definitions
- Example sentences and usage context
- Vocab mode toggle for focused learning

### 🎮 XP Progression System
- Experience points for all learning activities
- CEFR level progression (A1 → C2)
- Daily streak tracking with bonus rewards
- Visual progress bar with statistics

### 📊 Practice Modes
- **Listening Practice**: Audio comprehension exercises
- **Reading Practice**: Text-based learning with vocabulary support
- **Placement Test**: Initial CEFR level assessment

---

## 🖼️ Screenshots

| Chat Interface | Grammar Correction | Progress System |
|:---:|:---:|:---:|
| AI conversation with personas | Real-time error highlighting | XP & level tracking |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | PySide6 (Qt for Python) |
| **AI/LLM** | Groq API, Google Gemini API |
| **Speech** | Azure Cognitive Services |
| **Database** | Supabase (PostgreSQL) |
| **Auth** | Supabase Authentication |

---

## 📁 Project Structure

```
ai-language-tutor/
├── app/
│   ├── engines/
│   │   ├── gemini_engine.py      # AI conversation & grammar checking
│   │   ├── cloud_stt_azure.py    # Speech-to-text service
│   │   └── pron_eval.py          # Pronunciation evaluation
│   │
│   ├── services/
│   │   ├── db_supabase.py        # Database operations
│   │   └── progression.py        # XP & leveling system
│   │
│   ├── ui/
│   │   ├── main_window.py        # Main application window
│   │   ├── vocab_browser.py      # Chat with grammar highlighting
│   │   ├── listening_widget.py   # Listening practice
│   │   ├── reading_widget.py     # Reading practice
│   │   └── placement_test_dialog.py
│   │
│   └── modules/
│       ├── vocab_utils.py        # Vocabulary utilities
│       └── vocab_store.py        # Word list management
│
├── main.py                       # Application entry point
├── requirements.txt
└── .env.example
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Supabase](https://supabase.com) account (free tier)
- [Groq](https://console.groq.com) API key (free)
- [Azure Speech](https://azure.microsoft.com/en-us/services/cognitive-services/speech-services/) key (optional, for voice)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-language-tutor.git
cd ai-language-tutor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
python main.py
```

---

## 🎮 XP & Leveling System

| Activity | XP Reward |
|----------|-----------|
| Send message | +5 XP |
| Perfect grammar | +10 XP |
| Daily streak | +15 XP |
| Weekly bonus (7 days) | +50 XP |
| Complete listening | +20 XP |
| Learn new word | +5 XP |
| Level up bonus | +100 XP |

### CEFR Level Thresholds

| Level | XP Required | Description |
|-------|-------------|-------------|
| A1 | 0 | Beginner |
| A2 | 500 | Elementary |
| B1 | 1,500 | Intermediate |
| B2 | 3,500 | Upper-Intermediate |
| C1 | 7,000 | Advanced |
| C2 | 12,000 | Proficient |

---

## 🗄️ Database Schema

```sql
-- Core tables
profiles        -- User profiles, XP, CEFR level
chat_sessions   -- Conversation sessions
chat_messages   -- Individual messages
learning_events -- Activity tracking
xp_events       -- XP transaction history
placement_tests -- Assessment results
```

---

## 🔧 Configuration

Environment variables (`.env`):

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...

# AI Providers
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...

# Azure Speech
AZURE_SPEECH_KEY=xxx
AZURE_SPEECH_REGION=eastus
```

---

## 📈 Future Improvements

- [ ] Mobile app version (Flutter/React Native)
- [ ] More languages support
- [ ] Multiplayer conversation practice
- [ ] Spaced repetition for vocabulary
- [ ] Writing exercises with AI feedback
- [ ] Leaderboard system

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---


## 👨‍💻 Author

Hasan Özay Yılmaz


---

## 🙏 Acknowledgments

- [Groq](https://groq.com/) - Fast LLM inference
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI capabilities
- [Supabase](https://supabase.com/) - Backend infrastructure
- [Azure](https://azure.microsoft.com/) - Speech services
