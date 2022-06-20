from calendar import month
from flask import Flask, request, render_template, redirect, url_for
# import pyperclip
import os
from stockfish import Stockfish
import chess
import chess.pgn
import chess.engine
import chess.svg
import time
import urllib
import json

# import pyvips
# from svglib.svglib import svg2rlg
# from reportlab.graphics import renderPM
from chessapi import get_game_bydate, get_game_byindex

engine = chess.engine.SimpleEngine.popen_uci("stockfish_15_x64_avx2.exe")
stockfish = Stockfish('stockfish_15_x64_avx2.exe', parameters= {'Threads':4, 'Hash': 2048}) #path="/Users/zhelyabuzhsky/Work/stockfish/stockfish-9-64")


DEFAULT_THINK_TIME = 0.01
DEFAULT_THINK_TIME_BEST_MOVE = 0.1
def current_milli_time():
    return round(time.time() * 1000)

app = Flask(__name__)
# @app.route('/boardimg')
# def boardimg():
#     return 

@app.route('/')
def index():
    return render_template('index.html', moves=[], pgn='', think_time=DEFAULT_THINK_TIME, detailed_ret='')

@app.route("/gitupdate")
def gitupdate():
    os.system('gitupdate.bat')
    return redirect(url_for('index'))



def convert_piece(piece, is_white):
    pieces = ['♚','♛','♝','♞','♟','♜']
    if is_white :
        pieces = ['♔','♕','♗','♘','♙','♖']

    if piece.upper() == 'P':
        piece = ''

    if piece.upper() == 'K':
        piece = pieces[0]
    if piece.upper() == 'Q':
        piece = pieces[1]
    if piece.upper() == 'B':
        piece = pieces[2]
    if piece.upper() == 'N':
        piece = pieces[3]
    if piece.upper() == 'R':
        piece = pieces[5]

    return piece

