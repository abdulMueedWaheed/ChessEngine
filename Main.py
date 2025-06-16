"""
Main.py

This file is the entry point for the chess game application. It handles the initialization of the game, the main game loop, and user interactions.

Functions:
    main: The main function that initializes the game and starts the main game loop.
    loadImages: Loads the images for the chess pieces and the board.
    loadSounds: Loads the sounds for the game.
    drawGameState: Draws the current game state on the screen.
    drawBoard: Draws the chess board on the screen.
    drawPieces: Draws the chess pieces on the board.
    drawMoveLog: Draws the move log on the screen.
    animateMove: Animates a move on the board.
    highlightSquares: Highlights the squares for the selected piece and valid moves.
    handleTerminalState: Checks if the game has ended (checkmate, stalemate, etc.).
    handleEvents: Handles user input events (mouse clicks, keyboard presses).
    handleClick: Handles mouse click events.
    playSound: Plays a sound based on the move made.
	drawTextTerminalState: Draws the text for the terminal state (checkmate, stalemate, etc.).
	drawMoveList: Draws the move log and a graph analyzing the game state.
	drawGraph: Draws a graph based on the evaluation history of the game. !!!! Incomplete!!!!
"""

import pygame as py
from enum import Enum
import matplotlib.pyplot as plt
import io
from ChessEngine import *
from SmortPart import *
from multiprocessing import Process, Queue
from DB import *

# Constants
BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSIONS = 8
SQ_SIZE = BOARD_WIDTH // DIMENSIONS
MAX_FPS = 30
IMAGES = {}
SOUNDS = {}

# Enum for game states
class GameStateEnum(Enum):
	HOME_SCREEN = 1
	PLAYING = 2
	REVIEW = 3
	SETTINGS = 4


def loadImages():
	pieces = ["wp", "wR", "wN", "wB", "wQ", "wK", "bp", "bR", "bN", "bB", "bQ", "bK"]
	for piece in pieces:
		IMAGES[piece] = py.transform.scale(py.image.load(f"ChessPieces/{piece}.png"), (SQ_SIZE, SQ_SIZE))

def loadSounds():
	SOUNDS["move"] = pygame.mixer.Sound("Sounds/move-self.mp3")
	SOUNDS["capture"] = pygame.mixer.Sound("Sounds/capture.mp3")
	SOUNDS["check"] = pygame.mixer.Sound("Sounds/in-check.mp3")
	SOUNDS["checkmate"] = pygame.mixer.Sound("Sounds/game-end.mp3")

def drawGameState(screen: py.Surface, gs: GameState, moveLogFont: py.font.SysFont):
	drawBoard(screen)
	highlightSquares(screen, gs, gs.validMoves)
	drawPieces(screen, gs.board)
	drawMoveList(screen, gs, moveLogFont)


