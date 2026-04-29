from flask import Flask, jsonify
from flask_cors import CORS

from . import state, store

app = Flask(__name__)
CORS(app)


@app.get('/livestreams')
def get_livestreams():
    result = [
        {'id': ls.id, 'title': ls.title}
        for channel in state.channels
        for ls in store.get_livestreams(state.redis_client, channel.id)
    ]
    return jsonify(result)
