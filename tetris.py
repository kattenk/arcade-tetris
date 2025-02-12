import arcade
import random
from enum import Enum

class Position:
    """Position (x, y) on the board.

    Also used for relative positions and Direction.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def move(self, by):
        self.x += by.x
        self.y += by.y
    
    def add(self, other):
        return Position(self.x + other.x, self.y + other.y)
    
    def subtract(self, by):
        return Position(self.x - by.x, self.y - by.y)
    
    def copy(self):
        return Position(self.x, self.y)
    
    # This is for unpacking Positions like tuples
    def __iter__(self):
        return iter((self.x, self.y))


class Direction(Enum):
    """Direction in a bottom-left coordinate system."""
    UP = Position(0, 1)
    RIGHT = Position(1, 0)
    DOWN = Position(0, -1)
    LEFT = Position(-1, 0)

    def rotate(self, clockwise=True):
        return list(Direction)[(list(Direction).index(self) + (1 if clockwise else -1)) % len(list(Direction))]

    def get_opposite(self):
        opposite_directions = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT
        }

        return opposite_directions[self]


class Tetromino:
    """Tetromino with shape and color.

    Also handles origin and rotations.
    """

    def __init__(self, shape, color):
        self.shape: list[list[str]] = shape
        self.color: tuple[int, int, int] = color

    def get_origin(self, rotation: Direction = Direction.UP) -> Position:
        for y, row in enumerate(self.rotate(rotation)[::-1]):
            for x, cell in enumerate(row):
                if cell == 'O':
                    return Position(x, y)

        return Position(0, 0)

    def rotate(self, rotation: Direction):
        """ Rotates the tetromino shape in a given direction and returns the rotated shape """

        def transpose(matrix):
            """
            Transposes the matrix, this has the effect of turning the matrix on it's side.
            Columns become rows, rows become columns.
            """
            transposed = [['_' for _ in range(len(matrix))] for _ in range(len(matrix[0]))]

            for y, row in enumerate(matrix):
                for x, cell in enumerate(row):
                    transposed[x][y] = cell

            return transposed

        if rotation is Direction.UP:
            return self.shape

        if rotation is Direction.DOWN:
            # Reverse the rows and then reverse each row (180 degrees)
            return [row[::-1] for row in self.shape[::-1]]

        if rotation is Direction.RIGHT:
            # Reverse the rows first, then transpose for 90-degree clockwise rotation
            reversed_shape = self.shape[::-1]
            return transpose(reversed_shape)

        if rotation is Direction.LEFT:
            # Transpose and then reverse the rows for 90-degree counter-clockwise rotation
            transposed_shape = transpose(self.shape)
            return transposed_shape[::-1]

    @staticmethod
    def get_all():
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


class Piece:
    """A piece before it is placed on the board."""

    def __init__(self, tetromino, position, rotation=Direction.UP, is_ghost_piece=False):
        self.tetromino = tetromino
        self.position = position
        self.rotation = rotation
        self.is_ghost_piece = is_ghost_piece

    def draw(self, game):
        rotated_shape = self.tetromino.rotate(self.rotation)
        origin = self.tetromino.get_origin(self.rotation)

        if self.is_ghost_piece:
            color = (19, 19, 40)  # Hard-code a color for the ghost piece
        else:
            color = self.tetromino.color

        # Here we pass the shape with a reversed row ordering due to how I defined my shapes
        # to look right in the editor (top-left coordinate system)
        # whereas Arcade uses a bottom-right coordinate system so we do this to convert.
        game.draw_cells(rotated_shape[::-1], self.position.subtract(origin), color)

    def is_colliding(self, board):
        rotated_shape = self.tetromino.rotate(self.rotation)
        origin = self.tetromino.get_origin(self.rotation)

        # Check each cell of the rotated piece
        for y, row in enumerate(rotated_shape[::-1]):
            for x, cell in enumerate(row):
                # Check for any filled cell (not empty)
                if cell != '_':
                    x_pos, y_pos = self.position.subtract(origin).add(Position(x, y))

                    # Check if the position is out of bounds
                    if not board.is_within_bounds(x_pos, y_pos):
                        return True

                    # Check if the cell on the board is occupied
                    if board.cells[y_pos][x_pos] != '_':
                        return True

        # Piece does not collide with anything on the board
        return False

    def place(self, board):
        """ Inserts the piece into the given board """
        rotated_shape = self.tetromino.rotate(self.rotation)
        origin = self.tetromino.get_origin(self.rotation)

        for y, row in enumerate(rotated_shape[::-1]):
            for x, cell in enumerate(row):
                if cell != '_':
                    x_pos, y_pos = self.position.subtract(origin).add(Position(x, y))
                    board.cells[y_pos][x_pos] = self.tetromino.color  # Assign the color of the tetromino

        game.clear_rows()

    def fall(self, game):
        """ Moves the piece down 1, if it touches something it will automatically place itself into the board """
        self.position.move(Direction.DOWN.value)

        if self.is_colliding(game.board):
            self.position.move(Direction.UP.value)
            self.place(game.board)

            # Sloppy way to do this I guess, but it works
            game.falling_piece = game.spawn_piece()
            game.update_ghost_piece()

    def drop(self, board, place=True):
        """ Drops the piece until it hits something, then optionally places it """
        # Move the piece down until it collides with something
        while not self.is_colliding(board):
            self.position.move(Direction.DOWN.value)

        # Then move it up 1 to get it out of that thing
        self.position.move(Direction.UP.value)

        # Then place it if wanted
        if place:
            self.place(board)


class Board:
    """Tetris board representation."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [['_'] * width for _ in range(height)]
    
    def draw(self, game):
        game.draw_cells(self.cells, draw_background=True)
    
    def get_clearable_rows(self) -> list[int]:
        rows = []
        for y, row in enumerate(self.cells):
            if '_' not in row:
                rows.append(y)
        
        return rows
    
    def is_within_bounds(self, x, y):
        """Check if the coordinates (x, y) are within the bounds of the board."""
        return 0 <= x < len(self.cells[0]) and 0 <= y < len(self.cells)

    def clear_row(self, row):
        # Remove the specified row
        self.cells.pop(row)
        
        # Create a new row filled with '_'
        new_row = ['_'] * len(self.cells[0])
        
        # Append the new row at the bottom
        self.cells.append(new_row)


