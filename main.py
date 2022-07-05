#TODO view history of seacch
#TODO use database to full analyse board after view
#TODO differenciate suggestions quality
#TODO show lines somewhere
#TODO improve html to have chess board always shown (put comment under move, remove top moves text)
import threading
import sys
from calendar import month
from concurrent.futures import process
from flask import Flask, request, render_template, redirect, url_for, session
# import pyperclip
import os, signal, json, io, tempfile, pathlib, subprocess
import chess
from chess import pgn, engine, svg
import time
import urllib
from chessnode import ChessGame, ChessNode
from datetime import datetime, timedelta


DEFAULT_THINK_TIME_VIEW = 0.01
DEFAULT_THINK_TIME_ANALYSE = 0.1
DEFAULT_THINK_DEPTH = 18
LOG_FILE = 'static/chess-analysis.log'
   

app = Flask(__name__)
app.secret_key = 'mart is great'


def add_log(message):
    timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
    f = open(LOG_FILE, 'a')
    line = f'{request.remote_addr} {timestamp} {message}\n'
    f.write(line)
    f.close()

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=730)
    session.modified = True
    


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        username = request.form['username'].strip()
        session['username'] = username
        action = request.form['action']

        add_log(f'root POST action:{action} username:{username}')

        if action == 'games':
            return redirect(f'/games/{username}')
            # return view_games(username )
        elif action == 'last_game':
            return redirect(f'/game/{username}' )
        else:
            return redirect('/')

    else:
        username = ''
        if 'username' in session:
            username = session['username']

        add_log(f'root GET username:{username}')
        return render_template('index.html', user=username, message='')


def shutdown_app():
    time.sleep(1)
    os.kill(os.getpid(), signal.SIGINT)

@app.route("/gitupdate")
def gitupdate():
    add_log(f'gitupdate')
    # return "Restarting"
    msg = subprocess.getoutput('gitupdate.bat')
    threading.Thread(target=shutdown_app).start()

    username = ''
    if 'username' in session:
        username = session['username']

    return render_template('index.html', user=username, message=msg)

@app.route("/viewlog")
def viewlog():
    add_log(f'viewlog')


    msg = ''
    f = open(LOG_FILE)
    for line in f.readlines()[-100:]:
        msg += line 
    f.close()

    username = ''
    if 'username' in session:
        username = session['username']

    return render_template('index.html', user=username, message=msg)





