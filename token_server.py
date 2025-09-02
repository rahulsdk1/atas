from flask import Flask, request
from livekit.api import AccessToken, VideoGrants
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv('LIVEKIT_API_KEY')
API_SECRET = os.getenv('LIVEKIT_API_SECRET')

@app.route('/token', methods=['GET'])
def get_token():
    room_name = 'atas'
    participant_name = 'atas'

    if not API_KEY or not API_SECRET:
        return {'error': 'API key and secret not configured'}, 500

    token = AccessToken(API_KEY, API_SECRET)
    token.with_identity(participant_name)
    token.with_name(participant_name)
    grant = VideoGrants()
    grant.room_join = True
    grant.room = room_name
    token.with_grants(grant)

    return {'token': token.to_jwt()}

if __name__ == '__main__':
    app.run(debug=True)