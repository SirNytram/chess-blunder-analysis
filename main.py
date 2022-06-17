from flask import Flask, request, render_template
# import pyperclip
import os
from stockfish import Stockfish
import chess
import chess.pgn
import chess.engine
import time
engine = chess.engine.SimpleEngine.popen_uci("stockfish_15_x64_avx2.exe")



VALUE_MATE = 3200



def mate_to_value(mate: int) -> int:
    """
    Convert mate number to value.
    """
    if mate > 0:
        v = VALUE_MATE - 2*mate + 1
    else:
        v = -VALUE_MATE - 2*mate

    return v


def my_get_evaluation(fish: Stockfish, fen: str, timems: int):
    """
    Evaluate the fen with fish at a given timems.
    Returns a dict of score {'cp': '49', 'mate': None} and move.
    """
    score = {}
    bestmove = '0000'

    fish.set_fen_position(fen)
    res = fish.get_best_move_time(timems)

    search_info = fish.info
    try:
        bestmove = search_info.split(' pv ')[1].split()[0]

        if 'score cp ' in search_info:
            score_cp = search_info.split('score cp ')[1].split()[0]
            score.update({'cp': int(score_cp), 'mate': None})
        elif 'score mate ' in search_info:
            score_mate = search_info.split('score mate ')[1].split()[0]
            score_cp = mate_to_value(int(score_mate))
            score.update({'cp': int(score_cp), 'mate': int(score_mate)})
    except:
        print('error splitting')
        score.update({'cp': int(0), 'mate': None})

    return score, bestmove

def current_milli_time():
    return round(time.time() * 1000)


app = Flask(__name__)

@app.route('/')
def my_form():
    return render_template('index.html', moves=[], pgn='', think_time=0.01)

@app.route("/gitupdate")
def gitupdate():
    os.system('gitupdate.bat')
    # return redirect(url_for('searchimdb'))
    return render_template('index.html', moves=[], pgn='', think_time=0.01)

