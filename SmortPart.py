import random
from ChessEngine import *

materialScores = {
	"p": 100,  # Pawn
	"N": 320,  # Knight
	"B": 390,  # Bishop
	"R": 500,  # Rook
	"Q": 900,  # Queen
	"K": 1000     # King (value only matters in checkmate logic)
}

whitePawnTable = [
    [60, 60, 60, 60, 60, 60, 60, 60],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

blackPawnTable = whitePawnTable[::-1]  # Mirror for black pawns

knightTable = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-30,  10,  15,  20,  20,  15,  10, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-30,   0,  10,  15,  15,  10,   0, -30],
    [-40, -20,   0,   0,   0,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

bishopTable = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   5,   0,   0,   0,   0,   5, -10],
    [-10,  10,  10,  10,  10,  10,  10, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,   5,   5,  10,  10,   5,   5, -10],
    [-10,   0,   5,  10,  10,   5,   0, -10],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

whiteRookTable = [
	[0, 0, 0, 5, 5, 0, 0, 0],
	[20, 20, 20, 20, 20, 20, 20, 20],
	[5, 0, 20, 20, 20, 20, 0, 5],
	[5, 0, 0, 20, 20, 20, 0, 5],
	[5, 0, 0, 20, 20, 20, 0, 5],
	[5, 0, 0, 20, 20, 20, 20, 5],
	[5, 20, 20, 20, 20, 20, 20, 5],
	[0, 0, 0, 25, 25, 0, 0, 0],
]

blackRookTable = whiteRookTable[::-1]  # Mirror for black rooks

queenTable = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [-5,    0,   5,   5,   5,   5,   0,  -5],
    [0,     0,   5,   5,   5,   5,   0,  -5],
    [-10,   5,   5,   5,   5,   5,   0, -10],
    [-10,   0,   5,   0,   0,   0,   0, -10],
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
]

whiteKingTableMid = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20,  20,   0,   0,   0,   0,  20,  20],
    [20,  30,  10,   0,   0,  10,  30,  20],
]

blackKingTableMid = whiteKingTableMid[::-1]  # Mirror for black king

whiteKingTableEnd = [
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10,   0,   0, -10, -20, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -30,   0,   0,   0,   0, -30, -30],
    [-50, -40, -30, -20, -20, -30, -40, -50],
]

blackKingTableEnd = whiteKingTableEnd[::-1]  # Mirror for black king





CHECKMATE = 100000
STALEMATE = 0
DEPTH = 3

def findRandom(validMoves: list[Move]):
	if len(validMoves) != 0:
		return validMoves[random.randint(0, len(validMoves) - 1)]

def findBetterMoves(gs: GameState, validMoves: list[Move]):
	"""
	Finds the best move from the list of valid moves by evaluating the board position after each move.

	Args:
		gs (GameState): The current game state.
		validMoves (list): List of valid moves.

	Returns:
		Move: The best move based on material evaluation.
	"""
	turnMultiplier = 1 if gs.whiteToMove else -1  # Score multiplier based on the player's turn
	oppMinMaxScore = CHECKMATE  # Initialize to the worst score for the opponent
	bestPlayerMove = None
	random.shuffle(validMoves)

	for playerMove in validMoves:
		gs.makeMove(playerMove)
		if gs.checkmate:
			# Immediate checkmate is the best possible move
			gs.undoMove()
			return playerMove
		elif gs.stalemate:
			score = STALEMATE
		else:
			oppMoves = gs.validMoveIfCheck()
			opponentDreamScore = -CHECKMATE  # Initialize to the worst score for the opponent

			for oppMove in oppMoves:
				gs.makeMove(oppMove)
				gs.validMoveIfCheck()

				if gs.checkmate:
					score = CHECKMATE  # Opponent checkmates us
				elif gs.stalemate:
					score = STALEMATE
				else:
					score = -turnMultiplier * scoreMaterial(gs.board)

				
				opponentDreamScore = max(opponentDreamScore, score)  # Opponent maximizes their score
				gs.undoMove()

			score = -opponentDreamScore  # Negate because we're maximizing our score

		if score < oppMinMaxScore:
			oppMinMaxScore = score
			bestPlayerMove = playerMove

		gs.undoMove()  # Undo the move to restore the game state

	return bestPlayerMove

'''
First Call
'''
def findBestMove(gs: GameState, validMoves: list[Move]):
	global nextMove
	nextMove = None
	# findMoveMinMax(gs, validMoves, DEPTH, gs.whiteToMove)
	# findMoveNegaMax(gs, validMoves, DEPTH, 1 if gs.whiteToMove else -1)
	findMoveNegaMaxAlphaBeta(gs, validMoves, DEPTH, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1)
	return nextMove


