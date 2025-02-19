import socket
import chess
import pygame
import random

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.selected_square = None
        self.valid_moves = []
        self.window_size = 640
        self.square_size = self.window_size // 8
        self.colors = [(240, 217, 181), (181, 136, 99)]  # Light and dark squares
        self.piece_images = self.load_piece_images()
        self.sounds = self.load_sounds()
        self.play_with_bot = False
        self.multiplayer = False
        self.elo = 1200
        self.state = "home"  # Game state: "home" or "game"


        pygame.init()
        pygame.mixer.init()  # Initialize sound mixer
        self.screen = pygame.display.set_mode((self.window_size, self.window_size))
        pygame.display.set_caption("Chess Game")
        self.font = pygame.font.Font(None, 36)
        self.sounds = self.load_sounds()
        
    def load_sounds(self):
        sounds = {}
        try:
            sounds['move'] = pygame.mixer.Sound("assets/move.wav")
            sounds['check'] = pygame.mixer.Sound("assets/check.wav")
            sounds['checkmate'] = pygame.mixer.Sound("assets/checkmate.wav")
        except FileNotFoundError:
            print("Sound files not found. Please ensure they are in the assets folder.")
        return sounds



    def load_piece_images(self):
        pieces = ["p", "r", "n", "b", "q", "k", "WP", "WR", "WN", "WB", "WQ", "WK"]
        images = {}
        for piece in pieces:
            file_path = f"assets/{piece}.png"
            try:
                images[piece] = pygame.image.load(file_path)
                images[piece] = pygame.transform.scale(images[piece], (self.square_size, self.square_size))
            except FileNotFoundError:
                print(f"Error: File {file_path} not found. Please add the image to the assets folder.")
                placeholder = pygame.Surface((self.square_size, self.square_size))
                placeholder.fill((255, 0, 0))  # Red square as a placeholder
                images[piece] = placeholder
        return images



    def draw_board(self):
        for row in range(8):
            for col in range(8):
                color = self.colors[(row + col) % 2]
                pygame.draw.rect(
                    self.screen, color, pygame.Rect(col * self.square_size, row * self.square_size, self.square_size, self.square_size)
                )

    def draw_pieces(self):
        for row in range(8):
            for col in range(8):
                piece = self.board.piece_at(chess.square(col, 7 - row))
                if piece:
                    symbol = piece.symbol()
                    if symbol.isupper():  # White pieces
                        symbol = "W" + symbol
                    self.screen.blit(self.piece_images[symbol], (col * self.square_size, row * self.square_size))
  
    def bot_move(self):
        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            return

        # Basic piece values for evaluation
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

        def evaluate_position():
            if self.board.is_checkmate():
                return -20000 if self.board.turn else 20000
            
            score = 0
            for square in chess.SQUARES:
                piece = self.board.piece_at(square)
                if piece is None:
                    continue
                    
                value = piece_values[piece.piece_type]
                if piece.color:
                    score += value
                else:
                    score -= value
                    
            return score

        def evaluate_move(move):
            self.board.push(move)
            score = -evaluate_position()
            self.board.pop()
            return score

        # Different play styles based on ELO
        if self.elo < 800:  # Beginner: Mostly random moves
            if random.random() < 0.8:  # 80% random moves
                move = random.choice(legal_moves)
            else:
                move = max(legal_moves, key=evaluate_move)
                
        elif self.elo < 1200:  # Intermediate: Mix of random and calculated moves
            if random.random() < 0.1:  # 40% random moves
                move = random.choice(legal_moves)
            else:
                move = max(legal_moves, key=evaluate_move)
                
        elif self.elo < 1600:  # Advanced: Better evaluation with some mistakes
            if random.random() < 0.0:  # 20% random moves
                move = random.choice(legal_moves)
            else:
                move = max(legal_moves, key=evaluate_move)
                
        else:  # Expert: Best calculated moves
            move = max(legal_moves, key=evaluate_move)

        self.board.push(move)

    def play_bot_turn(self):
        if self.play_with_bot and not self.board.turn:  # If it's black's turn and bot is enabled
            self.bot_move()

    def handle_click(self, pos):
        if self.check_game_state():  # Check if game is over before handling clicks
            return
            
        col = pos[0] // self.square_size
        row = pos[1] // self.square_size
        square = chess.square(col, 7 - row)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece is not None and ((piece.color and self.board.turn) or (not piece.color and not self.board.turn)):
                self.selected_square = square
                self.valid_moves = [move.to_square for move in self.board.legal_moves if move.from_square == square]
        else:
            move = chess.Move(self.selected_square, square)
            
            # Check if it's a pawn promotion move
            piece = self.board.piece_at(self.selected_square)
            if (piece and piece.piece_type == chess.PAWN and
                ((chess.square_rank(square) == 7 and self.board.turn) or
                (chess.square_rank(square) == 0 and not self.board.turn))
            ):
                promotion_piece = self.show_promotion_dialog()
                if promotion_piece:
                    move = chess.Move(self.selected_square, square, promotion=promotion_piece)
                    if move in self.board.legal_moves:
                        self.board.push(move)
                        if not self.check_game_state() and self.play_with_bot:  # Check game state before bot move
                            self.play_bot_turn()
                        if 'move' in self.sounds:
                            self.sounds['move'].play()
            else:
                if move in self.board.legal_moves:
                    self.board.push(move)
                    if not self.check_game_state() and self.play_with_bot:  # Check game state before bot move
                        self.play_bot_turn()

            self.selected_square = None
            self.valid_moves = []



    def show_promotion_dialog(self):
        dialog_width = 200
        dialog_height = 250
        dialog_x = (self.window_size - dialog_width) // 2
        dialog_y = (self.window_size - dialog_height) // 2

        dialog_surface = pygame.Surface((dialog_width, dialog_height))
        dialog_surface.fill((255, 255, 255))
        pygame.draw.rect(dialog_surface, (0, 0, 0), pygame.Rect(0, 0, dialog_width, dialog_height), 2)

        pieces = [(chess.QUEEN, "Q"), (chess.ROOK, "R"), (chess.BISHOP, "B"), (chess.KNIGHT, "N")]
        button_height = 50
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    relative_y = mouse_pos[1] - dialog_y
                    
                    if dialog_y <= mouse_pos[1] <= dialog_y + dialog_height:
                        index = relative_y // button_height
                        if 0 <= index < len(pieces):
                            return pieces[index][0]

            # Draw promotion options
            for i, (piece, symbol) in enumerate(pieces):
                y_pos = i * button_height
                pygame.draw.rect(dialog_surface, (200, 200, 200), (0, y_pos, dialog_width, button_height))
                text = self.font.render(f"Promote to {symbol}", True, (0, 0, 0))
                text_rect = text.get_rect(center=(dialog_width // 2, y_pos + button_height // 2))
                dialog_surface.blit(text, text_rect)

            self.screen.blit(dialog_surface, (dialog_x, dialog_y))
            pygame.display.flip()

    def bot_move(self):
        legal_moves = list(self.board.legal_moves)
        if 'move' in self.sounds:
                self.sounds['move'].play()

        if self.elo < 1000:
            move = random.choice(legal_moves)
        else:
            move = max(legal_moves, key=lambda m: self.evaluate_move(m))
        self.board.push(move)
        

    def evaluate_move(self, move):
        return random.random()

    def draw_highlights(self):
        if self.selected_square is not None:
            row, col = 7 - chess.square_rank(self.selected_square), chess.square_file(self.selected_square)
            pygame.draw.rect(
                self.screen, (0, 255, 0, 128), pygame.Rect(col * self.square_size, row * self.square_size, self.square_size, self.square_size), 3
            )

            for square in self.valid_moves:
                row, col = 7 - chess.square_rank(square), chess.square_file(square)
                pygame.draw.circle(
                    self.screen, (0, 255, 0),
                    (col * self.square_size + self.square_size // 2, row * self.square_size + self.square_size // 2),
                    self.square_size // 6
                )

        if self.board.is_check():
            king_square = self.board.king(self.board.turn)
            row, col = 7 - chess.square_rank(king_square), chess.square_file(king_square)
            pygame.draw.rect(
                self.screen, (255, 0, 0), pygame.Rect(col * self.square_size, row * self.square_size, self.square_size, self.square_size), 3
            )
    def check_game_state(self):
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn else "White"
            if 'checkmate' in self.sounds:
                self.sounds['checkmate'].play()
            self.display_message(f"Checkmate! {winner} wins!", show_buttons=True)
            return True
        elif self.board.is_stalemate():
            self.display_message("Stalemate! It's a draw!", show_buttons=True)
            return True
        elif self.board.is_insufficient_material():
            self.display_message("Draw! Insufficient material!", show_buttons=True)
            return True
        return False
    
    def display_message(self, message, show_buttons=False):
        self.screen.fill((0, 0, 0))
        message_surface = self.font.render(message, True, (255, 255, 255))
        message_rect = message_surface.get_rect(center=(self.window_size // 2, self.window_size // 2 - 50))
        self.screen.blit(message_surface, message_rect)

        if show_buttons:
            new_game_button = pygame.Rect(180, 300, 120, 50)
            home_button = pygame.Rect(340, 300, 120, 50)

            pygame.draw.rect(self.screen, (0, 128, 0), new_game_button)
            pygame.draw.rect(self.screen, (0, 128, 0), home_button)

            new_game_text = self.font.render("New Game", True, (255, 255, 255))
            home_text = self.font.render("Home", True, (255, 255, 255))

            self.screen.blit(new_game_text, (new_game_button.x + 10, new_game_button.y + 10))
            self.screen.blit(home_text, (home_button.x + 30, home_button.y + 10))

            pygame.display.flip()

            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if new_game_button.collidepoint(event.pos):
                            self.__init__()
                            return
                        elif home_button.collidepoint(event.pos):
                            self.__init__()
                            self.state = "home"
                            return

    def display_home(self):
        self.screen.fill((30, 30, 30))

        play_bot_button = pygame.Rect(200, 150, 240, 50)
        multiplayer_button = pygame.Rect(200, 250, 240, 50)
        local_button = pygame.Rect(200, 350, 240, 50)
        elo_slider_rect = pygame.Rect(200, 450, 240, 50)

        pygame.draw.rect(self.screen, (0, 128, 128), play_bot_button)
        pygame.draw.rect(self.screen, (0, 128, 128), multiplayer_button)
        pygame.draw.rect(self.screen, (0, 128, 128), local_button)
        pygame.draw.rect(self.screen, (128, 0, 128), elo_slider_rect)

        play_bot_text = self.font.render("Play with Bot", True, (255, 255, 255))
        multiplayer_text = self.font.render("Multiplayer", True, (255, 255, 255))
        local_text = self.font.render("Play Locally", True, (255, 255, 255))
        elo_text = self.font.render(f"ELO: {self.elo}", True, (255, 255, 255))

        self.screen.blit(play_bot_text, (play_bot_button.x + 30, play_bot_button.y + 10))
        self.screen.blit(multiplayer_text, (multiplayer_button.x + 30, multiplayer_button.y + 10))
        self.screen.blit(local_text, (local_button.x + 30, local_button.y + 10))
        self.screen.blit(elo_text, (elo_slider_rect.x + 60, elo_slider_rect.y + 10))

        pygame.display.flip()

        return play_bot_button, multiplayer_button, local_button, elo_slider_rect

    def run(self):
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif self.state == "home" and event.type == pygame.MOUSEBUTTONDOWN:
                    play_bot_button, multiplayer_button, local_button, elo_slider_rect = self.display_home()

                    if play_bot_button.collidepoint(event.pos):
                        self.play_with_bot = True
                        self.state = "game"
                    elif multiplayer_button.collidepoint(event.pos):
                        self.multiplayer = True
                        self.state = "game"
                    elif local_button.collidepoint(event.pos):
                        self.play_with_bot = False
                        self.multiplayer = False
                        self.state = "game"
                    elif elo_slider_rect.collidepoint(event.pos):
                        self.elo = min(3200, max(400, self.elo + 200))

                elif self.state == "game" and event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            if self.state == "home":
                self.display_home()
            elif self.state == "game":
                self.screen.fill((0, 0, 0))
                self.draw_board()
                self.draw_pieces()
                self.draw_highlights()
                self.check_game_state()
                pygame.display.flip()

            clock.tick(60)

if __name__ == "__main__":
    app = ChessGame()
    app.run()
