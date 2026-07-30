"""
Voice AI Assistant & Smart City Emergency Audio Synthesizer.
Uses Web Audio API for sirens/chimes and Web Speech API (HTML5 SpeechSynthesis) for natural voice announcements.
Includes a 30-second alert cooldown to prevent redundant playback loops.
"""

import time

# In-memory cooldown tracking per alert message
_LAST_PLAYED_TIMES = {}
COOLDOWN_SECONDS = 30


def get_emergency_voice_script(road_name: str, event_type: str, vehicle_type: str = "AMBULANCE", resolved: bool = False) -> str:
    """Generates clear, natural emergency voice scripts based on requirement specifications."""
    if resolved:
        return f"The emergency situation on {road_name} has been resolved. Normal traffic operations are being restored."
    
    evt = event_type.upper()
    v_type = vehicle_type.upper()

    if "AMBULANCE" in v_type or evt == "MEDICAL EMERGENCY":
        return f"Emergency alert. An ambulance is approaching on {road_name}. Please move to the left and keep the road clear."
    elif "FIRE" in v_type or evt == "FIRE EMERGENCY":
        return f"Emergency alert. A fire emergency vehicle is approaching on {road_name}. Please clear the emergency corridor immediately."
    elif "POLICE" in v_type or evt == "POLICE EMERGENCY":
        return f"Emergency alert. A police emergency vehicle is approaching on {road_name}. Please yield right of way and maintain clear lanes."
    elif "ACCIDENT" in evt or "CRITICAL" in evt:
        return f"Emergency alert. A serious accident has been detected on {road_name}. Please slow down and avoid this area. An emergency vehicle is approaching. Please keep the emergency lane clear."
    else:
        return f"Emergency alert. Special traffic advisory active on {road_name}. Please proceed with caution."


def generate_voice_announcement_html(title: str, message: str, alert_type: str = "EMERGENCY", enabled: bool = True, force_play: bool = False) -> str:
    """
    Generates HTML/JS snippet to play emergency audio chimes and trigger browser speech synthesis with 30s cooldown.
    """
    if not enabled or not message:
        return ""

    now = time.time()
    msg_key = f"{title}_{message[:30]}"
    last_time = _LAST_PLAYED_TIMES.get(msg_key, 0)

    # Check alert cooldown (unless forced by manual button trigger)
    if not force_play and (now - last_time < COOLDOWN_SECONDS):
        # Render silent status bar during cooldown
        return f"""
        <div id="voice-assistant-status" style="font-family: Arial, sans-serif; background: #0F172A; padding: 8px 14px; border-radius: 8px; border: 1px solid #334155; display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 18px;">🎙️</span>
                <div>
                    <strong style="color: #38BDF8; font-size: 13px;">Voice AI Assistant (Active - Cooldown 30s)</strong>
                    <p style="margin: 2px 0 0 0; color: #94A3B8; font-size: 11px;">{title}</p>
                </div>
            </div>
            <button onclick="if(window.speechSynthesis) {{ var u = new SpeechSynthesisUtterance('{title}'); window.speechSynthesis.speak(u); }}" style="background: #0284C7; color: white; border: none; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 11px; cursor: pointer;">
                🔊 Replay
            </button>
        </div>
        """

    # Record playback timestamp
    _LAST_PLAYED_TIMES[msg_key] = now

    # Sanitize message string for JavaScript
    clean_text = f"{title}. {message}".replace('"', '\\"').replace("'", "\\'").replace('\n', ' ')
    is_emergency = (alert_type.upper() in ["EMERGENCY", "CRITICAL", "ACCIDENT"])

    html_code = f"""
    <div id="voice-assistant-status" style="font-family: Arial, sans-serif; background: #0F172A; padding: 10px 16px; border-radius: 8px; border: 1px solid #334155; display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 20px;">🎙️</span>
            <div>
                <strong style="color: {'#EF4444' if is_emergency else '#F59E0B'}; font-size: 14px;">Voice AI Assistant Broadcasting Live</strong>
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
