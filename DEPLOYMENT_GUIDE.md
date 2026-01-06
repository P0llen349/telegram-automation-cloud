# CLOUD AUTOMATION - DEPLOYMENT GUIDE

**Fully cloud-based ticket automation with Telegram bot**

---

## 🎯 What This Is

A **completely cloud-based** automation system that:
- ✅ Runs 24/7 on Railway (free tier)
- ✅ Downloads emails via IMAP (no local Outlook needed)
- ✅ Processes GPRS tickets in the cloud
- ✅ Uploads to Google Sheets
- ✅ Controlled via Telegram from anywhere

**No desktop computer needed!**

---

## 📦 Files in This Folder

```
Cloud_Automation/
├── cloud_bot.py              ← Main bot (integrates everything)
├── email_downloader.py        ← IMAP email downloader
├── ticket_processor.py        ← Ticket processing logic
├── google_credentials.json    ← Google API credentials
├── requirements.txt           ← Python dependencies
├── Procfile                   ← Railway startup command
├── .gitignore                ← Git ignore rules
└── DEPLOYMENT_GUIDE.md        ← This file
```

---

## 🚀 DEPLOYMENT STEPS

### Step 1: Create Railway Account (2 minutes)

1. Go to: https://railway.app/
2. Click "Start a New Project"
3. Sign up with GitHub (recommended) or email
4. ✅ Free tier: 500 hours/month (enough for 24/7 bot!)

---

### Step 2: Create New Project (1 minute)

