from flask import Flask, render_template, request, jsonify, send_from_directory
from kazoo.client import KazooClient
import json
import threading
import time

app = Flask(__name__)

# Connect to Zookeeper
zk_hosts = '172.16.57.233:2181'  # Use your actual Zookeeper host IP
zk = KazooClient(hosts=zk_hosts)
zk.start()

# Ensure the lobby node exists
lobby_path = '/lobby'
if not zk.exists(lobby_path):
    zk.create(lobby_path, b'')

def ensure_single_leader():
    while True:
        try:
            children = zk.get_children(lobby_path)
            leaders = [child for child in children if json.loads(zk.get(f"{lobby_path}/{child}")[0].decode())['isLeader']]
            if len(leaders) == 0 and children:  # No leaders and there are users
                new_leader = children[0]  # Assign the first user in the list as the new leader
                data, _ = zk.get(f"{lobby_path}/{new_leader}")
                new_data = json.loads(data.decode())
                new_data['isLeader'] = True
                zk.set(f"{lobby_path}/{new_leader}", json.dumps(new_data).encode())
        except Exception as e:
            app.logger.error(f"Error ensuring leader: {str(e)}")
        time.sleep(10)  # Check every 10 seconds

# Start the background thread to ensure there is always a single leader
threading.Thread(target=ensure_single_leader, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join', methods=['POST'])
def join():
    username = request.form['username']
    user_path = f"{lobby_path}/{username}"
    if not zk.exists(user_path):
        children = zk.get_children(lobby_path)
        is_leader = len(children) == 0  # First user to join becomes the leader
        user_data = json.dumps({'isLeader': is_leader, 'isReady': False})
        zk.create(user_path, user_data.encode(), ephemeral=True)
        return jsonify({'status': 'success', 'message': 'You have joined the lobby!', 'isLeader': is_leader})
    else:
        return jsonify({'status': 'error', 'message': 'Username already in use'})


@app.route('/lobby', methods=['GET'])
def get_lobby():
    children = zk.get_children(lobby_path)
    return jsonify({'users': children})


@app.route('/lobby.html')
def serve_lobby():
    return send_from_directory('templates', 'lobby.html')

@app.route('/torch.html')
def serve_torch():
    return send_from_directory('templates', 'torch.html')

@app.route('/api/userReady', methods=['GET'])
def user_ready():
    username = request.args.get('username')
    # handle the user being ready
    return jsonify({'message': f'{username} is ready'})

@app.route('/setReady', methods=['POST'])
def set_ready():
    username = request.form['username']
    user_path = f"{lobby_path}/{username}"
    user_data = json.loads(zk.get(user_path)[0].decode())
    user_data['isReady'] = True
    zk.set(user_path, json.dumps(user_data).encode())
    return jsonify({'status': 'success', 'message': f'{username} is now ready'})

@app.route('/checkReady', methods=['GET'])
def check_ready():
    children = zk.get_children(lobby_path)
    all_ready = True
    for child in children:
        data, _ = zk.get(f"{lobby_path}/{child}")
        if not json.loads(data.decode())['isReady']:
            all_ready = False
            break
    if all_ready:
        return jsonify({'message': 'All users ready, entering game now'})
    return jsonify({'message': 'Waiting for all users to be ready'})

@app.route('/treasures/timestamp', methods=['POST'])
def receive_timestamp():
    data = request.json
    timestamp = data.get('timestamp')

    # Here you can process the timestamp as needed
    # For example, you can save it to a database, perform further processing, etc.
    print("Received timestamp:", timestamp)

    # Optionally, you can send a response back to the frontend
    response = {'message': 'Timestamp received successfully'}
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6190)

