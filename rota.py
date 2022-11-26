# https://www.praetorian.com/challenges/rota/
# hash: 0a0c144ab3f4dd4566e141de01955b72a7fdd299a65e49d681bb78349c39f0cc7b2275736572223a2264617669647268656163726f7740676d61696c2e636f6d222c2274696d657374616d70223a313636393434343836347d

from requests import session
from random import choice

class Rota:

    def __init__(self):

        # initialize stuff for Praetorian's API
        self.email = "davidrheacrow@gmail.com"
        self.url = "https://rota.praetorian.com/rota/service/play.php"
        self.session = session()

        # track game state
        self.resp = None
        self.survived = False
        self.player_wins_saved = 0
        self.computer_wins_saved = 0

        # identify every square's neighboring squares
        self.neighbors = {
            1 : [2, 4, 5],
            2 : [1, 3, 5],
            3 : [2, 5, 6],
            4 : [1, 5, 7],
            5 : [1, 2, 3, 4, 6, 7, 8, 9],
            6 : [3, 5, 9],
            7 : [4, 5, 8],
            8 : [5, 7, 9],
            9 : [5, 6, 8]
        }

    # interface with Praetorian's API

    def startGame(self):
        return self.session.post(f"{self.url}?request=new&email={self.email}").json()

    def nextGame(self):
        return self.session.post(f"{self.url}?request=next").json()

    def placePiece(self, loc):
        return self.session.post(f"{self.url}?request=place&location={loc}").json()

    def movePiece(self, move):
        return self.session.post(f"{self.url}?request=move&from={move[0]}&to={move[1]}").json()

    @property
    def board(self):
        return self.resp["data"]["board"]

    @property
    def player_wins(self):
        return self.resp["data"]["player_wins"]

    @property
    def computer_wins(self):
        return self.resp["data"]["computer_wins"]

    @property
    def moves(self):
        return self.resp["data"]["moves"]

    # pretty-print the board
    def printBoard(self, board):
        print(f"\n\t{board[:3]}\n\t{board[3:6]}\n\t{board[6:]}\n")

    # identify the locations of the given player's pieces
    def getLocations(self, board, player):
        return [i + 1 for i, c in enumerate(board) if player == c]

    # identify all possible locations on which we can place a piece
    def getPlacements(self, board):
        return [(-1, i + 1) for i, cell in enumerate(board) if cell == "-"]

    # gets the number of placed pieces for a given player
    def getPieceCount(self, player):
        return self.board.count(player)

    # identify all possible moves for the given state
    def getMoves(self, board, player):
        old_locs = [i + 1 for i, cell in enumerate(board) if cell == player]
        new_locs = [i + 1 for i, cell in enumerate(board) if cell == "-"]
        return [(ol, nl) for ol in old_locs for nl in new_locs if self.isValidMove(ol, nl)]

    # generate the next board for a given board, player, and action
    def getNextBoard(self, board, player, action):

        # place a piece
        if action[0] == -1:
            return board[: action[1] - 1] + player + board[action[1] :]

        # move a piece
        board = board[: action[0] - 1] + "-" + board[action[0] :]
        return board[: action[1] - 1] + player + board[action[1] :]

    # compute the value for a given board and player
    def getValue(self, board):
        if board.count("p") == 3 and self.doesWin(board, "p"):
            return 1
        elif board.count("c") == 3 and self.doesWin(board, "c"):
            return -1
        return 0

    # identifies the winner (if one exists) for a given board
    def getWinner(self, board):
        if self.doesWin(board, "c"):
            return "c"
        elif self.doesWin(board, "p"):
            return "p"
        return False

    # determine whether a move is valid
    def isValidMove(self, old_loc, new_loc):
        return new_loc in self.neighbors[old_loc]

    # determines whether the given player won for the given state
    def doesWin(self, board, player):

        # check all possible win conditions
        return (all([cell == player for cell in board[0:3]]) or
                all([cell == player for cell in board[3:6]]) or
                all([cell == player for cell in board[6:9]]) or
                all([cell == player for cell in [board[0], board[3], board[6]]]) or
                all([cell == player for cell in [board[1], board[4], board[7]]]) or
                all([cell == player for cell in [board[2], board[5], board[8]]]) or
                all([cell == player for cell in [board[3], board[0], board[1]]]) or
                all([cell == player for cell in [board[1], board[2], board[5]]]) or
                all([cell == player for cell in [board[3], board[6], board[7]]]) or
                all([cell == player for cell in [board[7], board[8], board[5]]]) or
                all([cell == player for cell in [board[0], board[4], board[8]]]) or
                all([cell == player for cell in [board[2], board[4], board[6]]]))

    # determine whether we should move again
    def isGameOver(self):

        # if we've survived long enough to go to the next game
        if self.moves >= 30:
            self.survived = True
            return True

        # if the player won the current game
        elif self.player_wins > self.player_wins_saved:
            self.player_wins_saved += 1
            return True

        # if the computer won the current game
        elif self.computer_wins > self.computer_wins_saved:
            self.computer_wins_saved += 1
            return True

        # move again!
        return False

    # pick the best possible location on which we can place a piece
    def selectPlacement(self, counts):

        # if the computer has one piece, place a piece on the outer circle and adjacent to the piece
        if counts[1] == 1:
            loc = self.board.index("c") + 1

            for neighbor in self.neighbors[loc]:
                if neighbor != 5 and self.board[neighbor - 1] == "-":
                    return neighbor

        # otherwise, first piece can go anywhere
        if counts[0] == 0:
            return choice(self.getPlacements(self.board))[1]

        # finally, search for the best remaining placements
        best_placement = None
        best_value = -10

        # identify the best of the available placements for this state
        for placement in self.getPlacements(self.board):
            next_board = self.getNextBoard(self.board, "p", placement)

            # don't actually make winning placements
            if not self.doesWin(next_board, "p"):

                # use the minimax search algorithm to determine a placement's value
                value = self.minimax(next_board, player="c", action_type="placing", counts=(counts[0] + 1, counts[1]), depth=5, alpha=-100, beta=100)

                # update best placement as necessary
                if value > best_value:
                    best_value = value
                    best_placement = placement

        return best_placement[1]

    # pick the best possible move we can make
    def selectMove(self):
        best_move = None
        best_value = -10

        # identify the best of the available move for this state
        for move in self.getMoves(self.board, "p"):
            next_board = self.getNextBoard(self.board, "p", move)

            # don't actually make winning moves
            if not self.doesWin(next_board, "p"):

                # use the minimax search algorithm to determine a move's value
                value = self.minimax(next_board, player="c", action_type="moving", counts=(3, 3), depth=5, alpha=-100, beta=100)

                # update best move as necessary
                if value > best_value:
                    best_value = value
                    best_move = move

        return best_move

    # pick the best available action
    def minimax(self, board, player, action_type, counts, depth, alpha, beta):

        # check for end of search
        if self.getWinner(board) or depth == 0:
            return self.getValue(board)

        # if we're done placing pieces, start moving them
        if action_type == "placing" and counts == (3, 3):
            return self.minimax(board, player, "moving", counts, 5, -100, 100)

        # generate all available actions
        actions = self.getPlacements(board) if action_type == "placing" else self.getMoves(board, player)

        # place or move a max piece
        if player == "p":
            value = -10

            # identify the best of the available actions for this state
            for action in actions:
                next_board = self.getNextBoard(board, player, action)
                next_counts = (counts[0] + 1, counts[1]) if action_type == "placing" else counts
                value = max(value, self.minimax(next_board, "c", action_type, next_counts, depth - 1, alpha, beta))

                # prune as necessary
                if value >= beta:
                    break

                alpha = max(alpha, value)

        # place or move a min piece
        else:
            value = 10

            # identify the best of the available actions for this state
            for action in actions:
                next_board = self.getNextBoard(board, player, action)
                next_counts = (counts[0], counts[1] + 1) if action_type == "placing" else counts
                value = min(value, self.minimax(next_board, "p", action_type, next_counts, depth - 1, alpha, beta))

                # prune as necessary
                if value <= alpha:
                    break

                beta = min(beta, value)

        return value

    # driver function
    def play(self):
        played = 0
        self.resp = self.startGame()
        print()

        # we need to survive 50 consecutive games
        while played < 50:
            self.survived = False
            print(f"Playing game {played + 1}")

            # while nobody has won and we've made fewer than 30 moves
            while not self.isGameOver():

                # place a piece
                player_count = self.getPieceCount("p")

                if player_count < 3:
                    loc = self.selectPlacement((player_count, self.getPieceCount("c")))
                    self.resp = self.placePiece(loc)

                # move a piece
                else:
                    move = self.selectMove()
                    self.resp = self.movePiece(move)

            # handle what to do at the end of a game
            if self.survived:
                self.resp = self.nextGame()
                played += 1
            else:
                self.printBoard(self.board)
                return "we lost; no hash :("

        return self.resp["data"]["hash"]

if __name__ == "__main__":
    rota = Rota()
    hash = rota.play()
    print(f"\nHash: {hash}")
