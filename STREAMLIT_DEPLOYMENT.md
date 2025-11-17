# 🚀 Deploying to Streamlit Community Cloud

**FREE deployment for your Streamlit dashboard**

---

## ✅ Prerequisites

- [x] GitHub account
- [x] Your code in a GitHub repository
- [x] `requirements.txt` file (already exists)
- [x] `dashboard.py` (already exists)

---

## 📋 Step-by-Step Deployment

### 1. Prepare Your Repository

```bash
# Make sure everything is committed
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

**Verify these files exist:**
- `dashboard.py` ✅
- `requirements.txt` ✅
- `.streamlit/config.toml` ✅ (just created)
- `.streamlit/secrets.toml.example` ✅ (template)

### 2. Sign Up for Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click **"Sign up"**
3. **Sign in with GitHub** (recommended)
4. Authorize Streamlit to access your repositories

### 3. Deploy Your App

1. Click **"New app"** button
2. Fill in the form:
   - **Repository:** `YOUR_USERNAME/llm_momentum_strategy`
   - **Branch:** `main`
   - **Main file path:** `dashboard.py`
   - **App URL:** Choose a custom subdomain (e.g., `your-portfolio`)

3. Click **"Deploy!"**

### 4. Configure Secrets

After deployment starts:

1. Click **"⚙️ Settings"** (bottom left)
2. Click **"Secrets"**
3. Add your secrets in TOML format:

```toml
# OpenAI API Key (if using LLM features)
[openai]
api_key = "sk-your-actual-api-key"

# Add other secrets as needed
```

4. Click **"Save"**

### 5. Wait for Deployment

- First deployment takes ~2-3 minutes
- Watch the build logs for any errors
- App will auto-refresh when ready

---

## 🔧 Configuration

### Accessing Secrets in Code

Update your code to read from Streamlit secrets:

```python
import streamlit as st

# Read OpenAI API key from secrets
if "openai" in st.secrets:
    import os
    os.environ["OPENAI_API_KEY"] = st.secrets["openai"]["api_key"]
```

### File Storage Limitations

**Important:** Streamlit Cloud has limited persistent storage.

**For portfolio snapshots:**
- Data is stored in memory during app session
- Snapshots are lost when app restarts
- Consider using external storage (S3, Google Cloud Storage) for production

**Workaround for now:**
- Upload Robinhood CSV each time in the Daily Monitor tab
- Or connect to external database

---

## 📊 App URL

Your deployed app will be available at:
```
https://YOUR-APP-NAME.streamlit.app
```

Example: `https://my-portfolio.streamlit.app`

---

## 🔄 Auto-Deployment

**Every time you push to GitHub:**
- Streamlit Cloud automatically rebuilds your app
- Changes go live in ~1-2 minutes
- No manual redeployment needed!

---

## ⚙️ Advanced Settings

### Custom Domain (Pro Plan)

If you have Streamlit Cloud Pro:
1. Settings → General → Custom subdomain
2. Set your preferred URL

### Resource Limits (Free Tier)

- **RAM:** 1 GB
- **CPU:** 1 core shared
- **Storage:** Limited (ephemeral)
- **Sleep:** After 7 days of inactivity

**To prevent sleep:**
- Visit your app at least once per week
- Or upgrade to Pro ($20/month)

### Making App Private

**Free tier:** Apps are public by default

**To make private:**
1. Request access: https://streamlit.io/cloud
2. Or use Streamlit Cloud for Teams ($250/month)

---

## 🐛 Troubleshooting

### "Module not found" Error

**Fix:** Update `requirements.txt` with all dependencies

```bash
# Generate updated requirements
pip freeze > requirements.txt

# Or manually add missing packages
echo "missing-package==1.0.0" >> requirements.txt
```

### "File not found" Error

**Fix:** Check file paths are relative to repository root

```python
# ❌ Bad (absolute path)
data = pd.read_csv("/Users/you/data.csv")

# ✅ Good (relative path)
data = pd.read_csv("data/portfolio.csv")
```

### App Crashes on Startup

**Check logs:**
1. Streamlit Cloud dashboard
2. Click on your app
3. Check "Logs" tab
4. Fix errors shown

### Slow Performance

**Optimization tips:**
1. Use `@st.cache_data` for expensive computations
2. Reduce data loading
3. Minimize API calls
4. Consider upgrading to Pro for more resources

---

## 💡 Tips for Production

### 1. Add Caching

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    # Expensive data loading
    return data
```

### 2. Add Error Handling

```python
try:
    # Your code
except Exception as e:
    st.error(f"Error: {e}")
    st.info("Please try refreshing the page")
```

### 3. Add Loading States

```python
with st.spinner("Loading portfolio..."):
    data = load_data()
st.success("Loaded!")
```

### 4. Optimize Large DataFrames

```python
# Use st.dataframe instead of st.table for large data
st.dataframe(large_df, height=400)
```

---

## 📈 Monitoring Your App

### Check App Health

1. Go to https://share.streamlit.io
2. Click on your app
3. View metrics:
   - Number of visitors
   - App uptime
   - Error logs
   - Resource usage

### Update Your App

```bash
# Make changes locally
git add .
git commit -m "Update feature X"
git push origin main

# Streamlit Cloud auto-deploys in ~2 minutes
```

---

## 🆚 Alternatives Comparison

| Platform | Cost | Pros | Cons |
|----------|------|------|------|
| **Streamlit Cloud** | FREE | Built for Streamlit, easy setup | Limited storage, public by default |
| **Hugging Face** | FREE | ML-focused, GPU available | Community support only |
| **Railway** | $5/mo | Persistent storage, private | Paid |
| **Render** | FREE tier | Good free tier | Sleeps after inactivity |
| **Vercel** | FREE | Fast CDN | ❌ **NOT COMPATIBLE** with Streamlit |

---

## ✅ Deployment Checklist

Before deploying:

- [ ] Code pushed to GitHub
- [ ] `requirements.txt` includes all dependencies
- [ ] Secrets identified (API keys, passwords)
- [ ] File paths are relative (not absolute)
- [ ] Tested locally with `streamlit run dashboard.py`
- [ ] `.streamlit/config.toml` configured
- [ ] `.gitignore` excludes `secrets.toml`

After deploying:

- [ ] App loads without errors
- [ ] Secrets configured in Streamlit Cloud
- [ ] All features work as expected
- [ ] Bookmarked app URL
- [ ] Tested with real data

---

## 🎉 You're Live!

Once deployed, share your app:
```
https://your-portfolio.streamlit.app
```

**Remember:**
- App is public by default
- Don't include sensitive data in the code
- Use Streamlit secrets for API keys
- Monitor your usage to stay within free tier limits

---

## 📞 Support

- **Streamlit Docs:** https://docs.streamlit.io
- **Community Forum:** https://discuss.streamlit.io
- **GitHub Issues:** https://github.com/streamlit/streamlit/issues

---

**Happy deploying! 🚀**
