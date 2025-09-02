# android_control_middleware.py
"""
Middleware for Android app and device control via agent commands.
Detects user intent for app/device actions and routes to Android APIs (ADB/Appium/custom service).
Handles multi-language input/output using language middleware.
No changes required to original code. Import and use hooks as needed.
"""
import re
import subprocess
from language_middleware import detect_language, translate_text

# Example command patterns (expand as needed)
COMMAND_PATTERNS = {
    'open_app': r'open (\w+)',
    'close_app': r'close (\w+)',
    'search_youtube': r'search (.+) on youtube',
    'play_youtube': r'play (.+) on youtube',
    'set_volume': r'(up|down|low|raise|mute|max|increase|decrease) (the )?volume',
    'set_quality': r'(down|up|increase|decrease|set) (the )?quality( of youtube)?',
    'scroll_feed': r'scroll (feed|messages|whatsapp|facebook|instagram|shopping app|chrome|contacts|gallery|settings|notifications)',
    'send_message': r'send message to (.+)',
    'install_app': r'install (.+)',
    'uninstall_app': r'uninstall (.+)',
    'control_flashlight': r'(turn on|turn off|enable|disable|switch on|switch off) (flashlight|torch|light)',
    'set_brightness': r'(set|turn|low|raise|increase|decrease) brightness( to)? (\d+)%',
    'update_android': r'update android',
    'open_settings': r'open (settings|wifi|bluetooth|display|sound|battery|storage|security|location|apps|about)',
    'toggle_wifi': r'(turn on|turn off|enable|disable) wifi',
    'toggle_bluetooth': r'(turn on|turn off|enable|disable) bluetooth',
    'take_screenshot': r'(take|capture) (a )?screenshot',
    'lock_device': r'lock (the )?device',
    'unlock_device': r'unlock (the )?device',
    'open_camera': r'open camera',
    'close_camera': r'close camera',
    'play_media': r'play (.+) in (mx player|vlc|music app|jio saavn|spotify|google play music)',
    'pause_media': r'pause (music|video|media|song)',
    'resume_media': r'resume (music|video|media|song)',
    'next_track': r'next (track|song|video)',
    'previous_track': r'previous (track|song|video)',
    'search_playstore': r'search (.+) in playstore',
    'download_file': r'download (.+)',
    'delete_file': r'delete (.+)',
    'open_browser': r'open (chrome|browser|firefox|edge|opera)',
    'search_browser': r'search (.+) in (chrome|browser|firefox|edge|opera)',
    'visit_website': r'visit (.+) in (chrome|browser|firefox|edge|opera)',
    'clear_notifications': r'clear (all )?notifications',
    'mute_notifications': r'(mute|silence|disable) notifications',
    'unmute_notifications': r'(unmute|enable|activate) notifications',
    'open_contacts': r'open contacts',
    'call_contact': r'(call|dial) (.+)',
    'end_call': r'(end|hang up|disconnect) (call|phone)',
    'open_gallery': r'open gallery',
    'delete_photo': r'delete photo (.+)',
    'share_photo': r'share photo (.+) with (.+)',
    'open_calendar': r'open calendar',
    'add_event': r'add event (.+) on (.+)',
    'delete_event': r'delete event (.+)',
    'open_maps': r'open maps',
    'navigate_to': r'navigate to (.+)',
    'share_location': r'share my location',
    'open_email': r'open email',
    'send_email': r'send email to (.+)',
    'open_notes': r'open notes',
    'add_note': r'add note (.+)',
    'delete_note': r'delete note (.+)',
    'open_reminders': r'open reminders',
    'add_reminder': r'add reminder (.+) at (.+)',
    'delete_reminder': r'delete reminder (.+)',
    'open_calculator': r'open calculator',
    'calculate': r'calculate (.+)',
    'open_weather': r'open weather',
    'check_weather': r'check weather in (.+)',
    'open_clock': r'open clock',
    'set_alarm': r'set alarm for (.+)',
    'delete_alarm': r'delete alarm (.+)',
    'open_files': r'open files',
    'search_files': r'search files for (.+)',
    'delete_files': r'delete files (.+)',
    'open_recorder': r'open recorder',
    'start_recording': r'start recording',
    'stop_recording': r'stop recording',
    'open_todo': r'open to-do list',
    'add_todo': r'add to-do (.+)',
    'delete_todo': r'delete to-do (.+)',
    'open_airplane_mode': r'open airplane mode',
    'toggle_airplane_mode': r'(turn on|turn off|enable|disable) airplane mode',
    'open_hotspot': r'open hotspot',
    'toggle_hotspot': r'(turn on|turn off|enable|disable) hotspot',
    'open_dnd': r'open do not disturb',
    'toggle_dnd': r'(turn on|turn off|enable|disable) do not disturb',
    'open_accessibility': r'open accessibility',
    'open_language_settings': r'open language settings',
    'change_language': r'change language to (.+)',
    'open_wallpaper': r'open wallpaper settings',
    'set_wallpaper': r'set wallpaper to (.+)',
    'open_theme': r'open theme settings',
    'set_theme': r'set theme to (.+)',
    'open_security': r'open security settings',
    'scan_qr': r'scan qr code',
    'open_payment': r'open payment app',
    'make_payment': r'make payment to (.+) of (.+)',
    'open_otp': r'open otp app',
    'read_otp': r'read otp from (.+)',
    'open_news': r'open news app',
    'read_news': r'read news about (.+)',
    'open_podcast': r'open podcast app',
    'play_podcast': r'play podcast (.+)',
    'open_books': r'open books app',
    'read_book': r'read book (.+)',
    'open_dictionary': r'open dictionary',
    'define_word': r'define (.+)',
    'open_translation': r'open translation app',
    'translate_text': r'translate (.+) to (.+)',
    'open_health': r'open health app',
    'track_steps': r'track my steps',
    'track_sleep': r'track my sleep',
    'open_fitness': r'open fitness app',
    'start_workout': r'start workout (.+)',
    'stop_workout': r'stop workout',
    'open_reminder': r'open reminder app',
    'set_reminder': r'set reminder (.+) at (.+)',
    'delete_reminder': r'delete reminder (.+)',
    'open_bluetooth_settings': r'open bluetooth settings',
    'pair_bluetooth': r'pair bluetooth device (.+)',
    'disconnect_bluetooth': r'disconnect bluetooth device (.+)',
    'open_wifi_settings': r'open wifi settings',
    'connect_wifi': r'connect to wifi (.+)',
    'disconnect_wifi': r'disconnect wifi (.+)',
    'open_storage': r'open storage settings',
    'clear_cache': r'clear cache of (.+)',
    'open_app_info': r'open app info for (.+)',
    'force_stop_app': r'force stop (.+)',
    'open_developer_options': r'open developer options',
    'enable_developer_options': r'enable developer options',
    'disable_developer_options': r'disable developer options',
    'open_location_settings': r'open location settings',
    'enable_location': r'enable location',
    'disable_location': r'disable location',
    'open_security_settings': r'open security settings',
    'enable_screen_lock': r'enable screen lock',
    'disable_screen_lock': r'disable screen lock',
    'open_battery_settings': r'open battery settings',
    'optimize_battery': r'optimize battery',
    'open_app_drawer': r'open app drawer',
    'close_app_drawer': r'close app drawer',
    'open_recent_apps': r'open recent apps',
    'close_recent_apps': r'close recent apps',
    'open_split_screen': r'open split screen',
    'close_split_screen': r'close split screen',
    'open_picture_in_picture': r'open picture in picture',
    'close_picture_in_picture': r'close picture in picture',
    'open_notification_panel': r'open notification panel',
    'close_notification_panel': r'close notification panel',
    'open_quick_settings': r'open quick settings',
    'close_quick_settings': r'close quick settings',
    'open_emergency': r'open emergency info',
    'call_emergency': r'call emergency',
    'open_voice_assistant': r'open voice assistant',
    'activate_voice_assistant': r'activate voice assistant',
    'deactivate_voice_assistant': r'deactivate voice assistant',
    # Add more patterns as needed
}

