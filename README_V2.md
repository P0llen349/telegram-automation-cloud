# 🚀 Cloud Automation Bot V2 - Google Drive Queue

**Complete cloud-based ticket automation triggered from Telegram - Works with corporate firewalls!**

---

## 🎯 What This Does

Send **"RUNNIT"** from Telegram on your phone → Your work computer automatically:
1. Downloads email from Outlook
2. Processes tickets to GPRS format
3. Uploads to Google Sheets
4. Sends you confirmation on Telegram

**Works from anywhere in the world! ☁️**

---

## 🏗️ Architecture

```
📱 Your Phone
    ↓ (Send "RUNNIT")
☁️ Cloud Bot (Railway)
    ↓ (Writes command)
📁 Google Drive Queue
    ↑ (Polls every 30s)
💻 Work Computer
    ↓ (Runs automation)
📊 Outlook → Excel → Google Sheets
    ↓ (Writes result)
📁 Google Drive Queue
    ↑ (Checks for results)
☁️ Cloud Bot
    ↓ (Sends confirmation)
📱 Your Phone
```

**Key Benefit:** Work computer makes OUTBOUND requests only (allowed through corporate firewall)!

---

## 📦 What's In This Folder

### **Cloud Components** (Runs on Railway)
- `cloud_bot_v2.py` - Main Telegram bot (uses Google Drive queue)
- `gdrive_queue.py` - Google Drive queue manager
- `Procfile` - Railway startup config
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version (3.11.9)

### **Work Computer Components**
- `work_computer_poller.py` - Polls Google Drive and runs automation
- `START_WORK_POLLER.bat` - Easy start script for work computer

### **Configuration**
- `google_credentials.json` - Google API credentials
- `.gitignore` - Git ignore rules

---

## 🚀 DEPLOYMENT GUIDE

### **Part 1: Cloud Bot** (Already Done! ✅)

The cloud bot is deployed on Railway and running!

**What it does:**
- ✅ Receives "RUNNIT" from Telegram
- ✅ Writes command to Google Drive
- ✅ Waits for result
- ✅ Sends result back to Telegram

---

### **Part 2: Work Computer Setup** (Do This!)

#### **Step 1: Verify Files**

Make sure you have these files in `Cloud_Automation` folder:
- ✅ `work_computer_poller.py`
- ✅ `START_WORK_POLLER.bat`
- ✅ `google_credentials.json`
- ✅ `gdrive_queue.py`

#### **Step 2: Start the Poller**

1. **Double-click:** `START_WORK_POLLER.bat`
2. You should see:
   ```
   WORK COMPUTER POLLER - STARTED
   Polling interval: 30 seconds
   Waiting for commands...
   ```
3. **Keep this window open!** (Minimize it if you want)

**That's it!** The poller is now running.

---

## 📱 HOW TO USE

### **From Your Phone:**

1. Open Telegram
2. Find your bot
3. Send: `/start` (first time only)
4. Send: `RUNNIT`
5. Wait 20-60 seconds
6. Get success message! ✅

### **What Happens:**

```
[00:00] You send "RUNNIT" from your phone
[00:01] Cloud bot writes command to Google Drive
[00:05] Work computer picks up command (next 30s poll)
[00:06] Local automation starts
[00:40] Automation completes (~35s)
[00:41] Result written to Google Drive
[00:45] Cloud bot finds result (next 10s poll)
[00:46] You receive success message!
```

**Total time:** ~45-60 seconds

---

## 🔧 TROUBLESHOOTING

### **Issue: Bot doesn't respond**

**Check:**
1. Is Railway deployment active? (Check Railway dashboard)
2. Is bot token correct?

**Fix:** Restart Railway deployment

---

### **Issue: Timeout waiting for result**

**Check:**
1. Is work computer ON?
2. Is `START_WORK_POLLER.bat` running?
3. Check poller logs in `Cloud_Automation/logs/`

**Fix:**
- Start the work poller: Run `START_WORK_POLLER.bat`
- Check log file for errors

---

### **Issue: Automation fails on work computer**

**Check poller logs:**
- Location: `Cloud_Automation/logs/work_poller_YYYYMMDD.log`
- Look for ERROR lines

**Common issues:**
- Automation script path wrong
- Outlook not open
- Google Drive access issues

---

## 📊 MONITORING

### **Check Cloud Bot Status:**
Send `/status` on Telegram

Shows:
- Bot status
- Queue connection
- Pending commands/results

### **Check Work Computer:**
Look at the poller window - should say:
```
Still polling... (HH:MM:SS)
```

### **View Logs:**
- Work computer: `Cloud_Automation/logs/work_poller_YYYYMMDD.log`
- Railway: Click "View logs" in Railway dashboard

---

## ⚙️ ADVANCED CONFIGURATION

### **Change Polling Interval:**

Edit `work_computer_poller.py`:
```python
POLL_INTERVAL = 30  # Change to 15, 60, etc.
```

### **Run Poller as Windows Service:**

Use NSSM (already installed):
```batch
nssm install WorkComputerPoller
Path: Z:\...\Python\python.exe
Arguments: Z:\...\Cloud_Automation\work_computer_poller.py
```

---

## 🎉 SUCCESS CHECKLIST

- [x] Cloud bot deployed on Railway
- [x] Environment variables set
- [x] Google credentials uploaded
- [ ] Work computer poller running
- [ ] Tested with "RUNNIT" from Telegram
- [ ] Received success message

---

## 💡 BENEFITS

✅ **Works from anywhere** - Send "RUNNIT" from any location
✅ **No VPN needed** - Uses Google Drive as intermediary
✅ **Firewall friendly** - Only outbound HTTPS requests
✅ **Secure** - Only you can trigger (Telegram user ID)
✅ **Reliable** - Uses your existing working automation
✅ **Simple** - One command does everything

---

## 🆘 SUPPORT

**If stuck:**
1. Check Railway logs (cloud bot)
2. Check work poller logs (work computer)
3. Send `/status` on Telegram
4. Verify Google Drive access

---

**Created:** January 28, 2026
**Version:** 2.0 - Google Drive Queue Architecture
**Status:** ✅ Ready for deployment!

---

*Now you can run your automation from anywhere in the world! 🌍*
