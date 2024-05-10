from flask import Flask, render_template, request, jsonify, send_from_directory
from kazoo.client import KazooClient
from flask_socketio import SocketIO
import json
import time
import logging
import sys
import traceback
import threading

app = Flask(__name__)
socketio = SocketIO(app)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

# Connect to Zookeeper
zk_hosts = '172.16.57.246:2181'  # Use your actual Zookeeper host IP
zk = KazooClient(hosts=zk_hosts)
zk.start()

# Ensure the lobby node exists
lobby_path = '/lobby'
if not zk.exists(lobby_path):
    zk.create(lobby_path, b'')

#create a global variable for username to be stored
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
    'roundCounter': 0,
    'username': '',
    'clueFinders': "",
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

@app.route('/gameOver.html')
def serve_gameOver():
    return send_from_directory('templates', 'gameOver.html')

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
                    zk.set(f"{lobby_path}/{child}", json.dumps(user_data).encode(),)
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
    user_data['roundCounter'] += 1
    # app.logger.info(f"User {username} found the treasure at {user_data['timestampClue']}\n\n\n")
    # user_data['isRoundOver'] = True
    # user_data['isReady'] = False
    # user_data['gameStarted'] = False
    # socketio.emit('treasure updates', {'message': f'{username} found the treasure!'})
    # socketio.emit('round over', {'url':'lobby.html'})
    user_data['clueFinders'] = username
    children = zk.get_children(lobby_path)
    for child in children:
        data, _ = zk.get(f"{lobby_path}/{child}")
        other_users_data = json.loads(data.decode())
        if other_users_data['username'] == username:
            
            pass
        else:
            other_users_data['clueFinders'] = username
            zk.set(f"{lobby_path}/{child}", json.dumps(other_users_data).encode())
    # time.sleep(0.2)
    zk.set(user_path, json.dumps(user_data).encode())
    # if isLeader:
    #     compute_scores()
    return jsonify({'status': 'success', 'message': f'{username} found the treasure! \n\n'})

@app.route('/scores', methods=['GET'])
def get_scores():
    # exampleJSON = {
    #     'user1': 1000,
    #     'user2': 900,
    #     'user3': 800,
    # }
    time.sleep(5)
    children = zk.get_children(lobby_path)
    scores = {}
    for child in children:
        data, _ = zk.get(f"{lobby_path}/{child}")
        user_data = json.loads(data.decode())
        scores[child] = user_data['score']
    return jsonify(scores)
    # return jsonify(exampleJSON)

# @zk.DataWatch(lobby_path)
# def broadcastTreasureUpdates(data, stat, event):
#     )

@app.route('/removeUsers', methods=['GET'])
def remove_users():
    children = zk.get_children(lobby_path)
    for child in children:
        zk.delete(f"{lobby_path}/{child}")
    return jsonify({'status': 'success', 'message': 'All users removed'})

@zk.DataWatch(lobby_path)
def watch_children(data, stat, event):
    if data is None:
        # Node has been deleted
        app.logger.info("Node has been deleted.")
        return
    
    # app.logger.info(f"Child data changed: {data}")
    try:
        app.logger.info(f"{username} data update \n.{data}\n")
        user_data = json.loads(data.decode())
        if user_data['gameStarted'] and user_data['roundCounter'] == 1:
            socketio.emit('start game', {'url': 'torch.html'})
            # app.logger.info(f"Game started: {user_data}")
        if user_data['clueFinders'] != "":
            socketio.emit('treasure updates', {'message': f'{user_data["clueFinders"]} found the treasure!'})
            # app.logger.info(f"Clue finders broadcast: {user_data}")
    except Exception as e:
        app.logger.error(f"Error handling data change: {e}")

@zk.ChildrenWatch(lobby_path)
def ensure_leader_exists(children):
    app.logger.info(f"Lobby users have changed: {children}\n\n")

    leader_count = 0

    all_users_data = []

    for child in children:
        data, _ = zk.get(f"{lobby_path}/{child}")
        user_data = json.loads(data.decode())
        all_users_data.append(user_data)
        if user_data['isLeader']:
            leader_count += 1
    
    if leader_count ==0 and len(children) > 0:
        # Choose new leader, e.g., the first child or based on some criteria
        new_leader = max(all_users_data, key=lambda x: x['score'])
        # data, _ = zk.get(f"{lobby_path}/{new_leader['username']}")
        # new_data = json.loads(data.decode())
        # new_data['isLeader'] = True
        new_leader['isLeader'] = True
        zk.set(f"{lobby_path}/{new_leader['username']}", json.dumps(new_leader).encode())
        app.logger.info(f"New leader assigned: {new_leader}\n\n\n\n")

def compute_scores():
    #TODO change the leader after every round
    app.logger.info("Computing scores\n\n")
    try:
        max_attempts = 200000
        attempts = 0
        while attempts < max_attempts:
            app.logger.info(f"Attempt {attempts}\n")
            children = zk.get_children(lobby_path)
            # Check if any child has a timestampClue of 0
            all_done = False
            child_data = {}
            countFound = 0
            for child in children:
                data, _ = zk.get(f"{lobby_path}/{child}")
                decoded_data = json.loads(data.decode())
                child_data[child] = decoded_data
                timestampClue = decoded_data['timestampClue']
                app.logger.info(f"Data from the player {child} is {data.decode()}")
                if timestampClue == 0:
                    app.logger.info("Exiting: Not all players have found the clue.")
                    all_done=False  # Exit the function if any child has not found the clue
                else:
                    countFound += 1
            if countFound == len(children) and countFound > 0:
                all_done=True

            if all_done:
                # If all children have found the clue, proceed to compute score
                timestamps = [data['timestampClue'] for data in child_data.values()]
                earliest_timestamp = min(timestamps)

                # Calculate and set scores
                for child, data in child_data.items():
                    time_difference = data['timestampClue'] - earliest_timestamp
                    data['score'] = max(1000 - time_difference, 0)
                    zk.set(f"{lobby_path}/{child}", json.dumps(data).encode())
            
            time.sleep(1)
            attempts += 1

    except Exception as e:
        app.logger.error(f"Error computing scores: {str(e)}")


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

threading.Thread(target=compute_scores, daemon=True).start()

if __name__ == '__main__':
    # socketio.run(app, debug=True)
    socketio.run(app, debug=True, host='0.0.0.0', port=5004)