@app.route('/analyse/<user>')
@app.route('/analyse/<user>/<month_index>/<game_index>/<action>')
def analyse(user, month_index=0, game_index=0, action='view'):
    month_index = int(month_index)
    game_index = int(game_index)
    archives_url = f'https://api.chess.com/pub/player/{user}/games/archives'
    archives_json =  json.loads(urllib.request.urlopen(archives_url).read())
    month_url = archives_json['archives'][::-1][month_index]
    month_json = json.loads(urllib.request.urlopen(month_url).read())
    chessdotcom_game = month_json['games'][::-1][game_index]

    pgn = chessdotcom_game['pgn']
    detailed = False
    if action=='analyse':
        detailed = True
    think_time='0.01'
    # fenpos = pgn.find('[FEN')
    # if fenpos != -1:
    #     fenpos_close = pgn.find(']', fenpos)
    #     pgn = pgn[0:fenpos] + pgn[fenpos_close+1:] + ' * '

    moves = []
    game_id = f'{month_index}/{game_index}'

    start_time = current_milli_time()

    if pgn != '':
        f = open('game.pgn', 'w')
        
        f.write(pgn)
        f.close()

        os.system('.\\pgn-extract.exe -C --fencomments -w 100000 --output game-fen.pgn game.pgn')

        fn = 'game-fen.pgn'
        with open(fn, encoding='utf-8') as h:
            game = chess.pgn.read_game(h)

            topstr = ''
            prev_score = None
            prev_node = None
            moveno = 1.0

            
            for node in game.mainline():
                is_white = True
                movenostr = f'{moveno: >2.0f}'
                if moveno % 1 != 0:
                    movenostr = '  '
                    is_white = False

                
                fen = node.comment
                info = engine.analyse(node.board(), chess.engine.Limit(time=float(think_time)), multipv=None)
                score = info['score']
                
                square = f'{node.move}'[2:4]
                from_file = f'{node.move}'[0:1]
                piece = convert_piece(f'{node.board().piece_at(node.move.to_square)}'.upper(), is_white)
                
                if prev_node and prev_node.board().is_capture(node.move):
                    square = 'x' + square
                    if piece == '':
                        piece = from_file
                
                suffix = ''
                if node.board().is_check():
                    suffix += '+'
                if node.board().is_checkmate():
                    suffix += '#'
                # if node.move.promotion:

                top_moves = [] 


                score_diff = 0
                if not score.is_mate() and prev_score and not prev_score.is_mate():
                    score_diff = score.pov(chess.WHITE).score() - prev_score.pov(chess.WHITE).score()

                
                score_diff_formatted = f'{score_diff/100:.1f}'
                if (is_white and score_diff < -450) or (not is_white and score_diff > 450):
                        comment= f'BLUNDER'
                elif (is_white and score_diff < -140) or (not is_white and score_diff > 140):
                        comment= f'***'
                elif (is_white and score_diff < -80) or (not is_white and score_diff > 80):
                        comment= f'*'
                else:
                        comment= f'' 
                        #highlight_suf = ''


                if score.is_mate():
                    scorestr = f'M{score.pov(chess.WHITE).mate()}'
                    scoregraph = score.pov(chess.WHITE).score(mate_score = 30)
                    comment = 'MATE'
                else:
                    scorestr = f'{score.pov(chess.WHITE).score()/100:.1f}'
                    scoregraph = scorestr

                    
                topstr = ''
                top_moves = []
                img_arrows = []
                

                if prev_node and detailed:
                    if comment in ('***', 'BLUNDER', '*', 'MATE'): #abs(score_diff) >= 140:

                        stockfish.set_fen_position(prev_node.comment)
                        sf_top_moves = stockfish.get_top_moves(3)
                        #top_moves = [ engine.play(prev_node.board(),chess.engine.Limit(depth = 18, time=0.5), info= chess.engine.INFO_SCORE) ]
                        #top_moves = [] engine.play(prev_node.board(),chess.engine.Limit(time=float(DEFAULT_THINK_TIME_BEST_MOVE)), info= chess.engine.INFO_ALL) ]

                        if moveno == 23:
                            pass

                        for index, info_best_move in enumerate(sf_top_moves):
                            top_move = chess.Move(chess.parse_square(info_best_move['Move'][0:2]), chess.parse_square(info_best_move['Move'][2:4]))
                            # move = info_best_move.move
                            top_score = info_best_move['Centipawn']
                            # top_score = move.info['score'].pov(chess.WHITE).score()
                            top_square = f'{top_move}'[2:4]
                            top_from_file = f'{top_move}'[0:1]
                            top_piece = convert_piece(f'{prev_node.board().piece_at(top_move.from_square)}'.upper(), is_white)
                            if top_score != None:
                                top_score = f'{top_score/100:.1f}'
                                top_score_diff = ''
                                if 'M' not in scorestr:
                                    top_score_diff = f'{(float(top_score) - float(scorestr)):.1f}'
                            else:
                                top_score = f"M{info_best_move['Mate']}"
                            # next_board = node.board()
                            # next_board.push(move.move)

                            if prev_node.board().is_capture(top_move):
                                top_square = 'x' + top_square
                                if top_piece == '':
                                    top_piece = top_from_file


                            top_suffix = ''
                            board_next = prev_node.board()
                            # print(f'pushing {move.move}')
                            board_next.push(top_move) 
                            if board_next.is_check():
                                top_suffix += '+'
                            if board_next.is_checkmate():
                                top_suffix += '#'

                            if index == 1:
                                arrowcolor = 'blue'
                            elif index == 2:
                                arrowcolor = 'yellow'
                            else:
                                arrowcolor = 'green'

                            img_arrows.append(chess.svg.Arrow(top_move.from_square, top_move.to_square, color = arrowcolor))
                            top_moves.append({
                                'move': f'{top_piece}{top_square}{top_suffix}',
                                'score': f'{top_score}',
                                'score_diff': f'{top_score_diff}',
                            })

                        img_arrows.append(chess.svg.Arrow(node.move.from_square, node.move.to_square, color = 'red'))
                        board_img = chess.svg.board(prev_node.board(), arrows= img_arrows, size=350)
                        f = open(f'static\\board-{int(moveno*10)}.svg', 'w')
                        f.write(board_img)
                        f.close()
                        # image = pyvips.Image.new_from_file("board.svg", dpi=300)
                        # image.write_to_file("x.png")
                        # drawing = svg2rlg("board.svg ")
                        # renderPM.drawToFile(drawing, "board.png", fmt="PNG")

                        
                notfound = ''
                # if topstr.find(f'{piece}{square}') == -1 and topstr != '':
                #     notfound = '*'

                line = f'{comment} {movenostr}  ({scorestr})  {piece}{square}{notfound}            {topstr} {score_diff_formatted} '
 
                move_formatted = f'{piece}{square}{suffix}'
                # movenograph = f'{int(moveno)}{move_formatted}..'
                movenograph = f'{int(moveno)}'
                if moveno % 1 != 0:
                    # movenograph = f'{int(moveno)} ..{move_formatted}'
                    movenograph = ''


                moves.append({
                        'move_id':int(moveno * 10),
                        'graph_no':movenograph,
                        'graph_score':scoregraph,
                        'no':movenostr,
                        'move':f'{move_formatted}',
                        'score_diff': score_diff_formatted,
                        'score':scorestr,
                        'comment':comment,
                        'top_moves':top_moves,
                        # 'top0': top_moves[0]['move'],
                        # 'top1': top_moves[1]['move'],
                        # 'top2': top_moves[2]['move'],
                        # 'top0_score_diff': top_moves[0]['score_diff'],
                        # 'top1_score_diff': top_moves[1]['score_diff'],
                        # 'top2_score_diff': top_moves[2]['score_diff'],
                        # 'move_no_full':int(moveno * 10),
                        # 'move_no':movenostr,
                        # 'move_no_graph': movenograph,
                        # 'score': scorestr,
                        # 'score_graph': scoregraph,
                        # 'move': move_formatted,
                        # 'score_diff': score_diff_formatted,
                        'is_white': is_white,
                        # 'comment': comment,
                        # 'top_moves': top_moves
                    })
                print(line) 


                moveno+=0.5
                node_prev = node
                prev_score = score
                prev_node = node
                
                # print(stockfish.get_top_moves(3))
                # print(stockfish.get_best_move())


    #  render_template('index.html', moves=moves,pgn=pgn, time=f'{(current_milli_time()-start_time)/1000:.1f}', think_time=think_time, detailed_ret=detailed_ret)

    
    graph_title = f"{chessdotcom_game['white']['username']} ({chessdotcom_game['white']['rating']}) vs {chessdotcom_game['black']['username']} ({chessdotcom_game['black']['rating']})"
    return render_template('analyse.html', user=user, game_id=game_id, graph_title=graph_title, moves=moves, render_time=think_time)

