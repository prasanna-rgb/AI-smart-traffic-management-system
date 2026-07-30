"""
WhatsApp Traffic Alert Dispatcher Tool.
Supports direct WhatsApp Web/Mobile Deep Linking and Twilio WhatsApp REST API dispatch.
"""
import os
import urllib.parse
import requests
from typing import Dict, Any, Tuple


class WhatsAppNotifier:
    """Class responsible for generating and sending WhatsApp traffic advisories."""

    @staticmethod
    def format_whatsapp_message(title: str, severity: str, message: str, road: str, alternate_route: str = None) -> str:
        """
        Formats a citizen traffic broadcast message into a clean WhatsApp template.
        """
        icon = "🚨" if severity in ["EMERGENCY", "CRITICAL"] else ("⚠️" if severity == "WARNING" else "ℹ️")
        
        msg = f"{icon} *SMART TRAFFIC CITIZEN ADVISORY*\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"*Headline:* {title}\n"
        msg += f"*Severity:* {severity}\n"
        msg += f"*Affected Corridor:* {road}\n\n"
        msg += f"*Alert Details:* {message}\n"
        
        if alternate_route and alternate_route != "N/A":
            msg += f"\n🗺️ *Advised Detour:* {alternate_route}\n"
            
        msg += f"\n⏱️ *Issued By:* Smart City Urban Mobility AI Command Hub\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━"
        return msg

    @staticmethod
    def generate_whatsapp_web_link(phone_number: str, message_text: str) -> str:
        """
        Generates an instant click-to-chat WhatsApp deep link.
        
        Args:
            phone_number: Recipient number with country code (e.g. "+919876543210" or "919876543210").
            message_text: Unencoded string message.
            
        Returns:
            https://wa.me/... click-to-chat URL string.
        """
        clean_phone = "".join(filter(str.isdigit, phone_number))
        encoded_msg = urllib.parse.quote(message_text)
        return f"https://wa.me/{clean_phone}?text={encoded_msg}"

    @staticmethod
    def send_via_twilio(phone_number: str, message_text: str) -> Tuple[bool, str]:
        """
        Sends automated WhatsApp message via Twilio API if credentials exist in environment.
        
        Returns:
            Tuple of (success_boolean, status_message_string).
        """
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886") # Default Twilio Sandbox Number
        
        if not account_sid or not auth_token:
            return False, "Twilio API keys not found in .env. Click-to-Chat deep link available."
            
        clean_phone = "".join(filter(str.isdigit, phone_number))
        to_whatsapp = f"whatsapp:+{clean_phone}"
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        
        payload = {
            "From": from_number,
            "To": to_whatsapp,
            "Body": message_text
        }
        
        try:
            response = requests.post(url, data=payload, auth=(account_sid, auth_token), timeout=8)
            if response.status_code in [200, 201]:
                return True, f"WhatsApp message successfully dispatched to {to_whatsapp} via Twilio API!"
            else:
                return False, f"Twilio API Error ({response.status_code}): {response.text}"
        except Exception as e:
            return False, f"Network exception dispatching Twilio API message: {str(e)}"