def findMoveMinMax(gs: GameState, validMoves: list[Move], depth: int, whiteToMove: bool):
	global nextMove
	if depth == 0:
		return scoreBoard(gs)
	
	if gs.whiteToMove:
		maxScore = -CHECKMATE
		for move in validMoves:
			gs.makeMove(move)
			score = -findMoveMinMax(gs, gs.validMoveIfCheck(), depth - 1, whiteToMove)

			if score > maxScore:
				maxScore = score
				if depth == DEPTH:
					nextMove = move

			gs.undoMove()
		return maxScore
	else:
		minScore = CHECKMATE
		for move in validMoves:
			gs.makeMove(move)
			score = findMoveMinMax(gs, gs.validMoveIfCheck(), depth - 1, whiteToMove)
			
			if score < minScore:
				minScore = score
				if depth == DEPTH:
					nextMove = move
			
			gs.undoMove()
		return minScore

def findMoveNegaMax(gs: GameState, validMoves: list[Move], depth: int, turnMultiplier: int) -> int:
	global nextMove
	if depth == 0:
		return turnMultiplier * scoreBoard(gs)
	
	maxScore = - CHECKMATE

	for move in validMoves:
		gs.makeMove(move)
		nextMoves = gs.validMoveIfCheck()
		score = -findMoveNegaMax(gs, nextMoves, depth - 1, -turnMultiplier)
		if score > maxScore:
			maxScore = score
			if depth == DEPTH:
				nextMove = move	
		gs.undoMove()

	return maxScore

def findMoveNegaMaxAlphaBeta(gs: GameState, validMoves: list[Move], depth: int, alpha: int, beta: int, turnMultiplier: int) -> int:
		global nextMove
		if depth == 0 or gs.checkmate or gs.stalemate:
			return turnMultiplier * scoreBoard(gs)

		maxScore = -CHECKMATE
		for move in validMoves:
			gs.makeMove(move)
			nextMoves = gs.validMoveIfCheck()  # Avoid recomputing if not necessary
			score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
			gs.undoMove()

			if score > maxScore:
				maxScore = score
				if depth == DEPTH:
					nextMove = move

			alpha = max(alpha, score)
			if alpha >= beta:
				break  # Prune

		return maxScore

def scoreBoard(gs: GameState, isEndgame=False):
	"""
	Evaluate the current game state and return a score.
	Positive values favor white, and negative values favor black.

	Args:
		gs (GameState): The current game state.
		isEndgame (bool): Whether to use endgame evaluation for king positioning.

	Returns:
		int: The score of the game state.
	"""
	if gs.checkmate:
		return -CHECKMATE if gs.whiteToMove else CHECKMATE

	if gs.stalemate:
		return STALEMATE

	score = 0
	for row in range(len(gs.board)):
		for col in range(len(gs.board[row])):
			piece = gs.board[row][col]
			if piece != "--":
				pieceColor = piece[0]  # 'w' for white, 'b' for black
				pieceType = piece[1]  # 'p', 'N', 'B', 'R', 'Q', 'K'

				# Material score
				materialScore = materialScores[pieceType]
				score += materialScore if pieceColor == "w" else -materialScore

				# Positional score
				if pieceType == "p":
					positionScore = whitePawnTable[row][col] if pieceColor == "w" else blackPawnTable[row][col]
				elif pieceType == "N":
					positionScore = knightTable[row][col]
				elif pieceType == "B":
					positionScore = bishopTable[row][col]
				elif pieceType == "R":
					positionScore = whiteRookTable[row][col] if pieceColor == "w" else blackRookTable[row][col]
				elif pieceType == "Q":
					positionScore = queenTable[row][col] if pieceColor == "w" else -queenTable[row][col]  # Symmetrical
				elif pieceType == "K":
					if isEndgame:
						positionScore = whiteKingTableEnd[row][col] if pieceColor == "w" else blackKingTableEnd[row][col]
					else:
						positionScore = whiteKingTableMid[row][col] if pieceColor == "w" else blackKingTableMid[row][col]

				# Adjust the total score
				score += positionScore if pieceColor == "w" else -positionScore

	return score



def scoreMaterial(board):
	score = 0
	for row in board:
		for piece in row:
			if piece != "--":
				score += materialScores[piece[1]] * (1 if piece[0] == "w" else -1)
	return score

