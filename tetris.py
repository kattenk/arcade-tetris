import arcade, enum, random
from pyglet.math import Vec2

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# In the Tetris community, "repeat delay" is referred to as "DAS" (Delayed Auto-Shift)
# and "repeat rate" is called "ARR" (Auto Repeat Rate). I attempted to give them more descriptive names
# for this demo. you can read more about it here: https://tetris.wiki/DAS
REPEAT_DELAY = 0.167
REPEAT_RATE = 0.033

# This game is designed to work without any asset files,
# so load them if present, otherwise set them to None
try:
    sound_rotate = arcade.load_sound("sound_rotate.wav")
    sound_move = arcade.load_sound("sound_move.wav")
    sound_drop = arcade.load_sound("sound_drop.wav")
except FileNotFoundError:
    sound_rotate = None
    sound_move = None
    sound_drop = None

class Direction(enum.Enum):
    """
    Direction in coordinate system where the origin is in the
    bottom left-hand corner of the window.
    """

    UP = Vec2(0, 1)
    RIGHT = Vec2(1, 0)
    DOWN = Vec2(0, -1)
    LEFT = Vec2(-1, 0)

class Piece:
    # Here we define the shape and color of each Tetromino, each shape is a 2-dimensional lists of characters:
    # _ = Empty cell
    # T = Filled cell
    # O = Origin (center) point (This is used for producing the rotated versions of tetrominoes)

    I = ([["T"],
          ["O"],
          ["T"],
          ["T"]],
          (0, 209, 146))

    J = ([["_", "T"],
          ["_", "O"],
          ["T", "T"]],
          (48, 105, 152))

    L = ([["T", "_"],
          ["O", "_"],
          ["T", "T"]],
          (208, 112, 56))

    O = ([["T", "T"],
          ["T", "T"]],
          (221, 225, 0))

    S = ([["_", "O", "T"],
          ["T", "T", "_"]],
          (123, 209, 46))

    T = ([["T", "O", "T"],
          ["_", "T", "_"]],
          (186, 0, 166))

    Z = ([["T", "T", "_"],
          ["_", "O", "T"]],
          (202, 7, 67))
    
    @staticmethod
    def get_all_tetrominoes():
        return Piece.I, Piece.J, Piece.L, Piece.O, Piece.S, Piece.T, Piece.Z
    
    def __init__(self, tetromino, position):
        # Each tetromino is a tuple of shape and color
        self.shape, self.color = tetromino

        # We reverse the row order of the shape because Arcade uses a coordinate system where positive Y is up
        self.shape.reverse()

        self.origin: Vec2 = None
        self.update_origin()
        self.position = position
    
    def move(self, direction: Vec2, distance=1):
        self.position += direction * distance

    def update_origin(self):
        """
        Sets the Piece's "origin" to the offset of the 'O' character within it's shape.
        """

        for y, row in enumerate(self.shape):
            if "O" in row:
                x = row.index("O")
                self.origin = Vec2(x, y)
                return
        
        self.origin = Vec2(0, 0)
    
    def rotate(self, board):
        # Rotate the shape clockwise and update origin
        transpose = [list(row) for row in zip(*self.shape)]
        self.shape = transpose[::-1]
        self.update_origin()

        # When a rotation causes a piece to intersect a wall, it needs to be "pushed" out of it.
        # https://tetris.wiki/Wall_kick
        if board.is_piece_colliding(self):
            # For every direction there is, find out how much distance it takes in that direction,
            # until the piece no longer collides (if any) and then record that in a dictionary
            distance_needed = {}
            
            for direction in Direction:
                for distance in range(1, 4):
                    self.move(direction.value, distance)

                    if not board.is_piece_colliding(self):
                        distance_needed[direction] = distance
                        
                        # Move the piece back to its original position
                        self.move(-direction.value, distance)
                        break

                    # Move back to the original position if still colliding
                    self.move(-direction.value, distance)

            # If any directions were valid escape routes..
            if distance_needed:
                # Pick the shortest one,
                # using the 'key' parameter so min() compares the distances instead of the keys
                lowest_direction = min(distance_needed, key=distance_needed.get)

                # Escape!
                self.move(lowest_direction.value, distance_needed[lowest_direction])
            else:
                # If there is no escape, undo the original rotation, we will not rotate at all.
                # (Notice the inversion of the clockwise argument)
                # TODO: ACTUALLY IMPLEMENT
                pass

        board.update_sprites()

