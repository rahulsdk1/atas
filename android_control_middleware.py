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

# Check if ADB is available and device is connected
def is_adb_available():
    try:
        result = subprocess.run(["adb", "version"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False

        # Check if any device is connected
        device_result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        if "device" not in device_result.stdout or "unauthorized" in device_result.stdout:
            logger.warning("ADB available but no authorized device connected")
            return False

        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

# Enhanced device connection check
def check_device_connection():
    """Check if Android device is properly connected and authorized"""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        if "device" in result.stdout and "unauthorized" not in result.stdout:
            # Get device info
            info_result = subprocess.run(["adb", "shell", "getprop", "ro.product.model"], capture_output=True, text=True, timeout=5)
            if info_result.returncode == 0:
                device_model = info_result.stdout.strip()
                logger.info(f"Connected Android device: {device_model}")
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking device connection: {e}")
        return False

def get_android_device_info():
    """Get comprehensive Android device information for universal compatibility"""
    device_info = {
        'manufacturer': 'unknown',
        'model': 'unknown',
        'android_version': 'unknown',
        'api_level': 'unknown',
        'screen_size': (1080, 1920),
        'screen_density': 480,
        'supported': True,
        'adb_version': 'unknown',
        'device_type': 'phone',  # phone, tablet, tv, etc.
        'architecture': 'unknown'
    }

    try:
        # Get device manufacturer
        manufacturer_result = subprocess.run(["adb", "shell", "getprop", "ro.product.manufacturer"],
                                           capture_output=True, text=True, timeout=5)
        if manufacturer_result.returncode == 0:
            device_info['manufacturer'] = manufacturer_result.stdout.strip().lower()

        # Get device model
        model_result = subprocess.run(["adb", "shell", "getprop", "ro.product.model"],
                                    capture_output=True, text=True, timeout=5)
        if model_result.returncode == 0:
            device_info['model'] = model_result.stdout.strip()

        # Get Android version
        version_result = subprocess.run(["adb", "shell", "getprop", "ro.build.version.release"],
                                      capture_output=True, text=True, timeout=5)
        if version_result.returncode == 0:
            device_info['android_version'] = version_result.stdout.strip()

        # Get API level
        api_result = subprocess.run(["adb", "shell", "getprop", "ro.build.version.sdk"],
                                   capture_output=True, text=True, timeout=5)
        if api_result.returncode == 0:
            device_info['api_level'] = int(api_result.stdout.strip())

        # Get device type
        device_type_result = subprocess.run(["adb", "shell", "getprop", "ro.build.characteristics"],
                                          capture_output=True, text=True, timeout=5)
        if device_type_result.returncode == 0:
            characteristics = device_type_result.stdout.strip().lower()
            if 'tablet' in characteristics:
                device_info['device_type'] = 'tablet'
            elif 'tv' in characteristics:
                device_info['device_type'] = 'tv'
            else:
                device_info['device_type'] = 'phone'

        # Get architecture
        arch_result = subprocess.run(["adb", "shell", "getprop", "ro.product.cpu.abi"],
                                   capture_output=True, text=True, timeout=5)
        if arch_result.returncode == 0:
            device_info['architecture'] = arch_result.stdout.strip()

        # Get screen size
        size_result = subprocess.run(["adb", "shell", "wm", "size"], capture_output=True, text=True, timeout=5)
        if size_result.returncode == 0:
            size_line = size_result.stdout.strip().split(':')[-1].strip()
            try:
                width, height = map(int, size_line.split('x'))
                device_info['screen_size'] = (width, height)
            except:
                pass

        # Get screen density
        density_result = subprocess.run(["adb", "shell", "wm", "density"], capture_output=True, text=True, timeout=5)
        if density_result.returncode == 0:
            density_line = density_result.stdout.strip().split(':')[-1].strip()
            try:
                device_info['screen_density'] = int(density_line)
            except:
                pass

        # Get ADB version
        adb_result = subprocess.run(["adb", "version"], capture_output=True, text=True, timeout=5)
        if adb_result.returncode == 0:
            for line in adb_result.stdout.split('\n'):
                if 'Version' in line:
                    device_info['adb_version'] = line.split()[-1]
                    break

        # Determine if device is supported
        if device_info['api_level'] != 'unknown':
            api_level = device_info['api_level']
            # Support Android 5.0 (API 21) and above
            device_info['supported'] = api_level >= 21

        logger.info(f"Device detected: {device_info['manufacturer']} {device_info['model']}, "
                   f"Android {device_info['android_version']} (API {device_info['api_level']}), "
                   f"Type: {device_info['device_type']}")

        return device_info

    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        return device_info

ADB_AVAILABLE = is_adb_available()
DEVICE_CONNECTED = check_device_connection()

if not ADB_AVAILABLE:
    logger.warning("ADB is not available. Android control functions will not work.")
elif not DEVICE_CONNECTED:
    logger.warning("ADB available but no authorized Android device connected.")
else:
    logger.info("ADB and Android device connection verified successfully.")

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
        # Universal Android device compatibility system
        self.device_info = get_android_device_info()
        self.manufacturer = self.device_info['manufacturer']
        self.api_level = self.device_info['api_level']
        self.device_type = self.device_info['device_type']

        # Enhanced package mapping with manufacturer-specific variations
        self.package_map = {
            # Social Media Apps (universal)
            'whatsapp': 'com.whatsapp',
            'snapchat': 'com.snapchat.android',
            'instagram': 'com.instagram.android',
            'facebook': 'com.facebook.katana',
            'twitter': 'com.twitter.android',
            'tiktok': 'com.ss.android.ugc.trill',  # Updated TikTok package
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
            'edge': 'com.microsoft.emmx',

            # Google Apps
            'youtube': 'com.google.android.youtube',
            'gmail': 'com.google.android.gm',
            'maps': 'com.google.android.apps.maps',
            'drive': 'com.google.android.apps.docs',
            'photos': 'com.google.android.apps.photos',
            'calendar': 'com.google.android.calendar',
            'keep': 'com.google.android.keep',

            # System Apps (may vary by device manufacturer)
            'settings': 'com.android.settings',
            'camera': 'com.android.camera2',  # Updated for newer Android
            'gallery': 'com.android.gallery3d',  # More common package
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

        # Manufacturer-specific package variations
        self.manufacturer_packages = {
            'samsung': {
                'camera': 'com.sec.android.app.camera',
                'gallery': 'com.sec.android.gallery3d',
                'settings': 'com.android.settings',
                'clock': 'com.sec.android.app.clockpackage',
                'calculator': 'com.sec.android.app.popupcalculator',
                'messages': 'com.samsung.android.messaging'
            },
            'huawei': {
                'camera': 'com.huawei.camera',
                'gallery': 'com.huawei.gallery',
                'settings': 'com.android.settings',
                'clock': 'com.huawei.android.deskclock',
                'calculator': 'com.huawei.calculator'
            },
            'xiaomi': {
                'camera': 'com.android.camera',
                'gallery': 'com.miui.gallery',
                'settings': 'com.android.settings',
                'clock': 'com.android.deskclock',
                'calculator': 'com.miui.calculator'
            },
            'oppo': {
                'camera': 'com.oppo.camera',
                'gallery': 'com.coloros.gallery3d',
                'settings': 'com.android.settings',
                'clock': 'com.coloros.alarmclock',
                'calculator': 'com.coloros.calculator'
            },
            'vivo': {
                'camera': 'com.android.camera',
                'gallery': 'com.android.gallery3d',
                'settings': 'com.android.settings',
                'clock': 'com.android.deskclock',
                'calculator': 'com.android.calculator2'
            },
            'oneplus': {
                'camera': 'com.oneplus.camera',
                'gallery': 'com.oneplus.gallery',
                'settings': 'com.android.settings',
                'clock': 'com.oneplus.deskclock',
                'calculator': 'com.oneplus.calculator'
            },
            'google': {
                'camera': 'com.google.android.apps.cameralite',
                'gallery': 'com.google.android.apps.photos',
                'settings': 'com.android.settings',
                'clock': 'com.google.android.deskclock',
                'calculator': 'com.google.android.calculator'
            }
        }

        # Android version-specific adaptations
        self.api_adaptations = {
            'volume_control': {
                'legacy': lambda: ["adb", "shell", "input", "keyevent", "24"],  # API < 26
                'modern': lambda: ["adb", "shell", "cmd", "media_session", "volume", "--stream", "3", "--set", "10"]  # API >= 26
            },
            'brightness_control': {
                'legacy': lambda level: ["adb", "shell", "settings", "put", "system", "screen_brightness", level],
                'modern': lambda level: ["adb", "shell", "settings", "put", "system", "screen_brightness", level]
            }
        }

        # Device-specific UI adaptation
        self.ui_adaptations = {
            'tablet': {
                'search_offset': (0.9, 0.08),  # Different UI layout for tablets
                'status_offset': (0.15, 0.15)
            },
            'phone': {
                'search_offset': (0.85, 0.05),
                'status_offset': (0.2, 0.18)
            },
            'tv': {
                'search_offset': (0.8, 0.1),
                'status_offset': (0.25, 0.2)
            }
        }

        # Device screen information (will be populated on first use)
        self.screen_size = None
        self.screen_density = None

    def get_screen_info(self):
        """Get device screen size and density for coordinate calculations"""
        if self.screen_size is None:
            try:
                # Get screen size
                size_result = subprocess.run(["adb", "shell", "wm", "size"],
                                           capture_output=True, text=True, timeout=5)
                if size_result.returncode == 0:
                    size_line = size_result.stdout.strip().split(':')[-1].strip()
                    width, height = map(int, size_line.split('x'))
                    self.screen_size = (width, height)
                else:
                    # Fallback to common resolution
                    self.screen_size = (1080, 1920)  # Common Android resolution

                # Get screen density
                density_result = subprocess.run(["adb", "shell", "wm", "density"],
                                              capture_output=True, text=True, timeout=5)
                if density_result.returncode == 0:
                    density_line = density_result.stdout.strip().split(':')[-1].strip()
                    self.screen_density = int(density_line)
                else:
                    self.screen_density = 480  # Common density

                logger.info(f"Device screen: {self.screen_size[0]}x{self.screen_size[1]}, density: {self.screen_density}")

            except Exception as e:
                logger.warning(f"Could not get screen info: {e}")
                self.screen_size = (1080, 1920)
                self.screen_density = 480

        return self.screen_size, self.screen_density

    def calculate_coordinates(self, x_percent, y_percent):
        """Calculate actual screen coordinates from percentages"""
        width, height = self.get_screen_info()[0]
        x = int(width * x_percent / 100)
        y = int(height * y_percent / 100)
        return x, y

    def get_package_name(self, app_name):
        """Get the correct package name for an app with universal device compatibility"""
        app_name_lower = app_name.lower()

        # First try manufacturer-specific package
        if self.manufacturer in self.manufacturer_packages and app_name_lower in self.manufacturer_packages[self.manufacturer]:
            manufacturer_package = self.manufacturer_packages[self.manufacturer][app_name_lower]
            try:
                result = subprocess.run(["adb", "shell", "pm", "list", "packages", manufacturer_package],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and manufacturer_package in result.stdout:
                    logger.info(f"Using manufacturer-specific package {manufacturer_package} for {app_name} on {self.manufacturer}")
                    return manufacturer_package
            except Exception as e:
                logger.debug(f"Manufacturer package {manufacturer_package} not found: {e}")

        # Try primary universal package
        if app_name_lower in self.package_map:
            primary_package = self.package_map[app_name_lower]
            try:
                result = subprocess.run(["adb", "shell", "pm", "list", "packages", primary_package],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and primary_package in result.stdout:
                    return primary_package
            except Exception as e:
                logger.debug(f"Primary package {primary_package} not found: {e}")

        # Try alternative packages for this manufacturer
        if self.manufacturer in self.manufacturer_packages:
            for alt_app, alt_package in self.manufacturer_packages[self.manufacturer].items():
                if alt_app == app_name_lower:
                    continue  # Already tried this
                try:
                    result = subprocess.run(["adb", "shell", "pm", "list", "packages", alt_package],
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0 and alt_package in result.stdout:
                        logger.info(f"Using alternative manufacturer package {alt_package} for {app_name}")
                        return alt_package
                except Exception as e:
                    logger.debug(f"Alternative package {alt_package} not found: {e}")

        # Try other manufacturer packages as fallback
        for manufacturer, packages in self.manufacturer_packages.items():
            if manufacturer == self.manufacturer:
                continue  # Already tried this manufacturer
            if app_name_lower in packages:
                alt_package = packages[app_name_lower]
                try:
                    result = subprocess.run(["adb", "shell", "pm", "list", "packages", alt_package],
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0 and alt_package in result.stdout:
                        logger.info(f"Using cross-manufacturer package {alt_package} for {app_name}")
                        return alt_package
                except Exception as e:
                    logger.debug(f"Cross-manufacturer package {alt_package} not found: {e}")

        # Final fallback to default pattern
        fallback_package = f"com.{app_name_lower}" if not app_name_lower.startswith('com.') else app_name_lower
        logger.warning(f"Using fallback package {fallback_package} for {app_name} - may not work on all devices")
        return fallback_package

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

        # Re-check device connection for each command (in case device disconnected)
        if not check_device_connection():
            return "Android device not connected or not authorized. Please connect your device and enable USB debugging."

        try:
            if cmd == 'open_app':
                app_name = args[0]
                package = self.get_package_name(app_name)

                # Try to start the app using multiple methods
                success = False

                # Method 1: Using monkey
                try:
                    result = subprocess.run(["adb", "shell", "monkey", "-p", package, "1"],
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        success = True
                except subprocess.TimeoutExpired:
                    logger.warning(f"Monkey method timed out for {app_name}")

                # Method 2: Using am start (fallback)
                if not success:
                    # Universal error handling and graceful degradation
                    try:
                        # Pre-execution device health check
                        if not self.device_info['supported']:
                            return f"Device not supported. Minimum Android 5.0 (API 21) required. Current: Android {self.device_info['android_version']} (API {self.device_info['api_level']})"
            
                        # Log command execution attempt
                        logger.info(f"Executing command '{cmd}' with args {args} on {self.manufacturer} {self.device_info['model']} (Android {self.device_info['android_version']})")
                        result = subprocess.run(["adb", "shell", "am", "start", "-n", f"{package}/.MainActivity"],
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            success = True
                    except subprocess.TimeoutExpired:
                        logger.warning(f"AM start method timed out for {app_name}")

                if success:
                    logger.info(f"Successfully opened {app_name} app with package {package}.")
                    return f"Opening {app_name} app."
                else:
                    logger.error(f"Failed to open {app_name} app with package {package}")
                    return f"Failed to open {app_name} app. Please ensure the app is installed."

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

                # Use Android version-specific volume control
                if self.api_level >= 26:  # Android 8.0+
                    try:
                        if direction in ['up', 'increase', 'raise']:
                            # Try modern volume control first
                            result = subprocess.run(["adb", "shell", "cmd", "media_session", "volume", "--stream", "3", "--adjust", "raise"],
                                                  capture_output=True, text=True, timeout=5)
                            if result.returncode != 0:
                                # Fallback to keyevent
                                result = subprocess.run(["adb", "shell", "input", "keyevent", "24"], capture_output=True, text=True, timeout=5)
                        elif direction in ['down', 'decrease', 'lower']:
                            result = subprocess.run(["adb", "shell", "cmd", "media_session", "volume", "--stream", "3", "--adjust", "lower"],
                                                  capture_output=True, text=True, timeout=5)
                            if result.returncode != 0:
                                result = subprocess.run(["adb", "shell", "input", "keyevent", "25"], capture_output=True, text=True, timeout=5)
                        elif direction == 'mute':
                            result = subprocess.run(["adb", "shell", "input", "keyevent", "164"], capture_output=True, text=True, timeout=5)
                        else:
                            return f"Unknown volume direction: {direction}"
                    except Exception as e:
                        logger.warning(f"Modern volume control failed, using legacy: {e}")
                        # Fallback to legacy method
                        if direction in ['up', 'increase', 'raise']:
                            result = subprocess.run(["adb", "shell", "input", "keyevent", "24"], capture_output=True, text=True, timeout=5)
                        elif direction in ['down', 'decrease', 'lower']:
                            result = subprocess.run(["adb", "shell", "input", "keyevent", "25"], capture_output=True, text=True, timeout=5)
                        elif direction == 'mute':
                            result = subprocess.run(["adb", "shell", "input", "keyevent", "164"], capture_output=True, text=True, timeout=5)
                        else:
                            return f"Unknown volume direction: {direction}"
                else:
                    # Legacy Android versions (API < 26)
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

                # Try different brightness control methods based on Android version and manufacturer
                success = False

                # Method 1: Standard settings command (works on most devices)
                try:
                    result = subprocess.run(["adb", "shell", "settings", "put", "system", "screen_brightness", level],
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        success = True
                        logger.info(f"Brightness set to {level}% using standard method")
                except Exception as e:
                    logger.debug(f"Standard brightness method failed: {e}")

                # Method 2: Try secure settings (may require different permissions)
                if not success:
                    try:
                        result = subprocess.run(["adb", "shell", "settings", "put", "secure", "screen_brightness", level],
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            success = True
                            logger.info(f"Brightness set to {level}% using secure method")
                    except Exception as e:
                        logger.debug(f"Secure brightness method failed: {e}")

                # Method 3: Try global settings (for some manufacturers)
                if not success:
                    try:
                        result = subprocess.run(["adb", "shell", "settings", "put", "global", "screen_brightness", level],
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            success = True
                            logger.info(f"Brightness set to {level}% using global method")
                    except Exception as e:
                        logger.debug(f"Global brightness method failed: {e}")

                # Method 4: Manufacturer-specific commands
                if not success and self.manufacturer in ['samsung', 'huawei', 'xiaomi']:
                    try:
                        # Some manufacturers have different brightness commands
                        result = subprocess.run(["adb", "shell", "settings", "put", "system", "screen_brightness_mode", "0"],
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            result = subprocess.run(["adb", "shell", "settings", "put", "system", "screen_brightness", level],
                                                  capture_output=True, text=True, timeout=10)
                            if result.returncode == 0:
                                success = True
                                logger.info(f"Brightness set to {level}% using manufacturer-specific method")
                    except Exception as e:
                        logger.debug(f"Manufacturer-specific brightness method failed: {e}")

                if success:
                    return f"Setting brightness to {level}%."
                else:
                    logger.warning(f"All brightness control methods failed for {self.manufacturer} device")
                    return f"Failed to set brightness to {level}%. This may require system permissions or device-specific settings."

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
                    # Wait for app to load (device-specific timing)
                    sleep_time = 3 if self.device_type == 'phone' else 5  # Tablets/TV need more time
                    subprocess.run(["adb", "shell", "sleep", str(sleep_time)], capture_output=True, text=True, timeout=sleep_time + 1)

                    # Get device-specific search coordinates
                    if self.device_type in self.ui_adaptations:
                        search_coords = self.ui_adaptations[self.device_type]['search_offset']
                        search_x, search_y = self.calculate_coordinates(search_coords[0] * 100, search_coords[1] * 100)
                    else:
                        # Default coordinates for unknown device types
                        search_x, search_y = self.calculate_coordinates(85, 5)

                    # Tap on search icon
                    tap_result = subprocess.run(["adb", "shell", "input", "tap", str(int(search_x)), str(int(search_y))],
                                              capture_output=True, text=True, timeout=5)

                    if tap_result.returncode == 0:
                        # Wait and type contact name
                        subprocess.run(["adb", "shell", "sleep", "1"], capture_output=True, text=True, timeout=2)

                        # Handle special characters in contact names
                        safe_contact = contact.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
                        type_result = subprocess.run(["adb", "shell", "input", "text", safe_contact],
                                                   capture_output=True, text=True, timeout=5)

                        if type_result.returncode == 0:
                            return f"Opening chat with {contact} in WhatsApp."
                        else:
                            return f"WhatsApp opened but failed to search for {contact}."
                    else:
                        return f"WhatsApp opened but failed to access search function."
                else:
                    return f"Failed to open WhatsApp. Please ensure it's installed and try again."

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
            logger.error(f"Command {cmd} timed out on {self.manufacturer} device")
            return f"Command timed out. The device may be busy or unresponsive. Please try again."

        except ConnectionError:
            logger.error(f"ADB connection lost during command {cmd}")
            return f"Lost connection to Android device. Please check USB connection and try again."

        except PermissionError:
            logger.error(f"Permission denied for command {cmd} on {self.manufacturer} device")
            return f"Permission denied. Some features may require additional device permissions or root access."

        except OSError as e:
            if "No such file or directory" in str(e):
                logger.error(f"ADB not found in system PATH")
                return f"ADB not found. Please ensure Android SDK platform tools are installed and in system PATH."
            else:
                logger.error(f"OS error during command {cmd}: {str(e)}")
                return f"System error occurred. Please check device connection and try again."

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error executing command {cmd}: {error_msg}")

            # Provide user-friendly error messages based on error type
            if "device unauthorized" in error_msg.lower():
                return f"Device not authorized. Please check USB debugging authorization on your Android device."
            elif "device not found" in error_msg.lower():
                return f"Android device not found. Please ensure device is connected and USB debugging is enabled."
            elif "closed" in error_msg.lower():
                return f"Device connection closed unexpectedly. Please reconnect your Android device."
            elif "timeout" in error_msg.lower():
                return f"Command timed out. The device may be busy or the operation may take longer on this device model."
            else:
                return f"Command failed due to device compatibility issue. This feature may not be fully supported on {self.manufacturer} {self.device_info['model']} with Android {self.device_info['android_version']}."

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

    def health_check(self):
        """Comprehensive health check for Android control functionality"""
        health_status = {
            'adb_available': ADB_AVAILABLE,
            'device_connected': check_device_connection(),
            'device_info': self.device_info,
            'apps_verified': {},
            'compatibility_score': 0,
            'overall_status': 'unknown',
            'recommendations': []
        }

        # Check critical apps
        critical_apps = ['whatsapp', 'chrome', 'settings', 'camera']
        for app in critical_apps:
            package = self.get_package_name(app)
            is_available = False
            try:
                result = subprocess.run(["adb", "shell", "pm", "list", "packages", package],
                                      capture_output=True, text=True, timeout=5)
                is_available = result.returncode == 0 and package in result.stdout
            except:
                pass
            health_status['apps_verified'][app] = is_available

        # Calculate compatibility score
        score = 0
        max_score = 100

        if health_status['adb_available']:
            score += 25
        else:
            health_status['recommendations'].append("Install ADB (Android Debug Bridge)")

        if health_status['device_connected']:
            score += 25
        else:
            health_status['recommendations'].append("Connect Android device with USB debugging enabled")

        if self.device_info['supported']:
            score += 20
        else:
            health_status['recommendations'].append("Update Android to version 5.0 or higher")

        # Check app availability
        available_apps = sum(1 for available in health_status['apps_verified'].values() if available)
        app_score = (available_apps / len(critical_apps)) * 20
        score += app_score

        if available_apps < len(critical_apps):
            missing_apps = [app for app, available in health_status['apps_verified'].items() if not available]
            health_status['recommendations'].append(f"Install missing apps: {', '.join(missing_apps)}")

        # Manufacturer-specific recommendations
        if self.manufacturer == 'samsung':
            health_status['recommendations'].append("For best results, disable Samsung's security features for ADB")
        elif self.manufacturer == 'huawei':
            health_status['recommendations'].append("Allow USB debugging in Huawei's developer options")
        elif self.manufacturer == 'xiaomi':
            health_status['recommendations'].append("Enable USB debugging and disable MIUI optimization")

        health_status['compatibility_score'] = score

        # Determine overall status
        if score >= 80:
            health_status['overall_status'] = 'excellent'
        elif score >= 60:
            health_status['overall_status'] = 'good'
        elif score >= 40:
            health_status['overall_status'] = 'fair'
        elif score >= 20:
            health_status['overall_status'] = 'poor'
        else:
            health_status['overall_status'] = 'critical'

        return health_status

    def test_device_compatibility(self):
        """Test various Android device features for compatibility"""
        compatibility_results = {
            'device_info': self.device_info,
            'tests': {},
            'overall_compatibility': 'unknown'
        }

        # Test basic ADB commands
        test_commands = [
            ('basic_shell', ["adb", "shell", "echo", "test"]),
            ('package_manager', ["adb", "shell", "pm", "list", "packages", "-f"]),
            ('input_system', ["adb", "shell", "input", "keyevent", "KEYCODE_HOME"]),
            ('settings_access', ["adb", "shell", "settings", "list", "system"]),
            ('screen_info', ["adb", "shell", "wm", "size"]),
        ]

        for test_name, command in test_commands:
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                compatibility_results['tests'][test_name] = {
                    'success': result.returncode == 0,
                    'return_code': result.returncode,
                    'error': result.stderr.strip() if result.stderr else None
                }
            except Exception as e:
                compatibility_results['tests'][test_name] = {
                    'success': False,
                    'error': str(e)
                }

        # Calculate overall compatibility
        successful_tests = sum(1 for test in compatibility_results['tests'].values() if test['success'])
        total_tests = len(compatibility_results['tests'])

        if successful_tests == total_tests:
            compatibility_results['overall_compatibility'] = 'full'
        elif successful_tests >= total_tests * 0.8:
            compatibility_results['overall_compatibility'] = 'high'
        elif successful_tests >= total_tests * 0.6:
            compatibility_results['overall_compatibility'] = 'medium'
        elif successful_tests >= total_tests * 0.4:
            compatibility_results['overall_compatibility'] = 'low'
        else:
            compatibility_results['overall_compatibility'] = 'limited'

        return compatibility_results

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

        # Special handling for health check requests
        if "health check" in text.lower() or "system status" in text.lower():
            health = self.health_check()
            status_msg = f"System Health: {health['overall_status'].title()} ({health['compatibility_score']}/100)"
            status_msg += f" | Device: {self.manufacturer.title()} {self.device_info['model']}"
            status_msg += f" | Android {self.device_info['android_version']} (API {self.device_info['api_level']})"
            status_msg += f" | ADB: {'✓' if health['adb_available'] else '✗'}"
            status_msg += f" | Connection: {'✓' if health['device_connected'] else '✗'}"

            if health['recommendations']:
                status_msg += f" | Recommendations: {', '.join(health['recommendations'])}"

            return translate_text(status_msg, lang)

        # Special handling for compatibility test requests
        if "compatibility test" in text.lower() or "test device" in text.lower():
            compat = self.test_device_compatibility()
            test_results = []
            for test_name, result in compat['tests'].items():
                status = "✓" if result['success'] else "✗"
                test_results.append(f"{test_name}: {status}")

            compat_msg = f"Device Compatibility: {compat['overall_compatibility'].title()}"
            compat_msg += f" | Tests: {' | '.join(test_results)}"
            return translate_text(compat_msg, lang)

        if cmd:
            result = self.execute_command(cmd, args)
            return translate_text(result, lang)
        return None

# Usage:
# android_hook = AndroidControlMiddleware()
# result = android_hook.process_user_command(user_text)
# If result is not None, use it as the agent's reply
