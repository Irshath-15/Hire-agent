#!/bin/bash
# Quick deployment script for Streamlit Cloud

echo "🚀 HireIQ Agent - Quick Deploy"
echo "================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git not initialized. Run: git init"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Create it first."
    exit 1
fi

echo "✅ Checking requirements..."
git status

echo ""
echo "📝 Next steps:"
echo "1. Make sure .env is in .gitignore (it is ✓)"
echo "2. Commit and push to GitHub:"
echo "   git add ."
echo "   git commit -m 'Ready for deployment'"
echo "   git push origin main"
echo ""
echo "3. Go to https://share.streamlit.io"
echo "4. Click 'New app' and select your GitHub repo"
echo "5. Set file path to: ui/app.py"
echo "6. Add secrets in Streamlit Cloud Settings"
echo "7. Deploy!"
echo ""
echo "Your demo link will be: https://<username>-hire-agent.streamlit.app"
