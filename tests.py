import chessnode
import time
from datetime import datetime

def _timestamp(prec=0):
    t = time.time()
    s = time.strftime("%H:%M:%S", time.localtime(t))
    if prec > 0:
        s += ("%.9f" % (t % 1,))[1:2+prec]
    return s

if __name__ == '__main__':
    
    t = datetime.utcnow()
    print(t)
    print(_timestamp(3))

    game = chessnode.ChessGame('MartyMcShorty', 0, 9)
    game.analyse(0.01)
    for node in game.nodes:
        # if node.is_white and node.get_Score_diff
        # line = f"no: {node.move_no} move :{node.get_san(-1, True)} {node.get_score_str()} ({node.get_score_diff()})      G:{node.get_score_graph()}           " 
        line = f"no: {node.move_no} move :{node.get_san(-1, True)} {node.get_score_str()} ({node.get_score_diff()})                 " 
        for suggestion in node.get_suggestions(True):
            line = f"{line}    {suggestion['san']} {suggestion['score_str']} ({suggestion['score_diff']})"

        print(line)

    print(datetime.utcnow() - t)

    