1. Click "+ New Project"
2. Select "Deploy from GitHub repo"
3. Click "Deploy from local directory" (we'll use CLI method)

**OR simpler: Use "Empty Project"** and deploy via CLI

---

### Step 3: Install Railway CLI (3 minutes)

**On Windows:**
```powershell
# Using npm (if you have Node.js)
npm install -g @railway/cli

# OR download installer
# https://railway.app/cli
```

**Verify installation:**
```bash
railway --version
```

---

### Step 4: Login to Railway (1 minute)

```bash
cd "Z:\AAA-Mohammad Khair AbuShanab\ULTIMATE_BACKUP_FOLDER\Project_Organization\Cloud_Automation"
railway login
```

This will open your browser - authorize Railway CLI.

---

### Step 5: Link to Project (1 minute)

```bash
railway init
```

Follow prompts:
- Create new project
- Name it: "telegram-automation-bot"
- Select environment: production

---

### Step 6: Set Environment Variables (5 minutes)

These are your credentials - stored securely in Railway:

```bash
# Telegram
railway variables set BOT_TOKEN="8401341002:AAHf4fB2bp4JATnaYo3RbK9EG_ziRHxz1f4"
railway variables set AUTHORIZED_USER_ID="1003476862"
railway variables set TRIGGER_CODEWORD="RUNNIT"

# Outlook/Email
railway variables set OUTLOOK_EMAIL="mkhair.abushanab@jepco.com.jo"
railway variables set OUTLOOK_PASSWORD="Z%275067870790us"
railway variables set EMAIL_SENDER="mohammad.jarrar@jepco.com.jo"
railway variables set EMAIL_SUBJECT="Open tickets Summary"

# Google Sheets
railway variables set GOOGLE_SHEET_ID="1bfdWgSWpk25wt0tq5PPLuLySfJ-Vm4Ou7TVR2gVprag"
```

---

### Step 7: Upload Google Credentials (IMPORTANT!)

Railway needs your `google_credentials.json` file.

**Method A: Using Railway Dashboard (EASIEST)**

1. Go to Railway dashboard: https://railway.app/
2. Click your project
3. Click "Variables" tab
4. Click "Raw Editor"
5. Add this variable:
   ```
   GOOGLE_CREDENTIALS_JSON=<paste entire contents of google_credentials.json here>
   ```
6. Save

**Method B: Using base64 encoding**

```bash
# On Windows (PowerShell)
$credentials = Get-Content google_credentials.json -Raw
$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($credentials))
railway variables set GOOGLE_CREDENTIALS_BASE64=$encoded
```

Then modify `cloud_bot.py` to decode this at runtime.

---

### Step 8: Deploy to Railway (2 minutes)

```bash
railway up
```

This will:
- ✅ Upload all files to Railway
- ✅ Install dependencies from requirements.txt
- ✅ Start the bot using Procfile
- ✅ Show you the logs

---

### Step 9: Check Logs (1 minute)

```bash
railway logs
```

You should see:
```
======================================================================
CLOUD AUTOMATION BOT - STARTING
======================================================================
Authorized user: 1003476862
Trigger codeword: RUNNIT
Bot is now running... Press Ctrl+C to stop
```

---

### Step 10: Test on Telegram (2 minutes)

1. Open Telegram
2. Find your bot: @OneClickRun_bot
3. Send: `/start`
4. Send: `RUNNIT`
5. ✅ Wait for automation to complete!

---

## 🎉 SUCCESS!

Your bot is now running 24/7 in the cloud!

**You can now:**
- ✅ Send `RUNNIT` from anywhere in the world
- ✅ Bot downloads emails, processes tickets, uploads to Sheets
- ✅ Receive results on Telegram
- ✅ No desktop computer needed!

---

## 🔧 MANAGING YOUR DEPLOYMENT

### View Logs
```bash
railway logs
```

### Check Status
```bash
railway status
```

### Redeploy (after code changes)
```bash
railway up
```

### View Variables
```bash
railway variables
```

### Stop Service
```bash
railway down
```

### Start Service
```bash
railway up
```

---

## 💰 COST

**Railway Free Tier:**
- 500 hours/month
- Your bot uses: ~720 hours/month (24/7)
- **You'll need ~$5/month after free tier**

**Alternative Free Options:**
- **Render:** 750 hours/month (more than enough!)
- **PythonAnywhere:** Limited but always free

**Recommendation:** Start with Railway free tier, upgrade if needed (~$5/month)

---

## 🐛 TROUBLESHOOTING

### Bot doesn't start

**Check logs:**
```bash
railway logs
```

**Common issues:**
- Missing environment variable → Set it with `railway variables set`
- Google credentials missing → Upload google_credentials.json
- Wrong Python version → Railway uses Python 3.11+ automatically

### Bot doesn't respond on Telegram

**Check:**
1. Bot is running: `railway logs` should show "Bot is now running..."
2. Token is correct: Check BOT_TOKEN variable
3. User ID is correct: Check AUTHORIZED_USER_ID

### Email download fails

**Check:**
1. Outlook credentials correct: OUTLOOK_EMAIL and OUTLOOK_PASSWORD
2. IMAP enabled on Outlook account
3. Check logs for specific error

### Tickets not processing

**Check logs:**
```bash
railway logs
```

Look for errors in ticket processing step.

---

## 🔄 UPDATING THE BOT

When you make changes to the code:

1. **Edit files locally** (in Z:\...\Cloud_Automation)
2. **Test locally** (optional):
   ```bash
   python cloud_bot.py
   ```
3. **Deploy to Railway:**
   ```bash
   railway up
   ```
4. **Check logs:**
   ```bash
   railway logs
   ```

---

## 📊 MONITORING

### Check bot status via Telegram:
- Send: `/status`

### Check Railway dashboard:
- https://railway.app/
- View metrics, logs, usage

### Check Google Sheets:
- https://docs.google.com/spreadsheets/d/1bfdWgSWpk25wt0tq5PPLuLySfJ-Vm4Ou7TVR2gVprag/edit

---

## 🆘 SUPPORT

**If something goes wrong:**

1. Check Railway logs: `railway logs`
2. Test locally first: `python cloud_bot.py`
3. Verify all environment variables are set
4. Check that google_credentials.json is uploaded

**Railway Support:**
- https://railway.app/help
- Discord: https://discord.gg/railway

---

## ✅ POST-DEPLOYMENT CHECKLIST

- [ ] Railway account created
- [ ] Project created and linked
- [ ] All environment variables set
- [ ] google_credentials.json uploaded
- [ ] Bot deployed (`railway up`)
- [ ] Logs show "Bot is now running..."
- [ ] Tested with `/start` on Telegram
- [ ] Tested with `RUNNIT` on Telegram
- [ ] Automation completed successfully
- [ ] Google Sheets updated with data

---

**Created:** January 6, 2026
**Status:** Ready for deployment!
**Platform:** Railway (or Render/PythonAnywhere)

---

*Now your automation runs in the cloud, accessible from anywhere! 🚀*
