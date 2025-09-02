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
6. For Android device control: Ensure ADB is installed and your Android device is connected with USB debugging enabled.

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