def evaluateGameStateWithDetails(gs: GameState):
	"""
	Evaluates the current game state and calculates separate scores for White and Black.

	Args:
		gs (GameState): The current game state.

	Returns:
		tuple: A tuple containing:
			- White's score (int)
			- Black's score (int)
			- Net evaluation score (White's score - Black's score)
	"""
	# Separate scores for White and Black
	whiteScore = 0
	blackScore = 0

	# Checkmate and stalemate evaluation
	if gs.checkmate:
		if gs.whiteToMove:
			return 0, CHECKMATE, -CHECKMATE  # Black wins
		else:
			return CHECKMATE, 0, CHECKMATE  # White wins

	if gs.stalemate:
		return 0, 0, STALEMATE  # Draw

	# Calculate scores for each piece on the board
	for row in range(len(gs.board)):
		for col in range(len(gs.board[row])):
			piece = gs.board[row][col]
			if piece != "--":
				pieceColor = piece[0]  # 'w' for White, 'b' for Black
				pieceType = piece[1]  # 'p', 'N', 'B', 'R', 'Q', 'K'

				# Material score
				materialScore = materialScores[pieceType]

				# Positional score
				if pieceType == "p":
					positionScore = whitePawnTable[row][col] if pieceColor == "w" else blackPawnTable[row][col]
				elif pieceType == "N":
					positionScore = knightTable[row][col]
				elif pieceType == "B":
					positionScore = bishopTable[row][col]
				elif pieceType == "R":
					positionScore = whiteRookTable[row][col] if pieceColor == "w" else blackRookTable[row][col]
				elif pieceType == "Q":
					positionScore = queenTable[row][col]
				elif pieceType == "K":
					# Determine if we're in the endgame
					totalMaterial = sum(abs(materialScores[p[1]]) for r in gs.board for p in r if p != "--" and p[1] != 'K')
					isEndgame = totalMaterial <= 1400  # Endgame threshold
					if pieceColor == "w":
						positionScore = whiteKingTableEnd[row][col] if isEndgame else whiteKingTableMid[row][col]
					else:
						positionScore = blackKingTableEnd[row][col] if isEndgame else blackKingTableMid[row][col]

				# Add to the respective player's score
				if pieceColor == "w":
					whiteScore += materialScore + positionScore
				else:
					blackScore += materialScore + positionScore


def evaluateKnight(gs: GameState, row: int, col: int, pieceColor: str) -> int:
	"""
	Dynamically evaluates the knight's position based on a policy.

	Args:
		gs (GameState): The current game state.
		row (int): Row of the knight.
		col (int): Column of the knight.
		pieceColor (str): 'w' for white, 'b' for black.

	Returns:
		int: The score of the knight based on its position and policy.
	"""
	score = 0

	# 1. Centralization
	# Distance from the center (d4, d5, e4, e5 are most central)
	centerSquares = [(3, 3), (3, 4), (4, 3), (4, 4)]
	distanceToCenter = min(abs(row - center[0]) + abs(col - center[1]) for center in centerSquares)
	score += (4 - distanceToCenter) * 10  # Reward closer positions to the center

	# 2. Mobility
	knightMoves = gs.knightValidMoves(row, col)
	mobility = len(knightMoves)  # Function to get legal moves for the knight
	score += mobility * 5  # Reward for having more mobility

	# 3. Threats
	for move in knightMoves:
		targetPiece = gs.board[move[0]][move[1]]
		if targetPiece != "--" and targetPiece[0] != pieceColor:  # Enemy piece
			score += materialScores[targetPiece[1]] // 10  # Reward based on the target's material value

	# 4. Support (outpost)
	if isOutpost(gs, row, col, pieceColor):  # Function to determine if the knight is on an outpost
		score += 15

	return score if pieceColor == "w" else -score

def evaluateBishop(gs: GameState, row: int, col: int, pieceColor, validMoves: list[Move]):
	"""
	Evaluate a bishop's position.
	"""
	score = 0

	bishopMoves = []
	for i in range(len(validMoves)):
		if validMoves[i].pieceMoved[1] == 'B':
			bishopMoves.append(validMoves[i])
	
	# Mobility: Count valid moves for the bishop
	mobility = len(bishopMoves)
	score += mobility * 5  # Each move adds value

	# Control of open diagonals: Reward if bishop has long lines of sight
	directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
	for d in directions:
		for i in range(1, 8):
			r, c = row + d[0] * i, col + d[1] * i
			if 0 <= r < 8 and 0 <= c < 8:
				if gs.board[r][c] == "--":  # Empty square
					score += 2  # Control over empty squares
				elif gs.board[r][c][0] == pieceColor:  # Friendly piece blocks
					break
				else:  # Opponent piece
					score += 20  # Pressure on enemy piece
					break
			else:
				break

	# Centralization: Reward positions closer to the center
	centerBonus = 10 - abs(row - 3.5) - abs(col - 3.5)
	score += centerBonus

	return score





def isOutpost(gs: GameState, row: int, col: int, pieceColor: chr) -> bool:
    """
    Checks if the knight is on an outpost square.

    Args:
        gs (GameState): The current game state.
        row (int): Row of the knight.
        col (int): Column of the knight.
        pieceColor (str): 'w' for white, 'b' for black.

    Returns:
        bool: True if the knight is on an outpost, False otherwise.
    """
    # Direction of pawns for each color
    pawnDirection = -1 if pieceColor == "w" else 1

    # Check if the knight is protected by a friendly pawn
    if 0 <= row + pawnDirection < 8:
        if (0 <= col - 1 < 8 and gs.board[row + pawnDirection][col - 1] == pieceColor + "p") or \
           (0 <= col + 1 < 8 and gs.board[row + pawnDirection][col + 1] == pieceColor + "p"):
            
            # Use `isSquareAttacked` to check if the square is under attack
            if not gs.isSquareAttacked(row, col):
                return True

    return False
