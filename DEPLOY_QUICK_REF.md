# 🎯 DEPLOYMENT QUICK REFERENCE

## 📋 Your Checklist (5 minutes to deploy!)

- [ ] Push code to GitHub
- [ ] Create Streamlit Cloud account
- [ ] Deploy your repo
- [ ] Add secrets
- [ ] Share demo link

---

## ⚡ Step-by-Step (Copy-Paste Ready)

### 1️⃣ Prepare GitHub

```bash
git add .
git commit -m "Deploy HireIQ Agent"
git push origin main
```

### 2️⃣ Deploy on Streamlit Cloud

1. Go to: https://share.streamlit.io
2. Click: **"New app"**
3. Fill in:
   - **Repository**: yourusername/Hire-agent
   - **Branch**: main
   - **File path**: ui/app.py
4. Click: **"Deploy"**

*(Takes 1-2 minutes)*

### 3️⃣ Add Secrets

1. Go to deployed app
2. Click **Settings ⚙️** (top right)
3. Click **"Secrets"** tab
4. Paste this and fill with your values:

```
GROQ_API_KEY = "gsk_xxxxx"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"
HR_EMAIL_FROM = "your_email@gmail.com"
```

5. Click **"Save"**
6. Your app will auto-restart ✅

### 4️⃣ Get Your Demo Link

Your live app: `https://yourusername-hire-agent.streamlit.app`

Share this link! 🎉

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Secret not found" | Restart app after adding secrets (Settings → Reboot) |
| Database error | Clear cache: Settings → Manage app → Reboot |
| API key not working | Check Streamlit Cloud Secrets tab format |
| Upload folder missing | Create `/uploads` folder, upload folder will auto-create |

---

## 💡 Pro Tips

1. Test locally first: `streamlit run ui/app.py`
2. Watch deployment logs in Streamlit Cloud
3. Changes auto-deploy when you push to GitHub
4. Share the public link with stakeholders
5. Monitor costs on Groq's dashboard

---

## 📊 Expected Performance

- Resume parsing: 2-5 seconds per file
- Candidate scoring: AI processing
- First load: ~5 seconds
- Subsequent loads: ~2 seconds (cached)

---

Ready? Start with Step 1! ⬆️
