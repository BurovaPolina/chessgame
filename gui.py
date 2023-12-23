import tkinter as tk
import os
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from copy import deepcopy
import re
import sys

SHORT_NAME = {
    'R': 'Rook',
    'N': 'Knight',
    'B': 'Bishop',
    'Q': 'Queen',
    'K': 'King',
    'P': 'Pawn'
}


def create_piece(piece, color='white'):
    ''' Takes a piece name or shortname and returns the corresponding piece instance '''
    if piece in (None, ' '): return
    if len(piece) == 1:
        if piece.isupper():
            color = 'white'
        else:
            color = 'black'
        piece = SHORT_NAME[piece.upper()]
    module = sys.modules[__name__]
    return module.__dict__[piece](color)


class Piece(object):
    def __init__(self, color):
        if color == 'black':
            self.shortname = self.shortname.lower()
        elif color == 'white':
            self.shortname = self.shortname.upper()
        self.color = color

    def place(self, board):
        ''' Keep a reference to the board '''
        self.board = board

    def moves_available(self, pos, orthogonal, diagonal, distance):
        board = self.board
        allowed_moves = []
        orth = ((-1, 0), (0, -1), (0, 1), (1, 0))
        diag = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        piece = self
        beginningpos = board.num_notation(pos.upper())
        if orthogonal and diagonal:
            directions = diag + orth
        elif diagonal:
            directions = diag
        elif orthogonal:
            directions = orth
        for x, y in directions:
            collision = False
            for step in range(1, distance + 1):
                if collision: break
                dest = beginningpos[0] + step * x, beginningpos[1] + step * y
                if self.board.alpha_notation(dest) not in board.occupied(
                        'white') + board.occupied('black'):
                    allowed_moves.append(dest)
                elif self.board.alpha_notation(dest) in board.occupied(
                        piece.color):
                    collision = True
                else:
                    allowed_moves.append(dest)
                    collision = True
        allowed_moves = filter(board.is_on_board, allowed_moves)
        return map(board.alpha_notation, allowed_moves)


class King(Piece):
    shortname = 'k'

    def moves_available(self, pos):
        return super(King, self).moves_available(pos.upper(), True, True, 1)


class Queen(Piece):
    shortname = 'q'

    def moves_available(self, pos):
        return super(Queen, self).moves_available(pos.upper(), True, True, 8)


class Rook(Piece):
    shortname = 'r'

    def moves_available(self, pos):
        return super(Rook, self).moves_available(pos.upper(), True, False, 8)


class Bishop(Piece):
    shortname = 'b'

    def moves_available(self, pos):
        return super(Bishop, self).moves_available(pos.upper(), False, True, 8)


