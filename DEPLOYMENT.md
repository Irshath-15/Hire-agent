# 🚀 HireIQ Agent - Deployment Guide

## Deployment Options

### Option 1: Streamlit Cloud (Recommended - Easiest) ✅

**Pros:**
- Free hosting tier available
- One-click deployment
- Automatic HTTPS
- Built-in updates on git push

**Steps:**

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy to Streamlit Cloud"
   git push origin main
   ```

2. **Create Streamlit Cloud Account**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"

3. **Configure Your App**
   - **Repository**: Select your GitHub repo (e.g., `yourusername/Hire-agent`)
   - **Branch**: `main`
   - **File Path**: `ui/app.py`

4. **Add Secrets**
   - Click "Settings" → "Secrets"
   - Copy and paste your environment variables from `.env`:
   ```
   GROQ_API_KEY = "gsk_..."
   SMTP_HOST = "smtp.gmail.com"
   SMTP_PORT = 587
   SMTP_USER = "your_email@gmail.com"
   SMTP_PASSWORD = "your_app_password"
   HR_EMAIL_FROM = "your_email@gmail.com"
   ```

5. **Deploy**
   - Click "Deploy"
   - Your app will be live at: `https://yourusername-hire-agent.streamlit.app`

---

### Option 2: Heroku (Alternative)

**Pros:**
- More control over server
- Can deploy background workers

**Cons:**
- Paid after free tier
- Requires more setup

---

### Option 3: Docker + Cloud Run / AWS (Enterprise)

**Pros:**
- Full control
- Scalable

**Cons:**
- More complex setup
- Ongoing costs

---

## Pre-Deployment Checklist

- [ ] All dependencies in `requirements.txt`
- [ ] `.env` file NOT committed (check `.gitignore`)
- [ ] Secrets configured in Streamlit Cloud
- [ ] Test app locally: `streamlit run ui/app.py`
- [ ] `.streamlit/config.toml` configured
- [ ] Assets (uploads, db) folders included in repo

---

## Your Demo Link

Once deployed on Streamlit Cloud, your demo link will be:

```
https://yourusername-hire-agent.streamlit.app
```

Share this link with stakeholders!

---

## Local Testing Before Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Create .streamlit/secrets.toml with your .env values
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with actual values

# Run locally
streamlit run ui/app.py
```

---

## Troubleshooting

**App not loading?**
- Check Streamlit Cloud logs
- Verify all secrets are set correctly
- Ensure database path is correct (might need to use temp directory for cloud)

**Database issues?**
- Streamlit Cloud has read-only file system for uploads
- Consider using cloud database (PostgreSQL) for production
- Current SQLite works but data resets on deployments

**Secret not found?**
- Secrets must be in `.streamlit/secrets.toml` (local)
- Or in Streamlit Cloud Secrets manager (production)
- Restart the app after adding secrets

---

## Production Recommendations

1. **Switch to PostgreSQL** (instead of SQLite)
2. **Use cloud storage** for resume uploads (AWS S3, GCS)
3. **Add authentication** (if sensitive data)
4. **Enable caching** for AI calls to reduce costs
5. **Monitor costs** - Groq API charges per request

---

## Next Steps

1. Push code to GitHub
2. Deploy to Streamlit Cloud
3. Share your link: `https://yourusername-hire-agent.streamlit.app`
4. Start giving demos!

Good luck! 🎉
