import arcade, enum, random
from pyglet.math import Vec2

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

    def get_opposite(self):
        return {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT
        }[self]

class Tetromino:
    """
    Tetromino with shape and color.

    Also handles origin and rotations.
    """

    def __init__(self, shape, color):
        self.shape = shape
        self.color = color

    @staticmethod
    def get_cells_with_color(cells, color):
        return [[color if x != '_' else x for x in row] for row in cells]

    @staticmethod
    def get_all():
        # Here we define each Tetromino using 2-dimensional lists of characters:
        # _ = Empty space
        # T = Filled cell
        # O = Origin point (This is used later for producing the rotated versions of tetrominoes)

        I = Tetromino([['T'],
                       ['O'],
                       ['T'],
                       ['T']],
                      color=(0, 209, 146))

        J = Tetromino([['_', 'T'],
                       ['_', 'O'],
                       ['T', 'T']],
                      color=(48, 105, 152))

        L = Tetromino([['T', '_'],
                       ['O', '_'],
                       ['T', 'T']],
                      color=(208, 112, 56))

        O = Tetromino([['T', 'T'],
                       ['T', 'T']],
                      color=(221, 225, 0))

        S = Tetromino([['_', 'O', 'T'],
                       ['T', 'T', '_']],
                      color=(123, 209, 46))

        T = Tetromino([['T', 'O', 'T'],
                       ['_', 'T', '_']],
                      color=(186, 0, 166))

        Z = Tetromino([['T', 'T', '_'],
                       ['_', 'O', 'T']],
                      color=(202, 7, 67))

        return I, J, L, O, S, T, Z

    def get_origin(self, rotation: Direction = Direction.UP) -> Vec2:
        for y, row in enumerate(self.rotate(rotation)[::-1]):
            for x, cell in enumerate(row):
                if cell == 'O':
                    return Vec2(x, y)

        return Vec2(0, 0)

    def rotate(self, rotation: Direction):
        """Rotates the tetromino shape in a given direction and returns the rotated shape."""

        def transpose(matrix):
            """
            Transposes the matrix, this has the effect of turning the matrix on it's side:
            columns become rows, rows become columns.
            """
            transposed = [['_' for _ in range(len(matrix))] for _ in range(len(matrix[0]))]

            for y, row in enumerate(matrix):
                for x, cell in enumerate(row):
                    transposed[x][y] = cell

            return transposed
        
        return {
            Direction.UP: self.shape,
            Direction.DOWN: [row[::-1] for row in self.shape[::-1]], # Reverse the rows and then reverse each row (180 degrees)
            Direction.RIGHT: transpose(self.shape[::-1]), # Reverse the rows first, then transpose for 90-degree clockwise rotation
            Direction.LEFT: transpose(self.shape)[::-1] # Transpose and then reverse the rows for 90-degree counter-clockwise rotation
        }[rotation]

class Piece:
    """A piece before it is placed on the board."""

    def __init__(self, tetromino, position, rotation=Direction.UP, is_ghost_piece=False):
        self.tetromino: Tetromino = tetromino
        self.position: Vec2 = position
        self.rotation: Vec2 = rotation
        self.is_ghost_piece = is_ghost_piece

    def is_colliding(self, board):
        """Is the piece colliding with the board?"""

        rotated_shape = self.tetromino.rotate(self.rotation)
        origin = self.tetromino.get_origin(self.rotation)

        # Check each cell of the rotated piece
        for y, row in enumerate(rotated_shape[::-1]):
            for x, cell in enumerate(row):
                # Check for any filled cell (not empty)
                if cell != '_':
                    x_pos, y_pos = self.position - origin + Vec2(x, y)

                    # Check if the position is out of bounds (colliding with the wall)
                    if not board.is_within_bounds(x_pos, y_pos):
                        return True

                    # Check if the cell on the board is occupied
                    if board.cells[y_pos][x_pos] != '_':
                        return True

        # Piece does not collide with anything on the board
        return False

    def place(self, board):
        """Inserts the piece into the given board."""

        rotated_shape = self.tetromino.rotate(self.rotation)
        origin = self.tetromino.get_origin(self.rotation)

        for y, row in enumerate(rotated_shape[::-1]):
            for x, cell in enumerate(row):
                if cell != '_':
                    x_pos, y_pos = self.position -origin + Vec2(x, y)

                    # Assign the color of the tetromino
                    board.cells[y_pos][x_pos] = self.tetromino.color

