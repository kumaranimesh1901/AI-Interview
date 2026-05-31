# AI-Powered Interview Preparation & Evaluation System

Production-ready interview coaching platform with **Streamlit** frontend, **Ollama** LLM backend, **SQLite** persistence, and **Plotly** analytics.

## Features

| Module | Description |
|--------|-------------|
| **Authentication** | Register, login, bcrypt password hashing, session management |
| **Resume Analysis** | PDF upload, PyPDF2 extraction, LLM structured parsing |
| **Interviews** | 5 types × 3 difficulty levels, 10 questions/session |
| **Adaptive Engine** | Auto difficulty up/down based on scores |
| **Evaluation** | 0–10 score, strengths, weaknesses, missing concepts, model answer |
| **Analytics** | Bar, line, radar charts + history table (Plotly) |
| **PDF Reports** | Full session report via ReportLab |

## Tech Stack

- **Frontend:** Streamlit  
- **Backend:** Python 3.11+  
- **LLM:** Ollama (`qwen3:32b` default, switchable)  
- **Database:** SQLite + SQLAlchemy ORM  
- **PDF Parse:** PyPDF2  
- **PDF Reports:** ReportLab  
- **Charts:** Plotly  

## Project Structure

```
project/
├── app.py
├── pages/
│   ├── 1_login.py
│   ├── 2_register.py
│   ├── 3_resume.py
│   ├── 4_interview.py
│   ├── 5_feedback.py
│   ├── 6_analytics.py
│   └── 7_report.py
├── services/
├── database/
├── models/
├── prompts/
├── analytics/
├── reports/
├── utils/
├── config/
├── requirements.txt
└── README.md
```

## Prerequisites

1. **Python 3.11+**
2. **Ollama** installed and running: [https://ollama.com](https://ollama.com)

```bash
# Start Ollama (if not running)
ollama serve

# Pull default model
ollama pull qwen3:32b
```

## Installation

```bash
cd project
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Edit as needed
```

## Configuration

Create `.env` from `.env.example`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `OLLAMA_DEFAULT_MODEL` | `qwen3:32b` | Default LLM model |
| `OLLAMA_TIMEOUT` | `120` | Request timeout (seconds) |
| `DB_PATH` | `./data/interview_prep.db` | SQLite database path |
| `QUESTIONS_PER_SESSION` | `10` | Questions per interview |
| `SCORE_INCREASE_THRESHOLD` | `7.0` | Raise difficulty above this |
| `SCORE_DECREASE_THRESHOLD` | `4.0` | Lower difficulty below this |
| `DEBUG` | `false` | SQL echo + debug logging |

## Run the Application

```bash
cd project
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## Usage Flow

1. **Register** → create account  
2. **Login** → authenticate  
3. **Resume** → upload PDF for personalized questions  
4. **Interview** → pick type & difficulty, answer 10 questions  
5. **Feedback** → review scores and AI feedback per question  
6. **Analytics** → charts and performance trends  
7. **Report** → download PDF summary  

## Interview Types

- Technical Interview  
- HR Interview  
- DSA Interview  
- Machine Learning Interview  
- System Design Interview  

## Adaptive Difficulty

- Starts at selected level (Easy / Medium / Hard)  
- **Increases** when answer score **> 7/10**  
- **Decreases** when answer score **< 4/10**  

## Model Switching

Use the sidebar on any page to:

- Type a model name (e.g. `llama3.2`, `qwen3:32b`)  
- Select from installed models detected via Ollama API  

## Database

Tables are created automatically on first run:

- `users`, `resumes`, `resume_skills`, `resume_projects`, `resume_education`  
- `interview_sessions`, `interview_questions`, `interview_answers`  

Data is stored under `project/data/`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Ollama unreachable | Run `ollama serve`, check `OLLAMA_BASE_URL` |
| Model not found | `ollama pull <model-name>` |
| Slow responses | Use a smaller model or increase `OLLAMA_TIMEOUT` |
| Empty resume parse | Ensure PDF has selectable text (not scanned image-only) |

## License

MIT — use freely for learning and interview preparation.
