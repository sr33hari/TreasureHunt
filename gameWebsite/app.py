from flask import Flask, render_template, request, jsonify, send_from_directory
from kazoo.client import KazooClient
# from kazoo.recipe.watchers import ChildrenWatch
# from kazoo.recipe.watchers import DataWatch
from pydantic import BaseModel
from flask_socketio import SocketIO, emit
import json
import threading
import traceback
import time
import logging
import sys

app = Flask(__name__)
socketio = SocketIO(app)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

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
user_sockets = {}


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
    'leaderStartsGame': False,
    'isRoundOver': False,
    'roundCounter': 0,
    'username': ''
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
        user_data['username'] = username
        user_data = json.dumps(user_data)
        
        zk.create(user_path, user_data.encode(), ephemeral=True)
        zk.DataWatch(user_path, watch_children)
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
    # print("Checking if all users are ready\n\n\n")
    try:
        max_attempts = 20
        attempts = 0
        while attempts < max_attempts:
            print("Checking if all users are ready\n\n\n")
            print(f"Attempt {attempts}\n\n")
            children = zk.get_children(lobby_path)
            all_ready = True
            for child in children:
                data, _ = zk.get(f"{lobby_path}/{child}")
                if not json.loads(data.decode())['isReady']:
                    all_ready = False
            if all_ready:
                print("All users ready, entering game now\n\n\n")
                for child in children:
                    data, _ = zk.get(f"{lobby_path}/{child}", watch=watch_children )
                    user_data = json.loads(data.decode())
                    user_data['gameStarted'] = True
                    user_data['roundCounter'] += 1
                    if user_data['isLeader']:
                        user_data['leaderStartsGame'] = True
                    zk.set(f"{lobby_path}/{child}", json.dumps(user_data).encode(),)
                    childpath = f"{lobby_path}/{child}"
                    # watch_children(childpath, None, None)
                # pass the stat argument to the watch_children function
                # watch_children(children, None)
                return jsonify({'message': 'All users ready, entering game now'})
            time.sleep(1)
            attempts += 1
        # return jsonify({'message': 'Waiting for all users to be ready'})
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({'message': 'An error occurred'}), 500
    
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

@zk.DataWatch(lobby_path)
def watch_children(data, stat, event):
    if data is None:
        # Node has been deleted
        app.logger.info("Node has been deleted.")
        return
    
    app.logger.info(f"Child data changed: {data}")
    try:
        user_data = json.loads(data.decode())
        if user_data.get('gameStarted', False):
            socketio.emit('start game', {'url': 'torch.html'})
            app.logger.info(f"Game started: {user_data}")
    except Exception as e:
        app.logger.error(f"Error handling data change: {e}")


@zk.ChildrenWatch(lobby_path)
def ensure_leader_exists(children):
    app.logger.info(f"Children changed: {children}")

    if not children:
        return  # No children, no action needed
    leader_exists = any(json.loads(zk.get(f"{lobby_path}/{child}")[0].decode())['isLeader'] for child in children)
    if not leader_exists:
        # Choose new leader, e.g., the first child or based on some criteria
        new_leader = children[0]  # Simplified example, choose as needed
        data, _ = zk.get(f"{lobby_path}/{new_leader}")
        user_data = json.loads(data.decode())
        user_data['isLeader'] = True
        zk.set(f"{lobby_path}/{new_leader}", json.dumps(user_data).encode())
        app.logger.info(f"New leader assigned: {new_leader}")

# @zk.DataWatch(lobby_path)
# def watch_data(data, stat):
#     print(f"Data changed: {data}")
#     app.logger.info(f"Data changed: {data}")
#     socketio.emit('start game', {'url': 'torch.html'})

# Start the background thread to ensure there is always a single leader
# threading.Thread(target=ensure_single_leader, daemon=True).start()

if __name__ == '__main__':
    # socketio.run(app, debug=True)
    socketio.run(app, debug=True, host='0.0.0.0', port=5004)

