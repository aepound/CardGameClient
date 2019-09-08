
from flask import Flask, render_template, redirect, url_for, send_from_directory, session
from flask_socketio  import SocketIO, join_room, leave_room, send, emit
from objects.Room import Room

import random
import string

app = Flask(__name__, static_url_path = '', static_folder='../public', template_folder='../public')
socketio = SocketIO(app)
rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    # if 'room_id' not in session:
    #     return redirect(url_for('index'))
    return render_template('game.html')

@app.route('/game/<string:room_id>')
def render_room(room_id):
    on_join(room_id)
    return redirect(url_for('game'))

def generate_room_id():
    """ Generate ID for room """
    id_length = 6
    while True:
        id_tmp = ''.join(random.SystemRandom().choice(string.ascii_uppercase) for _ in range(id_length))
        conflict = id_tmp in rooms.keys()
        if not conflict:
            return id_tmp

@socketio.on('generate_user_id')
def generate_user_id():
    emit('generate_user_id',{'data': generate_room_id()})

@socketio.on('create')
def on_create(data):
    ''' Creates game lobby '''
    game_id = generate_room_id()
    room = Room(room_id=game_id, settings=data['settings'])
    rooms[game_id] = room
    join_room(game_id)
    emit('join_room', {'room' : room})

@socketio.on('createExtra')
def on_createExtra(data):
    ''' Creates game lobby '''
    game_id = 'A'
    if game_id not in rooms:
        room = Room(room_id=game_id)
        rooms[game_id] = room
        on_join({'room': game_id})

@socketio.on('join_room')
def on_join(data):
    room_id = data['room']
    if 'room_id' in session and room_id == session['room_id']:
        pass
    elif room_id in rooms:
        join_room(room_id)
        session['room_id'] = room_id
    else:
        emit('error', {'error' : f'Room {room_id} passed does not exist'})

def get_room(session):
    return rooms[session['room_id']]

# Stuff with the commands

@socketio.on('cursor')
def cursor_move(msg):
    # TODO: implement each player's cursor, then do a broadcast that tells everyone the cursor position
    room = get_room(session)

@socketio.on('card_move')
def card_move(msg):
    room = get_room(session)
    card = room.get_card(msg['cardName'])
    card.set_position(msg['newX'], msg['newY'])
    room.update_card(card)
    # broadcast new position to all
    emit('card_move',msg,broadcast=True)

@socketio.on('transfer')
def transfer(msg):
    room = get_room(session)
    card = room.get_card(msg['cardName'])
    card.set_owner(msg['newOwner'])
    room.update_card(card)
    # broadcast this information
    emit('transfer',msg,broadcast=True)

@socketio.on('card_front')
def on_card_front(msg):
    ''' Brings card to front '''
    emit('card_front', msg, broadcast = True)

@socketio.on('card_flip')
def on_card_flip(msg):
    ''' Flips card '''
    card_id = msg['cardName']
    room = get_room(session)
    room.card_list[card_id].flip()
    emit('card_flip', msg, broadcast = True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
