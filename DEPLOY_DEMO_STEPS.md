# 🚀 DEPLOY TO STREAMLIT CLOUD - COMPLETE GUIDE

## ⏱️ Time Required: 10-15 minutes

---

## 📋 STEP 1: Prepare Your Code (5 minutes)

### 1.1 Open PowerShell in your project folder
```powershell
cd m:\Hire-agent
```

### 1.2 Check Git status
```powershell
git status
```

You should see:
- ✅ Modified files in green/red
- ✅ .env should NOT be listed (already in .gitignore)

### 1.3 Add all changes and commit
```powershell
git add .
git commit -m "Ready for deployment - professional email templates and dark UI"
```

### 1.4 Push to GitHub
```powershell
git push origin main
```

**Wait for it to complete** (you'll see "Main -> main")

---

## 🌐 STEP 2: Create/Login to Streamlit Cloud (2 minutes)

### 2.1 Go to: https://share.streamlit.io

### 2.2 Click "Sign in with GitHub"
- If first time: Create account
- If returning: Just sign in

### 2.3 Allow permissions (GitHub will ask)
- Click "Authorize Streamlit"

---

## ⚡ STEP 3: Deploy Your App (3 minutes)

### 3.1 After login, click "New app" (top-left button)

### 3.2 Fill in the deployment form:

**Repository field:**
```
yourusername/Hire-agent
```
(Replace `yourusername` with your actual GitHub username)

**Branch field:**
```
main
```

**File path field:**
```
ui/app.py
```

### 3.3 Click "Deploy"

**⏳ Wait 1-2 minutes** while it deploys...

You'll see:
- "Starting deployment..."
- "Building Docker image..."
- "Launching app..."
- ✅ "App is ready!"

---

## 🔐 STEP 4: Add Secrets (Critical!) (3 minutes)

### 4.1 Once app is deployed, click Settings ⚙️ (top-right corner)

### 4.2 Click "Secrets" tab

### 4.3 Copy and paste this (EXACTLY):

```
GROQ_API_KEY = "your_groq_api_key_here"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password_here"
HR_EMAIL_FROM = "your_email@gmail.com"
```

(Get these values from your `.env` file - copy the actual values, not these placeholders)

### 4.4 Click "Save"

**App will auto-restart** ✅

---

## 🎉 STEP 5: Get Your Demo Link (Instant!)

### The URL is:

```
https://yourusername-hire-agent.streamlit.app
```

Replace `yourusername` with your actual GitHub username.

**Example:** If your GitHub is `john-doe`, your link is:
```
https://john-doe-hire-agent.streamlit.app
```

---

## 📤 SHARE YOUR DEMO LINK

Copy and send to stakeholders/clients:

```
🎯 HireIQ Agent Demo
https://yourusername-hire-agent.streamlit.app

Features:
✅ AI-powered resume screening
✅ Intelligent candidate scoring
✅ Automated interview scheduling
✅ Dark modern UI
```

---

## ✅ VERIFICATION CHECKLIST

After deployment, verify everything works:

- [ ] App loads without errors
- [ ] Dark theme displays correctly
- [ ] Can post a job
- [ ] Can upload a resume
- [ ] Email preview works
- [ ] Interview scheduling works

---

## 🚨 TROUBLESHOOTING

### App shows "Secret not found"
1. Go back to Settings → Secrets
2. Verify all secrets are pasted correctly
3. Click "Save" again
4. Wait 30 seconds for restart

### Nothing changed after deployment
1. Clear browser cache: `Ctrl+Shift+Del`
2. Hard refresh: `Ctrl+F5`
3. Try in incognito mode

### App crashes on resume upload
1. Check Streamlit Cloud logs
2. Verify GROQ_API_KEY is correct
3. Try a smaller PDF file

### Can't see deployed app
1. Wait 2-3 minutes after "Deploy"
2. Check repository is PUBLIC on GitHub
3. Check GitHub has `.streamlit/config.toml` file

---

## 📱 SHARE METHODS

### Email
```
Subject: HireIQ Agent Demo - Review Live

Hi [Name],

I've deployed the HireIQ Agent demo for you to review:

🔗 https://yourusername-hire-agent.streamlit.app

Features:
- AI Resume Screening
- Candidate Scoring
- Interview Scheduling
- Professional Dark UI

Please test and let me know your feedback!
```

### Slack
```
🚀 HireIQ Agent is LIVE!

Demo Link: https://yourusername-hire-agent.streamlit.app

Try uploading a resume and see the AI magic! ✨
```

### LinkedIn
```
Excited to announce the HireIQ Agent is now live! 

An AI-powered hiring solution that automates resume screening and candidate evaluation.

👉 Try it here: https://yourusername-hire-agent.streamlit.app

#AI #Hiring #Automation
```

---

## 📊 MONITORING

### View logs in Streamlit Cloud:
1. Go to your app dashboard
2. Click app name
3. Scroll down to see recent logs
4. Check for errors

### Update after making changes:
1. Make code changes locally
2. Commit: `git commit -m "..."`
3. Push: `git push origin main`
4. **Streamlit auto-deploys in 1-2 minutes** ✅

---

## 🎯 THAT'S IT!

You now have a live, shareable demo link! 🎉

**Summary:**
- ✅ Push code to GitHub
- ✅ Deploy on Streamlit Cloud
- ✅ Add secrets
- ✅ Share link

**Time taken:** ~15 minutes
**Cost:** FREE (Streamlit Cloud free tier)
**Maintenance:** Auto-updates on git push

---

## 💡 PRO TIPS

1. **Keep it running:** Streamlit Cloud keeps apps live for free
2. **Updates:** Just push to GitHub, auto-deploys
3. **Monitor:** Check logs weekly
4. **Feedback:** Ask users to test each feature

---

**Ready? Start with STEP 1 now!** 🚀
