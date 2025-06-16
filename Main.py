import pygame as py
from enum import Enum
import matplotlib.pyplot as plt
import io
from ChessEngine import *
from SmortPart import *

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


def loadImages():
	pieces = ["wp", "wR", "wN", "wB", "wQ", "wK", "bp", "bR", "bN", "bB", "bQ", "bK"]
	for piece in pieces:
		IMAGES[piece] = py.transform.scale(py.image.load(f"ChessPieces/{piece}.png"), (SQ_SIZE, SQ_SIZE))

def loadSounds():
	SOUNDS["move"] = pygame.mixer.Sound("Sounds/move-self.mp3")
	SOUNDS["capture"] = pygame.mixer.Sound("Sounds/capture.mp3")
	SOUNDS["check"] = pygame.mixer.Sound("Sounds/in-check.mp3")
	SOUNDS["checkmate"] = pygame.mixer.Sound("Sounds/game-end.mp3")

def drawGameState(screen: py.Surface, gs: GameState, moveLogFont: py.font.SysFont, evalHistory: list):
	drawBoard(screen)
	highlightSquares(screen, gs, gs.validMoves)
	drawPieces(screen, gs.board)
	drawMoveList(screen, gs, moveLogFont, evalHistory)


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
	

def drawMoveList(screen: py.Surface, gs: GameState, font: py.font.SysFont, analysis_data: list):
	"""
	Draws the move log and a graph analyzing the game state.

	Args:
		screen (py.Surface): The game display surface.
		gs (GameState): The current game state.
		font (py.font.SysFont): The font to render the text.
		analysis_data (list): A list of scores representing game state analysis (e.g., from evaluation function).
	"""
	# Move log panel setup
	moveLogRect = py.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
	py.draw.rect(screen, py.Color('black'), moveLogRect)

	# Split the panel into two parts
	moveLogHeight = MOVE_LOG_PANEL_HEIGHT // 2
	moveLogRectTop = py.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, moveLogHeight)
	graphRect = py.Rect(BOARD_WIDTH, moveLogHeight, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT - moveLogHeight)

	# Draw moves in the top half
	moveLog = gs.moveLog
	moveTexts = []

	for i in range(0, len(moveLog), 2):
		moveString = str(i // 2 + 1) + ". " + moveLog[i].getChessNotation(gs) + "  "
		if i + 1 < len(moveLog):
			moveString += moveLog[i + 1].getChessNotation(gs)
		moveTexts.append(moveString)
		#drawGraph(screen, graphRect, analysis_data)
	

	pad_X = 5
	pad_Y = 5
	for i in range(len(moveTexts)):
		toPrint = moveTexts[i]
		textObject = font.render(toPrint, True, py.Color('White'))  # Enable anti-aliasing
		textLocation = moveLogRectTop.move(pad_X, pad_Y)
		screen.blit(textObject, textLocation)
		pad_Y += textObject.get_height() + 2



def drawGraph(screen: py.Surface, rect: py.Rect, evalHistory: list):
    """
    Draws a graph based on the evaluation history of the game.

    Args:
        screen (py.Surface): The surface to draw the graph on.
        rect (py.Rect): The rectangle defining the area for the graph.
        evalHistory (list): A list of tuples (whiteScore, blackScore, netScore).
    """
    # Check if evalHistory is valid
    if not evalHistory or not isinstance(evalHistory, list):
        print("Warning: evalHistory is empty or invalid")
        return

    try:
        # Extract scores
        whiteScores: int = [evalHistory[0]]
        blackScores: int = [evalHistory[1]]
        netScores: int = [evalHistory[1]]
    except IndexError:
        print("Error: Invalid structure in evalHistory")
        return

    # Graph dimensions and margins
    margin = 10
    graphWidth = rect.width - 2 * margin
    graphHeight = rect.height - 2 * margin
    graphRect = py.Rect(rect.x + margin, rect.y + margin, graphWidth, graphHeight)

    # Background
    py.draw.rect(screen, py.Color("gray"), graphRect)

    # Normalize scores to fit in the graph
    allScores = whiteScores + blackScores + netScores
    maxScore = allScores if allScores else 1  # Avoid division by zero
    minScore = allScores if allScores else 0

    def normalize(score):
        return graphRect.height - int((score - minScore) / (maxScore - minScore) * graphRect.height)

    # Draw scores as lines
    for i in range(1, len(evalHistory)):
        startX = graphRect.x + (i - 1) * graphWidth // len(evalHistory)
        endX = graphRect.x + i * graphWidth // len(evalHistory)

        py.draw.line(screen, py.Color("white"), (startX, graphRect.y + normalize(whiteScores[i - 1])),
                     (endX, graphRect.y + normalize(whiteScores[i])), 2)
        py.draw.line(screen, py.Color("black"), (startX, graphRect.y + normalize(blackScores[i - 1])),
                     (endX, graphRect.y + normalize(blackScores[i])), 2)
        py.draw.line(screen, py.Color("red"), (startX, graphRect.y + normalize(netScores[i - 1])),
                     (endX, graphRect.y + normalize(netScores[i])), 2)





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


class HomeScreen:
	def __init__(self, screen):
		self.screen = screen
		self.play_button_rect = py.Rect(BOARD_WIDTH // 3, BOARD_HEIGHT // 3, BOARD_WIDTH // 3, BOARD_HEIGHT // 10)
		self.quit_button_rect = py.Rect(BOARD_WIDTH // 3, BOARD_HEIGHT // 2, BOARD_WIDTH // 3, BOARD_HEIGHT // 10)

	def draw(self):
		self.screen.fill(py.Color("black"))
		font = py.font.Font(None, 50)
		
		# Title
		title = font.render("Chess Game", True, py.Color("white"))
		title_rect = title.get_rect(center=(BOARD_WIDTH // 2, BOARD_HEIGHT // 4))
		self.screen.blit(title, title_rect)
		
		# Play Button
		py.draw.rect(self.screen, py.Color("green"), self.play_button_rect)
		play_text = font.render("Play", True, py.Color("black"))
		play_rect = play_text.get_rect(center=self.play_button_rect.center)
		self.screen.blit(play_text, play_rect)

		# Quit Button
		py.draw.rect(self.screen, py.Color("red"), self.quit_button_rect)
		quit_text = font.render("Quit", True, py.Color("black"))
		quit_rect = quit_text.get_rect(center=self.quit_button_rect.center)
		self.screen.blit(quit_text, quit_rect)

	def handle_event(self, event):
		if event.type == py.MOUSEBUTTONDOWN:
			if self.play_button_rect.collidepoint(event.pos):
				return "play"
			elif self.quit_button_rect.collidepoint(event.pos):
				return "quit"
		return None
	

def main():
	py.init()
	screen = py.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
	py.display.set_caption("Chess")
	clock = py.time.Clock()
	playerOne = True  # Human is white
	playerTwo = True  # AI is black
	evalHistory = []

	# Game states
	state = GameStateEnum.HOME_SCREEN
	home_screen = HomeScreen(screen)
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
					humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
				elif action == "quit":
					running = False

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
				# AI's turn
				validMoves = gs.validMoveIfCheck()
				if len(validMoves) == 0:
					handleTerminalState(gs, screen)
					break

				AIMove = findBestMove(gs, validMoves)
			
				print(f"AI Move: {AIMove.getChessNotation(gs)}")  # Debug AI move
				gs.makeMove(AIMove)
				gs.isChecked, gs.pins, gs.checks = gs.checkForPinsandChecks()

				

				gs.moveMade = True
				animateMove(gs.moveLog[-1], screen, clock, gs)
				playSound(AIMove, gs)

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
			evalHistory.append(evaluateGameStateWithDetails(gs))
			drawGameState(screen, gs, moveLogFont, evalHistory)

		py.display.flip()
		clock.tick(MAX_FPS)




if __name__ == "__main__":
	main()
