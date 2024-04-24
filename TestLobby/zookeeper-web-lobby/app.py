from flask import Flask, render_template, request, jsonify
from kazoo.client import KazooClient

app = Flask(__name__)

# Connect to Zookeeper
zk_hosts = '172.16.57.246:2181'  # Change to your Zookeeper host IP
zk = KazooClient(hosts=zk_hosts)
zk.start()

# Ensure the lobby node exists
lobby_path = '/lobby'
if not zk.exists(lobby_path):
    zk.create(lobby_path, b'')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join', methods=['POST'])
def join():
    username = request.form['username']
    user_path = f"{lobby_path}/{username}"
    if not zk.exists(user_path):
        zk.create(user_path, ephemeral=True)
        return jsonify({'status': 'success', 'message': 'You have joined the lobby!'})
    else:
        return jsonify({'status': 'error', 'message': 'Username already in use'})

@app.route('/lobby', methods=['GET'])
def get_lobby():
    children = zk.get_children(lobby_path)
    return jsonify({'users': children})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6190)