class Knight(Piece):
    shortname = 'n'

    def moves_available(self, pos):
        board = self.board
        allowed_moves = []
        beginningpos = board.num_notation(pos.upper())
        piece = board.get(pos.upper())
        deltas = (
        (-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for x, y in deltas:
            dest = beginningpos[0] + x, beginningpos[1] + y
            if (board.alpha_notation(dest) not in board.occupied(piece.color)):
                allowed_moves.append(dest)
        allowed_moves = filter(board.is_on_board, allowed_moves)
        return map(board.alpha_notation, allowed_moves)


class Pawn(Piece):
    shortname = 'p'

    def moves_available(self, pos):
        board = self.board
        piece = self
        if self.color == 'white':
            startpos, direction, enemy = 1, 1, 'black'
        else:
            startpos, direction, enemy = 6, -1, 'white'
        allowed_moves = []
        # Moving
        prohibited = board.occupied('white') + board.occupied('black')
        beginningpos = board.num_notation(pos.upper())
        forward = beginningpos[0] + direction, beginningpos[1]
        if board.alpha_notation(forward) not in prohibited:
            allowed_moves.append(forward)
            if beginningpos[0] == startpos:
                # If pawn is in starting position allow double moves
                double_forward = (forward[0] + direction, forward[1])
                if board.alpha_notation(double_forward) not in prohibited:
                    allowed_moves.append(double_forward)
        # Attacking
        for a in range(-1, 2, 2):
            attack = beginningpos[0] + direction, beginningpos[1] + a
            if board.alpha_notation(attack) in board.occupied(enemy):
                allowed_moves.append(attack)
        allowed_moves = filter(board.is_on_board, allowed_moves)
        return map(board.alpha_notation, allowed_moves)


START_PATTERN = '/4kn/8/8/8/8//2KNN w 0 1'


class Board(dict):
    y_axis = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')
    x_axis = (1, 2, 3, 4, 5, 6, 7, 8)
    captured_pieces = {'white': [], 'black': []}
    player_turn = None
    halfmove_clock = 0
    fullmove_number = 1
    history = []

    def __init__(self, pat=None):
        self.show(START_PATTERN)

    def is_in_check_after_move(self, p1, p2):
        print(p1, p2)
        tmp = deepcopy(self)
        tmp.move(p1, p2)
        return tmp.king_in_check(self[p1].color)

    def shift(self, p1, p2):
        p1, p2 = p1.upper(), p2.upper()
        piece = self[p1]
        try:
            dest = self[p2]
        except:
            dest = None
        if self.player_turn != piece.color:
            raise NotYourTurn("Not " + piece.color + "'s turn!")
        enemy = ('white' if piece.color == 'black' else 'black')
        moves_available = piece.moves_available(p1)
        if p2 not in moves_available:
            raise InvalidMove
        if self.all_moves_available(enemy):
            if self.is_in_check_after_move(p1, p2):
                raise Check
        if not moves_available and self.king_in_check(piece.color):
            raise CheckMate
        elif not moves_available:
            raise Draw
        else:
            self.move(p1, p2)
            self.complete_move(piece, dest, p1, p2)

    def move(self, p1, p2):
        piece = self[p1]
        try:
            dest = self[p2]
        except:
            pass
        del self[p1]
        self[p2] = piece

    def complete_move(self, piece, dest, p1, p2):
        enemy = ('white' if piece.color == 'black' else 'black')
        if piece.color == 'black':
            self.fullmove_number += 1
        self.halfmove_clock += 1
        self.player_turn = enemy
        abbr = piece.shortname
        if abbr == 'P':
            abbr = ''
            self.halfmove_clock = 0
        if dest is None:
            movetext = abbr + p2.lower()
        else:
            movetext = abbr + 'x' + p2.lower()
            self.halfmove_clock = 0
        self.history.append(movetext)

    def all_moves_available(self, color):

        result = []
        for coord in self.keys():
            if (self[coord] is not None) and self[coord].color == color:
                moves = self[coord].moves_available(coord)
                if moves: result += moves
        return result

    def occupied(self, color):
        result = []

        for coord in iter(self.keys()):
            if self[coord].color == color:
                result.append(coord)
        return result

    def position_of_king(self, color):
        for pos in self.keys():
            if isinstance(self[pos], King) and self[pos].color == color:
                return pos

    def king_in_check(self, color):
        kingpos = self.position_of_king(color)
        opponent = ('black' if color == 'white' else 'white')
        for pieces in self.items():
            if kingpos in self.all_moves_available(opponent):
                return True
            else:
                return False

    def alpha_notation(self, xycoord):
        if xycoord[0] < 0 or xycoord[0] > 7 or xycoord[1] < 0 or xycoord[
            1] > 7: return
        return self.y_axis[int(xycoord[1])] + str(self.x_axis[int(xycoord[0])])

    def num_notation(self, coord):
        return int(coord[1]) - 1, self.y_axis.index(coord[0])

    def is_on_board(self, coord):
        if coord[1] < 0 or coord[1] > 7 or coord[0] < 0 or coord[0] > 7:
            return False
        else:
            return True

    def show(self, pat):
        self.clear()
        pat = pat.split(' ')

        def expand(match):
            return ' ' * int(match.group(0))

        pat[0] = re.compile(r'\d').sub(expand, pat[0])
        for x, row in enumerate(pat[0].split('/')):
            for y, letter in enumerate(row):
                if letter == ' ': continue
                coord = self.alpha_notation((7 - x, y))
                self[coord] = create_piece(letter)
                self[coord].place(self)
        if pat[1] == 'w':
            self.player_turn = 'white'
        else:
            self.player_turn = 'black'
        self.halfmove_clock = int(pat[2])
        self.fullmove_number = int(pat[3])


class ChessError(Exception): pass


class Check(ChessError): pass


class InvalidMove(ChessError): pass


class CheckMate(ChessError): pass


class Draw(ChessError): pass


class NotYourTurn(ChessError): pass


class InvalidCoord(ChessError): pass


def open_file():
    try:
        text = open(r"authorization_file.txt", "r+")
        return text
    except FileNotFoundError:
        text = open(r"authorization_file.txt", "w")
        text.close()
        text = open(r"authorization_file.txt", "r+")
        return text


def dismiss(windows):
    windows.grab_release()
    windows.destroy()


class StartWindow:
    def __init__(self, window):
        self.auth_window = window
        self.accounts = {}

        style_text = ttk.Style()
        style_text.configure("my.TButton", font="Arial 9")

        self.login = ttk.Entry(self.auth_window, width=20)
        self.password = ttk.Entry(self.auth_window, width=20)

        self.login.place(x=200, y=70)
        self.password.place(x=200, y=100)

        Label(self.auth_window, text="Добро пожаловать, введите свой логин и пароль", font="Arial 10").place(x=100, y=20)
        Label(self.auth_window, text="Логин", font="Arial 10").place(x=150, y=70)
        Label(self.auth_window, text="Пароль", font="Arial 10").place(x=142, y=100)
        ttk.Button(self.auth_window, text="Авторизация", width=17, style="my.TButton", command=lambda: self.authorization()).place(x=200, y=130)
        ttk.Button(self.auth_window, text="Регистрация", width=17, style="my.TButton", command=lambda: self.registration()).place(x=200, y=160)

    def authorization(self):
        login = self.login.get()
        password = self.password.get()

        if len(login) == 0 or len(password) == 0:
            messagebox.showwarning(title="Ошибка", message="Поле заполнения пусто")

        else:
            file = open_file()
            a = file.readline()[:-1].split(" ")

            while True:
                if a != [""]:
                    self.accounts[a[0]] = a[1]
                    a = file.readline()[:-1].split(" ")
                else:
                    break

            flag_reg = False
            flag_password = True
            for i in self.accounts.items():
                l, p = i
                if login == l and password == p:
                    flag_reg = True
                    break
                elif login == l and password != p:
                    flag_password = False

            if flag_reg:
                for widget in self.auth_window.winfo_children():
                    widget.destroy()

                game = Board()
                Label(self.auth_window, text="Вы успешно авторизовались!", font="Arial 12 bold").place(x=120, y=80)
                ttk.Button(self.auth_window, text="Играть", style="my.TButton",
                           command=lambda: (self.auth_window.destroy(), main(game))).place(x=200, y=150)

            elif not flag_password:
                messagebox.showwarning(title="Ошибка", message="Неверный пароль")
            else:
                messagebox.showwarning(title="Ошибка", message="Такого аккаунта не существует")

    def registration(self):
        window = Toplevel()
        window.geometry("480x320+100+100")
        window.title("Регистрация")
        window.resizable(False, False)
        window.protocol("WM_DELETE_WINDOW", lambda: dismiss(window))
        window.grab_set()

        login_reg = ttk.Entry(window, width=20)
        password_reg = ttk.Entry(window, width=20)

        login_reg.place(x=200, y=70)
        password_reg.place(x=200, y=100)

        Label(window, text="Введите желаемый логин и пароль", font="Arial 10").place(x=100, y=20)
        Label(window, text="Логин", font="Arial 10").place(x=150, y=70)
        Label(window, text="Пароль", font="Arial 10").place(x=142, y=100)
        ttk.Button(window, text="Регистрация", width=17, style="my.TButton", command=lambda: registrate()).place(x=200, y=130)

        def registrate():
            login = login_reg.get()
            password = password_reg.get()

            if len(login) == 0 or len(password) == 0:
                messagebox.showwarning(title="Ошибка", message="Поле заполнения пусто")
            else:
                file = open_file()
                a = file.readline()[:-1].split(" ")

                while True:
                    if a != ['']:
                        self.accounts[a[0]] = a[1]
                        a = file.readline()[:-1].split(" ")
                    else:
                        break

                flag_reg = False

                for i in self.accounts.items():
                    log, pasw = i
                    if login == log:
                        flag_reg = True

                if not flag_reg:
                    file = open_file()
                    file.seek(0, os.SEEK_END)
                    file.write(f'{login} {password}\n')
                    file.close()

                    for h in window.winfo_children():
                        h.destroy()

                    Label(window, text="Вы успешно зарегистрировались", font="Arial 10 bold").place(x=120, y=80)
                    window.after(2000, lambda: (window.destroy(), window.grab_release()))
                else:
                    messagebox.showwarning(title="Ошибка", message="Такой аккаунт уже существует")


class GUI:
    pieces = {}
    selected_piece = None
    focused = None
    images = {}
    color1 = "#b4d6d2"
    color2 = "#4c5d64"
    highlightcolor = "lightgray"
    rows = 8
    columns = 8
    dim_square = 64

    def __init__(self, parent, chessboard):
        self.chessboard = chessboard
        self.parent = parent
        # Adding Top Menu
        self.menubar = tk.Menu(parent)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="New Game", command=self.new_game)


        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.parent.config(menu=self.menubar)

        # Adding Frame
        self.btmfrm = tk.Frame(parent, height=64)
        self.info_label = tk.Label(self.btmfrm,
                                text="   White to Start the Game  ",
                                fg=self.color2)
        self.info_label.pack(side=tk.RIGHT, padx=8, pady=5)
        self.btmfrm.pack(fill="x", side=tk.BOTTOM)

        canvas_width = self.columns * self.dim_square
        canvas_height = self.rows * self.dim_square
        self.canvas = tk.Canvas(parent, width=canvas_width,
                               height=canvas_height)
        self.canvas.pack(padx=8, pady=8)
        self.draw_board()
        self.canvas.bind("<Button-1>", self.square_clicked)

    def new_game(self):
        self.chessboard.show(START_PATTERN)
        self.draw_board()
        self.draw_pieces()
        self.info_label.config(text="   White to Start the Game  ", fg='red')

    def square_clicked(self, event):
        col_size = row_size = self.dim_square
        selected_column = int(event.x / col_size)
        selected_row = 7 - int(event.y / row_size)
        pos = self.chessboard.alpha_notation((selected_row, selected_column))
        print('pos', pos)
        try:
            piece = self.chessboard[pos]
        except:
            pass
        if self.selected_piece:
            self.shift(self.selected_piece[1], pos)
            self.selected_piece = None
            self.focused = None
            self.pieces = {}
            self.draw_board()
            self.draw_pieces()
        self.focus(pos)
        self.draw_board()

        pos = self.chessboard.alpha_notation((7, 5))
        self.focus(pos)
        self.draw_board()

    def shift(self, p1, p2):
        piece = self.chessboard[p1]
        try:
            dest_piece = self.chessboard[p2]
        except:
            dest_piece = None
        if dest_piece is None or dest_piece.color != piece.color:
            try:
                self.chessboard.shift(p1, p2)
            except ChessError as error:
                self.info_label["text"] = error.__class__.__name__
            else:
                turn = ('white' if piece.color == 'black' else 'black')
                self.info_label[
                    "text"] = '' + piece.color.capitalize() + "  :  " + p1 + p2 + '    ' + turn.capitalize() + '\'s turn'

    def focus(self, pos):
        try:
            piece = self.chessboard[pos]
            print('piece', piece)
        except:
            piece = None
        if piece is not None and (piece.color == self.chessboard.player_turn):
            self.selected_piece = (self.chessboard[pos], pos)
            self.focused = list(map(self.chessboard.num_notation,
                               (self.chessboard[pos].moves_available(pos))))

    def draw_board(self):
        color = self.color2
        for row in range(self.rows):
            color = self.color1 if color == self.color2 else self.color2
            for col in range(self.columns):
                x1 = (col * self.dim_square)
                y1 = ((7 - row) * self.dim_square)
                x2 = x1 + self.dim_square
                y2 = y1 + self.dim_square
                if self.focused is not None and (row, col) in self.focused:
                    self.canvas.create_rectangle(x1, y1, x2, y2,
                                                 fill=self.highlightcolor,
                                                 tags="area")
                else:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color,
                                                 tags="area")
                color = self.color1 if color == self.color2 else self.color2
        for name in self.pieces:
            self.pieces[name] = (self.pieces[name][0], self.pieces[name][1])
            x0 = (self.pieces[name][1] * self.dim_square) + int(
                self.dim_square / 2)
            y0 = ((7 - self.pieces[name][0]) * self.dim_square) + int(
                self.dim_square / 2)
            self.canvas.coords(name, x0, y0)
        self.canvas.tag_raise("occupied")
        self.canvas.tag_lower("area")

    def draw_pieces(self):
        self.canvas.delete("occupied")
        for coord, piece in self.chessboard.items():
            x, y = self.chessboard.num_notation(coord)
            if piece is not None:
                filename = "pieces_image/%s%s.png" % (
                piece.shortname.lower(), piece.color)
                piecename = "%s%s%s" % (piece.shortname, x, y)
                if filename not in self.images:
                    self.images[filename] = tk.PhotoImage(file=filename)
                self.canvas.create_image(0, 0, image=self.images[filename],
                                         tags=(piecename, "occupied"),
                                         anchor="c")
                x0 = (y * self.dim_square) + int(self.dim_square / 2)
                y0 = ((7 - x) * self.dim_square) + int(self.dim_square / 2)
                self.canvas.coords(piecename, x0, y0)


def main(chessboard):
    root = tk.Tk()
    root.title("Chess")
    gui = GUI(root, chessboard)
    gui.draw_board()
    gui.draw_pieces()


auth = Tk()
auth.title("Авторизация")
auth.geometry("480x320+100+100")
auth.resizable(False, False)

StartWindow(auth)

auth.mainloop()
