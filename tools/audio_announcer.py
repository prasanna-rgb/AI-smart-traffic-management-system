"""
Voice AI Assistant & Smart City Emergency Audio Synthesizer.
Uses Web Audio API for sirens/chimes and Web Speech API (HTML5 SpeechSynthesis) for natural voice announcements.
"""

def generate_voice_announcement_html(title: str, message: str, alert_type: str = "EMERGENCY", enabled: bool = True) -> str:
    """
    Generates HTML/JS snippet to play emergency audio chimes and trigger browser speech synthesis.
    
    Args:
        title: Alert headline.
        message: Alert message.
        alert_type: "EMERGENCY", "ACCIDENT", or "WARNING".
        enabled: If True, triggers audio speech synthesis.
        
    Returns:
        HTML component script string with Web Audio API sound & Web Speech API TTS.
    """
    if not enabled or not message:
        return ""

    # Sanitize message string for JavaScript
    clean_text = f"{title}. {message}".replace('"', '\\"').replace("'", "\\'").replace('\n', ' ')

    is_emergency = (alert_type.upper() == "EMERGENCY")
    
    html_code = f"""
    <div id="voice-assistant-status" style="font-family: Arial, sans-serif; background: #0F172A; padding: 10px 16px; border-radius: 8px; border: 1px solid #334155; display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 20px;">🎙️</span>
            <div>
                <strong style="color: {'#EF4444' if is_emergency else '#F59E0B'}; font-size: 14px;">Voice AI Assistant Broadcasting</strong>
                <p style="margin: 2px 0 0 0; color: #94A3B8; font-size: 12px;">{title}</p>
            </div>
        </div>
        <button onclick="playAnnouncement()" style="background: #0284C7; color: white; border: none; padding: 6px 14px; border-radius: 4px; font-weight: bold; font-size: 12px; cursor: pointer;">
            🔊 Replay Announcement
        </button>
    </div>

    <script>
        function playAnnouncement() {{
            try {{
                // 1. Play Emergency Siren / Chime using Web Audio API
                var AudioContext = window.AudioContext || window.webkitAudioContext;
                if (AudioContext) {{
                    var ctx = new AudioContext();
                    var osc = ctx.createOscillator();
                    var gain = ctx.createGain();
                    
                    osc.type = "{'sawtooth' if is_emergency else 'sine'}";
                    osc.frequency.setValueAtTime({'880' if is_emergency else '587'}, ctx.currentTime);
                    osc.frequency.exponentialRampToValueAtTime({'440' if is_emergency else '440'}, ctx.currentTime + 0.4);
                    
                    gain.gain.setValueAtTime(0.2, ctx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.45);
                    
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start();
                    osc.stop(ctx.currentTime + 0.45);
                }}

                // 2. Speak Voice Speech Synthesis Announcement after short delay
                setTimeout(function() {{
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel(); // Clear previous speech
                        var text = "{clean_text}";
                        var utterance = new SpeechSynthesisUtterance(text);
                        utterance.rate = 0.95;  // Natural speech rate
                        utterance.pitch = {'1.1' if is_emergency else '1.0'}; 
                        utterance.lang = 'en-US';
                        window.speechSynthesis.speak(utterance);
                    }}
                }}, 350);
            }} catch(e) {{
                console.log("Audio synthesis error:", e);
            }}
        }}

        // Trigger announcement on load
        playAnnouncement();
    </script>
    """
    return html_code