@app.route('/games/<user>')
@app.route('/games/<user>/<month_index>')
def games(user, month_index=0):
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

        moves = 0
        
        games.append({
            'color': color,
            'players': f"{cur_game['white']['username']} ({cur_game['white']['rating']})<br>{cur_game['black']['username']} ({cur_game['black']['rating']})",
            'result': f"{cur_game[user_color]['result']}",
            'moves': f"{cur_game['fen'].split()[-1]}",
            'date':'',
            'game_id':f'{month_index}/{i}',
        })
    


    return render_template('games.html', user=user, title_month=title_month, games=games, months=months)

@app.route('/lastgame/<user>')
def analyse_last_game(user):
    return redirect(url_for('analyse_by_index', user=user, month_index=-1, game_index=-1))

    # pgn = get_game_byindex(user, 0, 0)['pgn']
    # return analyse_pgn(pgn)

@app.route('/gamebyindex/<user>/<month_index>/<game_index>')
def analyse_by_index(user, month_index, game_index):
    pgn = get_game_byindex(user, int(month_index), int(game_index))['pgn']
    return analyse_pgn(pgn)



@app.route('/', methods=['POST'])
def root():
    pgn = request.form['pgn']
    detailed = request.form.get('detailed')
    think_time = request.form.get('think_time')
    return analyse_pgn(pgn, detailed, think_time)


