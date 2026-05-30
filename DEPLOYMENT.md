# Deployment Guide

## Deploying to Streamlit Community Cloud

### Prerequisites

1. GitHub account
2. Streamlit Community Cloud account (free at https://streamlit.io/cloud)

### Steps

1. **Push code to GitHub**

```bash
git init
git add .
git commit -m "Initial commit: Bus Charging Scheduler"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/bus-charging-scheduler.git
git push -u origin main
```

2. **Deploy on Streamlit Cloud**

   a. Go to https://share.streamlit.io/
   
   b. Click "New app"
   
   c. Select your repository: `YOUR_USERNAME/bus-charging-scheduler`
   
   d. Set main file path: `app.py`
   
   e. Click "Deploy"

3. **Wait for deployment**

   Streamlit Cloud will:
   - Clone your repository
   - Install dependencies from `requirements.txt`
   - Start the app
   - Provide a public URL (e.g., `https://YOUR_USERNAME-bus-charging-scheduler.streamlit.app`)

### Configuration

No additional configuration needed! Streamlit Cloud automatically:
- Installs Python 3.9+
- Installs all packages from `requirements.txt`
- Serves the app on a public URL
- Provides HTTPS by default

### Troubleshooting

**Build fails:**
- Check that `requirements.txt` has correct package names
- Ensure all files are committed to GitHub
- Check Streamlit Cloud logs for specific errors

**App crashes:**
- Check that `scenarios/` directory exists with all 5 JSON files
- Verify Python version compatibility (3.8+)
- Check logs in Streamlit Cloud dashboard

**Slow performance:**
- Streamlit Community Cloud has resource limits
- Consider reducing `time_limit_seconds` in optimizer if needed
- Caching is already implemented for scenarios and schedules

### Local Testing Before Deployment

Always test locally first:

```bash
streamlit run app.py
```

Open browser to `http://localhost:8501` and verify:
- All 5 scenarios load
- Schedule generation works
- No errors in console

### Updating the Deployed App

Simply push changes to GitHub:

```bash
git add .
git commit -m "Update: description of changes"
git push
```

Streamlit Cloud will automatically detect changes and redeploy.

### Custom Domain (Optional)

Streamlit Community Cloud provides a default URL. For a custom domain:
1. Upgrade to Streamlit Cloud Teams (paid)
2. Configure DNS settings
3. Follow Streamlit's custom domain guide

### Monitoring

- View app logs in Streamlit Cloud dashboard
- Monitor resource usage (CPU, memory)
- Check app analytics (views, errors)

### Limits (Free Tier)

- 1 GB RAM
- 1 CPU core
- Unlimited public apps
- Apps sleep after inactivity (wake on first request)

These limits are sufficient for this assignment's requirements.
