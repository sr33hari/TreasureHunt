from flask import Flask, render_template, request, jsonify, send_from_directory
from kazoo.client import KazooClient
from pydantic import BaseModel
from flask_socketio import SocketIO, emit
import json
import threading
import traceback
import time

app = Flask(__name__)
socketio = SocketIO(app)

# Connect to Zookeeper
zk_hosts = '10.0.0.13:2181'  # Use your actual Zookeeper host IP
zk = KazooClient(hosts=zk_hosts)
zk.start()

# Ensure the lobby node exists
lobby_path = '/lobby'
if not zk.exists(lobby_path):
    zk.create(lobby_path, b'')

#create a global variable for username to store
username = ''


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join', methods=['POST'])
def join():
    #define initial user data
    user_data = {
    'isLeader': False,
    'isReady': False,
    'timestampClue': 0,
    'score': 0,
    'gameStarted': False,
    'isRoundOver': False,
    'roundCounter': 0
}
    #set the global variable username to the username entered by the user
    global username
    username = request.form['username']

    user_path = f"{lobby_path}/{username}"
    if not zk.exists(user_path):
        children = zk.get_children(lobby_path)
        is_leader = len(children) == 0  # First user to join becomes the leader
        user_data['isLeader'] = is_leader
        user_data['isReady'] = False
        user_data = json.dumps(user_data)
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
    max_attempts = 20
    attempts = 0
    while attempts < max_attempts:
        children = zk.get_children(lobby_path)
        all_ready = True
        for child in children:
            data, _ = zk.get(f"{lobby_path}/{child}")
            if not json.loads(data.decode())['isReady']:
                all_ready = False
                break
        if all_ready:
            #get the user data and set the gameStarted flag to True
            for child in children:
                data, _ = zk.get(f"{lobby_path}/{child}")
                user_data = json.loads(data.decode())
                user_data['gameStarted'] = True
                user_data['roundCounter'] += 1
                zk.set(f"{lobby_path}/{child}", json.dumps(user_data).encode())

                #emit the start game event to all users
                socketio.emit('start game', {'url': 'torch.html'})

            return jsonify({'message': 'All users ready, entering game now'})
        time.sleep(1)  # wait for 1 second before checking again
        attempts += 1
    return jsonify({'message': 'Waiting for all users to be ready'})

@app.route('/api/treasureFound', methods=['POST'])
def treasure_found():
    username = request.form['username']
    user_path = f"{lobby_path}/{username}"
    user_data = json.loads(zk.get(user_path)[0].decode())
    user_data['timestampClue'] = int(time.time())
    user_data['isRoundOver'] = True
    user_data['isReady'] = False
    user_data['gameStarted'] = False
    socketio.emit('treasure updates', {'message': f'{username} found the treasure!'})
    socketio.emit('round over', {'url':'lobby.html'})
    zk.set(user_path, json.dumps(user_data).encode())
    return jsonify({'status': 'success', 'message': f'{username} found the treasure!'})


def compute_scores():
    while True:
        try:
            children = zk.get_children(lobby_path)
            # Check if any child has a timestampClue of 0
            for child in children:
                data, _ = zk.get(f"{lobby_path}/{child}")
                timestampClue = json.loads(data.decode())['timestampClue']
                app.logger.info(f"Data from the player {child} is {data.decode()}")
                if timestampClue == 0:
                    app.logger.info("Exiting: Not all players have found the clue.")
                    return  # Exit the function if any child has not found the clue

            # If all children have found the clue, proceed to compute scores
            child_data = {}
            for child in children:
                data, _ = zk.get(f"{lobby_path}/{child}")
                decoded_data = json.loads(data.decode())
                child_data[child] = decoded_data

            timestamps = [data['timestampClue'] for data in child_data.values()]
            earliest_timestamp = min(timestamps)

            # Calculate and set scores
            for child, data in child_data.items():
                time_difference = data['timestampClue'] - earliest_timestamp
                data['score'] = max(1000 - time_difference, 0)
                zk.set(f"{lobby_path}/{child}", json.dumps(data).encode())

        except Exception as e:
            app.logger.error(f"Error computing scores: {str(e)}")
            break  # Consider what to do in case of an exception, possibly continue or exit based on your use case


def ensure_single_leader():
    while True:
        try:
            children = zk.get_children(lobby_path)
            leaders = [child for child in children if json.loads(zk.get(f"{lobby_path}/{child}")[0].decode())['isLeader']]
            if len(leaders) == 0 and children:  # No leaders and there are users
                json_data = []
                for child in children:
                    data, _ = zk.get(f"{lobby_path}/{child}")
                    json_data.append(json.loads(data.decode()))
                #check for the user with the highest score and make him the leader 
                new_leader = max(json_data, key=lambda x: x['score'])
                data, _ = zk.get(f"{lobby_path}/{new_leader}")
                new_data = json.loads(data.decode())
                new_data['isLeader'] = True
                zk.set(f"{lobby_path}/{new_leader}", json.dumps(new_data).encode())

            #If there are two users in the lobby, set the isLastRound flag to True
            if len(children) == 2:
                for child in children:
                    data, _ = zk.get(f"{lobby_path}/{child}")
                    user_data = json.loads(data.decode())
                    user_data['isLastRound'] = True
                    zk.set(f"{lobby_path}/{child}", json.dumps(user_data).encode())
                
            #check if username is not empty string:
            if username != '':
                data, _ = zk.get(f"{lobby_path}/{username}")
                json_data = json.loads(data.decode())
                if json_data['isLeader']:
                    compute_scores() #have this function return the results of the game, if the respinse is valid then update the score board and start a new round.
            
            
        except Exception as e:
            app.logger.error(f"Error ensuring leader: {str(e)}")
            traceback.print_exc()
        time.sleep(10)  # Check every 10 seconds

# Start the background thread to ensure there is always a single leader
threading.Thread(target=ensure_single_leader, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=6190)