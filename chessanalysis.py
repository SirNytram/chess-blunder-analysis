import pyperclip
import os

clipboard = pyperclip.paste()
f = open('game.pgn', 'w')
f.write(clipboard)
f.close()

#.\pgn-extract.exe --quiet -C --fencomments -w 100000 --output game-fen.pgn game.pgn
os.system('.\\pgn-extract.exe --quiet -C --fencomments -w 100000 --output game-fen.pgn game.pgn')
from stockfish import Stockfish
stockfish = Stockfish('stockfish_15_x64_avx2.exe') #path="/Users/zhelyabuzhsky/Work/stockfish/stockfish-9-64")
# stockfish.set_fen_position("rnbqkb1r/ppp2ppp/3p4/4P3/4n3/5N2/PPP2PPP/RNBQKB1R w KQkq - 0 5")
# print(stockfish.get_top_moves(3))
 
 
import chess
import chess.pgn


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

        stockfish.set_fen_position(fen)
        score = stockfish.get_evaluation()
        square = f'{node.move}'[2:4]
        piece = f'{node.board().piece_at(chess.parse_square(square))}'.upper()
        top_moves = [] #stockfish.get_top_moves(5)

        movenostr = f'{moveno: >2.0f}'
        is_white = True
        if moveno % 1 != 0:
            movenostr = '  '
            is_white = False

        score_diff = 0
        if prev_score:
            score_diff = score['value'] - prev_score['value']

        
        highlight_suf = f'({score_diff/100:+.1f})'.replace('+', ' ')
        if (is_white and score_diff < -450) or (not is_white and score_diff > 450):
                highlight= f'BLUNDER'
        elif abs(score_diff) >= 150:
                highlight= f'  ***  '
        elif abs(score_diff) >= 100:
                highlight= f'   *   '
        else:
                highlight= f'       ' 
                #highlight_suf = ''



        if score['type'] == 'cp':
            scorestr = f'{score["value"]/100:+.1f}'.replace('+', ' ')
        else:
            scorestr = f'M{score["value"]}'

        if prev_fen:
            if abs(score_diff) >= 450:
                stockfish.set_fen_position(prev_fen)
                top_moves = stockfish.get_top_moves(3)

        topstr = ''
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


        notfound = ' '
        if topstr.find(f'{piece}{square}') == -1 and topstr != '':
            notfound = '*'


        print(f'{highlight} {movenostr}  ({scorestr})  {piece}{square}{notfound}            {topstr} {highlight_suf}')

        moveno+=0.5
        node_prev = node
        prev_score = score
        prev_fen = fen
        prev_board = node.board()
        # print(stockfish.get_top_moves(3))
        # print(stockfish.get_best_move())