@app.route('/game/<user>')
@app.route('/game/<user>/<month_index>/<game_index>/<action>')
def analyse_game(user, month_index=0, game_index=0, action='view'):
    start_time = time.time() #datetime.now()
    print(f'Preparing data. {datetime.now()}')

    if 'uuid' not in session:
        os.makedirs('static/boards', exist_ok=True)
        path = pathlib.Path(tempfile.mkdtemp(dir='static/boards'))
        session['uuid'] = path.name
            
    cur_uuid = session['uuid']

    add_log(f'game action: user:{user}, month_index:{month_index}, game_index:{game_index}, action:{action} uuid:{cur_uuid}')


    path = f'static/boards/{cur_uuid}/'
    for f in os.listdir(path):
        curfile = f'{path}{f}'
        if os.path.isfile(curfile):
            os.remove(curfile)

    month_index = int(month_index)
    game_index = int(game_index)
    game = ChessGame(user, month_index, game_index)
    think_time = DEFAULT_THINK_TIME_VIEW
    think_depth = None
    if action == 'analyse':
        think_time = DEFAULT_THINK_TIME_ANALYSE
        # think_depth = DEFAULT_THINK_DEPTH

    game.analyse(think_time= think_time, think_depth=think_depth)
    print(f'Preparing data. {datetime.now()}')
    game_id = f'{month_index}/{game_index}'
    graph_title = f"{game.chessdotcom_game['white']['username']} ({game.chessdotcom_game['white']['rating']}) - {game.chessdotcom_game['white']['result']} vs {game.chessdotcom_game['black']['username']} ({game.chessdotcom_game['black']['rating']}) - {game.chessdotcom_game['black']['result']}" 
    
    user_is_white = True
    if game.chessdotcom_game['black']['username'] == user:
        user_is_white = False
    
    moves = []
    for node in game.nodes:
        top_moves = []
        img_arrows = []

        user_move = node.get_san(-1, True)
        for suggestion in node.get_suggestions(True):
            # line = f"{line}    {suggestion['san']} {suggestion['score_str']} ({suggestion['score_diff']})"

            cur_sug_move = suggestion['san']
            cell_color = ''
            if user_move == cur_sug_move:
                cell_color = 'table-primary'

            top_moves.append({
                'move': cur_sug_move,
                'score':suggestion['score_str'],
                'score_diff':suggestion['score_diff'],
                'cell_color':cell_color,
            })

            img_arrows.append(chess.svg.Arrow(suggestion['from_square'], suggestion['to_square'], color = suggestion['arrow_color']))
         
        move_no_formatted = f'{node.move_no:.0f}'
        if node.move_no % 1 != 0:
            move_no_formatted = ''

        comment = ''
        comment_color = ''
        mult = 1
        if not node.is_white:
            mult = -1
        score_diff = node.get_score_diff()
        if score_diff[0] != 'M':
            score_diff = float(score_diff) * mult

            if score_diff < -4.50:
                    comment= f'Blunder'
                    comment_color = 'table-danger'
            elif score_diff < -1.40:
                    comment= f'Mistake'
            elif score_diff < -0.80:
                    comment= f'??'
        else:
            comment = 'MATE'


        move_id = int(node.move_no * 10)

        if node.prev_chessnode:
            img_arrows.append(chess.svg.Arrow(node.node.move.from_square, node.node.move.to_square, color = '#FF0000'))
            board_img = chess.svg.board(node.prev_chessnode.node.board(), arrows= img_arrows, size=350, flipped=not user_is_white)
            f = open(f'static\\boards\\{cur_uuid}\\top-{int(move_id)}.svg', 'w')
            f.write(board_img)
            f.close()

            board_img = chess.svg.board(node.prev_chessnode.node.board(), arrows= [chess.svg.Arrow(node.node.move.from_square, node.node.move.to_square, color = '#0000FF')], size=350, flipped=not user_is_white)
            f = open(f'static\\boards\\{cur_uuid}\\move-{int(move_id)}.svg', 'w')
            f.write(board_img)
            f.close()

        graph_move_no = f'{int(node.move_no)}'
        if not node.is_white:
            graph_move_no = f'..{int(node.move_no)}'
        moves.append({
                'move_id':move_id,
                'graph_no': graph_move_no, # node.move_no,
                'graph_score':node.get_score_graph(),
                'no':move_no_formatted,
                'move':node.get_san(-1, True),
                'score_diff': node.get_score_diff(),
                'score':node.get_score_str(),
                'comment': comment,
                'comment_color': comment_color,
                'top_moves':top_moves,
                'is_white': node.is_white,
        })

    
    render_time=F'{time.time() - start_time:.1f}'
    print(f'Render time: {render_time} ')
    return render_template('analyse.html', user=user, game_id=game_id, graph_title=graph_title, moves=moves, render_time=render_time, uuid=cur_uuid)



@app.route('/games/<user>')
@app.route('/games/<user>/<month_index>')
def view_games(user, month_index=0):
    add_log(f'games history user:{user} month_index:{month_index}')

    month_index = int(month_index)
    games = []
    months = []

    archives_url = f'https://api.chess.com/pub/player/{user}/games/archives'
    archives_json =  json.loads(urllib.request.urlopen(archives_url).read())

    month_url = archives_json['archives'][::-1][month_index]
    month_url_splitted = month_url.split('/')
    title_month = f'{month_url_splitted[-2]}-{month_url_splitted[-1]}'
    for i, cur_month in enumerate(archives_json['archives'][::-1]):
        if cur_month != month_url:
            cur_month_splitted = cur_month.split('/')
            months.append({
                'month': f'{cur_month_splitted[-2]}-{cur_month_splitted[-1]}',
                'month_index': i
            })
    month_json = json.loads(urllib.request.urlopen(month_url).read())
    for i, cur_game in enumerate(month_json['games'][::-1]):

        user_color = 'white'
        if cur_game['black']['username'] == user:
            user_color = 'black'

        color = 'table-danger'
        if cur_game[user_color]['result'] == 'win':
            color = 'table-success'

        game_moves = 0.0
        for move in chess.pgn.read_game(io.StringIO(cur_game['pgn'])).mainline_moves():
            game_moves += 1


        if 'end_time' in cur_game:
            game_date = datetime.fromtimestamp(cur_game['end_time']).strftime("%m/%d<br>%H:%M")
        else:
            game_date = ''

        games.append({
            'color': color,
            'players': f"{cur_game['white']['username']} ({cur_game['white']['rating']}) - {cur_game['white']['result']}<br>{cur_game['black']['username']} ({cur_game['black']['rating']}) - {cur_game['black']['result']}",
            'result': f"{cur_game[user_color]['result']}",
            'moves': f"{round((game_moves + .1)/2.0)}",
            'date': game_date,
            'game_id':f'{month_index}/{i}',
        })
    


    return render_template('games.html', user=user, title_month=title_month, games=games, months=months)

if __name__ == '__main__':
    if 'debug' in sys.argv:
        app.run(debug=True, host='0.0.0.0', port=5080)
    else:
        app.run(debug=False, host='0.0.0.0', port=5080)
