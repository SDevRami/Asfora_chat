from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Generates a random 32-character hex string

socketio = SocketIO(app)

clients = {}
rooms = []

def generate_room_id():
    room_id = secrets.token_urlsafe(4)
    while True:
        room_id = secrets.token_urlsafe(4)
        if room_id not in rooms:
            break
    return room_id

@app.route('/')
def index():
    room_id = generate_room_id()
    return render_template('index.html', room_id=room_id)

@app.route('/host', methods=['POST'])
def host():
    nickname = request.form['nickname']
    room_id = request.form['room_id']
    clients[nickname] = {'room_id': room_id}
    rooms.append(room_id)
    client_number = 1
    return render_template('host.html', nickname=nickname, room_id=room_id, clients=clients, client_number=client_number)

@app.route('/join', methods=['POST'])
def join():
    nickname = request.form['nickname']
    room_id = request.form['room_id']
    clients[nickname] = {'room_id': room_id}
    if room_id in rooms:
        return render_template('join.html', nickname=nickname, room_id=room_id)
    else:
        room_id = generate_room_id()
        return render_template('index.html', room_id=room_id)

@socketio.on('close_session')
def close_session(data):
    room_id = data['roomid']
    nickname = data['nickname']
    if room_id in rooms:
        emit('closesession', {'message': "closesession"}, broadcast=True)
        del clients[nickname]
        rooms.remove(room_id)

@socketio.on('kick_client')
def kick_client(data):
    room_id = data['roomid']
    nickname = data['nickname']
    if room_id in rooms:
        emit('kickclient', {'nickname': nickname}, broadcast=True)

@socketio.on('mute_client')
def mute_client(data):
    room_id = data['roomid']
    nickname = data['nickname']
    if room_id in rooms:
        emit('muteclient', {'nickname': nickname}, broadcast=True)

@socketio.on('un_mute_client')
def un_mute_client(data):
    room_id = data['roomid']
    nickname = data['nickname']
    if room_id in rooms:
        emit('unmuteclient', {'nickname': nickname}, broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    emit('receive_message', data, broadcast=True)  # Broadcast to all clients, including the host


@socketio.on('connect')
def handle_connect():
    nickname = request.args.get('nickname')
    print(clients)
    if nickname:
        emit('room_client_list', clients, broadcast=True)
        emit('feedback', {'message': f"{nickname} has connected."}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    # Get the nickname from the request
    nickname = request.args.get('nickname')
    if nickname in clients:
        del clients[nickname]
        emit('room_client_list', clients, broadcast=True)
        print(clients)
        emit('feedback', {'message': f"{nickname} has disconnected."}, broadcast=True)
        
@app.before_request
def before_request():
   app.logger.info(f"Incoming request: {request.method} {request.url} Headers: {request.headers}")
   if request.headers.get('X-Forwarded-Proto') != 'https':
       return redirect(request.url.replace('http://', 'https://', 1))
       
if __name__ == '__main__':
    socketio.run(app)