@app.route('/', methods=['POST'])
def my_form_post():
    pgn = request.form['pgn']
    moves = []

    detailed = request.form.get('detailed')

    think_time = request.form.get('think_time')

    output = ''
    start_time = current_milli_time()

    if pgn != '':
        # clipboard = pyperclip.paste()
        f = open('game.pgn', 'w')
        f.write(pgn)
        f.close()

        #.\pgn-extract.exe --quiet -C --fencomments -w 100000 --output game-fen.pgn game.pgn
        os.system('.\\pgn-extract.exe --quiet -C --fencomments -w 100000 --output game-fen.pgn game.pgn')
        stockfish = Stockfish('stockfish_15_x64_avx2.exe') #path="/Users/zhelyabuzhsky/Work/stockfish/stockfish-9-64")
        # stockfish.set_fen_position("rnbqkb1r/ppp2ppp/3p4/4P3/4n3/5N2/PPP2PPP/RNBQKB1R w KQkq - 0 5")
        # print(stockfish.get_top_moves(3))
        # print(stockfish.get_parameters())
        # stockfish.set_elo_rating(500)
        


        fn = 'game-fen.pgn'

        with open(fn, encoding='utf-8') as h:
            game = chess.pgn.read_game(h)

            topstr = ''
            prev_score = None
            prev_fen = None
            moveno = 1.0

            
            for node in game.mainline():
                fen = node.comment
                # com = comment.split('\n')
                # fen = ''
                # val = com[0]
                # if len(com) > 1:
                #     fen = com[1]

                # score, bm = my_get_evaluation(stockfish, fen, 10)

                info = engine.analyse(node.board(), chess.engine.Limit(time=float(think_time)))
                score = info['score']
                


                # stockfish.set_fen_position(fen)
                # stockfish.get_best_move_time(100)
                # score = stockfish.get_evaluation()
                # print(stockfish.info)

                square = f'{node.move}'[2:4]
                piece = f'{node.board().piece_at(chess.parse_square(square))}'.upper()
                top_moves = [] #stockfish.get_top_moves(5)

                movenostr = f'{moveno: >2.0f}'
                is_white = True
                if moveno % 1 != 0:
                    movenostr = '  '
                    is_white = False

                score_diff = 0
                if not score.is_mate() and prev_score and not prev_score.is_mate():
                    score_diff = score.pov(chess.WHITE).score() - prev_score.pov(chess.WHITE).score()

                
                highlight_suf = f'{score_diff/100:+.1f}'.replace('+', ' ')
                if (is_white and score_diff < -450) or (not is_white and score_diff > 450):
                        highlight= f'BLUNDER'
                elif abs(score_diff) >= 150:
                        highlight= f'  ***  '
                elif abs(score_diff) >= 100:
                        highlight= f'   *   '
                else:
                        highlight= f'       ' 
                        #highlight_suf = ''


                if score.is_mate():
                    scorestr = f'M{score.pov(chess.WHITE).mate()}'
                    scoregraph = score.pov(chess.WHITE).score(mate_score = 30)
                    # if is_white:
                    #     scoregraph = 30 - score.relative.moves
                    # else:
                    #     scoregraph = -30 - score.relative.moves
                else:
                    scorestr = f'{score.pov(chess.WHITE).score()/100:+.1f}'.replace('+', ' ')
                    scoregraph = scorestr
                # if score['type'] == 'cp':
                #     scorestr = f'{score["value"]/100:+.1f}'.replace('+', ' ')
                #     scoregraph = f'{score["value"]/100:.1f}'
                # else:
                #     scorestr = f'M{score["value"]}'
                #     if score["value"] == 0:
                #         if is_white:
                #             scoregraph = 30
                #         else:
                #             scoregraph = -30

                #     elif score["value"] > 0:
                #         scoregraph = f'{30 - (score["value"])}'
                #     else:
                #         scoregraph = f'{-30 + (score["value"] * -1)}'

                if prev_fen and detailed:
                    if abs(score_diff) >= 450:
                        stockfish.set_fen_position(prev_fen)
                        top_moves = stockfish.get_top_moves(3)

                topstr = ''
                top_moves_str = []
                for cur_top_move in top_moves:
                    top_square1_src = f'{cur_top_move["Move"]}'[0:2]
                    top_piece1 = f'{prev_board.piece_at(chess.parse_square(top_square1_src))}'.upper()
                    top_square1 = f'{cur_top_move["Move"]}'[2:4]
                    top_centipawn1 = cur_top_move['Centipawn']
                    if top_centipawn1:
                        top_centipawn1 = f'{top_centipawn1/100:+.1f}'.replace('+', ' ')
                    if not top_centipawn1:
                        top_centipawn1 = ''

                    top_mate = ''
                    if cur_top_move['Mate']:
                        top_mate = f'M{cur_top_move["Mate"]}'

                    topstr = f'{topstr} {top_piece1}{top_square1} ({top_centipawn1}{top_mate})    '
                    top_moves_str.append([top_piece1, top_square1, top_centipawn1, top_mate])

                if len(top_moves_str) == 0:
                    top_moves_str = ['','','']

                notfound = ' '
                if topstr.find(f'{piece}{square}') == -1 and topstr != '':
                    notfound = '*'

                line = f'{highlight} {movenostr}  ({scorestr})  {piece}{square}{notfound}            {topstr} {highlight_suf} '
                output += f'{line}<br>\n'
                moves.append([highlight, movenostr, scorestr, piece, square, top_moves_str, highlight_suf, scoregraph])
                print(line)

                moveno+=0.5
                node_prev = node
                prev_score = score
                prev_fen = fen
                prev_board = node.board()
                # print(stockfish.get_top_moves(3))
                # print(stockfish.get_best_move())
    # return output

    return render_template('index.html', moves=moves,pgn=pgn, time=current_milli_time()-start_time, think_time=think_time)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5080)