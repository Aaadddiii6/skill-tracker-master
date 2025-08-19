# 🚀 Render Deployment Guide for SkillTrack Pro

## Prerequisites

1. **GitHub Account**: Your code should be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **Supabase Project**: Ensure your Supabase project is set up and running

## Step 1: Prepare Your Code

### 1.1 Update Environment Variables

Make sure your `.env` file has the correct production values:

```bash
DATABASE_URL=postgresql://username:password@host:port/database_name
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

### 1.2 Commit and Push to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

## Step 2: Deploy to Render

### 2.1 Create New Web Service

1. Go to [render.com](https://render.com) and sign in
2. Click "New +" button
3. Select "Web Service"
4. Connect your GitHub repository

### 2.2 Configure Your Service

**Basic Settings:**

- **Name**: `skilltrack-pro-backend` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your default branch)

**Build & Deploy Settings:**

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn wsgi:app`

**Environment Variables:**
Add these in the Render dashboard:

```
DATABASE_URL = your-supabase-postgres-connection-string
SUPABASE_URL = your-supabase-project-url
SUPABASE_KEY = your-supabase-anon-key
SECRET_KEY = render-will-generate-this
FLASK_ENV = production
```

### 2.3 Advanced Settings

- **Auto-Deploy**: Enable to automatically deploy on git push
- **Health Check Path**: `/` (your home route)

## Step 3: Database Setup

### 3.1 Supabase Database

1. Go to your Supabase project dashboard
2. Navigate to Settings > Database
3. Copy the connection string from "Connection string" section
4. Use this as your `DATABASE_URL` in Render

### 3.2 Database Migration

Your app will automatically create tables on first run with:

```python
db.create_all()
```

## Step 4: Test Your Deployment

### 4.1 Check Build Logs

1. In Render dashboard, go to your service
2. Check "Logs" tab for any build errors
3. Ensure all dependencies are installed correctly

### 4.2 Test Your App

1. Visit your Render URL (e.g., `https://your-app.onrender.com`)
2. Test login functionality
3. Test all major features

## Step 5: Custom Domain (Optional)

### 5.1 Add Custom Domain

1. In Render dashboard, go to your service
2. Click "Settings" tab
3. Scroll to "Custom Domains"
4. Add your domain and configure DNS

### 5.2 DNS Configuration

Add these records to your domain provider:

```
Type: CNAME
Name: @
Value: your-app.onrender.com
```

## Troubleshooting

### Common Issues:

#### 1. Build Failures

- Check `requirements.txt` has all dependencies
- Ensure Python version compatibility
- Check build logs for specific errors

#### 2. Database Connection Issues

- Verify `DATABASE_URL` format
- Check Supabase database is running
- Ensure IP allowlist includes Render's IPs

#### 3. App Crashes

- Check start command: `gunicorn wsgi:app`
- Verify `wsgi.py` exists and imports correctly
- Check environment variables are set

#### 4. Static Files Not Loading

- Ensure static folder structure is correct
- Check file paths in templates

### Debug Commands:

```bash
# Check logs
render logs skilltrack-pro-backend

# Restart service
render restart skilltrack-pro-backend

# Check environment variables
render env ls skilltrack-pro-backend
```

## Monitoring & Maintenance

### 1. Health Checks

- Monitor your app's health check endpoint
- Set up alerts for downtime

### 2. Logs

- Regularly check Render logs
- Monitor for errors or performance issues

### 3. Updates

- Keep dependencies updated
- Test locally before deploying
- Use staging environment if possible

## Security Considerations

### 1. Environment Variables

- Never commit `.env` files
- Use Render's environment variable system
- Rotate secrets regularly

### 2. Database Security

- Use connection pooling
- Implement proper authentication
- Regular security updates

### 3. HTTPS

- Render provides HTTPS by default
- Ensure all external links use HTTPS

## Cost Optimization

### 1. Free Tier Limits

- 750 hours/month for free tier
- Service sleeps after 15 minutes of inactivity
- Consider paid plans for production use

### 2. Resource Usage

- Monitor memory and CPU usage
- Optimize code for efficiency
- Use appropriate instance sizes

## Support Resources

- [Render Documentation](https://render.com/docs)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Supabase Documentation](https://supabase.com/docs)

---

## Quick Deploy Checklist

- [ ] Code pushed to GitHub
- [ ] Requirements.txt updated
- [ ] wsgi.py created
- [ ] Environment variables configured
- [ ] Database connection tested
- [ ] Build successful
- [ ] App accessible via URL
- [ ] All features working
- [ ] Custom domain configured (if needed)
- [ ] Monitoring set up

---

**Need Help?** Check Render's community forum or create a support ticket in your Render dashboard.
