# HireIQ Agent - Smart Hiring Pipeline

A powerful AI-driven hiring agent that automates resume screening, candidate scoring, and interview scheduling using Groq's Llama 3.3 model.

## 🎯 Features

- **Autonomous Resume Screening** - AI-powered resume parsing and analysis
- **Intelligent Scoring** - Automated candidate ranking based on job requirements
- **Interview Scheduling** - Integrated calendar and email notifications
- **Dark Modern UI** - Professional Streamlit interface with purple/white accents
- **Batch Processing** - Screen multiple resumes against multiple job roles
- **Candidate Pipeline** - Manage shortlisted, under review, and rejected candidates
- **Database Management** - Full CRUD operations for jobs, candidates, and decisions

## 🚀 Quick Start

### Local Development

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd Hire-agent

# 2. Create virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Run the app
streamlit run ui/app.py
```

## 📦 Deployment

### Streamlit Cloud (Recommended)

The easiest way to deploy! See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

**Quick summary:**
1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Click "New app" → Select your repo → File: `ui/app.py`
4. Add secrets in Settings → Secrets
5. Deploy!

Your demo link: `https://<username>-hire-agent.streamlit.app`

### Other Options
- Heroku, Docker, AWS Cloud Run, etc. (See DEPLOYMENT.md)

## 🔑 Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
HR_EMAIL_FROM=your_email@gmail.com
```

## 📁 Project Structure

```
Hire-agent/
├── ui/
│   └── app.py              # Main Streamlit app
├── agent/
│   ├── pipeline.py         # Core AI pipeline
│   ├── parser.py           # Resume parser
│   ├── scorer.py           # Candidate scorer
│   ├── semantic.py         # Semantic search
│   └── actions.py          # Email/Calendar actions
├── db/
│   ├── models.py           # SQLModel schemas
│   ├── database.py         # Database config
│   └── seed.py             # Sample data
├── requirements.txt        # Python dependencies
├── .env                    # Secrets (DO NOT COMMIT)
├── DEPLOYMENT.md           # Deployment guide
└── .streamlit/
    ├── config.toml         # Streamlit config
    └── secrets.toml        # Local secrets
```

## 🎨 UI Theme

- **Dark Modern Theme**: #0F1419 background
- **Primary Color**: Purple (#4F46E5)
- **Accent Colors**: Green (#10b981), Orange (#f59e0b), Red (#ef4444)
- **Text**: White (#FFFFFF) on dark backgrounds

## 🔐 Security Notes

- Never commit `.env` files
- Keep API keys in Streamlit Cloud Secrets manager
- Use app passwords for Gmail, not main password
- Consider adding authentication for production

## 🤖 AI Model

Uses **Groq's Llama 3.3** for:
- Resume analysis and extraction
- Candidate scoring and ranking
- Interview email drafting
- Weakness/strength identification

## 📞 Support

For issues or questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for troubleshooting
2. Review logs in Streamlit Cloud dashboard
3. Test locally before deploying: `streamlit run ui/app.py`

## 📄 License

MIT

---

**Ready to deploy?** → See [DEPLOYMENT.md](DEPLOYMENT.md) 🚀