def drawBoard(screen):
	global colors
	colors = ("white", (222, 184, 135))

	for row in range(DIMENSIONS):
		for col in range(DIMENSIONS):
			color = colors[0] if (row + col) % 2 == 0 else colors[1]
			py.draw.rect(screen, py.Color(color), (col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def drawPieces(screen, board):
	for row in range(DIMENSIONS):
		for col in range(DIMENSIONS):
			piece = board[row][col]
			if piece != "--":
				screen.blit(IMAGES[piece], (col * SQ_SIZE, row * SQ_SIZE))


def highlightSquares(screen: py.Surface, gs: GameState, validMoves: list[Move]):
	if gs.sqSelected:  # A square is selected
		row, col = gs.sqSelected

		if 0 <= row <= 7 and 0 <= col <= 7:
			piece = gs.board[row][col]
			if piece != "--" and piece[0] == ("w" if gs.whiteToMove else "b"):
				# Highlight the selected piece's square in yellow
				surface = pygame.Surface((SQ_SIZE, SQ_SIZE))
				surface.set_alpha(100)  # Transparency
				surface.fill(pygame.Color("yellow"))
				screen.blit(surface, (col * SQ_SIZE, row * SQ_SIZE))

				# Highlight valid moves for the selected piece
				for move in validMoves:
					if move.startRow == row and move.startCol == col:
						endRow, endCol = move.endRow, move.endCol
						if gs.board[endRow][endCol] == "--":  # Regular move
							# Draw a black circle
							center = (endCol * SQ_SIZE + SQ_SIZE // 2, endRow * SQ_SIZE + SQ_SIZE // 2)
							pygame.draw.circle(screen, pygame.Color("black"), center, 10)
						else:  # Capture move
							# Draw a red square
							surface.fill(pygame.Color("red"))
							screen.blit(surface, (endCol * SQ_SIZE, endRow * SQ_SIZE))


def handleClick(gs: GameState, pos, screen, clock):
	row, col = pos[1] // SQ_SIZE, pos[0] // SQ_SIZE
	
	if gs.sqSelected == (row, col) or col >= 8:  # Deselect if the same square is clicked
		gs.sqSelected = ()
		gs.playerClick = []
	
	else:
		gs.sqSelected = (row, col)
		gs.playerClick.append(gs.sqSelected)

		# If two clicks are made, attempt to make a move
		if len(gs.playerClick) == 2:
			startSq, endSq = gs.playerClick
			move = Move(startSq, endSq, gs.board)
			
			for i in range(len(gs.validMoves)):
				if move == gs.validMoves[i]:  # Check if it's a valid move
					gs.makeMove(gs.validMoves[i])
					if gs.threeMoveRule():
						gs.threeMoveRepetition = True
						gs.gameOver = True
					gs.moveMade = True
					gs.sqSelected = ()
					gs.playerClick = []

					gs.isChecked, gs.pins, gs.checks = gs.checkForPinsandChecks()
					

					animateMove(move, screen, clock, gs)

					playSound(move, gs)
			
			if not gs.moveMade:
				gs.playerClick = [gs.sqSelected]


def animateMove(move: Move, screen: py.Surface, clock, gameState: GameState):
	global colors
	coords = []
	dx = move.endRow - move.startRow
	dy = move.endCol - move.startCol
	framesPerSquare = 10
	frameCount = (abs(dx) + abs(dy)) * framesPerSquare

	for frame in range(frameCount + 1):
		r, c = (move.startRow + dx * frame / frameCount, move.startCol + dy * frame / frameCount)
		drawBoard(screen)
		drawPieces(screen, gameState.board)
		color = colors[(move.endRow + move.endCol) % 2]
		endSquare = py.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
		py.draw.rect(screen, color, endSquare)

		if move.pieceCaptured != "--":
			screen.blit(IMAGES[move.pieceCaptured], endSquare)
		
		screen.blit(IMAGES[move.pieceMoved], py.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
		py.display.flip()
		clock.tick(MAX_FPS * 4)
	

def drawTextTerminalState(screen: py.Surface, toPrint):
	font = pygame.font.SysFont("Helvetica", 32, True, False)  # Bold=True, Italic=False
	textObject = font.render(toPrint, True, pygame.Color('Black'))  # Enable anti-aliasing
	textLocation = pygame.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(
		BOARD_WIDTH / 2 - textObject.get_width() / 2, 
		BOARD_HEIGHT / 2 - textObject.get_height() / 2
	)
	screen.blit(textObject, textLocation)
	textObject = font.render(toPrint, 0, pygame.Color('Black'))
	screen.blit(textObject, textLocation.move(2, 2))


def playSound(move: Move, gs: GameState):
	if gs.isChecked:
		SOUNDS["check"].play()
	elif move.pieceCaptured == "--":
		SOUNDS["move"].play()
	elif move.pieceCaptured != "--":
		SOUNDS["capture"].play()
	

def drawMoveList(screen: py.Surface, gs: GameState, font: py.font.SysFont, scroll_offset: int = 40, max_scroll: int = 40):
	"""
	Draws the move log and a graph analyzing the game state. Adds scroll functionality and a title.

	Args:
		screen (py.Surface): The game display surface.
		gs (GameState): The current game state.
		font (py.font.SysFont): The font to render the text.
		analysis_data (list): A list of scores representing game state analysis (e.g., from evaluation function).
		scroll_offset (int): The vertical scroll offset to move through the move log.
		max_scroll (int): The maximum scroll position that restricts how far you can scroll.
	"""
	# Move log panel setup
	moveLogRect = py.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
	py.draw.rect(screen, py.Color('black'), moveLogRect)

	# Split the panel into two parts
	moveLogHeight = MOVE_LOG_PANEL_HEIGHT // 2
	moveLogRectTop = py.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, moveLogHeight)
	graphRect = py.Rect(BOARD_WIDTH, moveLogHeight, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT - moveLogHeight)

	# Title for the move log
	title_text = "Move Log"
	title_text_object = font.render(title_text, True, py.Color('White'))
	screen.blit(title_text_object, (BOARD_WIDTH + 5, 5))  # Title position

	# Draw moves in the top half with scrolling
	moveLog = gs.moveLog
	moveTexts = []
	for i in range(0, len(moveLog), 2):
		moveString = str(i // 2 + 1) + ". " + moveLog[i].getChessNotation(gs) + "  "
		if i + 1 < len(moveLog):
			moveString += moveLog[i + 1].getChessNotation(gs)
		moveTexts.append(moveString)

	# Set the vertical position to start drawing based on scroll offset
	pad_X = 5
	pad_Y = 5 - scroll_offset  # Adjust the scroll offset to move the text up or down

	# Draw each move text, applying the scroll offset
	for i in range(len(moveTexts)):
		toPrint = moveTexts[i]
		textObject = font.render(toPrint, True, py.Color('White'))  # Enable anti-aliasing
		textLocation = moveLogRectTop.move(pad_X, pad_Y)
		screen.blit(textObject, textLocation)
		pad_Y += textObject.get_height() + 2

	# Scroll bar handling (visual)
	scroll_bar_rect = py.Rect(BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH - 10, 5, 10, MOVE_LOG_PANEL_HEIGHT - 10)  # Background of scroll bar
	py.draw.rect(screen, py.Color('gray'), scroll_bar_rect)  # Scroll bar background

	# Scroll thumb
	scroll_thumb_rect = py.Rect(BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH - 10, 5 + scroll_offset, 10, 20)  # Thumb on the scroll bar
	py.draw.rect(screen, py.Color('white'), scroll_thumb_rect)  # Scroll bar thumb

	return scroll_thumb_rect, scroll_bar_rect


def handleScrollEvents(event, scroll_offset, max_scroll, scroll_thumb_rect, scroll_bar_rect):
	"""
	Handles mouse events for the scroll bar interaction.

	Args:
		event (pygame.event): The event to process.
		scroll_offset (int): Current vertical scroll offset.
		max_scroll (int): Maximum scroll offset.
		scroll_thumb_rect (pygame.Rect): Rectangle of the scroll thumb.
		scroll_bar_rect (pygame.Rect): Rectangle of the scroll bar background.

	Returns:
		int: Updated scroll offset.
	"""
	if event.type == py.MOUSEBUTTONDOWN:
		if scroll_thumb_rect.collidepoint(event.pos):  # Check if the user clicked on the scroll thumb
			dragging = True
			mouse_start_y = event.pos[1]
			offset_start = scroll_offset

	elif event.type == py.MOUSEMOTION and dragging:
		mouse_y = event.pos[1]
		new_scroll_offset = offset_start + (mouse_y - mouse_start_y)

		# Ensure scroll offset stays within bounds
		scroll_offset = max(0, min(max_scroll, new_scroll_offset))

	elif event.type == py.MOUSEBUTTONUP:
		dragging = False

	# Mouse wheel scroll
	elif event.type == py.MOUSEWHEEL:
		if event.y > 0:  # Scroll up
			scroll_offset = max(0, scroll_offset - 30)
		elif event.y < 0:  # Scroll down
			scroll_offset = min(max_scroll, scroll_offset + 30)

	return scroll_offset


def handleTerminalState(gs: GameState, screen):
	gs.gameOver = True
	if gs.checkmate:
		drawTextTerminalState(screen, f"{('White' if gs.whiteToMove else 'Black')} is in checkmate!")
		pygame.display.update()  # Refresh the display
		pygame.time.wait(3000)  # Pause for 3 seconds

	elif gs.stalemate:
		drawTextTerminalState(screen, "Stalemate!")
		pygame.display.update()  # Refresh the display
		pygame.time.wait(3000)  # Pause for 3 seconds
	
	elif gs.threeMoveRepetition:
		drawTextTerminalState(screen, "Three-move repetition!")
		pygame.display.update()  # Refresh the display
		pygame.time.wait(3000)  # Pause for 3 seconds


class HomeScreen:
    def __init__(self, screen):
        self.screen = screen
        button_width = (BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH) // 3
        button_height = BOARD_HEIGHT // 10
        x_pos = (BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH) // 3

        self.play_button_rect = py.Rect(x_pos, BOARD_HEIGHT // 3, button_width, button_height)
        self.quit_button_rect = py.Rect(x_pos, BOARD_HEIGHT // 2, button_width, button_height)
        self.settings_button_rect = py.Rect(x_pos, BOARD_HEIGHT * 2 // 3, button_width, button_height)

    def draw(self):
        self.screen.fill(py.Color("black"))
        font = py.font.Font(None, 50)

        # Title
        title = font.render("Chess Game", True, py.Color("white"))
        title_rect = title.get_rect(center=((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH) // 2, BOARD_HEIGHT // 4))
        self.screen.blit(title, title_rect)

        # Play Button
        py.draw.rect(self.screen, py.Color("green"), self.play_button_rect)
        play_text = font.render("Play", True, py.Color("black"))
        play_rect = play_text.get_rect(center=self.play_button_rect.center)
        self.screen.blit(play_text, play_rect)

        # Settings Button
        py.draw.rect(self.screen, py.Color("blue"), self.settings_button_rect)
        settings_text = font.render("Settings", True, py.Color("white"))
        settings_rect = settings_text.get_rect(center=self.settings_button_rect.center)
        self.screen.blit(settings_text, settings_rect)

        # Quit Button
        py.draw.rect(self.screen, py.Color("red"), self.quit_button_rect)
        quit_text = font.render("Quit", True, py.Color("black"))
        quit_rect = quit_text.get_rect(center=self.quit_button_rect.center)
        self.screen.blit(quit_text, quit_rect)

    def handle_event(self, event):
        if event.type == py.MOUSEBUTTONDOWN:
            if self.play_button_rect.collidepoint(event.pos):
                return "play"
            elif self.settings_button_rect.collidepoint(event.pos):
                return "settings"
            elif self.quit_button_rect.collidepoint(event.pos):
                return "quit"
        return None


class SettingsScreen:
	def __init__(self, screen):
		self.screen = screen
		self.font = py.font.Font(None, 30)

		# Button dimensions and positions
		self.button_width = 300
		self.button_height = 50
		self.button_x = (self.screen.get_width() - self.button_width) // 2
		self.spacing = 20

		# Button rectangles
		self.whiteFirstButtonRect = py.Rect(self.button_x, 100, self.button_width, self.button_height)
		self.playerOneButtonRect = py.Rect(self.button_x, 100 + self.button_height + self.spacing, self.button_width, self.button_height)
		self.playerTwoButtonRect = py.Rect(self.button_x, 100 + 2 * (self.button_height + self.spacing), self.button_width, self.button_height)
		self.flipBoardButtonRect = py.Rect(self.button_x, 100 + 3 * (self.button_height + self.spacing), self.button_width, self.button_height)
		self.backButtonRect = py.Rect(self.button_x, 100 + 4 * (self.button_height + self.spacing), self.button_width, self.button_height)

		# Default settings
		self.whiteFirst = True  # White moves first
		self.playerOneIsAI = False  # Player One is Human by default
		self.playerTwoIsAI = False  # Player Two is Human by default
		self.toFlip = False  # Board is not flipped by default

	def draw(self):
		# Fill background
		self.screen.fill(py.Color("black"))

		# Title
		title = self.font.render("Settings", True, py.Color("white"))
		title_rect = title.get_rect(center=(self.screen.get_width() // 2, 50))
		self.screen.blit(title, title_rect)

		# Draw buttons with updated text
		self._draw_button(self.whiteFirstButtonRect, "White First" if self.whiteFirst else "Black First")
		self._draw_button(self.playerOneButtonRect, "Player One: Human" if not self.playerOneIsAI else "Player One: AI")
		self._draw_button(self.playerTwoButtonRect, "Player Two: Human" if not self.playerTwoIsAI else "Player Two: AI")
		self._draw_button(self.flipBoardButtonRect, "Flip Board" if self.toFlip else "Normal Board")
		self._draw_button(self.backButtonRect, "Back")

	def _draw_button(self, buttonRect, text):
		# Draw button rectangle with cream color
		py.draw.rect(self.screen, py.Color(255, 253, 208), buttonRect)
		# Draw text on the button
		buttonText = self.font.render(text, True, py.Color("black"))
		buttonTextRect = buttonText.get_rect(center=buttonRect.center)
		self.screen.blit(buttonText, buttonTextRect)

	def handle_event(self, event):
		if event.type == py.MOUSEBUTTONDOWN:
			# Toggle settings based on which button is clicked
			if self.whiteFirstButtonRect.collidepoint(event.pos):
				self.whiteFirst = not self.whiteFirst
			elif self.playerOneButtonRect.collidepoint(event.pos):
				self.playerOneIsAI = not self.playerOneIsAI
			elif self.playerTwoButtonRect.collidepoint(event.pos):
				self.playerTwoIsAI = not self.playerTwoIsAI
			elif self.flipBoardButtonRect.collidepoint(event.pos):
				self.toFlip = not self.toFlip
			elif self.backButtonRect.collidepoint(event.pos):
				return "back"  # Return to the previous screen

		# Return the updated settings or None if no "back" event occurred
		return {
			"whiteFirst": self.whiteFirst,
			"playerOneIsAI": self.playerOneIsAI,
			"playerTwoIsAI": self.playerTwoIsAI,
			"toFlip": self.toFlip
		}

	def update(self):
		"""Redraw the screen to reflect changes."""
		self.draw()
		py.display.flip()


class ReviewMode:
	def __init__(self, gs: GameState):
		"""
		Initializes the review mode with the game state.
		
		Args:
			gs (GameState): The final game state.
		"""
		self.gs = gs
		self.moveLog = gs.moveLog  # Accessing moveLog from the GameState object
		self.current_move = 0  # Start at the first move
		self.max_move_index = len(self.moveLog) // 2  # Max move index (since each move is two turns)
		
		# Initialize font for rendering text
		self.font = py.font.SysFont("Arial", 20)  # You can change the font and size here
		
		# Initialize analysis data by evaluating each move
		self.analysis_data = self.evaluateMoves()

	def evaluateMoves(self):
		"""
		Evaluates the game state at each move and returns the analysis data (evaluation scores).
		
		Returns:
			list: A list of evaluation scores for each move.
		"""
		analysis_data = []
		
		for i in range(0, len(self.moveLog), 2):  # Iterate through the moveLog in pairs (white and black moves)
			# Make the move for white
			self.gs.makeMove(self.moveLog[i])
			score = self.evaluateGameState()
			analysis_data.append(score)
			
			if i + 1 < len(self.moveLog):
				# Make the move for black
				self.gs.makeMove(self.moveLog[i + 1])
				score = self.evaluateGameState()
				analysis_data.append(score)
		
		return analysis_data

	def evaluateGameState(self):
		return scoreBoard(self.gs)  # Assume the function `evaluateBoard` evaluates the game state

	def draw(self, screen: py.Surface):
		"""
		Draw the board and the analysis graph.
		
		Args:
			screen (py.Surface): The game display surface.
		"""
		# Draw the board
		self.gs.drawBoard(screen)
		
		# Draw the move and evaluation graph
		self.drawMoveList(screen)

	def drawMoveList(self, screen: py.Surface):
		"""
		Draw the move log and evaluation scores.
		
		Args:
			screen (py.Surface): The game display surface.
		"""
		# Display the move and evaluation log
		moveLogRect = py.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
		py.draw.rect(screen, py.Color('black'), moveLogRect)

		# Draw the moves and evaluation scores
		moveTexts = []
		for i in range(0, len(self.moveLog), 2):
			moveString = str(i // 2 + 1) + ". " + self.moveLog[i].getChessNotation(self.gs) + "  "
			if i + 1 < len(self.moveLog):
				moveString += self.moveLog[i + 1].getChessNotation(self.gs)
			
			# Add evaluation score for the move
			moveString += f"  ({self.analysis_data[i]})"
			
			moveTexts.append(moveString)
		
		# Render the move texts
		pad_X = 5
		pad_Y = 5
		for text in moveTexts:
			textObject = self.font.render(text, True, py.Color('White'))
			textLocation = moveLogRect.move(pad_X, pad_Y)
			screen.blit(textObject, textLocation)
			pad_Y += textObject.get_height() + 2



def main():
	py.init()
	screen = py.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
	py.display.set_caption("Chess")
	clock = py.time.Clock()
	playerOne = True  # Human is white
	playerTwo = False  # AI is black
	toFlip = True

	WhiteFirst = True
	Computing = False  # If True, the AI is computing its move
	moveFindingProcess = None
	evalHistory = []
	jsonStorage = BestMoveFinder("best_moves.json")

	# Game states
	state = GameStateEnum.HOME_SCREEN
	home_screen = HomeScreen(screen)
	settings_screen = SettingsScreen(screen)
	loadImages()
	loadSounds()

	gs = None
	running = True
	moveLogFont = py.font.SysFont("Arial", 20, True, False)

	while running:
		for event in py.event.get():
			if event.type == py.QUIT:
				running = False

			if state == GameStateEnum.HOME_SCREEN:
				action = home_screen.handle_event(event)
				if action == "play":
					state = GameStateEnum.PLAYING
					gs = GameState()
					gs.whiteToMove = WhiteFirst
					humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
				
				elif action == "settings":
					state = GameStateEnum.SETTINGS
				
				elif action == "quit":
					running = False

			elif state == GameStateEnum.SETTINGS:
				result = settings_screen.handle_event(event)
				if result == "back":
					state = GameStateEnum.HOME_SCREEN
				else:
					WhiteFirst = result["whiteFirst"]
					playerOne = result["playerOneIsAI"]
					playerTwo = result["playerTwoIsAI"]
					toFlip = result["toFlip"]

			elif state == GameStateEnum.PLAYING:

				if event.type == py.MOUSEBUTTONDOWN:
					if not gs.gameOver and humanTurn:
						pos = py.mouse.get_pos()  # Get mouse position
						handleClick(gs, pos, screen, clock)

				elif event.type == py.KEYDOWN:
					if event.key == py.K_z and len(gs.moveLog) > 0:  # Undo move
						gs.undoMove()
						gs.moveMade = True

					elif event.key == py.K_r:  # Restart the game
						gs = GameState()
			

		# Game logic outside the event loop
		if state == GameStateEnum.PLAYING and not gs.gameOver:
			humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)

			if not humanTurn and not gs.gameOver:
				if not Computing:
					validMoves = gs.validMoveIfCheck()
					print(f"Valid moves: {[move.getChessNotation(gs) for move in validMoves]}")
					if len(validMoves) == 0:
						handleTerminalState(gs, screen)
						break

					Computing = True
					print("Computing AI move...")
					returnQueue = Queue()
					moveFindingProcess = Process(target=findBestMove, args=(gs, validMoves, returnQueue, jsonStorage))

					moveFindingProcess.start()
					moveFindingProcess.join()  # Wait for the process to complete

					if not returnQueue.empty():
						AIMove = returnQueue.get()
						if AIMove:
							print(f"AI Move: {AIMove.getChessNotation(gs)}")
							gs.makeMove(AIMove)
							if gs.threeMoveRule():
								gs.threeMoveRepetition = True
								gs.gameOver = True
							
							gs.isChecked, gs.pins, gs.checks = gs.checkForPinsandChecks()
							gs.moveMade = True
							animateMove(gs.moveLog[-1], screen, clock, gs)
							playSound(AIMove, gs)
						else:
							print("Error: AIMove is None")
					else:
						print("Error: returnQueue is empty")

					Computing = False
					moveFindingProcess.terminate()

			if gs.moveMade:
				gs.validMoves = gs.validMoveIfCheck()
				if len(gs.validMoves) == 0:
					handleTerminalState(gs, screen)
					break
				
				gs.moveMade = False

		# Drawing the game state
		screen.fill(py.Color("white"))
		if state == GameStateEnum.HOME_SCREEN:
			home_screen.draw()
		elif state == GameStateEnum.PLAYING:
			drawGameState(screen, gs, moveLogFont)
		elif state == GameStateEnum.SETTINGS:
			settings_screen.draw()
		elif state == GameStateEnum.REVIEW:
			drawGameState(screen, gs, moveLogFont)
		
		
		if state == GameStateEnum.PLAYING and gs.gameOver:
			state = GameStateEnum.REVIEW
			gs.board = [
				["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
				["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
				["--", "--", "--", "--", "--", "--", "--", "--"],
				["--", "--", "--", "--", "--", "--", "--", "--"],
				["--", "--", "--", "--", "--", "--", "--", "--"],
				["--", "--", "--", "--", "--", "--", "--", "--"],
				["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
				["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
			]
			review_screen = ReviewMode(gs)

		if toFlip:
			py.display.flip()
		clock.tick(MAX_FPS)




if __name__ == "__main__":
	main()
