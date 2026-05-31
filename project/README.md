# AI-Powered Interview Preparation & Evaluation System

Production-ready interview coaching platform with **Streamlit** frontend, **Groq** LLM backend, **Supabase** PostgreSQL persistence, **Cloudinary** file storage, and **Plotly** analytics.

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

- **Frontend:** Streamlit (deployed on Streamlit Community Cloud)
- **Backend:** Python 3.11+
- **LLM:** Groq API (`llama3-70b-8192` default, switchable)
- **Database:** Supabase PostgreSQL + SQLAlchemy ORM
- **File Storage:** Cloudinary (resume PDFs)
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
│   ├── llm_service.py      # Groq LLM client
│   ├── storage_service.py   # Cloudinary storage
│   ├── auth_service.py
│   ├── evaluation_service.py
│   ├── interview_service.py
│   ├── report_service.py
│   └── resume_service.py
├── database/
├── models/
├── prompts/
├── analytics/
├── reports/
├── utils/
├── config/
├── .streamlit/
│   └── config.toml
├── requirements.txt
└── README.md
```

## Free Cloud Services

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [Groq](https://console.groq.com/) | LLM API | Free tier with rate limits |
| [Supabase](https://supabase.com/) | PostgreSQL Database | 500MB, 2 projects |
| [Cloudinary](https://cloudinary.com/) | File Storage | 25GB bandwidth/month |
| [Streamlit Cloud](https://streamlit.io/cloud) | App Hosting | Free for public repos |

## Prerequisites

1. **Python 3.11+**
2. **Groq API Key** — Sign up at [console.groq.com](https://console.groq.com/)
3. **Supabase Project** — Create at [supabase.com](https://supabase.com/)
4. **Cloudinary Account** — Sign up at [cloudinary.com](https://cloudinary.com/)

## Installation (Local Development)

```bash
cd project
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Edit with your API keys
```

## Configuration

Create `.env` from `.env.example`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | _(required)_ | Groq API key |
| `GROQ_MODEL` | `llama3-70b-8192` | Default LLM model |
| `SUPABASE_DB_URL` | _(required)_ | PostgreSQL connection string |
| `SUPABASE_URL` | _(required)_ | Supabase project URL |
| `SUPABASE_KEY` | _(required)_ | Supabase anon/public key |
| `CLOUDINARY_CLOUD_NAME` | _(required)_ | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | _(required)_ | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | _(required)_ | Cloudinary API secret |
| `QUESTIONS_PER_SESSION` | `10` | Questions per interview |
| `SCORE_INCREASE_THRESHOLD` | `7.0` | Raise difficulty above this |
| `SCORE_DECREASE_THRESHOLD` | `4.0` | Lower difficulty below this |
| `DEBUG` | `false` | SQL echo + debug logging |
| `SECRET_KEY` | `changeme` | App secret key |

## Run the Application

```bash
cd project
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub
2. Sign up at [share.streamlit.io](https://share.streamlit.io/)
3. Click **New app** and select:
   - **Repository:** `your-username/AI-Interview`
   - **Branch:** `main`
   - **Main file path:** `project/app.py`
4. Add secrets in **Advanced settings → Secrets** (TOML format):

```toml
GROQ_API_KEY = "your_groq_api_key"
GROQ_MODEL = "llama3-70b-8192"
SUPABASE_DB_URL = "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "your_supabase_anon_key"
CLOUDINARY_CLOUD_NAME = "your_cloud_name"
CLOUDINARY_API_KEY = "your_cloudinary_api_key"
CLOUDINARY_API_SECRET = "your_cloudinary_api_secret"
SECRET_KEY = "your_random_secret_key"
```

5. Click **Deploy**

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

## Available LLM Models

| Model | Description |
|-------|-------------|
| `llama3-70b-8192` | Best quality (default) |
| `llama3-8b-8192` | Faster responses |
| `mixtral-8x7b-32768` | Good balance |
| `gemma-7b-it` | Lightweight |

Use the sidebar on any page to switch models.

## Adaptive Difficulty

- Starts at selected level (Easy / Medium / Hard)
- **Increases** when answer score **> 7/10**
- **Decreases** when answer score **< 4/10**

## Database

Tables are created automatically on first run via SQLAlchemy ORM:

- `users`, `resumes`, `resume_skills`, `resume_projects`, `resume_education`
- `interview_sessions`, `interview_questions`, `interview_answers`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Groq API errors | Verify `GROQ_API_KEY` is valid at [console.groq.com](https://console.groq.com/) |
| Rate limit errors | Switch to a smaller/faster model or wait and retry |
| Database connection failed | Verify `SUPABASE_DB_URL` and check Supabase dashboard |
| Slow responses | Use `llama3-8b-8192` or `gemma-7b-it` for faster inference |
| Empty resume parse | Ensure PDF has selectable text (not scanned image-only) |

## License

MIT — use freely for learning and interview preparation.
