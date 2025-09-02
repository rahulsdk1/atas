# 🧠 Friday - Your Personal AI Assistant

This is a Python-based AI assistant inspired by *Jarvis*, capable of:

- 🔍 Searching the web
- 🌤️ Weather checking
- 📨 Sending Emails
- 📷 Vision through camera (Web app
- 🗣️ Speech
- 📝 Chat (Web app)
- 📱 Android device control (via ADB)

This agent uses LiveKit that is 100% free!

---

## 📽️ Tutorial Video

Before you start, **make sure to follow this tutorial to set up the voice agent correctly**:  
🎥 [Watch here](https://youtu.be/An4NwL8QSQ4?si=v1dNDDonmpCG1Els)

---
1. Create the Virtual Envrionment first!
2. Activate it
3. Install all the required libraries in the requirements.txt file
4. In the .ENV - File you should paste your API-Keys and your LiveKit Secret, LiveKit URL.
   If you want to use the Send Email Tool also specify your Gmail Account and App Password.
5. Make sure that your LiveKit Account is set-up correctly.
6. **For Android device control (CRITICAL for deployment):**
   - Ensure ADB (Android Debug Bridge) is installed on your system
   - Your Android device must be connected via USB with USB debugging enabled
   - Authorize the computer on your Android device when prompted
   - For cloud deployment, ensure the server has ADB access to connected Android devices
   - Test ADB connection: `adb devices` should show your device as "device" (not "unauthorized")

### 🔧 Android Device Setup Requirements

**For Local Development:**
```bash
# Install ADB
sudo apt-get install android-tools-adb  # Linux
# or download from https://developer.android.com/studio/releases/platform-tools

# Enable USB Debugging on Android device:
# 1. Go to Settings > Developer Options
# 2. Enable "USB Debugging"
# 3. Connect device via USB
# 4. Authorize computer when prompted

# Verify connection
adb devices  # Should show device as "device"
```

**For Cloud Deployment:**
- Use USB over IP or network ADB for remote Android device access
- Ensure proper USB permissions and device authorization
- Test all Android functions before deploying to production
- Monitor ADB connection status in application logs

### 📱 Supported Android Functions

**WhatsApp Controls:**
- Open/close WhatsApp
- Scroll up/down in chats
- Open specific chats with contacts
- View contact status updates
- Send messages (with UI automation)
- Summarize chat conversations
- Mute/unmute chat notifications

**Social Media Controls:**
- Instagram: Like posts, follow users, view stories, scroll feed
- Facebook: Like posts, comment, share, scroll feed
- Snapchat: View stories, send snaps, chat with friends
- YouTube: Search, play, like, comment, subscribe
- TikTok, Twitter, LinkedIn, Telegram, Discord

**Device Controls:**
- Volume control (up/down/mute)
- Brightness adjustment
- WiFi and Bluetooth toggle
- Screenshot capture
- Device lock/unlock
- Camera operations

**System Health Monitoring:**
- ADB connection status
- Device authorization check
- App installation verification
- Screen size and density detection

---

## 🚀 Docker Deployment

### Build and Run Locally
```bash
docker build -t atas-voice-assistant .
docker run -p 5000:5000 --env-file .env atas-voice-assistant
```

### Deploy to Google Cloud Run
1. **Push to GitHub first**
2. **Deploy both token server and agent:**
   ```bash
   gcloud run deploy atas-voice-assistant \
     --source https://github.com/rahulsdk1/atas \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars LIVEKIT_API_KEY="your-key",LIVEKIT_API_SECRET="your-secret",LIVEKIT_URL="your-url"
   ```

### Services Running:
- **Token Server**: `https://your-service-url/token` (port 5000)
- **LiveKit Agent**: Runs as background worker for voice interactions

