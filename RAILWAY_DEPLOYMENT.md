# Deploy StudyBuddy to Railway.app

## Quick Fix: Database Migration Error

If you see `Could not parse SQLAlchemy URL from string ''` error:

**The Issue**: Migrations need DATABASE_URL to be set first.

**The Fix**:
1. Deploy backend WITHOUT migrations in start command
2. After backend is running, run migrations via Railway CLI:
   ```bash
   railway run alembic upgrade head
   ```

See **Step 4e** below for detailed instructions.

---

## Why Railway?

✅ **All-in-one**: Backend, Frontend, Database in one dashboard
✅ **Simple**: Deploy in 10 minutes
✅ **GitHub Integration**: Auto-deploy on push
✅ **Free Trial**: $5 credit per month (lasts ~1 month for this app)
✅ **No Sleep**: Your app stays awake (unlike Render free tier)

**Cost**: ~$5-10/month after free trial

---

## Prerequisites

- GitHub account with your StudyBuddy code
- Railway account (sign up at https://railway.app)
- Google OAuth credentials
- Gemini API key

---

## Step 1: Create Railway Account

1. Go to https://railway.app
2. Click **"Login with GitHub"**
3. Authorize Railway to access your repos

---

## Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your **StudyBuddy** repository
4. Railway will detect it's a monorepo

---

## Step 3: Deploy Database (PostgreSQL)

1. In your project dashboard, click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway creates the database instantly
4. Click on the database service
5. Go to **"Variables"** tab
6. Copy the **`DATABASE_URL`** (you'll need this)

**Note**: Railway automatically creates these variables:
- `PGHOST`
- `PGPORT`
- `PGUSER`
- `PGPASSWORD`
- `PGDATABASE`
- `DATABASE_URL` (full connection string)

---

## Step 4: Deploy Backend

### 4a. Add Backend Service

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your StudyBuddy repo again
3. Railway will ask for **Root Directory**
4. Enter: `backend`
5. Click **"Add variables"**

### 4b. Configure Environment Variables

In the **Variables** tab, add:

```bash
# Database (Reference the PostgreSQL service)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Google OAuth
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
GOOGLE_REDIRECT_URI=${{RAILWAY_PUBLIC_DOMAIN}}/auth/google/callback

# JWT
JWT_SECRET_KEY=<generate-random-32-char-string>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=168

# Gemini AI
GEMINI_API_KEY=<your-gemini-api-key>

# Frontend (will update after frontend deploys)
FRONTEND_URL=https://your-frontend-url.railway.app

# Python
PYTHONUNBUFFERED=1
```

**Tip**: Railway variables support references like `${{Postgres.DATABASE_URL}}` which automatically links to your database!

### 4c. Configure Build Settings

1. Go to **"Settings"** tab
2. Under **"Build"**:
   - **Builder**: Nixpacks (auto-detected)
   - **Install Command**: Leave empty (Railway auto-detects requirements.txt)
   - **Build Command**: Leave empty
3. Under **"Deploy"**:
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Click **"Generate Domain"** to get a public URL

**Note**: We'll run migrations separately after the service is deployed and DATABASE_URL is available.

### 4d. Deploy

- Railway automatically starts deploying
- Wait 2-3 minutes
- Check **"Deployments"** tab for progress
- Once live, copy your backend URL: `https://studybuddy-backend-production-xxxx.up.railway.app`

### 4e. Run Database Migrations

After your backend is deployed, run migrations:

**Option 1: Via Railway CLI** (Recommended)
```bash
# Install Railway CLI if you haven't
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Select your backend service
railway service

# Run migrations
railway run bash railway_migrate.sh
```

**Option 2: Via Railway Dashboard**
1. Go to your **backend service**
2. Click the **overflow menu (...)** → **"Deploy"**
3. In the deploy logs, once it says "Waiting for application startup"
4. Open a new tab and go to the service
5. Click **"..." → "Shell"** (if available) or use CLI

**Option 3: One-time migration command**
In Railway CLI:
```bash
railway run alembic upgrade head
```

Your database tables should now be created! ✅

---

## Step 5: Deploy Frontend

### 5a. Add Frontend Service

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your StudyBuddy repo again
3. **Root Directory**: `frontend`
4. Click **"Add variables"**

### 5b. Configure Environment Variables

```bash
NEXT_PUBLIC_API_URL=<your-backend-url-from-step-4>
```

**Example**:
```bash
NEXT_PUBLIC_API_URL=https://studybuddy-backend-production-xxxx.up.railway.app
```

### 5c. Configure Build Settings

1. Go to **"Settings"** tab
2. Under **"Build"**:
   - **Builder**: Nixpacks
   - **Install Command**: `npm install`
   - **Build Command**: `npm run build`
3. Under **"Deploy"**:
   - **Start Command**: `npm start`
   - **Port**: 3000
4. Click **"Generate Domain"**

### 5d. Deploy

- Railway starts deploying
- Wait 2-3 minutes
- Copy your frontend URL: `https://studybuddy-frontend-production-xxxx.up.railway.app`

---

## Step 6: Update Backend FRONTEND_URL

1. Go back to your **backend service**
2. Click **"Variables"** tab
3. Update `FRONTEND_URL` with your frontend URL from Step 5
4. Backend will redeploy automatically (~1 minute)

---

## Step 7: Update Google OAuth Settings

1. Go to **Google Cloud Console**: https://console.cloud.google.com/
2. Navigate to **APIs & Services** → **Credentials**
3. Click your OAuth 2.0 Client ID
4. **Add Authorized Redirect URIs**:
   ```
   https://studybuddy-backend-production-xxxx.up.railway.app/auth/google/callback
   ```
5. **Add Authorized JavaScript Origins**:
   ```
   https://studybuddy-frontend-production-xxxx.up.railway.app
   ```
6. Click **"Save"**

---

## Step 8: Test Your Deployment

1. Visit your frontend URL: `https://studybuddy-frontend-production-xxxx.up.railway.app`
2. Click **"Sign in with Google"**
3. Approve permissions
4. Test features:
   - ✅ Create assignment
   - ✅ View dashboard
   - ✅ Create custom event
   - ✅ Sync to Google Calendar

---

## Railway Dashboard Overview

Your project will have 3 services:

```
📦 StudyBuddy Project
├── 🗄️  Postgres (Database)
├── 🐍  Backend (FastAPI)
└── ⚛️  Frontend (Next.js)
```

**Each service has**:
- **Deployments**: View build logs and history
- **Metrics**: CPU, Memory, Network usage
- **Variables**: Environment variables
- **Settings**: Build and deploy config
- **Logs**: Real-time application logs

---

## Monitoring & Logs

### View Logs

1. Click on any service
2. Go to **"Deployments"** tab
3. Click on latest deployment
4. View **"Build Logs"** and **"Deploy Logs"**

### Real-time Logs

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# View logs
railway logs
```

---

## Auto-Deployment

Railway automatically deploys when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin main

# Railway automatically:
# 1. Detects the push
# 2. Rebuilds affected services
# 3. Deploys new version
# 4. Zero downtime (if configured)
```

---

## Cost Breakdown

Railway charges based on usage:

### Free Trial
- $5 credit per month
- **Lasts ~3-4 weeks for this app**

### After Trial (Developer Plan - $5/mo)
**Included**:
- $5 in credits
- 500 GB bandwidth
- 500 GB-hours compute

**Your app usage** (estimated):
- Backend: ~$3/mo (always on)
- Frontend: ~$2/mo (static + SSR)
- Database: ~$2/mo (storage + compute)
- **Total**: ~$7/mo (includes the $5 plan + $2 overage)

### Cost Optimization Tips

1. **Sleep backend during inactivity** (save ~40%):
   ```bash
   # Settings → Deploy → Sleep when inactive (after 10 min)
   ```

2. **Use static export for frontend** (save ~50%):
   ```bash
   # frontend/package.json
   "scripts": {
     "build": "next build && next export"
   }
   # Settings → Start Command → "npx serve out"
   ```

3. **Optimize database** (save ~20%):
   - Enable connection pooling
   - Use pgBouncer (built-in on Railway)

**Optimized cost**: ~$5-6/mo

---

## Railway vs Render + Vercel

| Feature | Railway | Render + Vercel |
|---------|---------|-----------------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ Single dashboard | ⭐⭐⭐ Two platforms |
| **Cost (Free Tier)** | $5 credit/mo (~1 month) | 90 days free |
| **Cost (Paid)** | ~$7/mo | ~$7/mo |
| **Backend Sleep** | Optional | Yes (free tier) |
| **Custom Domains** | ✅ Free | ✅ Free |
| **CI/CD** | ✅ Built-in | ✅ Built-in |
| **Logs** | ⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Good |
| **Metrics** | ⭐⭐⭐⭐⭐ Real-time | ⭐⭐⭐ Basic |
| **Database Backups** | ✅ Daily | ✅ Daily |
| **Learning Curve** | ⭐⭐⭐⭐⭐ Very Easy | ⭐⭐⭐⭐ Easy |

**Recommendation**:
- **Railway** if you want simplicity and don't mind $7/mo
- **Render + Vercel** if you want 90 days free and can handle two platforms

---

## Custom Domain Setup

### Backend

1. Go to **Backend service** → **Settings**
2. Click **"Generate Domain"** or **"Custom Domain"**
3. Enter: `api.yourdomain.com`
4. Add CNAME record to your DNS:
   ```
   api.yourdomain.com → studybuddy-backend-production.up.railway.app
   ```

### Frontend

1. Go to **Frontend service** → **Settings**
2. Click **"Custom Domain"**
3. Enter: `yourdomain.com` or `app.yourdomain.com`
4. Add DNS records (Railway provides exact values)

**Don't forget to update**:
- `FRONTEND_URL` in backend variables
- `GOOGLE_REDIRECT_URI` in backend variables
- Google OAuth authorized URIs

---

## Troubleshooting

### Build Fails

**Check logs**:
1. Go to service → Deployments
2. Click failed deployment
3. View **Build Logs**

**Common issues**:
- Missing `requirements.txt` or `package.json`
- Wrong root directory
- Python version mismatch

**Fix**:
- Ensure `backend/requirements.txt` exists
- Add `runtime.txt` with `python-3.12` if needed

### Backend Can't Connect to Database

**Check**:
- `DATABASE_URL` variable is set
- Database service is running (green dot)
- Reference syntax: `${{Postgres.DATABASE_URL}}`

### Frontend Can't Reach Backend

**Check**:
- `NEXT_PUBLIC_API_URL` is set correctly
- Backend has public domain generated
- CORS is configured in backend (already done in your code)

### OAuth Fails

**Check**:
- Google OAuth redirect URI matches exactly
- No trailing slashes
- HTTPS is used (Railway provides SSL automatically)

---

## Advanced: Railway CLI

Install CLI for advanced features:

```bash
# Install
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# View logs
railway logs

# Shell into service
railway shell

# Run migrations
railway run alembic upgrade head

# Environment variables
railway variables
railway variables set KEY=value
```

---

## Database Management

### Access via Railway Dashboard

1. Click **Postgres** service
2. Go to **"Data"** tab
3. Browse tables and run queries

### Access via CLI

```bash
# Get connection string
railway variables | grep DATABASE_URL

# Connect with psql
psql <DATABASE_URL>

# Or use Railway CLI
railway connect postgres
```

### Backups

Railway automatically backs up your database daily:

1. Go to **Postgres** service
2. Click **"Backups"** tab
3. View/download backups
4. Restore from backup

---

## Scaling (When You Get Popular!)

Railway makes scaling easy:

### Vertical Scaling
1. Go to service → **Settings**
2. Under **"Resources"**:
   - Increase CPU (0.5 → 2 vCPUs)
   - Increase Memory (512MB → 8GB)

### Horizontal Scaling
1. Add more service replicas
2. Railway load balances automatically

### Database Scaling
1. Upgrade to larger database plan
2. Enable read replicas
3. Connection pooling (built-in)

---

## Migration from Local to Railway

Your local setup is already ready! Railway will:

1. ✅ Detect Python and install dependencies
2. ✅ Detect Next.js and build frontend
3. ✅ Create PostgreSQL database
4. ✅ Run migrations on startup

Just push to GitHub and deploy! 🚀

---

## Helpful Links

- **Railway Dashboard**: https://railway.app/dashboard
- **Railway Docs**: https://docs.railway.app/
- **Railway Discord**: https://discord.gg/railway (great support!)
- **Status Page**: https://status.railway.app/

---

## Support

If you get stuck:

1. **Check Railway docs**: Very comprehensive
2. **Railway Discord**: Super responsive community
3. **GitHub Issues**: Report bugs to Railway team
4. **Your deployment logs**: Most answers are in the logs!

---

## Summary: Quick Deploy Checklist

- [ ] Push code to GitHub
- [ ] Create Railway account
- [ ] Create new project from GitHub
- [ ] Add PostgreSQL database
- [ ] Deploy backend with environment variables
- [ ] Deploy frontend with API URL
- [ ] Update Google OAuth redirect URIs
- [ ] Test login and features
- [ ] Set up custom domain (optional)
- [ ] Enable monitoring and alerts

**Time to deploy**: ~15 minutes
**Cost**: $5 credit free, then ~$7/mo

You're all set! 🎉
