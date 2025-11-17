# 🔒 Authentication Setup

**Protect your LLM API token from unauthorized use in production**

---

## 📋 How It Works

### **Local Development:**
- ✅ **NO authentication required**
- Runs freely on `localhost`
- Easy development and testing

### **Production (Deployed):**
- 🔒 **Login required**
- Username + password authentication
- Protects your OpenAI API token
- Prevents unauthorized users from consuming your API credits

---

## 🚀 Setup Authentication

### **1. Local Development (No Setup Needed)**

Authentication is automatically **disabled** for local development:

```bash
streamlit run dashboard.py
```

✅ Dashboard opens directly without login
✅ No authentication required
✅ Works immediately

---

### **2. Production Deployment**

#### **Step 1: Add Credentials to Streamlit Cloud**

1. Go to https://share.streamlit.io
2. Click on your app → **Settings** (⚙️)
3. Click **"Secrets"**
4. Add this to your secrets:

```toml
[openai]
api_key = "sk-your-actual-openai-key"

[auth]
username = "your-username"
password = "your-secure-password"
```

5. Click **"Save"**

#### **Step 2: Push Code to GitHub**

```bash
git add auth.py dashboard.py .streamlit/secrets.toml.example
git commit -m "Add authentication for production"
git push origin main
```

#### **Step 3: Test**

1. Wait for deployment to complete (~2 minutes)
2. Visit your deployed app URL
3. You should see a **login screen**
4. Enter your username/password
5. Access granted! ✅

---

## 🔑 Recommended Credentials

### **Username:**
- Your name or email
- Examples: `john`, `admin`, `john@example.com`

### **Password:**
- **Strong** password (12+ characters)
- Mix of letters, numbers, symbols
- Use a password manager
- Examples: `MySecure#Pass2024`, `D@shb0ard!Str0ng`

---

## 🔧 Advanced Configuration

### **Manually Enable Auth for Testing**

To test authentication locally:

```bash
export ENABLE_AUTH=true
streamlit run dashboard.py
```

Now local will require login too.

### **Disable Auth in Production (Not Recommended)**

If you want to disable auth in production:

1. Remove `[auth]` section from Streamlit Cloud secrets
2. App will run without authentication

⚠️ **Warning:** Anyone with your URL can use your OpenAI API token!

---

## 🎯 How Authentication is Detected

The auth system automatically detects if you're in production:

```python
def is_production():
    # Checks multiple signals:
    1. Are auth secrets configured?
    2. Is STREAMLIT_RUNTIME_ENV = cloud?
    3. Is ENABLE_AUTH = true?

# If any is true → Show login
# If all are false → Skip login (local dev)
```

---

## 🧪 Testing

### **Test Locally (Should Skip Auth):**

```bash
streamlit run dashboard.py
# Should open directly without login
```

### **Test Production Auth Locally:**

```bash
# Create .streamlit/secrets.toml with auth credentials
echo '[auth]
username = "test"
password = "test123"' > .streamlit/secrets.toml

# Run dashboard
streamlit run dashboard.py
# Should now require login
```

⚠️ Don't commit `.streamlit/secrets.toml`!

---

## 🔐 Security Features

### **✅ What's Protected:**
- OpenAI API token usage
- Portfolio generation features
- LLM-powered analysis
- All dashboard functionality

### **✅ How It's Protected:**
- Password required to access
- Session-based authentication
- Logout functionality included
- Only runs in production

### **✅ Local Development:**
- No authentication needed
- Fast iteration
- Easy testing
- No password management

---

## 📱 User Experience

### **First Visit (Not Logged In):**

```
┌─────────────────────────────────┐
│   🔒 Login Required              │
│                                  │
│   Please enter your credentials  │
│   to access the dashboard.       │
│                                  │
│   Username: [____________]       │
│   Password: [____________]       │
│                                  │
│          [Login]                 │
└─────────────────────────────────┘
```

### **After Login:**

```
┌─────────────────────────────────┐
│  📊 Navigation                   │
│  ○ Overview                      │
│  ○ Daily Monitor                 │
│  ○ Generate Portfolio            │
│  ...                             │
│  ─────────────────────            │
│  📌 Portfolio Stats              │
│  Portfolio Value: $10,234        │
│  ─────────────────────            │
│  🚪 Logout                       │  ← Logout button
└─────────────────────────────────┘
```

---

## 🆘 Troubleshooting

### **"Authentication not configured" Warning**

**Cause:** No `[auth]` section in secrets
**Fix:** Add auth credentials to Streamlit Cloud secrets

### **Login Not Showing Locally**

**Expected!** Auth is disabled for local development.

**To enable locally:**
```bash
export ENABLE_AUTH=true
```

### **Can't Login (Wrong Password)**

**Fix:** Check Streamlit Cloud secrets:
1. Settings → Secrets
2. Verify `[auth]` username/password
3. No typos, correct formatting

### **Logged Out Automatically**

**Cause:** Streamlit session expired or app restarted
**Fix:** Just login again

---

## 📊 Comparison

| Environment | Authentication | API Token Usage | Setup Time |
|-------------|----------------|-----------------|------------|
| **Local** | ❌ Disabled | Your token | 0 minutes |
| **Production (no auth)** | ❌ Disabled | Anyone can use | 0 minutes |
| **Production (with auth)** | ✅ Enabled | Only you | 2 minutes |

---

## 💡 Best Practices

### **DO:**
- ✅ Use strong, unique password
- ✅ Enable auth in production
- ✅ Keep credentials in Streamlit Cloud secrets
- ✅ Share credentials securely (if needed)

### **DON'T:**
- ❌ Commit secrets.toml to git
- ❌ Use weak passwords
- ❌ Share credentials publicly
- ❌ Hardcode credentials in code

---

## 🎉 Summary

**Setup time:** 2 minutes
**Local development:** No changes needed
**Production:** Protected with login
**Security:** API token safe from rogues

---

## 🔗 Related Files

- `auth.py` - Authentication logic
- `dashboard.py` - Dashboard with auth integrated
- `.streamlit/secrets.toml.example` - Secrets template

---

**Your OpenAI API token is now protected in production!** 🔒

Local development remains fast and password-free. 🚀
