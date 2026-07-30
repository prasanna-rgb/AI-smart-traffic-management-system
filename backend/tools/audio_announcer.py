"""
Voice Alert Assistant & Smart City Audio Announcer.
Uses Web Speech API (HTML5 SpeechSynthesis) to broadcast live voice alerts in the browser.
"""

def generate_voice_announcement_html(title: str, message: str, enabled: bool = True) -> str:
    """Generates HTML/JS snippet to trigger browser speech synthesis for citizen traffic broadcasts."""
    if not enabled or not message:
        return ""

    clean_text = f"{title}. {message}".replace('"', '\\"').replace("'", "\\'").replace('\n', ' ')

    html_code = f"""
    <script>
        (function() {{
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                var text = "{clean_text}";
                var utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 0.95;
                utterance.pitch = 1.05;
                utterance.lang = 'en-US';
                window.speechSynthesis.speak(utterance);
            }}
        }})();
    </script>
    """
    return html_code
