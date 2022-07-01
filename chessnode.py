from typing import List
import io
import chess
import chess.pgn
import chess.engine
import chess.svg
import urllib.request
import json




def convert_san(san, is_white=True):
    pieces = ['♚','♛','♝','♞','♟','♜']
    if is_white :
        pieces = ['♔','♕','♗','♘','♙','♖']

    if san[0].upper() == 'K':
        san = pieces[0] + san[1:]
    if san[0].upper() == 'Q':
        san = pieces[1] + san[1:]
    if san[0].upper() == 'B':
        san = pieces[2] + san[1:]
    if san[0].upper() == 'N':
        san = pieces[3] + san[1:]
    if san[0].upper() == 'R':
        san = pieces[5] + san[1:]

    return san


class ChessNode():
    def __init__(self, move_no, node, analysis, prev_chessnode):
        self.move_no = move_no
        self.node:chess.pgn.ChildNode = node
        self.analysis = analysis
        self.prev_chessnode = prev_chessnode

        self.is_white = True
        if self.move_no % 1 != 0:
            self.is_white = False

    def get_san(self, no=-1, formatted=False):
        board = self.node.board()
        if no == -1:
            # print(f'san for node before pop {board.fen()}')
            board.pop()
            # print(f'after  pop {board.fen()}')
            # print(f'move: {self.node.move}')
            if formatted:
                return convert_san(board.san(self.node.move), self.is_white)
            else:
                return board.san(self.node.move)
        else:
            # board.pop()
            # print(f' san for child line get {board.fen()}')
            move = self.analysis[no]['pv'][0]
            # print(f'move: {move}')
            if formatted:
                return convert_san(board.san(move), not self.is_white)
            else:
                return board.san(move)
    

    def get_suggestions(self, formatted=False):
        suggestions = []
        if self.prev_chessnode:
            for i, analysis in enumerate(self.prev_chessnode.analysis):

                # save images
                arrowcolor = '#00FF00'   #green
                if i == 1:
                    arrowcolor = '#32CD32'   # darker green
                elif i == 2:
                    arrowcolor = '#FFFF00'   # yellow
                elif i == 3:
                    arrowcolor = '#FFA500'   # orange

                suggestions.append({
                    'san':self.prev_chessnode.get_san(i, formatted),
                    'score_int':self.prev_chessnode.get_score_int(i),
                    'score_str':self.prev_chessnode.get_score_str(i),
                    'score_diff':self.prev_chessnode.get_score_diff(i),
                    'score_graph':self.prev_chessnode.get_score_graph(i),
                    'from_square':analysis['pv'][0].from_square,
                    'to_square':analysis['pv'][0].to_square,
                    'arrow_color':arrowcolor,
                })

        return suggestions

    def get_score_int(self, no=-1):
        score = 0
        if no == -1 :
            score = self.get_score_int(0)
        else:
            score = self.analysis[no]['score']
            if score.is_mate():
                score = score.pov(chess.WHITE).score(mate_score = 100000)
            else:
                score = score.pov(chess.WHITE).score()
        return score

    def get_score_diff(self, no=-1):
        score = None
        if no == -1 :
            if self.prev_chessnode:
                prev_score = self.prev_chessnode.get_score_str(0)
                score = self.get_score_str(0)

                if score[0] == 'M':
                    return score
                else:
                    if prev_score[0] == 'M':
                        return score
                    else:
                        score = float(score)
                        prev_score = float(prev_score)
                        score = f'{score - prev_score:.1f}'
            else:
                score = self.get_score_str(-1)            

        else:
            # prev_score = self.get_score_str(0) #self.prev_chessnode.get_score_str(no)
            prev_score = '0.0'
            if self.prev_chessnode:
                prev_score = self.prev_chessnode.get_score_str(-1)

            score = self.get_score_str(no)

            if score[0] == 'M':
                return score
            else:
                if prev_score[0] == 'M':
                    return score
                else:
                    score = float(score)
                    prev_score = float(prev_score)
                    score = f'{score - prev_score:.1f}'
   
        return score

    def get_score_str(self, no=-1):
        score = None
        if no == -1 :
            score = self.get_score_str(0)
        else:
            score = self.analysis[no]['score']
            if score.is_mate():
                score = f'M{score.pov(chess.WHITE).mate()}'
            else:
                score = f'{score.pov(chess.WHITE).score()/100:.1f}'

        return score

    def get_score_graph(self, no=-1):

        score = None
        if no == -1 :
            return self.get_score_graph(0)
        else:
            score = self.analysis[no]['score']
            mult = 1
            if score.pov(chess.WHITE).score(mate_score = 100000) < 0:
                # print('mult is -1')
                mult = -1

            if score.is_mate():
                mate_in = abs(score.pov(chess.WHITE).mate())
                if mate_in > 9:
                    mate_in = 9
                score = 11 - (mate_in / 10)
            else:
                score = abs(score.pov(chess.WHITE).score()/100)
                if score > 10:
                    score = 10


            score = f'{mult * score:.1f}'
        return score


class ChessGame():
    def __init__(self, user, month_index:int, game_index:int):
        self.engine = chess.engine.SimpleEngine.popen_uci("stockfish_15_x64_avx2.exe")
        self.nodes: List[ChessNode] = []
        self.user=user
        self.month_index = month_index
        self.game_index = game_index
        print('loading game from chess.com')
        archives_url = f'https://api.chess.com/pub/player/{user}/games/archives'
        archives_json =  json.loads(urllib.request.urlopen(archives_url).read())
        month_url = archives_json['archives'][::-1][month_index]
        month_json = json.loads(urllib.request.urlopen(month_url).read())
        self.chessdotcom_game = month_json['games'][::-1][game_index]

        self.game = chess.pgn.read_game(io.StringIO(self.chessdotcom_game['pgn']))
        
    def __del__(self):
        self.engine.quit()


    def analyse(self, think_time=None, think_depth=None, min=0, max=999999):
        print(f'Analysing time:{think_time} depth:{think_depth}...')
        self.nodes.clear() #:List[node] = []
        prev_chessnode  = None
        moves = self.game.mainline_moves()
        mainline = self.game.mainline()
        for i,node in enumerate(self.game.mainline()):
            move_no= (i+2)/2


            # info = engine.analyse(node.board(), chess.engine.Limit(depth=14), multipv=3, info=chess.engine.INFO_ALL)
            info = None
            if i >= min and i < max:
                if think_depth:
                    info = self.engine.analyse(node.board(), chess.engine.Limit(depth=think_depth), multipv=4, info=chess.engine.INFO_ALL)
                elif think_time:
                    info = self.engine.analyse(node.board(), chess.engine.Limit(time=think_time), multipv=4, info=chess.engine.INFO_ALL)
                else:
                    info = self.engine.analyse(node.board(), chess.engine.Limit(time=0.01), multipv=4, info=chess.engine.INFO_ALL)
                    
                chessnode = ChessNode(move_no, node, info, prev_chessnode)
                self.nodes.append(chessnode)

                prev_chessnode = chessnode
        print('done')