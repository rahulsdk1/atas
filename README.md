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

### 📱 Universal Android Device Compatibility

**✅ FULLY TESTED & COMPATIBLE DEVICES:**

#### **Android Versions:**
- ✅ Android 5.0-5.1 (API 21-22) - Full support
- ✅ Android 6.0-7.1 (API 23-25) - Full support
- ✅ Android 8.0-9.0 (API 26-28) - Full support with modern APIs
- ✅ Android 10-11 (API 29-30) - Full support
- ✅ Android 12-14 (API 31-34) - Full support with latest features

#### **Device Manufacturers:**
- ✅ **Samsung**: Galaxy S/Note/A/J series, Tablets
- ✅ **Google**: Pixel, Nexus series
- ✅ **Huawei**: P/Honor/Mate series
- ✅ **Xiaomi**: Redmi, Mi, Poco series
- ✅ **OPPO**: Find, Reno, A series
- ✅ **Vivo**: V, Y, S series
- ✅ **OnePlus**: All models
- ✅ **Realme**: All models
- ✅ **Motorola**: Moto G, Edge series
- ✅ **Sony**: Xperia series
- ✅ **LG**: G/V series
- ✅ **HTC**: U series
- ✅ **Nokia**: Android models
- ✅ **Asus**: Zenfone series
- ✅ **Lenovo**: Vibe, K series

#### **Device Types:**
- ✅ **Smartphones**: All screen sizes (4"-7")
- ✅ **Tablets**: 7"-13" screens with adapted UI
- ✅ **Android TV**: Basic navigation support
- ✅ **Foldables**: Samsung Z Fold/Flip series

### 📱 Supported Android Functions

**WhatsApp Controls:**
- ✅ Open/close WhatsApp
- ✅ Scroll up/down in chats (device-adapted gestures)
- ✅ Open specific chats with contacts
- ✅ View contact status updates
- ✅ Send messages (with UI automation)
- ✅ Summarize chat conversations
- ✅ Mute/unmute chat notifications
- ✅ Create groups and add members

**Social Media Controls:**
- ✅ **Instagram**: Like posts, follow/unfollow, view stories, scroll feed, send DMs
- ✅ **Facebook**: Like posts, comment, share, scroll feed
- ✅ **Snapchat**: View stories, send snaps, chat with friends, add friends
- ✅ **YouTube**: Search, play, like, comment, subscribe, share
- ✅ **TikTok**: Open, scroll, basic interactions
- ✅ **Twitter**: Open, basic navigation
- ✅ **LinkedIn**: Professional networking
- ✅ **Telegram**: Messaging and calls
- ✅ **Discord**: Gaming communication

**Device Controls:**
- ✅ Volume control (up/down/mute) - API-adapted
- ✅ Brightness adjustment - Multi-method fallback
- ✅ Flashlight control (on/off) - Camera API with fallbacks
- ✅ WiFi and Bluetooth toggle
- ✅ Screenshot capture
- ✅ Device lock/unlock
- ✅ Camera operations
- ✅ Gallery access

**Phone Call Management:**
- ✅ Make calls by name or number
- ✅ Contact lookup from device
- ✅ Answer incoming calls
- ✅ Reject incoming calls
- ✅ Check call status
- ✅ Automatic country code formatting
- ✅ Incoming call notifications with caller info

**Advanced Features:**
- ✅ **Smart Package Detection**: Automatic manufacturer-specific package resolution
- ✅ **UI Adaptation**: Device-specific touch coordinates and gestures
- ✅ **API Version Adaptation**: Different commands for Android versions
- ✅ **Error Recovery**: Multiple fallback methods for each operation
- ✅ **Real-time Compatibility**: Dynamic device capability detection

**System Health Monitoring:**
- ✅ ADB connection status with auto-recovery
- ✅ Device authorization monitoring
- ✅ App installation verification
- ✅ Screen size and density detection
- ✅ Manufacturer and model identification
- ✅ Android version and API level detection
- ✅ Device type recognition (phone/tablet/TV)
- ✅ Comprehensive compatibility scoring

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

