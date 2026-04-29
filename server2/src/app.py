from flask import Flask, jsonify

from . import state, store

app = Flask(__name__)


@app.get('/livestreams')
def get_livestreams():
    result = [
        {'id': ls.id, 'title': ls.title}
        for channel in state.channels
        for ls in store.get_livestreams(state.redis_client, channel.id)
    ]
    return jsonify(result)