class Game(arcade.Window):
    """Main Arcade Tetris game class."""
    def __init__(self):
        super().__init__(width=400, height=600, title='Simple Tetris', antialiasing=False, resizable=True)

        # This is the set of keys that are pressed this frame
        self.keys = set()

        # This is the set of keys that were pressed last frame, and it is used for comparison between the two,
        # to tell if a key was just pressed or is being held down (so that actions don't repeat too much)
        self.last_keys = set()

        # Some actions we do want to repeat, but with a reasonable, FPS-independent delay,
        # instead of every frame. This dictionary maps held keys to the time left (in seconds) before they activate again.
        self.repeat_delays = {}

        # To create our game board we use the Board class defined later in the file,
        # it is mostly just a wrapper around a 2-dimensional list of characters.
        # The falling piece and it's "Ghost Piece" (shadow) are the only actual instances of the Piece class in the game,
        # once you place your piece it just gets added to the Board.
        # this simplifies collision and clearing lines a ton..
        self.board = Board(width=10, height=20)

        # Initialize stats
        self.score = 0
        self.lines = 0

        # Dictionary of number of lines cleared in one move -> score added
        self.score_rewards = {
            1: 100,
            2: 300,
            3: 500,
            4: 800  # <-- Tetris!!!
        }

        # Fall interval starts out at 1 second,
        # this is reduced as the score increases, until it stops at min_fall_interval
        self.fall_interval = 1.0
        self.min_fall_interval = 0.3

        self.fall_increase_threshold = 1000
        self.fall_increase_rate = 0.05

        # Keep track of how much time (in seconds) is left before the piece falls again
        self.fall_timer = self.fall_interval

        # Is the game over yet...
        self.game_over = False

        # Create the first piece
        self.falling_piece = self.spawn_piece()

        # This is the "Ghost Piece", the "shadow" of the falling piece that shows you where it will land,
        # to achieve this I simply added a field to the Piece class (is_ghost_piece) to handle this functionality
        self.ghost_piece = Piece(self.falling_piece.tetromino,
                                 # Use the falling pieces Tetromino, since Tetrominoes don't change it's safe to use the direct reference
                                 self.falling_piece.position.copy(),
                                 # use copy() for the Position as using a reference to the position would not allow the ghost piece to have a separate position.
                                 is_ghost_piece=True)

        # Do the initial dropping of the ghost piece (moving it down until it hits the floor)
        # Notice the place=False argument, we don't want the ghost piece actually being added to the board..
        self.ghost_piece.drop(self.board, place=False)

    # This is the main update method, this is where the game logic happens,
    # Arcade will call this method for us more than 60 times a second.
    # "time_delta" is the amount of time in seconds since the previous frame (very important for any kind of timing)
    def on_update(self, time_delta):
        if self.game_over:
            return

        # Apply gravity to the falling piece
        if self.fall_timer <= 0:
            self.falling_piece.fall(self)
            self.fall_timer = self.fall_interval
        else:
            self.fall_timer -= time_delta

        # Move action
        def move(d: Direction):
            self.falling_piece.position.move(d.value)

            if self.falling_piece.is_colliding(self.board):
                self.falling_piece.position.move(d.get_opposite().value)

        # Rotate action
        def rotate(d: Direction):
            # Apply the intended rotation for either direction
            self.falling_piece.rotation = self.falling_piece.rotation.rotate(clockwise=d is Direction.RIGHT)

            # This code is my implementation of so-called "Wall Kicking",
            # when a rotation causes a piece to intersect a wall, it needs to be "pushed" out of it behind the scenes..
            if self.falling_piece.is_colliding(self.board):
                # Define a helper function for moving a piece in a direction a number of times.
                def move_piece(direction, distance):
                    for _ in range(distance):
                        self.falling_piece.position.move(direction)

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

        # Drop action (It doesn't have a direction but takes 'd' anyway because I'm lazy and Python isn't very clean with HOFs)
        def drop(d):
            # This method will move the piece down until it touches the ground, then move it up 1 cell, then add it to the board.
            self.falling_piece.drop(self.board, place=True)

            # Spawn us a new piece
            self.falling_piece = self.spawn_piece()

        # Map keys to these actions, so the user can call them with their keyboard!
        key_actions = {
            arcade.key.UP: (rotate, Direction.RIGHT, None),
            arcade.key.DOWN: (rotate, Direction.LEFT, None),
            arcade.key.LEFT: (move, Direction.LEFT, 0.13),
            arcade.key.RIGHT: (move, Direction.RIGHT, 0.13),
            arcade.key.SPACE: (drop, None, None)
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
                    self.update_ghost_piece()  # Update the ghost piece
                    self.repeat_delays[key] = repeat_after  # Reset the delay
                else:
                    # Decrement the delay in a frame-rate independent way, ensuring delay is never negative
                    self.repeat_delays[key] = max(0, delay - time_delta) if delay is not None else 0

        # Store the pressed keys on this frame for the next frame to compare to
        self.last_keys = self.keys.copy()

    def on_draw(self):
        self.clear()

        if self.game_over:
            arcade.draw_text(
                "Game Over",
                self.width // 2,
                self.height // 2,
                arcade.color.WHITE,
                35,
                anchor_x="center",
                anchor_y="center",
            )
            return

        self.board.draw(self)
        self.ghost_piece.draw(self)
        self.falling_piece.draw(self)
        self.draw_grid()

    def draw_grid(self):
        cell_width = self.width / self.board.width
        cell_height = self.height / self.board.height

        # Loop through each cell in the grid
        for y in range(self.board.height + 1):  # +1 for the bottom edge
            for x in range(self.board.width + 1):  # +1 for the right edge
                # Calculate the position for the rectangle outline
                pos_x = x * cell_width
                pos_y = y * cell_height

                # Draw the rectangle outline
                arcade.draw_rect_outline(
                    arcade.Rect(
                        left=x * cell_width,
                        right=(x + 1) * cell_width,
                        bottom=y * cell_height,
                        top=(y + 1) * cell_height,
                        width=cell_width,
                        height=cell_height,
                        x=x,
                        y=y,
                    ),
                    arcade.color.BLACK,
                    5,
                )

                # Draw the circle at the center
                arcade.draw_circle_filled(pos_x, pos_y, 5, arcade.color.BLACK)

    def draw_cells(self, cells, position=Position(0, 0), color=None, draw_background=False):
        """ Draws a 2D list of cells onto the screen, this method is used to draw both the pieces and the board. """
        cell_width = self.width / self.board.width
        cell_height = self.height / self.board.height

        for y, row in enumerate(cells):
            for x, cell in enumerate(row):
                # Find out where on the screen to draw this cell,
                # by adding the position offset passed to this method to the position of the current cell in the matrix
                # Arcade draws rectangles from the center, so we must adjust for that as well.
                center_x = ((position.x + x) * cell_width) + (cell_width / 2)
                center_y = ((position.y + y) * cell_height) + (cell_height / 2)

                if not color and draw_background and cell == '_':
                    draw_color = (7, 7, 30)  # <-- This color is for background tiles..
                elif cell != '_':
                    draw_color = color if color else cell
                else:
                    continue

                # Draw the rectangle for this cell
                arcade.draw_rect_filled(arcade.Rect(left=center_x - cell_width / 2,
                                                    right=center_x + cell_width / 2,
                                                    bottom=center_y - cell_height / 2,
                                                    top=center_y + cell_height / 2,
                                                    width=cell_width,
                                                    height=cell_height,
                                                    x=center_x,
                                                    y=center_y), draw_color)

    # Arcade will call these handler functions when there is a key event
    def on_key_press(self, key, modifiers):
        self.keys.add(key)

    def on_key_release(self, key, modifiers):
        self.keys.discard(key)

    def spawn_piece(self) -> Piece:
        """ Creates a new random piece at the top of the board and returns it """
        tetromino = random.choice(Tetromino.get_all())
        x = self.board.width // 2
        y = self.board.height - (len(tetromino.shape) - tetromino.get_origin(Direction.UP).y)
        new_piece = Piece(tetromino, Position(x, y))

        if new_piece.is_colliding(self.board):
            self.game_over = True

        # Return the piece regardless of weather the game is over or not to prevent errors
        return new_piece

    # This function is kind of messy I guess, it gets called when something happens that might cause a row clear.
    # it handles clearing the rows as well as adding score
    def clear_rows(self):
        if len(self.board.get_clearable_rows()) != 0:
            self.score += self.score_rewards[len(self.board.get_clearable_rows())]

        # Do this in reverse to prevent issues with the index changing meaning as the rows are being cleared.
        # It seems to work?
        for row in sorted(self.board.get_clearable_rows(), reverse=True):
            self.board.clear_row(row)
            self.lines += 1

        # Calculate how many thresholds have been crossed
        thresholds_crossed = self.score // self.fall_increase_threshold

        # Update the fall interval
        new_fall_interval = 1 - (thresholds_crossed * self.fall_increase_rate)

        # Clamp the fall interval to the minimum value
        self.fall_interval = max(new_fall_interval, self.min_fall_interval)

        # Finally, update the stats in the window title
        self.update_caption()

    def update_ghost_piece(self):
        self.ghost_piece.rotation = self.falling_piece.rotation
        self.ghost_piece.position = self.falling_piece.position.copy()
        self.ghost_piece.tetromino = self.falling_piece.tetromino
        self.ghost_piece.drop(self.board, place=False)

    def update_caption(self):
        """ Updates the window title to reflect the current game stats """
        self.set_caption(f'Simple Tetris - Lines: {self.lines} Score: {self.score}')


# You could put this code outside of the "if __name__ == "__main__"" block
# but this theoretically allows you to load this file without starting the game
# allowing for other modules to use classes from this, etc.
# It's entirely useless in this case, but I thought I'd leave it in.
if __name__ == "__main__":
    game = Game()
    arcade.run()
