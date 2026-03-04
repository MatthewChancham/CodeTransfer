import tkinter as tk

# Emoji piece representation:
PIECE_EMOJI = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟",
}

START_POSITION = [
    ["r", "n", "b", "q", "k", "b", "n", "r"],
    ["p", "p", "p", "p", "p", "p", "p", "p"],
    ["",  "",  "",  "",  "",  "",  "",  ""],
    ["",  "",  "",  "",  "",  "",  "",  ""],
    ["",  "",  "",  "",  "",  "",  "",  ""],
    ["",  "",  "",  "",  "",  "",  "",  ""],
    ["P", "P", "P", "P", "P", "P", "P", "P"],
    ["R", "N", "B", "Q", "K", "B", "N", "R"],
]

SQUARE_SIZE = 64

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Two-Player Chess (Tkinter)")

        self.canvas = tk.Canvas(root, width=8*SQUARE_SIZE, height=8*SQUARE_SIZE)
        self.canvas.pack()

        self.board = [row[:] for row in START_POSITION]
        self.selected = None
        self.turn = "white"

        self.canvas.bind("<Button-1>", self.on_click)

        self.draw_board()
        self.draw_pieces()

    def draw_board(self):
        self.canvas.delete("square")
        colors = ["#EEEED2", "#769656"]
        for row in range(8):
            for col in range(8):
                x1 = col * SQUARE_SIZE
                y1 = row * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE
                color = colors[(row + col) % 2]
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color, outline="", tags="square"
                )

    def draw_pieces(self):
        self.canvas.delete("piece")
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                    y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                    emoji = PIECE_EMOJI[piece]
                    self.canvas.create_text(
                        x, y, text=emoji,
                        font=("Helvetica", 40),
                        tags="piece"
                    )

        if self.selected:
            r, c = self.selected
            x1 = c * SQUARE_SIZE
            y1 = r * SQUARE_SIZE
            x2 = x1 + SQUARE_SIZE
            y2 = y1 + SQUARE_SIZE
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="red", width=3, tags="piece"
            )

    def on_click(self, event):
        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE
        if row < 0 or row > 7 or col < 0 or col > 7:
            return

        if self.selected is None:
            self.handle_select(row, col)
        else:
            self.handle_move(row, col)

        self.draw_board()
        self.draw_pieces()

    def handle_select(self, row, col):
        piece = self.board[row][col]
        if not piece:
            return
        if self.turn == "white" and piece.islower():
            return
        if self.turn == "black" and piece.isupper():
            return
        self.selected = (row, col)

    def handle_move(self, row, col):
        from_row, from_col = self.selected
        piece = self.board[from_row][from_col]
        target = self.board[row][col]

        if (from_row, from_col) == (row, col):
            self.selected = None
            return

        if not self.is_legal_move(piece, from_row, from_col, row, col):
            self.selected = None
            return

        if target and ((target.isupper() and piece.isupper()) or (target.islower() and piece.islower())):
            self.selected = None
            return

        self.board[row][col] = piece
        self.board[from_row][from_col] = ""

        if piece == "P" and row == 0:
            self.board[row][col] = "Q"
        if piece == "p" and row == 7:
            self.board[row][col] = "q"

        self.turn = "black" if self.turn == "white" else "white"
        self.selected = None

    def is_legal_move(self, piece, fr, fc, tr, tc):
        dr = tr - fr
        dc = tc - fc
        abs_dr = abs(dr)
        abs_dc = abs(dc)

        if piece == "P":
            if dc == 0 and dr == -1 and self.board[tr][tc] == "":
                return True
            if dc == 0 and dr == -2 and fr == 6 and self.board[fr-1][fc] == "" and self.board[tr][tc] == "":
                return True
            if abs_dc == 1 and dr == -1 and self.board[tr][tc] and self.board[tr][tc].islower():
                return True
            return False

        if piece == "p":
            if dc == 0 and dr == 1 and self.board[tr][tc] == "":
                return True
            if dc == 0 and dr == 2 and fr == 1 and self.board[fr+1][fc] == "" and self.board[tr][tc] == "":
                return True
            if abs_dc == 1 and dr == 1 and self.board[tr][tc] and self.board[tr][tc].isupper():
                return True
            return False

        if piece.upper() == "R":
            if fr != tr and fc != tc:
                return False
            return self.clear_path(fr, fc, tr, tc)

        if piece.upper() == "B":
            if abs_dr != abs_dc:
                return False
            return self.clear_path(fr, fc, tr, tc)

        if piece.upper() == "Q":
            if (fr == tr or fc == tc) or (abs_dr == abs_dc):
                return self.clear_path(fr, fc, tr, tc)
            return False

        if piece.upper() == "N":
            return (abs_dr, abs_dc) in [(1, 2), (2, 1)]

        if piece.upper() == "K":
            return abs_dr <= 1 and abs_dc <= 1

        return False

    def clear_path(self, fr, fc, tr, tc):
        step_r = 0 if fr == tr else (1 if tr > fr else -1)
        step_c = 0 if fc == tc else (1 if tc > fc else -1)

        r = fr + step_r
        c = fc + step_c
        while (r, c) != (tr, tc):
            if self.board[r][c] != "":
                return False
            r += step_r
            c += step_c
        return True


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessGUI(root)
    root.mainloop()
