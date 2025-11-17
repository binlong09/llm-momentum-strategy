# 🌐 Custom Domain Setup for Streamlit

Multiple options for using your own domain with Streamlit.

---

## Option 1: Streamlit Cloud for Teams (Official)

### Cost: $250/month

**Pros:**
- ✅ Official support
- ✅ Easy setup (5 minutes)
- ✅ SSL included
- ✅ No server management

**Steps:**
1. Upgrade to Streamlit Cloud for Teams: https://streamlit.io/cloud
2. Go to your app → Settings → Custom domain
3. Enter your domain: `portfolio.yourdomain.com`
4. Add CNAME record to your DNS:
   ```
   Type: CNAME
   Name: portfolio
   Value: [provided by Streamlit]
   ```
5. Wait for DNS propagation (5-60 minutes)
6. Done!

**Recommended for:** Business/professional use only (expensive for personal projects)

---

## Option 2: Reverse Proxy with Your Own Server (FREE)

### Cost: FREE + domain ($10/year)

**Pros:**
- ✅ Free
- ✅ Full control
- ✅ Can use any domain
- ✅ Works with Streamlit Community Cloud (free tier)

**Cons:**
- ❌ Requires technical setup
- ❌ Need to maintain a server
- ❌ More complexity

### Requirements:
- Your own domain ($10-15/year)
- A VPS/server (can use free tier from Oracle Cloud, AWS Free Tier, etc.)
- Basic server administration knowledge

### Setup Steps:

#### 1. Deploy to Streamlit Cloud (Free)

Deploy your app normally to get:
```
https://your-app.streamlit.app
```

#### 2. Set Up Server with Nginx

**On your server (Ubuntu/Debian):**

```bash
# Install Nginx
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/portfolio
```

**Nginx Configuration:**