def analyse_pgn(pgn, detailed = 'on', think_time='0.01'):
    fenpos = pgn.find('[FEN')
    if fenpos != -1:
        fenpos_close = pgn.find(']', fenpos)
        pgn = pgn[0:fenpos] + pgn[fenpos_close+1:] + ' * '

    moves = []

    output = ''
    start_time = current_milli_time()

    if pgn != '':
        f = open('game.pgn', 'w')
        
        f.write(pgn)
        f.close()

        os.system('.\\pgn-extract.exe -C --fencomments -w 100000 --output game-fen.pgn game.pgn')

        fn = 'game-fen.pgn'
        with open(fn, encoding='utf-8') as h:
            game = chess.pgn.read_game(h)

            topstr = ''
            prev_score = None
            prev_node = None
            moveno = 1.0

            
            for node in game.mainline():
                if moveno == 42.5:
                    pass

                is_white = True
                movenostr = f'{moveno: >2.0f}'
                if moveno % 1 != 0:
                    movenostr = '  '
                    is_white = False

                
                fen = node.comment
                info = engine.analyse(node.board(), chess.engine.Limit(time=float(think_time)), multipv=None)
                score = info['score']
                
                square = f'{node.move}'[2:4]
                from_file = f'{node.move}'[0:1]
                piece = convert_piece(f'{node.board().piece_at(node.move.to_square)}'.upper(), is_white)
                
                if prev_node and prev_node.board().is_capture(node.move):
                    square = 'x' + square
                    if piece == '':
                        piece = from_file
                
                suffix = ''
                if node.board().is_check():
                    suffix += '+'
                if node.board().is_checkmate():
                    suffix += '#'
                # if node.move.promotion:

                top_moves = [] 


                score_diff = 0
                if not score.is_mate() and prev_score and not prev_score.is_mate():
                    score_diff = score.pov(chess.WHITE).score() - prev_score.pov(chess.WHITE).score()

                
                score_diff_formatted = f'{score_diff/100:.1f}'
                if (is_white and score_diff < -450) or (not is_white and score_diff > 450):
                        comment= f'BLUNDER'
                elif (is_white and score_diff < -140) or (not is_white and score_diff > 140):
                        comment= f'***'
                elif (is_white and score_diff < -80) or (not is_white and score_diff > 80):
                        comment= f'*'
                else:
                        comment= f'' 
                        #highlight_suf = ''


                if score.is_mate():
                    scorestr = f'M{score.pov(chess.WHITE).mate()}'
                    scoregraph = score.pov(chess.WHITE).score(mate_score = 30)
                    comment = 'MATE'
                else:
                    scorestr = f'{score.pov(chess.WHITE).score()/100:.1f}'
                    scoregraph = scorestr

                    
                topstr = ''
                top_moves = []
                img_arrows = []
                

                if prev_node and detailed:
                    if comment in ('***', 'BLUNDER', '*', 'MATE'): #abs(score_diff) >= 140:

                        stockfish.set_fen_position(prev_node.comment)
                        sf_top_moves = stockfish.get_top_moves(3)
                        #top_moves = [ engine.play(prev_node.board(),chess.engine.Limit(depth = 18, time=0.5), info= chess.engine.INFO_SCORE) ]
                        #top_moves = [] engine.play(prev_node.board(),chess.engine.Limit(time=float(DEFAULT_THINK_TIME_BEST_MOVE)), info= chess.engine.INFO_ALL) ]

                        if moveno == 23:
                            pass

                        for index, info_best_move in enumerate(sf_top_moves):
                            top_move = chess.Move(chess.parse_square(info_best_move['Move'][0:2]), chess.parse_square(info_best_move['Move'][2:4]))
                            # move = info_best_move.move
                            top_score = info_best_move['Centipawn']
                            # top_score = move.info['score'].pov(chess.WHITE).score()
                            top_square = f'{top_move}'[2:4]
                            top_from_file = f'{top_move}'[0:1]
                            top_piece = convert_piece(f'{prev_node.board().piece_at(top_move.from_square)}'.upper(), is_white)
                            if top_score != None:
                                top_score = f'{top_score/100:.1f}'
                                top_score_diff = ''
                                if 'M' not in scorestr:
                                    top_score_diff = f'{(float(top_score) - float(scorestr)):.1f}'
                            else:
                                top_score = f"M{info_best_move['Mate']}"
                            # next_board = node.board()
                            # next_board.push(move.move)

                            if prev_node.board().is_capture(top_move):
                                top_square = 'x' + top_square
                                if top_piece == '':
                                    top_piece = top_from_file


                            top_suffix = ''
                            board_next = prev_node.board()
                            # print(f'pushing {move.move}')
                            board_next.push(top_move) 
                            if board_next.is_check():
                                top_suffix += '+'
                            if board_next.is_checkmate():
                                top_suffix += '#'

                            if index == 1:
                                arrowcolor = 'blue'
                            elif index == 2:
                                arrowcolor = 'yellow'
                            else:
                                arrowcolor = 'green'

                            img_arrows.append(chess.svg.Arrow(top_move.from_square, top_move.to_square, color = arrowcolor))
                            top_moves.append({
                                'move': f'{top_piece}{top_square}{top_suffix}',
                                'score': f'{top_score}',
                                'score_diff': f'{top_score_diff}',
                            })

                        img_arrows.append(chess.svg.Arrow(node.move.from_square, node.move.to_square, color = 'red'))
                        board_img = chess.svg.board(prev_node.board(), arrows= img_arrows, size=350)
                        f = open(f'static\\board-{int(moveno*10)}.svg', 'w')
                        f.write(board_img)
                        f.close()
                        # image = pyvips.Image.new_from_file("board.svg", dpi=300)
                        # image.write_to_file("x.png")
                        # drawing = svg2rlg("board.svg ")
                        # renderPM.drawToFile(drawing, "board.png", fmt="PNG")

                        


                # while len(top_moves) < 5:
                #     top_moves.append({
                #         'move': '',
                #         'score': ''
                #     })
                    
                notfound = ''
                # if topstr.find(f'{piece}{square}') == -1 and topstr != '':
                #     notfound = '*'

                line = f'{comment} {movenostr}  ({scorestr})  {piece}{square}{notfound}            {topstr} {score_diff_formatted} '
                output += f'{line}<br>\n'
 
                move_formatted = f'{piece}{square}{suffix}'
                # movenograph = f'{int(moveno)}{move_formatted}..'
                movenograph = f'{int(moveno)}'
                if moveno % 1 != 0:
                    # movenograph = f'{int(moveno)} ..{move_formatted}'
                    movenograph = ''

                moves.append(
                    {
                        'move_no_full':int(moveno * 10),
                        'move_no':movenostr,
                        'move_no_graph': movenograph,
                        'score': scorestr,
                        'score_graph': scoregraph,
                        'move': move_formatted,
                        'score_diff': score_diff_formatted,
                        'is_white': is_white,
                        'comment': comment,
                        'top_moves': top_moves
                    }

                )
                print(line) 


                moveno+=0.5
                node_prev = node
                prev_score = score
                prev_node = node
                
                # print(stockfish.get_top_moves(3))
                # print(stockfish.get_best_move())

    detailed_ret = ''
    if detailed:
        detailed_ret = 'checked'

    return render_template('index.html', moves=moves,pgn=pgn, time=f'{(current_milli_time()-start_time)/1000:.1f}', think_time=think_time, detailed_ret=detailed_ret)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5080)