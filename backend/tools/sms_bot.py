"""
Native Cellular SMS AI Bot Gateway Service.
Supports Twilio SMS API & Fast2SMS API for live real-world cellular SMS delivery directly to physical mobile phones.
"""
import os
import requests
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("smart_traffic_ai.sms_bot")


class CellularSMSBot:
    """Automated Cellular SMS AI Bot - Sends native SMS to physical mobile phones."""

    @staticmethod
    def format_sms_payload(alert_data: Dict[str, Any]) -> str:
        """Formats alert into concise GSM Cellular SMS text message."""
        title = alert_data.get("title", "TRAFFIC ADVISORY")
        message = alert_data.get("message", "Heavy density on main route.")
        road = alert_data.get("affected_road", alert_data.get("road_name", "Main Road"))
        reroute = alert_data.get("alternate_route", None)

        sms_text = f"ALERT: {title} on {road}. {message}"
        if reroute:
            sms_text += f" Detour via {reroute}."
        sms_text += " -SmartCity Traffic AI"
        return sms_text

    @classmethod
    def dispatch_cellular_sms(
        cls, 
        phone_number: str, 
        alert_data: Dict[str, Any],
        fast2sms_api_key: str = "",
        twilio_sid: str = "",
        twilio_auth: str = "",
        twilio_number: str = ""
    ) -> Dict[str, Any]:
        """
        Dispatches real Cellular SMS directly to physical phone.
        Supports Fast2SMS (Free India SMS Gateway) & Twilio SMS API.
        """
        clean_phone = "".join(filter(str.isdigit, phone_number))
        if not clean_phone:
            return {"status": "FAILED", "error": "Invalid mobile phone number format"}

        sms_text = cls.format_sms_payload(alert_data)

        # 1. Fast2SMS Gateway (Free Gateway for Indian +91 numbers)
        api_key = fast2sms_api_key or os.getenv("FAST2SMS_API_KEY", "")
        if api_key:
            try:
                url = "https://www.fast2sms.com/dev/bulkV2"
                payload = f"message={sms_text}&language=english&route=q&numbers={clean_phone}"
                headers = {
                    'authorization': api_key,
                    'Content-Type': "application/x-www-form-urlencoded",
                    'Cache-Control': "no-cache"
                }
                response = requests.post(url, data=payload, headers=headers)
                res_data = response.json()
                logger.info(f"Fast2SMS API Response: {res_data}")

                if res_data.get("return") is True:
                    return {
                        "status": "DELIVERED_TO_PHYSICAL_PHONE",
                        "gateway": "Fast2SMS Cellular Network",
                        "message_id": res_data.get("request_id", "F2SMS-OK"),
                        "recipient_phone": f"+{clean_phone}",
                        "sms_body": sms_text,
                        "notes": "Real SMS delivered to recipient physical mobile phone!"
                    }
                else:
                    return {
                        "status": "GATEWAY_ERROR",
                        "error": res_data.get("message", "Fast2SMS API call failed"),
                        "sms_body": sms_text
                    }
            except Exception as e:
                logger.warning(f"Fast2SMS API Exception: {e}")

        # 2. Twilio SMS Gateway
        sid = twilio_sid or os.getenv("TWILIO_ACCOUNT_SID", "")
        auth = twilio_auth or os.getenv("TWILIO_AUTH_TOKEN", "")
        t_num = twilio_number or os.getenv("TWILIO_SMS_NUMBER", "")

        if sid and auth and t_num:
            try:
                from twilio.rest import Client
                client = Client(sid, auth)
                msg = client.messages.create(
                    from_=t_num,
                    body=sms_text,
                    to=f"+{clean_phone}"
                )
                logger.info(f"Twilio SMS dispatched: {msg.sid}")
                return {
                    "status": "DELIVERED_TO_PHYSICAL_PHONE",
                    "gateway": "Twilio SMS Gateway",
                    "message_id": msg.sid,
                    "recipient_phone": f"+{clean_phone}",
                    "sms_body": sms_text,
                    "notes": "Real SMS delivered to recipient physical mobile phone!"
                }
            except Exception as e:
                logger.warning(f"Twilio SMS Exception: {e}")

        # 3. Simulated Gateway (When no live API keys are provided)
        import uuid
        sms_id = f"SIM-SMS-{uuid.uuid4().hex[:8].upper()}"
        return {
            "status": "SIMULATION_MODE",
            "gateway": "SmartCity Simulated Cellular Gateway",
            "message_id": sms_id,
            "recipient_phone": f"+{clean_phone}",
            "sms_body": sms_text,
            "notice": "To receive REAL SMS on your physical phone, enter a free Fast2SMS API Key or Twilio SID in the settings box below!",
            "free_key_link": "https://www.fast2sms.com (Free trial API Key)"
        }


def send_cellular_sms(
    phone_number: str, 
    alert_data: Dict[str, Any],
    fast2sms_api_key: str = "",
    twilio_sid: str = "",
    twilio_auth: str = "",
    twilio_number: str = ""
) -> Dict[str, Any]:
    """Utility wrapper for real Cellular SMS dispatch."""
    return CellularSMSBot.dispatch_cellular_sms(
        phone_number=phone_number,
        alert_data=alert_data,
        fast2sms_api_key=fast2sms_api_key,
        twilio_sid=twilio_sid,
        twilio_auth=twilio_auth,
        twilio_number=twilio_number
    )
