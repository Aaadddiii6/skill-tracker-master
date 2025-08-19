#!/bin/bash

echo "🚀 Preparing SkillTrack Pro for Render deployment..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first:"
    echo "   git init"
    echo "   git remote add origin <your-github-repo-url>"
    exit 1
fi

# Check if all required files exist
required_files=("requirements.txt" "wsgi.py" "app.py" "models.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done

echo "✅ All required files found"

# Add all files
echo "📁 Adding files to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Prepare for Render deployment - $(date)"

# Push to remote
echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "🎉 Code pushed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Go to https://render.com"
echo "2. Create new Web Service"
echo "3. Connect your GitHub repository"
echo "4. Use these settings:"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: gunicorn wsgi:app"
echo "5. Add environment variables:"
echo "   - DATABASE_URL"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_KEY"
echo "   - SECRET_KEY (Render will generate this)"
echo ""
echo "📖 See DEPLOYMENT_GUIDE.md for detailed instructions"
