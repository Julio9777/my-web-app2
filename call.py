import urllib.request
import urllib.parse
import json
import os

# Load from environment
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")
APP_URL = os.environ.get("APP_URL", "")

def make_call(to_number: str, question: str) -> dict:
    """
    Tells Twilio to call a number and ask a question.
    Returns the call SID so we can check the result later.
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, APP_URL]):
        return {"error": "Missing Twilio credentials in environment variables."}

    # The TwiML webhook URL — Twilio will call this to get instructions
    twiml_url = f"{APP_URL}/twiml?question={urllib.parse.quote(question)}"

    # Twilio REST API call
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"

    data = urllib.parse.urlencode({
        "To": to_number,
        "From": TWILIO_PHONE_NUMBER,
        "Url": twiml_url,
        "Method": "POST"
    }).encode()

    # Basic auth with Account SID and Auth Token
    import base64
    credentials = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()

    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    })

    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read())
            return {"success": True, "call_sid": result.get("sid"), "status": result.get("status")}
    except urllib.error.HTTPError as e:
        error = json.loads(e.read())
        return {"error": error.get("message", "Unknown Twilio error")}
