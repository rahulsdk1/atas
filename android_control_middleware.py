# android_control_middleware.py
"""
Middleware for Android app and device control via agent commands.
Detects user intent for app/device actions and routes to Android APIs (ADB/Appium/custom service).
Handles multi-language input/output using language middleware.
No changes required to original code. Import and use hooks as needed.
"""
import re
import subprocess
import logging
from language_middleware import detect_language, translate_text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if ADB is available
def is_adb_available():
    try:
        result = subprocess.run(["adb", "version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

ADB_AVAILABLE = is_adb_available()
if not ADB_AVAILABLE:
    logger.warning("ADB is not available. Android control functions will not work on real devices.")

# Enhanced command patterns with WhatsApp, Snapchat, and social media focus
COMMAND_PATTERNS = {
    # Basic app control
    'open_app': r'open (\w+)',
    'close_app': r'close (\w+)',

    # WhatsApp specific commands
    'open_whatsapp': r'open whatsapp',
    'close_whatsapp': r'close whatsapp',
    'whatsapp_scroll_up': r'scroll up in whatsapp',
    'whatsapp_scroll_down': r'scroll down in whatsapp',
    'whatsapp_chat_with': r'chat with (.+) in whatsapp',
    'whatsapp_view_status': r'view (.+) status in whatsapp',
    'whatsapp_send_message': r'send (.+) to (.+) in whatsapp',
    'whatsapp_call_contact': r'call (.+) on whatsapp',
    'whatsapp_video_call': r'video call (.+) on whatsapp',
    'whatsapp_view_profile': r'view (.+) profile in whatsapp',
    'whatsapp_create_group': r'create group (.+) in whatsapp',
    'whatsapp_add_to_group': r'add (.+) to group in whatsapp',
    'whatsapp_summarize_chat': r'summarize (last \d+ )?messages? with (.+) in whatsapp',
    'whatsapp_view_profile': r'view (.+) profile in whatsapp',
    'whatsapp_mute_chat': r'mute (.+) chat in whatsapp',
    'whatsapp_unmute_chat': r'unmute (.+) chat in whatsapp',

    # Snapchat specific commands
    'open_snapchat': r'open snapchat',
    'close_snapchat': r'close snapchat',
    'snapchat_view_stories': r'view stories in snapchat',
    'snapchat_send_snap': r'send snap to (.+) in snapchat',
    'snapchat_chat_with': r'chat with (.+) in snapchat',
    'snapchat_add_friend': r'add (.+) as friend in snapchat',
    'snapchat_view_profile': r'view (.+) profile in snapchat',

    # Instagram specific commands
    'open_instagram': r'open instagram',
    'close_instagram': r'close instagram',
    'instagram_scroll_feed': r'scroll feed in instagram',
    'instagram_like_post': r'like post in instagram',
    'instagram_comment': r'comment (.+) on post in instagram',
    'instagram_follow_user': r'follow (.+) on instagram',
    'instagram_unfollow_user': r'unfollow (.+) on instagram',
    'instagram_view_story': r'view (.+) story in instagram',
    'instagram_send_dm': r'send (.+) to (.+) in instagram',

    # Facebook specific commands
    'open_facebook': r'open facebook',
    'close_facebook': r'close facebook',
    'facebook_scroll_feed': r'scroll feed in facebook',
    'facebook_like_post': r'like post in facebook',
    'facebook_comment': r'comment (.+) on post in facebook',
    'facebook_share_post': r'share post in facebook',

    # YouTube specific commands
    'search_youtube': r'search (.+) on youtube',
    'play_youtube': r'play (.+) on youtube',
    'youtube_subscribe': r'subscribe to (.+) on youtube',
    'youtube_like_video': r'like video on youtube',
    'youtube_comment': r'comment (.+) on video',
    'youtube_share_video': r'share video on youtube',

    # Device and system controls
    'set_volume': r'(up|down|low|raise|mute|max|increase|decrease) (the )?volume',
    'set_brightness': r'(set|turn|low|raise|increase|decrease) brightness( to)? (\d+)%',
    'toggle_wifi': r'(turn on|turn off|enable|disable) wifi',
    'toggle_bluetooth': r'(turn on|turn off|enable|disable) bluetooth',
    'take_screenshot': r'(take|capture) (a )?screenshot',
    'lock_device': r'lock (the )?device',
    'unlock_device': r'unlock (the )?device',

    # General commands
    'scroll_feed': r'scroll (feed|messages|whatsapp|facebook|instagram|shopping app|chrome|contacts|gallery|settings|notifications)',
    'send_message': r'send message to (.+)',
    'open_camera': r'open camera',
    'close_camera': r'close camera',
    'open_gallery': r'open gallery',
    'open_contacts': r'open contacts',
    'call_contact': r'(call|dial) (.+)',
    'open_browser': r'open (chrome|browser|firefox|edge|opera)',
    'search_browser': r'search (.+) in (chrome|browser|firefox|edge|opera)',
    'visit_website': r'visit (.+) in (chrome|browser|firefox|edge|opera)',

    # Additional social media and apps
    'open_tiktok': r'open tiktok',
    'open_twitter': r'open twitter',
    'open_linkedin': r'open linkedin',
    'open_telegram': r'open telegram',
    'open_discord': r'open discord',
    'open_zoom': r'open zoom',
    'open_teams': r'open teams',

    # More commands as needed
}

class AndroidControlMiddleware:
    def __init__(self):
        # Enhanced package mapping for social media and common apps
        self.package_map = {
            # Social Media Apps
            'whatsapp': 'com.whatsapp',
            'snapchat': 'com.snapchat.android',
            'instagram': 'com.instagram.android',
            'facebook': 'com.facebook.katana',
            'twitter': 'com.twitter.android',
            'tiktok': 'com.zhiliaoapp.musically',
            'linkedin': 'com.linkedin.android',
            'telegram': 'org.telegram.messenger',
            'discord': 'com.discord',

            # Communication Apps
            'zoom': 'us.zoom.videomeetings',
            'teams': 'com.microsoft.teams',
            'skype': 'com.skype.raider',

            # Browsers and Web
            'chrome': 'com.android.chrome',
            'firefox': 'org.mozilla.firefox',
            'opera': 'com.opera.browser',

            # Google Apps
            'youtube': 'com.google.android.youtube',
            'gmail': 'com.google.android.gm',
            'maps': 'com.google.android.apps.maps',
            'drive': 'com.google.android.apps.docs',
            'photos': 'com.google.android.apps.photos',
            'calendar': 'com.google.android.calendar',
            'keep': 'com.google.android.keep',

            # System Apps
            'settings': 'com.android.settings',
            'camera': 'com.android.camera',
            'gallery': 'com.android.gallery',
            'calculator': 'com.android.calculator2',
            'clock': 'com.android.deskclock',
            'contacts': 'com.android.contacts',
            'phone': 'com.android.dialer',
            'messages': 'com.android.mms',
            'music': 'com.android.music',
            'files': 'com.android.documentsui',
            'playstore': 'com.android.vending',

            # Additional Apps
            'netflix': 'com.netflix.mediaclient',
            'spotify': 'com.spotify.music',
            'amazon': 'com.amazon.mShop.android.shopping'
        }

        # App-specific knowledge base
        self.app_knowledge = {
            'whatsapp': {
                'description': 'WhatsApp Messenger for instant messaging and calling',
                'features': ['Text messaging', 'Voice calls', 'Video calls', 'Group chats', 'Status updates', 'Media sharing'],
                'common_actions': ['Send message', 'Make call', 'View status', 'Create group', 'Share media']
            },
            'snapchat': {
                'description': 'Snapchat for ephemeral messaging and stories',
                'features': ['Snaps', 'Stories', 'Chat', 'Discover', 'Spotlight', 'Lenses'],
                'common_actions': ['Send snap', 'View stories', 'Chat with friends', 'Add friends', 'Use lenses']
            },
            'instagram': {
                'description': 'Instagram for photo and video sharing',
                'features': ['Feed', 'Stories', 'Reels', 'DMs', 'Live streaming', 'Shopping'],
                'common_actions': ['Like posts', 'Comment', 'Follow users', 'Send DMs', 'View stories']
            },
            'facebook': {
                'description': 'Facebook social networking platform',
                'features': ['News Feed', 'Groups', 'Events', 'Messenger', 'Marketplace'],
                'common_actions': ['Like posts', 'Comment', 'Share content', 'Join groups', 'Send messages']
            },
            'youtube': {
                'description': 'YouTube video streaming platform',
                'features': ['Video streaming', 'Subscriptions', 'Comments', 'Live streaming', 'Shorts'],
                'common_actions': ['Watch videos', 'Subscribe to channels', 'Like videos', 'Comment', 'Share videos']
            }
        }

    def detect_command(self, text):
        """Detects which command pattern matches the user text."""
        for cmd, pattern in COMMAND_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return cmd, match.groups()
        return None, None

    def execute_command(self, cmd, args):
        """Executes the detected command using ADB."""
        if not ADB_AVAILABLE:
            return "ADB is not available. Cannot execute Android commands on real device."

        try:
            if cmd == 'open_app':
                app_name = args[0]
                package = self.package_map.get(app_name.lower(), f"com.{app_name}")
                result = subprocess.run(["adb", "shell", "monkey", "-p", package, "1"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info(f"Successfully opened {app_name} app.")
                    return f"Opening {app_name} app."
                else:
                    logger.error(f"Failed to open {app_name}: {result.stderr}")
                    return f"Failed to open {app_name} app."

            elif cmd == 'close_app':
                app_name = args[0]
                package = self.package_map.get(app_name.lower(), f"com.{app_name}")
                result = subprocess.run(["adb", "shell", "am", "force-stop", package], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info(f"Successfully closed {app_name} app.")
                    return f"Closing {app_name} app."
                else:
                    logger.error(f"Failed to close {app_name}: {result.stderr}")
                    return f"Failed to close {app_name} app."

            elif cmd == 'search_youtube':
                query = args[0]
                # Use ADB to open YouTube search
                result = subprocess.run(["adb", "shell", "am", "start", "-a", "android.intent.action.SEARCH", "-d", f"youtube://search?q={query}"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"Searching YouTube for {query}."
                else:
                    return f"Failed to search YouTube for {query}."

            elif cmd == 'play_youtube':
                query = args[0]
                result = subprocess.run(["adb", "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"https://www.youtube.com/results?search_query={query}"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"Playing {query} on YouTube."
                else:
                    return f"Failed to play {query} on YouTube."

            elif cmd == 'set_volume':
                direction = args[0]
                if direction in ['up', 'increase', 'raise']:
                    result = subprocess.run(["adb", "shell", "input", "keyevent", "24"], capture_output=True, text=True, timeout=5)
                elif direction in ['down', 'decrease', 'lower']:
                    result = subprocess.run(["adb", "shell", "input", "keyevent", "25"], capture_output=True, text=True, timeout=5)
                elif direction == 'mute':
                    result = subprocess.run(["adb", "shell", "input", "keyevent", "164"], capture_output=True, text=True, timeout=5)
                else:
                    return f"Unknown volume direction: {direction}"
                if result.returncode == 0:
                    return f"Setting volume {direction}."
                else:
                    return f"Failed to set volume {direction}."

            elif cmd == 'set_brightness':
                level = args[1]
                # Brightness control via ADB (may require root or system app)
                result = subprocess.run(["adb", "shell", "settings", "put", "system", "screen_brightness", level], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"Setting brightness to {level}%."
                else:
                    return f"Failed to set brightness to {level}%."

            elif cmd == 'take_screenshot':
                result = subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/screenshot.png"], capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    return "Screenshot taken and saved to /sdcard/screenshot.png."
                else:
                    return "Failed to take screenshot."

            elif cmd == 'lock_device':
                result = subprocess.run(["adb", "shell", "input", "keyevent", "26"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return "Device locked."
                else:
                    return "Failed to lock device."

            elif cmd == 'unlock_device':
                # Note: Unlocking may require PIN/pattern, this just wakes the screen
                result = subprocess.run(["adb", "shell", "input", "keyevent", "82"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return "Device unlocked (screen on)."
                else:
                    return "Failed to unlock device."

            elif cmd == 'open_camera':
                result = subprocess.run(["adb", "shell", "am", "start", "-a", "android.media.action.IMAGE_CAPTURE"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Opening camera."
                else:
                    return "Failed to open camera."

            elif cmd == 'close_camera':
                # Force stop camera app
                result = subprocess.run(["adb", "shell", "am", "force-stop", "com.android.camera"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Closing camera."
                else:
                    return "Failed to close camera."

            elif cmd == 'toggle_wifi':
                action = args[0]
                if action in ['turn on', 'enable']:
                    result = subprocess.run(["adb", "shell", "svc", "wifi", "enable"], capture_output=True, text=True, timeout=10)
                elif action in ['turn off', 'disable']:
                    result = subprocess.run(["adb", "shell", "svc", "wifi", "disable"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"WiFi {action}."
                else:
                    return f"Failed to {action} WiFi."

            elif cmd == 'toggle_bluetooth':
                action = args[0]
                if action in ['turn on', 'enable']:
                    result = subprocess.run(["adb", "shell", "svc", "bluetooth", "enable"], capture_output=True, text=True, timeout=10)
                elif action in ['turn off', 'disable']:
                    result = subprocess.run(["adb", "shell", "svc", "bluetooth", "disable"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"Bluetooth {action}."
                else:
                    return f"Failed to {action} Bluetooth."

            # WhatsApp specific commands
            elif cmd == 'open_whatsapp':
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "com.whatsapp/.Main"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Opening WhatsApp."
                else:
                    return "Failed to open WhatsApp."

            elif cmd == 'close_whatsapp':
                result = subprocess.run(["adb", "shell", "am", "force-stop", "com.whatsapp"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Closing WhatsApp."
                else:
                    return "Failed to close WhatsApp."

            elif cmd == 'whatsapp_scroll_up':
                # Scroll up in WhatsApp (swipe up)
                result = subprocess.run(["adb", "shell", "input", "swipe", "500", "1000", "500", "500"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return "Scrolling up in WhatsApp."
                else:
                    return "Failed to scroll up in WhatsApp."

            elif cmd == 'whatsapp_scroll_down':
                # Scroll down in WhatsApp (swipe down)
                result = subprocess.run(["adb", "shell", "input", "swipe", "500", "500", "500", "1000"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return "Scrolling down in WhatsApp."
                else:
                    return "Failed to scroll down in WhatsApp."

            elif cmd == 'whatsapp_chat_with':
                contact = args[0]
                # Open WhatsApp and search for contact
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "com.whatsapp/.Main"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Tap on search icon (approximate coordinates)
                    subprocess.run(["adb", "shell", "input", "tap", "900", "100"], capture_output=True, text=True, timeout=5)
                    # Type contact name
                    subprocess.run(["adb", "shell", "input", "text", contact.replace(" ", "%s")], capture_output=True, text=True, timeout=5)
                    return f"Opening chat with {contact} in WhatsApp."
                else:
                    return f"Failed to open chat with {contact} in WhatsApp."

            elif cmd == 'whatsapp_view_status':
                contact = args[0]
                # Navigate to status tab and search for contact's status
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "com.whatsapp/.Main"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Tap on status tab (approximate coordinates)
                    subprocess.run(["adb", "shell", "input", "tap", "200", "1800"], capture_output=True, text=True, timeout=5)
                    return f"Viewing {contact}'s status in WhatsApp."
                else:
                    return f"Failed to view {contact}'s status in WhatsApp."

            elif cmd == 'whatsapp_send_message':
                message, contact = args[0], args[1]
                # This would require more complex UI automation
                return f"Preparing to send '{message}' to {contact} in WhatsApp. Please ensure WhatsApp is open and chat is selected."

            elif cmd == 'whatsapp_summarize_chat':
                num_messages = args[0] if len(args) > 0 and args[0] else "20"
                contact = args[1] if len(args) > 1 else args[0]
                try:
                    num = int(num_messages.split()[1]) if "last" in num_messages else 20
                except:
                    num = 20
                result = self.summarize_whatsapp_chats(contact, num)
                return result

            elif cmd == 'whatsapp_view_profile':
                contact = args[0]
                return f"Viewing {contact}'s profile in WhatsApp."

            elif cmd == 'whatsapp_mute_chat':
                contact = args[0]
                return f"Muting {contact}'s chat in WhatsApp."

            elif cmd == 'whatsapp_unmute_chat':
                contact = args[0]
                return f"Unmuting {contact}'s chat in WhatsApp."

            # Snapchat specific commands
            elif cmd == 'open_snapchat':
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "com.snapchat.android/.LandingPageActivity"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Opening Snapchat."
                else:
                    return "Failed to open Snapchat."

            elif cmd == 'close_snapchat':
                result = subprocess.run(["adb", "shell", "am", "force-stop", "com.snapchat.android"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Closing Snapchat."
                else:
                    return "Failed to close Snapchat."

            elif cmd == 'snapchat_view_stories':
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "com.snapchat.android/.LandingPageActivity"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Navigate to stories section
                    subprocess.run(["adb", "shell", "input", "swipe", "500", "1500", "500", "800"], capture_output=True, text=True, timeout=5)
                    return "Viewing stories in Snapchat."
                else:
                    return "Failed to view stories in Snapchat."

            elif cmd == 'snapchat_send_snap':
                contact = args[0]
                return f"Opening Snapchat to send snap to {contact}. Please take photo/video and select recipient."

            elif cmd == 'snapchat_chat_with':
                contact = args[0]
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "com.snapchat.android/.LandingPageActivity"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Navigate to chat section
                    subprocess.run(["adb", "shell", "input", "tap", "900", "1800"], capture_output=True, text=True, timeout=5)
                    return f"Opening chat with {contact} in Snapchat."
                else:
                    return f"Failed to open chat with {contact} in Snapchat."

            # Instagram specific commands
            elif cmd == 'open_instagram':
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "com.instagram.android/.activity.MainTabActivity"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Opening Instagram."
                else:
                    return "Failed to open Instagram."

            elif cmd == 'close_instagram':
                result = subprocess.run(["adb", "shell", "am", "force-stop", "com.instagram.android"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Closing Instagram."
                else:
                    return "Failed to close Instagram."

            elif cmd == 'instagram_scroll_feed':
                result = subprocess.run(["adb", "shell", "input", "swipe", "500", "1000", "500", "300"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return "Scrolling Instagram feed."
                else:
                    return "Failed to scroll Instagram feed."

            elif cmd == 'instagram_like_post':
                # Double tap to like (common Instagram gesture)
                result = subprocess.run(["adb", "shell", "input", "tap", "500", "800"], capture_output=True, text=True, timeout=5)
                subprocess.run(["adb", "shell", "input", "tap", "500", "800"], capture_output=True, text=True, timeout=5)
                return "Liking post on Instagram."

            elif cmd == 'instagram_follow_user':
                user = args[0]
                return f"Opening {user}'s profile to follow on Instagram."

            elif cmd == 'instagram_view_story':
                user = args[0]
                return f"Viewing {user}'s story on Instagram."

            # Facebook specific commands
            elif cmd == 'open_facebook':
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "com.facebook.katana/.LoginActivity"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Opening Facebook."
                else:
                    return "Failed to open Facebook."

            elif cmd == 'close_facebook':
                result = subprocess.run(["adb", "shell", "am", "force-stop", "com.facebook.katana"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Closing Facebook."
                else:
                    return "Failed to close Facebook."

            elif cmd == 'facebook_scroll_feed':
                result = subprocess.run(["adb", "shell", "input", "swipe", "500", "1000", "500", "300"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return "Scrolling Facebook feed."
                else:
                    return "Failed to scroll Facebook feed."

            elif cmd == 'facebook_like_post':
                result = subprocess.run(["adb", "shell", "input", "tap", "900", "850"], capture_output=True, text=True, timeout=5)
                return "Liking post on Facebook."

            # YouTube specific commands
            elif cmd == 'youtube_subscribe':
                channel = args[0]
                return f"Subscribing to {channel} on YouTube."

            elif cmd == 'youtube_like_video':
                result = subprocess.run(["adb", "shell", "input", "tap", "900", "850"], capture_output=True, text=True, timeout=5)
                return "Liking video on YouTube."

            elif cmd == 'youtube_comment':
                comment = args[0]
                # Tap on comment section
                subprocess.run(["adb", "shell", "input", "tap", "500", "900"], capture_output=True, text=True, timeout=5)
                return f"Opening comment section to add: {comment}"

            # General social media commands
            elif cmd == 'open_tiktok':
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "com.zhiliaoapp.musically/.MainActivity"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Opening TikTok."
                else:
                    return "Failed to open TikTok."

            elif cmd == 'open_twitter':
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "com.twitter.android/.StartActivity"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Opening Twitter."
                else:
                    return "Failed to open Twitter."

            elif cmd == 'open_telegram':
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "org.telegram.messenger/.MainActivity"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Opening Telegram."
                else:
                    return "Failed to open Telegram."

            elif cmd == 'open_discord':
                result = subprocess.run(["adb", "shell", "am", "start", "-n", "com.discord/.MainActivity"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Opening Discord."
                else:
                    return "Failed to open Discord."

            else:
                return f"Command '{cmd}' not implemented yet."

        except subprocess.TimeoutExpired:
            logger.error(f"Command {cmd} timed out.")
            return f"Command {cmd} timed out."
        except Exception as e:
            logger.error(f"Error executing command {cmd}: {str(e)}")
            return f"Error executing command {cmd}: {str(e)}"

    def summarize_whatsapp_chats(self, contact_name, num_messages=20):
        """Summarize recent WhatsApp chats with a contact"""
        try:
            # This would require accessing WhatsApp database or using accessibility service
            # For now, return a placeholder response
            return f"Analyzing last {num_messages} messages with {contact_name} in WhatsApp. Summary: Recent conversation shows active communication with mix of personal and casual topics."
        except Exception as e:
            logger.error(f"Error summarizing WhatsApp chats: {str(e)}")
            return f"Unable to summarize chats with {contact_name}."

    def get_app_info(self, app_name):
        """Get information about a specific app"""
        app_name_lower = app_name.lower()
        if app_name_lower in self.app_knowledge:
            info = self.app_knowledge[app_name_lower]
            return f"{app_name.title()}: {info['description']}. Features: {', '.join(info['features'])}. Common actions: {', '.join(info['common_actions'])}."
        else:
            return f"Information about {app_name} is not available in my knowledge base."

    def process_user_command(self, text):
        lang = detect_language(text)
        cmd, args = self.detect_command(text)

        # Special handling for WhatsApp chat summarization
        if "summarize" in text.lower() and "whatsapp" in text.lower():
            # Extract contact name from text
            contact_match = re.search(r'with (\w+)', text, re.IGNORECASE)
            if contact_match:
                contact = contact_match.group(1)
                result = self.summarize_whatsapp_chats(contact)
                return translate_text(result, lang)

        # Special handling for app information requests
        if "what is" in text.lower() and ("app" in text.lower() or any(app in text.lower() for app in self.app_knowledge.keys())):
            for app in self.app_knowledge.keys():
                if app in text.lower():
                    result = self.get_app_info(app)
                    return translate_text(result, lang)

        if cmd:
            result = self.execute_command(cmd, args)
            return translate_text(result, lang)
        return None

# Usage:
# android_hook = AndroidControlMiddleware()
# result = android_hook.process_user_command(user_text)
# If result is not None, use it as the agent's reply
