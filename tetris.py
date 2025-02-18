import arcade, enum, random
from pyglet.math import Vec2

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# In the Tetris community, "Repeat Delay" is referred to as "DAS" (Delayed Auto-Shift)
# and "Repeat Rate" is called "ARR" (Auto Repeat Rate). I attempted to give them more descriptive names
# for this demo. you can read more about it here: https://tetris.wiki/DAS
REPEAT_DELAY = 0.5
REPEAT_RATE = 0.2

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
    
    def __init__(self, tetromino, position, rotation=Direction.UP):
        # Each tetromino is a tuple of shape and color
        self.shape, self.color = tetromino

        # We reverse the row order of the shape because Arcade uses a coordinate system where positive Y is up
        self.shape.reverse()

        self.origin: Vec2 = None
        self.update_origin()
        self.position = position
        self.rotation = rotation
    
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

class Board:
    def __init__(self, width, height, window_width, window_height, pieces=[]):
        self.width, self.height = (width, height)
        self.window_width, self.window_height = (window_width, window_height)
        self.cells = [["_" for _ in range(height)] for _ in range(width)]

        self.pieces = pieces

        # TODO: nice comment here
        self.sprites, self.sprite_list = self.create_sprites()
        self.update_sprites()

    def create_sprites(self):
        sprites = [[None for _ in range(self.height)] for _ in range(self.width)]
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
                cell_sprite = arcade.SpriteSolidColor(width=cell_size.x - gap_width,
                                                      height=cell_size.y - gap_width,
                                                      center_x=center.x,
                                                      center_y=center.y,
                                                      color=color)

                sprites[x][y] = cell_sprite
                sprite_list.append(cell_sprite)
        
        return sprites, sprite_list
    
    def update_sprites(self):
        def add_cells(cells, position, color=None):
            empty_cell_color = (8, 6, 27)

            for y, row in enumerate(cells):
                for x, cell in enumerate(row):
                    if cell == "_":
                        color_to_use = empty_cell_color
                    else:
                        color_to_use = color if color is not None else cell
                    
                    if cell == "O":
                        color_to_use = arcade.color.YANKEES_BLUE

                    self.sprites[x + position.x][y + position.y].color = color_to_use

        for piece in self.pieces:
            add_cells(piece.shape, piece.position - piece.origin, piece.color)
    
    def is_within_bounds(self, piece):
        """True/False: is the piece within the bounds of the board?"""

        rotated_shape = piece.get_rotated_shape()
        shape_width, shape_height = (len(rotated_shape[0]), len(rotated_shape))

        min_position = piece.position - piece.origin

        max_position = Vec2(min_position.x + shape_width, min_position.y + shape_height)

        if max_position.x > self.width or max_position.y > self.height or min_position.x < 0 or max_position.y < 0:
            return False
        else:
            return True

class GameView(arcade.View):
    def __init__(self):
        super().__init__()

        # Spawn the first piece
        self.falling_piece = self.spawn_piece()

        # Initialize the board, which will also handle drawing our falling piece
        self.board = Board(BOARD_WIDTH, BOARD_HEIGHT, self.width, self.height,
                           pieces=[self.falling_piece])

        # Define the game controls
        controls = {
            #                 Method        Argument         Should Repeat
            arcade.key.UP:    (self.rotate, Direction.RIGHT, False),
            arcade.key.DOWN:  (self.rotate, Direction.LEFT,  False),
            arcade.key.LEFT:  (self.move,   Direction.LEFT,  True),
            arcade.key.RIGHT: (self.move,   Direction.RIGHT, True),
            arcade.key.SPACE: (self.drop,   None,            False)
        }

        # Initialize the input system with the controls
        self.input = Input(REPEAT_DELAY, REPEAT_RATE, controls)
        self.on_key_press = self.input.on_key_press
        self.on_key_release = self.input.on_key_release
    
    def rotate(self, d: Direction):
        pass
    
    def move(self, d: Direction):
        print(f"MOVE {d = }")
        pass
    
    def drop(self):
        pass
    
    def spawn_piece(self) -> Piece:
        """Creates a new piece at the top of the board and returns it."""
        
        tetromino = random.choice(Piece.get_all_tetrominoes())
        new_piece = Piece(tetromino, Vec2(0, 0))

        # Calculate the starting position at the top-center of the board
        new_piece.position = Vec2(x=BOARD_WIDTH // 2, y=BOARD_HEIGHT - len(tetromino[0]) + new_piece.origin.y)

        return new_piece
    
    def on_update(self, delta_time):
        self.input.process_input(delta_time)

    def on_draw(self):
        self.clear()
        self.board.sprite_list.draw()

class Input:
    def __init__(self, repeat_delay, repeat_rate, controls):
        self.repeat_delay = repeat_delay
        self.repeat_rate = repeat_rate
        self.controls = controls

        self.keys = set()
        self.last_keys = set()
        self.repeat_delay_timer = 0
        self.repeat_rate_timer = 0
    
    def process_input(self, delta_time):
        self.last_keys = self.keys.copy()

        for key in self.keys:
            if key in self.controls.keys():
                if self.repeat_delay_timer <= 0:
                    method, argument, should_repeat = self.controls[key]

                    if self.repeat_rate_timer <= 0:
                        if argument:
                            method(argument)
                        else:
                            method()
                        
                        self.repeat_rate_timer = self.repeat_rate

        self.repeat_delay_timer -= delta_time
        self.repeat_rate_timer -= delta_time
    
    def on_key_press(self, key, modifiers):
        self.keys.add(key)
        self.repeat_delay_timer = self.repeat_delay
    
    def on_key_release(self, key, modifiers):
        self.keys.discard(key)
        self.repeat_delay_timer = 0

# You could put this outside of the "if __name__ == "__main__"" block
# but this theoretically allows you to load this file without starting the game
# allowing for other modules to use classes from this, etc.
# It's entirely useless in this case, but I thought I'd leave it in.
if __name__ == "__main__":
    window = arcade.Window(400, 600, "Simple Tetris")
    window.show_view(GameView())
    arcade.run()