class Board:
    """Stores the game board along with some management things."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [['_'] * width for _ in range(height)]
    
    def get_clearable_rows(self):
        """Returns a list of row indices that are ready to be cleared."""

        rows = []
        for y, row in enumerate(self.cells):
            if '_' not in row:
                rows.append(y)
        
        return rows
    
    def is_within_bounds(self, x, y):
        """Check if the coordinates (x, y) are within the bounds of the board."""

        return 0 <= x < len(self.cells[0]) and 0 <= y < len(self.cells)

    def clear_row(self, row):
        self.cells.pop(row) # Remove the specified row
        new_row = ['_'] * len(self.cells[0]) # Create a new row filled with '_'

        # TODO: clarify the bottom = the top
        self.cells.append(new_row) # Append the new row at the bottom

class GameView(arcade.View):
    def __init__(self):
        super().__init__()

        self.keys = None
        self.last_keys = None
        self.board = None
        self.falling_piece = None
        self.ghost_piece = None
        self.sprites = None

    def setup(self):
        # This is the set of keys that are pressed this frame
        self.keys = set()

        # This is the set of keys that were pressed last frame, and it is used for comparison between the two,
        # to tell if a key was just pressed or is being held down (so that actions don't repeat too much)
        self.last_keys = set()
    
        # Some actions we do want to repeat, but with a reasonable, FPS-independent delay,
        # instead of every frame. This dictionary maps held keys to the time left (in seconds) before they activate again.
        self.repeat_delays = {}

        self.gravity_clock = arcade.clock.Clock()
        self.last_gravity_application = 0

        # TODO: verify this comment is correct
        # Here is our board, it is mostly just a wrapper around a 2-dimensional list of characters.
        # The falling piece and it's "Ghost Piece" (shadow) are the only instances of the Piece class in the game,
        # once you place your piece it just gets added to the Board, this simplifies collision and clearing lines.
        self.board = Board(width=10, height=20)

        # The falling piece is the piece the player currently has control over, there is only one at a time
        self.falling_piece = self.spawn_piece()

        self.sprites = arcade.SpriteList()
        self.update_sprite_list()

    def on_key_press(self, key, modifiers):
        self.keys.add(key)

    def on_key_release(self, key, modifiers):
        self.keys.discard(key)
    
    def rotate(self, d: Direction):
        # Apply the intended rotation for either direction
        self.falling_piece.rotation = self.falling_piece.rotation.rotate(clockwise=d is Direction.RIGHT)

        # This code is my implementation of so-called "Wall Kicking",
        # when a rotation causes a piece to intersect a wall, it needs to be "pushed" out of it behind the scenes..
        if self.falling_piece.is_colliding(self.board):
            # Define a helper function for moving a piece in a direction a number of times.
            def move_piece(direction, distance):
                for _ in range(distance):
                    self.falling_piece.position += direction

            # For every direction there is, find out how much distance it takes in that direction,
            # until the piece no longer collides (if any) and then record that in a dictionary
            distance_needed = {}
            for direction in Direction:
                for distance in range(1, 4):
                    move_piece(direction.value, distance)

                    if not self.falling_piece.is_colliding(self.board):
                        distance_needed[direction] = distance
                        # Move the piece back to its original position
                        move_piece(direction.get_opposite().value, distance)
                        break

                    # Move back to the original position if still colliding
                    move_piece(direction.get_opposite().value, distance)

            # If any directions were valid escape routes..
            if distance_needed:
                # Pick the shortest one,
                # using the 'key' parameter so min() compares the distances instead of the keys
                lowest_direction = min(distance_needed, key=distance_needed.get)

                # Escape!
                move_piece(lowest_direction.value, distance_needed[lowest_direction])
            else:
                # If there is no escape, undo the original rotation, we will not rotate at all.
                # (Notice the inversion of the clockwise argument)
                self.falling_piece.rotation = self.falling_piece.rotation.rotate(clockwise=d is Direction.LEFT)
    
    def move(self, d: Direction):
        self.falling_piece.position += d.value

        # If this move causes a collision, reverse it
        if self.falling_piece.is_colliding(self.board):
            self.falling_piece.position += d.get_opposite().value

    def drop(self, d: Direction):
        # Move it down until it hits something
        while not self.falling_piece.is_colliding(self.board):
            self.falling_piece.position += Direction.DOWN.value

        # Then move it up to get it out of that thing
        self.falling_piece.position += Direction.UP.value

        # Place it
        self.falling_piece.place(self.board)

        # Spawn the next piece
        self.falling_piece = self.spawn_piece()
    
    def on_update(self, delta_time):
        self.handle_gravity(delta_time)

        # Map keys to actions, so the player can call them with their keyboard!
        key_actions = {
            arcade.key.UP: (self.rotate, Direction.RIGHT, None),
            arcade.key.DOWN: (self.rotate, Direction.LEFT, None),
            arcade.key.LEFT: (self.move, Direction.LEFT, 0.13),
            arcade.key.RIGHT: (self.move, Direction.RIGHT, 0.13),
            arcade.key.SPACE: (self.drop, None, None)
        }

        # Loop over all the actions we have in the game
        for key, (action, direction, repeat_after) in key_actions.items():
            # Retrieve the active delay for this key, defaulting to 0
            delay = self.repeat_delays.get(key, 0)

            if delay == None:
                delay = 0

            # Loop over all the pressed keys
            if key in self.keys:
                # Initialize delay to 0 if not set
                delay = self.repeat_delays.get(key, 0)

                # If the key was just pressed or the action's delay has run out
                if key not in self.last_keys or (repeat_after is not None and delay <= 0):
                    action(direction)
                    
                    self.update_sprite_list()

                    self.repeat_delays[key] = repeat_after # Reset the delay
                else:
                    # Decrement the delay in a frame-rate independent way, ensuring delay is never negative
                    self.repeat_delays[key] = max(0, delay - delta_time) if delay is not None else 0

        # Store the pressed keys on this frame for the next frame to compare to
        self.last_keys = self.keys.copy()
    
    def update_sprite_list(self):
        self.sprites.clear()

        def add_cells(cells, position, add_background=False):
            cell_size = Vec2(self.width // self.board.width,
                             self.height // self.board.height)
            
            for y, row in enumerate(cells):
                for x, cell in enumerate(row):
                    if cell == "_":
                        if not add_background:
                            continue
                        else:
                            color = (8, 6, 27)
                    else:
                        color = cell

                    center = Vec2(((position.x + x) * (cell_size.x)) + cell_size.x / 2,
                                  ((position.y + y) * (cell_size.y)) + cell_size.y / 2)

                    cell_sprite = arcade.SpriteSolidColor(cell_size.x - 5, cell_size.y - 5, center.x, center.y, color)

                    self.sprites.append(cell_sprite)

        def add_piece(piece):
            if not piece.is_ghost_piece:
                color = piece.tetromino.color
            else:
                color = (18, 18, 39)

            add_cells(Tetromino.get_cells_with_color(piece.tetromino.rotate(piece.rotation)[::-1], color),
                      piece.position - piece.tetromino.get_origin(piece.rotation))

        add_cells(self.board.cells, Vec2(0, 0), add_background=True)
        add_piece(self.create_ghost_piece())
        add_piece(self.falling_piece)
    
    def on_draw(self):
        # Clear the screen
        self.clear()
        self.sprites.draw(pixelated=True)
    
    def spawn_piece(self) -> Piece:
        """Creates a new random piece at the top of the board and returns it."""

        tetromino = random.choice(Tetromino.get_all())

        new_piece = Piece(tetromino, Vec2(x=self.board.width // 2,
                                          y=self.board.height - (len(tetromino.shape) - tetromino.get_origin(Direction.UP).y)))

        return new_piece
    
    def create_ghost_piece(self) -> Piece:
        ghost_piece = Piece(tetromino=self.falling_piece.tetromino,
                                 position=Vec2(self.falling_piece.position.x, self.falling_piece.position.y),
                                 rotation=self.falling_piece.rotation,
                                 is_ghost_piece=True)
        
        while not ghost_piece.is_colliding(self.board):
            ghost_piece.position += Direction.DOWN.value
        
        ghost_piece.position += Direction.UP.value

        return ghost_piece
    
    def handle_gravity(self, delta_time):
        self.gravity_clock.tick(delta_time)

        if self.gravity_clock.ticks_since(self.last_gravity_application) * delta_time > 1:
            self.falling_piece.position += Direction.DOWN.value

            if self.falling_piece.is_colliding(self.board):
                self.falling_piece.position += Direction.UP.value

                self.falling_piece.place(self.board)
                self.falling_piece = self.spawn_piece()
            
            self.update_sprite_list()

            self.last_gravity_application = self.gravity_clock.tick_count

# You could put this code outside of the "if __name__ == "__main__"" block
# but this theoretically allows you to load this file without starting the game
# allowing for other modules to use classes from this, etc.
# It's entirely useless in this case, but I thought I'd leave it in.
if __name__ == "__main__":
    window = arcade.Window(400, 600, "Simple Tetris", resizable=True)
    start_view = GameView()
    window.show_view(start_view)
    start_view.setup()
    arcade.run()