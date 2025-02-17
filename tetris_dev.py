import arcade, enum, random
from pyglet.math import Vec2

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

class Direction(enum.Enum):
    """
    Direction in coordinate system where the origin is in the
    bottom left-hand corner of the window.
    """

    UP = Vec2(0, 1)
    RIGHT = Vec2(1, 0)
    DOWN = Vec2(0, -1)
    LEFT = Vec2(-1, 0)

    def rotate(self, clockwise=True):
        """Cycles through the directions either clockwise or counter-clockwise."""
        return list(Direction)[(list(Direction).index(self) + (1 if clockwise else -1)) % len(list(Direction))]

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
        self.shape, self.color = tetromino
        self.position = position
        self.rotation = rotation
    
    def find_origin(self) -> Vec2:
        """
        Attempts to locate the 'O' character within the shape, and return it's position
        """

        for x, row in enumerate(self.shape):
            if "O" in row:
                y = row.index("O")
                return Vec2(x, y)
        
        return Vec2(0, 0)
    
    def get_rotated_shape(self):
        """Returns the pieces shape rotated according to it's current rotation."""

        def transpose(shape):
            """
            Transposes a shape, this has the effect of turning the shape on it's side:
            columns become rows, rows become columns.
            """

            return [list(row) for row in zip(*shape)]

        return {
            Direction.UP:    self.shape,                              # Return the shape as-is for UP
            Direction.DOWN:  [row[::-1] for row in self.shape[::-1]], # Reverse the rows and then reverse each row (180 degrees)
            Direction.RIGHT: transpose(self.shape[::-1]),             # Reverse the rows first, then transpose for 90-degree clockwise rotation
            Direction.LEFT:  transpose(self.shape)[::-1]              # Transpose and then reverse the rows for 90-degree counter-clockwise rotation
        }[self.rotation]

class Board:
    def __init__(self, width, height, window_width, window_height):
        self.width, self.height = (width, height)
        self.window_width, self.window_height = (window_width, window_height)
        self.cells = [[None for _ in range(height)] for _ in range(width)]

        self.pieces = []

        # TODO: nice comment here
        self.sprites, self.sprite_list = self.create_sprites()

    def create_sprites(self):
        sprites = [[None for _ in range(self.height)] for _ in range(self.width)]
        sprite_list = arcade.SpriteList()

        cell_size = Vec2(self.window_width // self.width,
                         self.window_height // self.height)

        for y in range(self.height):
            for x in range(self.width):
                color = (8, 6, 27)

                center = Vec2(((x) * (cell_size.x)) + cell_size.x / 2,
                              ((y) * (cell_size.y)) + cell_size.y / 2)
                
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
            for y, row in enumerate(cells):
                for x, cell in enumerate(row):
                    if cell == "_":
                        continue
                    
                    if cell == None:
                        color = (8, 6, 27)
                    else:
                        if color == None:
                            color = cell
                        else:
                            color = color
                    
                    self.sprites[x + position.x][y + position.y].color = color

        for piece in self.pieces:
            add_cells(piece.get_rotated_shape(), piece.position - piece.find_origin(), piece.color)
    
    def is_within_bounds(self, piece):
        """True/False: is the piece within the bounds of the board?"""

        rotated_shape = piece.get_rotated_shape()
        shape_width, shape_height = (len(rotated_shape[0]), len(rotated_shape))

        min_position = piece.position

        if piece.find_origin():
            min_position -= piece.find_origin()

        max_position = Vec2(min_position.x + shape_width, min_position.y + shape_height)

        if max_position.x > self.width or max_position.y > self.height or min_position.x < 0 or max_position.y < 0:
            return False
        else:
            return True

class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.board = Board(BOARD_WIDTH, BOARD_HEIGHT, self.width, self.height)

        self.falling_piece = self.spawn_piece()
        self.board.pieces.append(self.falling_piece)
        self.board.update_sprites()
    
    def spawn_piece(self) -> Piece:
        """Creates a new piece at the top of the board and returns it."""
        
        tetromino = random.choice(Piece.get_all_tetrominoes())
        new_piece = Piece(tetromino, Vec2(0, 0))

        # Calculate the starting position at the top-center of the board
        new_piece.position = Vec2(x=self.board.width // 2, y=self.board.height - len(tetromino[0]) - new_piece.find_origin().y)

        return new_piece

    def on_draw(self):
        self.clear()
        self.board.sprite_list.draw()

# You could put this outside of the "if __name__ == "__main__"" block
# but this theoretically allows you to load this file without starting the game
# allowing for other modules to use classes from this, etc.
# It's entirely useless in this case, but I thought I'd leave it in.
if __name__ == "__main__":
    window = arcade.Window(400, 600, "Simple Tetris")
    window.show_view(GameView())
    arcade.run()