class AndroidControlMiddleware:
    def __init__(self):
        pass

    def detect_command(self, text):
        """Detects which command pattern matches the user text."""
        for cmd, pattern in COMMAND_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return cmd, match.groups()
        return None, None

    def execute_command(self, cmd, args):
        """Executes the detected command using ADB (as example)."""
        # This is a stub. Replace with actual ADB/Appium/custom service calls.
        if cmd == 'open_app':
            app_name = args[0]
            # Example: subprocess.run(["adb", "shell", "monkey", "-p", f"com.{app_name}", "1"])
            return f"Opening {app_name} app."
        elif cmd == 'close_app':
            app_name = args[0]
            # Example: subprocess.run(["adb", "shell", "am", "force-stop", f"com.{app_name}"])
            return f"Closing {app_name} app."
        elif cmd == 'search_youtube':
            query = args[0]
            return f"Searching YouTube for {query}."
        elif cmd == 'play_youtube':
            query = args[0]
            return f"Playing {query} on YouTube."
        elif cmd == 'set_volume':
            direction = args[0]
            return f"Setting volume {direction}."
        elif cmd == 'set_quality':
            direction = args[0]
            return f"Setting YouTube quality {direction}."
        elif cmd == 'scroll_feed':
            feed = args[0]
            return f"Scrolling {feed}."
        elif cmd == 'send_message':
            contact = args[0]
            return f"Sending message to {contact}."
        elif cmd == 'install_app':
            app = args[0]
            return f"Installing {app}."
        elif cmd == 'uninstall_app':
            app = args[0]
            return f"Uninstalling {app}."
        elif cmd == 'control_flashlight':
            action = args[0]
            return f"{action.capitalize()} flashlight."
        elif cmd == 'set_brightness':
            level = args[1]
            return f"Setting brightness to {level}%."
        elif cmd == 'update_android':
            return "Updating Android software."
        else:
            return "Command not recognized."

    def process_user_command(self, text):
        lang = detect_language(text)
        cmd, args = self.detect_command(text)
        if cmd:
            result = self.execute_command(cmd, args)
            return translate_text(result, lang)
        return None

# Usage:
# android_hook = AndroidControlMiddleware()
# result = android_hook.process_user_command(user_text)
# If result is not None, use it as the agent's reply
