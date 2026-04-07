import http.server
import json
import urllib.request
import urllib.error
import urllib.parse
import os
from call import make_call

# Load config from environment variables
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN", "")
PORT = int(os.environ.get("PORT", 8000))
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

if not API_KEY:
    print("ERROR: ANTHROPIC_API_KEY is not set.")
    exit(1)

if not SECRET_TOKEN:
    print("ERROR: SECRET_TOKEN is not set.")
    exit(1)

class Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/' or path == '':
            path = '/my-web-app2.html'
        filepath = os.path.join(STATIC_DIR, path.lstrip('/'))
        if os.path.exists(filepath):
            self.send_response(200)
            if filepath.endswith('.html'):
                self.send_header('Content-Type', 'text/html')
            self.end_headers()
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        # Handle Twilio TwiML webhook — no token needed, called by Twilio
        if self.path.startswith('/twiml'):
            self._handle_twiml()
            return

        # Handle Twilio transcription callback
        if self.path.startswith('/transcription'):
            self._handle_transcription()
            return

        # All other POST requests require secret token
        token = self.headers.get('X-Secret-Token', '')
        if token != SECRET_TOKEN:
            self.send_response(401)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": {"message": "Unauthorized."}}')
            return

        if self.path == '/chat':
            self._handle_chat()
        elif self.path == '/call':
            self._handle_call()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_chat(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=body,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': API_KEY,
                'anthropic-version': '2023-06-01'
            },
            method='POST'
        )
        try:
            with urllib.request.urlopen(req) as res:
                result = res.read()
            self.send_response(200)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(result)
        except urllib.error.HTTPError as e:
            error_body = e.read()
            self.send_response(e.code)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(error_body)

    def _handle_call(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        to_number = body.get('to_number', '')
        question = body.get('question', 'Hello, what would you like for dinner tonight?')

        if not to_number:
            self.send_response(400)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing to_number"}).encode())
            return

        result = make_call(to_number, question)
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _handle_twiml(self):
        # Parse question from URL
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        question = params.get('question', ['Hello, what would you like for dinner tonight?'])[0]
        app_url = os.environ.get("APP_URL", "")

        # TwiML — instructions for Twilio on what to say and how to listen
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="fr-FR" voice="Polly.Lea">{question}</Say>
    <Record maxLength="30" transcribe="true" transcribeCallback="{app_url}/transcription" playBeep="true"/>
    <Say language="fr-FR">Merci, au revoir!</Say>
</Response>"""

        self.send_response(200)
        self.send_header('Content-Type', 'text/xml')
        self.end_headers()
        self.wfile.write(twiml.encode())

    def _handle_transcription(self):
        # Twilio sends the transcription here after the call
        length = int(self.headers.get('Content-Length', 0))
        body = urllib.parse.parse_qs(self.rfile.read(length).decode())
        transcript = body.get('TranscriptionText', ['(no response)'])[0]
        print(f"[transcription] {transcript}")

        # Store latest transcription in a temp file
        with open(os.path.join(STATIC_DIR, 'latest_transcription.txt'), 'w') as f:
            f.write(transcript)

        self.send_response(200)
        self.end_headers()

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Secret-Token')

    def log_message(self, format, *args):
        print(f"[server] {args[0]} {args[1]}")

print(f"Server running at http://localhost:{PORT}")
print(f"Serving files from: {STATIC_DIR}")
print("Press Ctrl+C to stop")
http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