class Board:
    def __init__(self, width, height, window_width, window_height):
        self.width, self.height = (width, height)
        self.window_width, self.window_height = (window_width, window_height)
        self.cells = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.piece = None

        # TODO: nice comment here
        self.sprites, self.sprite_list = self.create_sprites()
        self.update_sprites()

    def create_sprites(self):
        sprites = [[None for _ in range(self.width)] for _ in range(self.height)]
        sprite_list = arcade.SpriteList()

        cell_size = Vec2(self.window_width // self.width,
                         self.window_height // self.height)

        for y in range(self.height):
            for x in range(self.width):
                color = (8, 6, 27)

                center = Vec2((x * cell_size.x) + cell_size.x / 2,
                              (y * cell_size.y) + cell_size.y / 2)
                
                # Make the gaps proportional to the cell-size
                gap_width = cell_size.x // 7

                # Arcade can generate a sprite that's just a solid color for us -- without needing to load a file
                # cell_sprite = arcade.SpriteSolidColor(width=cell_size.x - gap_width,
                #                                       height=cell_size.y - gap_width,
                #                                       center_x=center.x,
                #                                       center_y=center.y,
                #                                       color=color)
                cell_sprite = arcade.Sprite("sprite.png", 1, center.x, center.y)
                cell_sprite.width = cell_size.x
                cell_sprite.height = cell_size.y

                sprites[y][x] = cell_sprite
                sprite_list.append(cell_sprite)
        
        return sprites, sprite_list
    
    def update_sprites(self):
        def add_cells(cells, position, color=None):
            empty_cell_color = (8, 6, 27)

            for y, row in enumerate(cells):
                for x, cell in enumerate(row):
                    if cell != "_":
                        if cell is None:
                            color_to_use = empty_cell_color
                        else:
                            color_to_use = color if color is not None else cell
                        
                        # if cell == "O":
                        #     color_to_use = arcade.color.YANKEES_BLUE

                        self.sprites[y + position.y][x + position.x].color = color_to_use

        add_cells(self.cells, Vec2(0, 0))
        
        if self.piece:
            shadow = self.create_shadow()
            add_cells(shadow.shape, shadow.position - shadow.origin, (53, 53, 87))

            add_cells(self.piece.shape, self.piece.position - self.piece.origin, self.piece.color)
    
    def is_piece_colliding(self, piece):
        """Is the piece overlapping any of the cells on the board or out of bounds?"""

        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell != "_":
                    x_pos, y_pos = piece.position - piece.origin + Vec2(x, y)

                    rows = len(self.cells)
                    cols = len(self.cells[0])

                    if x_pos < 0 or x_pos >= cols or y_pos < 0 or y_pos >= rows:
                        return True

                    if self.cells[y_pos][x_pos] != None:
                        return True

        return False
    
    def get_clearable_lines(self):
        pass
    
    def place_piece(self, piece):
        """Inserts the piece into the board and removes it from the piece list."""

        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell != "_":
                    x_pos, y_pos = piece.position - piece.origin + Vec2(x, y)
                    self.cells[y_pos][x_pos] = piece.color
    
    def create_shadow(self) -> Piece:
        shadow = Piece((list(self.piece.shape)[::-1], arcade.color.GRAY), Vec2(int(self.piece.position.x), int(self.piece.position.y)))

        while not self.is_piece_colliding(shadow):
            shadow.move(Direction.DOWN.value)
        
        shadow.move(Direction.UP.value)
        
        return shadow

class GameView(arcade.View):
    def __init__(self):
        super().__init__()

        # Board and falling piece
        self.board = Board(BOARD_WIDTH, BOARD_HEIGHT, self.width, self.height)
        self.falling_piece = self.spawn_piece()

        # Input
        controls = {
            #                  Action                               Should Repeat
            arcade.key.UP:     (lambda: self.rotate(),              False),
            arcade.key.LEFT:   (lambda: self.move(Direction.LEFT),  True),
            arcade.key.RIGHT:  (lambda: self.move(Direction.RIGHT), True),
            arcade.key.DOWN:   (lambda: self.move(Direction.DOWN),  True),
            arcade.key.SPACE:  (lambda: self.drop(),                False),
            arcade.key.ESCAPE: (lambda: quit(),                     False)
        }

        self.input = Input(REPEAT_DELAY, REPEAT_RATE, controls)
        self.on_key_press = self.input.on_key_press
        self.on_key_release = self.input.on_key_release

        # Gravity
        self.gravity_timer = 1
    
    def on_update(self, delta_time):
        self.input.process_input(delta_time)
        self.apply_gravity(delta_time)

    def on_draw(self):
        self.clear()
        self.board.sprite_list.draw(pixelated=True)

    def rotate(self):
        """Rotates the piece clockwise"""
        
        self.falling_piece.rotate(self.board)

        if sound_rotate:
            arcade.play_sound(sound_rotate)
    
    def move(self, d: Direction):
        """Attempts to move the piece in the direction."""

        self.falling_piece.move(d.value)

        if self.board.is_piece_colliding(self.falling_piece):
            self.falling_piece.move(-d.value)
        else:
            if sound_move:
                arcade.play_sound(sound_move)
            
            self.board.update_sprites()
    
    def drop(self):
        """Performs a hard-drop."""
        
        while not self.board.is_piece_colliding(self.falling_piece):
            self.falling_piece.move(Direction.DOWN.value)
        
        self.falling_piece.move(Direction.UP.value)

        # Place and spawn new piece
        self.board.place_piece(self.falling_piece)
        self.falling_piece = self.spawn_piece()
        
        if sound_drop:
            arcade.play_sound(sound_drop)
    
    def spawn_piece(self) -> Piece:
        """Creates a new piece at the top of the board and returns it."""

        tetromino = random.choice(Piece.get_all_tetrominoes())
        new_piece = Piece(tetromino, Vec2(0, 0))

        # Calculate the starting position at the top-center of the board
        new_piece.position = Vec2(x=BOARD_WIDTH // 2, y=BOARD_HEIGHT - len(tetromino[0]) + new_piece.origin.y)

        self.board.piece = new_piece
        self.board.update_sprites()

        return new_piece
    
    def apply_gravity(self, delta_time):
        """Applies gravity and will place the piece and re-spawn upon collision."""

        if self.gravity_timer <= 0:
            self.falling_piece.move(Direction.DOWN.value)
            self.gravity_timer = 1

            if self.board.is_piece_colliding(self.falling_piece):
                self.falling_piece.move(Direction.UP.value)

                # Place and spawn new piece
                self.board.place_piece(self.falling_piece)
                self.falling_piece = self.spawn_piece()

                if sound_drop:
                    arcade.play_sound(sound_drop)

            self.board.update_sprites()

        self.gravity_timer -= delta_time

class Input:
    def __init__(self, repeat_delay, repeat_rate, controls: dict):
        """
        Parameters:
            repeat_delay : float
                DAS: Time in seconds before an action starts repeating after the first time.
            repeat_rate : float
                ARR: Time in seconds between repeats after the initial delay.
            controls : dict
                A dictionary mapping keys to actions (method, argument, repeat flag).
        """

        self.repeat_delay = repeat_delay
        self.repeat_rate = repeat_rate
        self.controls = controls

        self.keys = set()
        self.last_keys = set()
        self.repeat_delay_timers = {}
        self.repeat_rate_timers = {}

    def process_input(self, delta_time):
        for key in self.keys:
            if key in self.controls:
                delay_timer = self.repeat_delay_timers.setdefault(key, 0)
                rate_timer = self.repeat_rate_timers.setdefault(key, 0)

                if delay_timer <= 0 or key not in self.last_keys:
                    if rate_timer <= 0:
                        method, should_repeat = self.controls[key] # Unpack the data for this action
                        method() # Execute the action for the key

                        # Set repeat rate timer, if the action shouldn't repeat, set it to infinity
                        self.repeat_rate_timers[key] = self.repeat_rate if should_repeat else float('inf')

        # Update the timers for all pressed keys
        for key in self.keys:
            self.repeat_delay_timers[key] -= delta_time
            self.repeat_rate_timers[key] -= delta_time
        
        self.last_keys = self.keys.copy()

    def on_key_press(self, key, modifiers):
        self.keys.add(key)
        self.repeat_delay_timers[key] = self.repeat_delay
        self.repeat_rate_timers[key] = 0

    def on_key_release(self, key, modifiers):
        self.keys.discard(key)
        self.repeat_delay_timers.pop(key, None)
        self.repeat_rate_timers.pop(key, None)

# You could put this outside of the "if __name__ == "__main__"" block
# but this theoretically allows you to load this file without starting the game
# allowing for other modules to use classes from this, etc.
# It's entirely useless in this case, but I thought I'd leave it in.
if __name__ == "__main__":
    window = arcade.Window(400, 600, "Tetris")
    window.show_view(GameView())
    arcade.run()