```nginx
server {
    listen 80;
    server_name portfolio.yourdomain.com;

    location / {
        proxy_pass https://your-app.streamlit.app;
        proxy_set_header Host your-app.streamlit.app;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (required for Streamlit)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

**Enable the site:**

```bash
sudo ln -s /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 3. Add SSL Certificate (Free with Let's Encrypt)

```bash
sudo certbot --nginx -d portfolio.yourdomain.com
```

Follow the prompts to set up HTTPS.

#### 4. Update DNS Records

In your domain registrar (GoDaddy, Namecheap, etc.):

```
Type: A
Name: portfolio
Value: [Your server IP address]
TTL: 300
```

#### 5. Done!

Your app is now accessible at:
```
https://portfolio.yourdomain.com
```

---

## Option 3: Cloudflare Workers (FREE, Easy-ish)

### Cost: FREE

**Pros:**
- ✅ Free
- ✅ No server needed
- ✅ Cloudflare's CDN
- ✅ Easy SSL

**Cons:**
- ❌ May have issues with WebSockets
- ❌ Not officially supported

### Setup Steps:

#### 1. Add Domain to Cloudflare

1. Sign up at https://cloudflare.com (free)
2. Add your domain
3. Update nameservers at your registrar

#### 2. Create Cloudflare Worker

Go to Workers → Create a Service

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)

  // Replace with your Streamlit app URL
  const streamlitUrl = 'https://your-app.streamlit.app'

  // Build new URL
  const newUrl = streamlitUrl + url.pathname + url.search

  // Fetch from Streamlit
  const response = await fetch(newUrl, {
    method: request.method,
    headers: request.headers,
    body: request.body
  })

  // Return response
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers
  })
}
```

#### 3. Add Custom Domain

Workers → Your worker → Triggers → Add route:
```
portfolio.yourdomain.com/*
```

#### 4. DNS Setup

In Cloudflare DNS:
```
Type: CNAME
Name: portfolio
Value: your-app.streamlit.app
Proxy: Enabled (orange cloud)
```

**Note:** This may have issues with Streamlit's WebSocket connections. Test thoroughly.

---

## Option 4: Deploy to Different Platform with Custom Domain Support

### Platforms that support custom domains on free/cheap tiers:

#### Railway ($5/month)
- ✅ Custom domains included
- ✅ Easy setup
- ✅ Good for Streamlit

**Setup:**
1. Deploy to Railway (see Railway deployment guide)
2. Settings → Domains → Add custom domain
3. Add CNAME record to your DNS
4. Done!

**Cost:** $5/month + domain

---

#### Render.com (Free tier or $7/month)
- ✅ Custom domains on free tier
- ✅ Easy setup
- ✅ Auto-SSL

**Setup:**
1. Deploy to Render
2. Dashboard → Settings → Custom Domain
3. Add your domain
4. Update DNS (CNAME or A record)
5. Done!

**Cost:** FREE (with limitations) or $7/month

---

#### Fly.io (Free tier available)
- ✅ Custom domains on free tier
- ✅ Good performance
- ✅ Easy setup

**Setup:**
1. Deploy to Fly.io
2. `fly certs add portfolio.yourdomain.com`
3. Update DNS records
4. Done!

**Cost:** FREE (with limits)

---

## Comparison Table

| Option | Cost | Ease | Limitations |
|--------|------|------|-------------|
| **Streamlit Teams** | $250/mo | ⭐⭐⭐⭐⭐ | None - official |
| **Reverse Proxy** | FREE | ⭐⭐ | Need server |
| **Cloudflare Workers** | FREE | ⭐⭐⭐ | WebSocket issues |
| **Railway** | $5/mo | ⭐⭐⭐⭐ | None |
| **Render.com** | FREE/$7 | ⭐⭐⭐⭐ | Free tier sleeps |
| **Fly.io** | FREE | ⭐⭐⭐ | Resource limits |

---

## 🎯 Recommended Approach

### For Personal Use (Budget-Conscious):

**Best Option: Railway ($5/month)**

1. Deploy to Railway instead of Streamlit Cloud
2. Add custom domain in Railway settings (included!)
3. Update DNS
4. Done!

**Why Railway?**
- Cheap ($5/month)
- Custom domains included
- No technical setup needed
- Perfect for Streamlit apps
- Always-on (no sleeping)

### For Business Use:

**Best Option: Streamlit Cloud for Teams ($250/month)**

Official support, zero configuration, professional-grade.

### For Free Option:

**Best Option: Render.com (Free tier)**

1. Deploy to Render.com
2. Add custom domain (free!)
3. Accept that it sleeps after 15 minutes of inactivity
4. Done!

---

## Step-by-Step: Railway with Custom Domain (Recommended)

### Prerequisites:
- Domain purchased (GoDaddy, Namecheap, etc.)
- GitHub account

### Steps:

#### 1. Deploy to Railway

```bash
# Make sure code is pushed to GitHub
git push origin main

# Go to https://railway.app
# Sign up with GitHub
# Click "New Project" → "Deploy from GitHub repo"
# Select your llm_momentum_strategy repo
```

#### 2. Configure Railway

**Build settings:**
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0`

**Environment variables:**
```
OPENAI_API_KEY=sk-...
```

#### 3. Add Custom Domain

In Railway:
1. Your service → Settings → Networking
2. Custom domain → Add domain
3. Enter: `portfolio.yourdomain.com`
4. Railway provides CNAME value

#### 4. Update DNS

In your domain registrar:
```
Type: CNAME
Name: portfolio
Value: [CNAME provided by Railway]
TTL: 300
```

#### 5. Wait & Verify

- DNS propagation: 5-60 minutes
- SSL certificate: Auto-provisioned by Railway
- Your app will be live at: `https://portfolio.yourdomain.com`

**Cost:** $5/month + domain (~$10/year) = **~$70/year total**

---

## Troubleshooting

### Custom domain not working?

**Check DNS:**
```bash
dig portfolio.yourdomain.com
```

**Check SSL:**
```bash
curl -I https://portfolio.yourdomain.com
```

### WebSocket issues?

Ensure your reverse proxy includes:
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### SSL certificate issues?

Most platforms auto-provision SSL. Wait 15-30 minutes after DNS propagation.

---

## Summary

### What I Recommend:

**For you (personal use):**

Deploy to **Railway** with custom domain:
- ✅ Only $5/month (+ domain)
- ✅ Custom domain included
- ✅ Easy setup (20 minutes)
- ✅ No technical server management
- ✅ Always-on, no sleeping
- ✅ Perfect for Streamlit

**vs. Streamlit Cloud + reverse proxy:**
- Easier setup
- No server to maintain
- Similar cost (~$5/mo vs FREE+server)
- More reliable

**vs. Streamlit Teams ($250/mo):**
- 50x cheaper
- Same features for your use case
- Custom domain included

---

## Next Steps

1. **Choose platform:** Railway recommended
2. **Buy domain:** ~$10/year (GoDaddy, Namecheap, etc.)
3. **Deploy:** Follow steps above
4. **Add domain:** In platform settings
5. **Update DNS:** Point to platform
6. **Done!** Your app at `portfolio.yourdomain.com`

---

**Questions? Each platform has detailed docs and support!**
