"""
ChessEngine.py

This module contains the core logic for the chess engine, including the representation of moves, game state, and the rules of chess. It handles move generation, validation, and special rules such as castling, en passant, and pawn promotion.

Classes:
    Move: Represents a chess move, including its start and end positions, the piece moved, and any special move types.
    GameState: Represents the current state of the chess game, including the board configuration, move history, and game status.
    CastleRights: Represents the castling rights for both players.

Functions:
    __init__: Initializes the Move, GameState, and CastleRights classes.
    getChessNotation: Generates the algebraic notation for a move.
    getRankFile: Converts row and column indices to chess rank-file notation.
    __eq__: Checks equality between two Move objects based on their unique move ID.
    findSimilarPieceMoves: Finds all pieces of the same type that can move to the same destination square.
    makeMove: Executes a move on the board and updates the game state.
    undoMove: Reverts the last move and restores the previous game state.
    updateCastleRights: Updates the castling rights based on the given move.
    updateCastleRightsUndo: Restores the castling rights to their state before the last move.
    validMoveIfCheck: Filters out moves that leave the king in check.
    validMoveIfNotCheck: Generates a list of moves without considering checks.
    checkForPinsandChecks: Checks if the king is in check and finds the squares that would block or capture it.
    inCheck: Checks if the current player's king is in check.
    isSquareAttacked: Checks if a square is attacked by any opponent piece.
    pawnValidMoves: Generates valid moves for pawns.
    isEnPassantSafe: Checks if performing en passant leaves the king in check.
    rookValidMoves: Generates valid moves for rooks.
    knightValidMoves: Generates valid moves for knights.
    bishopValidMoves: Generates valid moves for bishops.
    queenValidMoves: Generates valid moves for queens.
    kingValidMoves: Generates valid moves for the king.
    getCastlingMoves: Generates castling moves for the king.
    kingSideCastling: Generates king-side castling moves.
    queenSideCastling: Generates queen-side castling moves.
"""

import json
import os
from typing import Tuple, Optional
import pygame

class Move:
	def __init__(self, startSq, endSq, board, isEnPassantMove=False, isCastleMove=False):
		self.startRow = startSq[0]
		self.startCol = startSq[1]
		self.endRow = endSq[0]
		self.endCol = endSq[1]

		self.pieceMoved = board[self.startRow][self.startCol]
		self.pieceCaptured = board[self.endRow][self.endCol]

		# Handle en passant captured piece
		if isEnPassantMove:
			self.pieceCaptured = 'bp' if self.pieceMoved == 'wp' else 'wp'  # Captured pawn is opposite color

		# Pawn Promotion
		self.isPawnPromotion = (
			(self.pieceMoved == 'wp' and self.endRow == 0) or 
			(self.pieceMoved == 'bp' and self.endRow == 7)
		)

		# Castling and en passant flags
		self.isCastleMove = isCastleMove
		self.isEnPassantMove = isEnPassantMove

		# Unique ID for the move
		self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

	# Mappings for chess notation
	ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
	filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
	rowsToRanks = {v: k for k, v in ranksToRows.items()}
	colsToFiles = {v: k for k, v in filesToCols.items()}

	# Algebraic notation
	def getChessNotation(self, gs) -> str:
		"""
		Generate the chess notation for the move in algebraic notation.
		Handles pawn promotions, castling, captures, and other special cases.
		"""
		# Handle castling
		if self.isCastleMove:
			return "O-O" if self.endCol - self.startCol == 2 else "O-O-O"

		moveNotation = ""

		# Get piece type (empty string for pawns)
		piece = self.pieceMoved[1]
		pieceNotation = "" if piece == "p" else piece.upper()

		# Handle piece disambiguation
		if piece != "p":
			sameDestinationPieces = self.findSimilarPieceMoves(gs)
			if len(sameDestinationPieces) > 1:  # Disambiguation required
				disambiguation = ""
				sameFile = any(move.startCol == self.startCol for move in sameDestinationPieces if move != self)
				sameRank = any(move.startRow == self.startRow for move in sameDestinationPieces if move != self)

				if sameFile and sameRank:
					disambiguation = self.getRankFile(self.startRow, self.startCol)
				elif sameFile:
					disambiguation = str(self.startRow + 1)  # Rank only
				else:
					disambiguation = chr(self.startCol + ord('a'))  # File only

				moveNotation += pieceNotation + disambiguation
			else:
				moveNotation += pieceNotation

		# Handle captures
		if self.pieceCaptured != "--":  # A piece was captured
			if piece == "p":  # Pawns need file of origin for captures
				moveNotation += self.getRankFile(self.startRow, self.startCol)[0]
			moveNotation += "x"  # Indicate capture

		# Add destination square
		moveNotation += self.getRankFile(self.endRow, self.endCol)

		# Handle pawn promotion
		if self.isPawnPromotion:
			moveNotation += "=Q"  # Default to queen promotion; allow flexibility if needed

		# Handle check and checkmate
		if gs.checkmate:
			moveNotation += "#"
		elif gs.isChecked:
			moveNotation += "+"

		return moveNotation



	# Convert row and col to rank-file notation
	def getRankFile(self, row, col) -> str:
		return self.colsToFiles[col] + self.rowsToRanks[row]

	# Equality based on unique move ID
	def __eq__(self, other) -> bool:
		if isinstance(other, Move):
			return self.moveID == other.moveID
		return False
	
	def findSimilarPieceMoves(self, gs):
		"""
		Find all pieces of the same type that can move to the same destination square.
		"""
		sameTypeMoves = []
		for move in gs.validMoves:
			if (
				move.pieceMoved[1] == self.pieceMoved[1]  # Same type of piece
				and move.endRow == self.endRow  # Same destination row
				and move.endCol == self.endCol  # Same destination column
			):
				sameTypeMoves.append(move)
		return sameTypeMoves



class GameState():
	def __init__(self):
		self.board = [
			["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
			["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
			["--", "--", "--", "--", "--", "--", "--", "--"],
			["--", "--", "--", "--", "--", "--", "--", "--"],
			["--", "--", "--", "--", "--", "--", "--", "--"],
			["--", "--", "--", "--", "--", "--", "--", "--"],
			["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
			["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
		]

		self.whiteToMove = True
		self.moveLog: list[Move] = []

		self.moveFunction = {
			'p' :self.pawnValidMoves,
			'N' :self.knightValidMoves,
			'B' :self.bishopValidMoves,
			'Q' :self.queenValidMoves,
			'K' :self.kingValidMoves,
			'R' :self.rookValidMoves,
		}

		self.isChecked = False
		self.pins: list[str] = []
		self.checks = []

		self.enPassantTargetSquare = ()  # The square the pawn moved two squares to capture en passant
		self.enPassantTargetSquareLog: list[tuple[int, int]] = []  # Tracks the en passant target square for each move made

		self.castleRights = CastleRights(True, True, True, True)
		self.castleRightsLog: list[CastleRights] = []
		self.castleRightsLog.append(
			CastleRights(
				self.castleRights.whiteKingSide,
				self.castleRights.whiteQueenSide,
				self.castleRights.blackKingSide,
				self.castleRights.blackQueenSide
				)
			)

		self.whiteKingLocation = (7, 4)
		self.blackKingLocation = (0, 4)
	
		self.sqSelected = ()  # Tracks the currently selected square
		self.playerClick = []
		self.validMoves = self.validMoveIfCheck()
		self.moveMade = False

		self.gameOver = False
		self.checkmate = False
		self.stalemate = False
		self.threeMoveRepetition = False



	def makeMove(self, move: Move):
		self.board[move.startRow][move.startCol] = "--"
		self.board[move.endRow][move.endCol] = move.pieceMoved
		self.moveLog.append(move)
		self.whiteToMove = not self.whiteToMove

		# Update the king's location if the move was a king move
		if move.pieceMoved == "wK":
			self.whiteKingLocation = (move.endRow, move.endCol)
		elif move.pieceMoved == "bK":
			self.blackKingLocation = (move.endRow, move.endCol)

		# Promote Pawn
		if move.isPawnPromotion:
			self.board[move.endRow][move.endCol] = move.pieceMoved[0] + 'Q'
				

		# enPassant !!!!
		if move.isEnPassantMove:
			self.board[move.startRow][move.endCol] = "--"

		if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
			self.enPassantTargetSquare = ((move.startRow + move.endRow) // 2, move.endCol)
		else:
			self.enPassantTargetSquare = ()
		
		self.enPassantTargetSquareLog.append(self.enPassantTargetSquare)

		
		# Castling... wow so fuuunn
		if move.isCastleMove:
			if move.endCol - move.startCol == 2:
				self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1]
				self.board[move.endRow][move.endCol + 1] = "--"
			else:
				self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2]
				self.board[move.endRow][move.endCol - 2] = "--"


		self.updateCastleRights(move)
		self.castleRightsLog.append(
			CastleRights(
				self.castleRights.whiteKingSide,
				self.castleRights.whiteQueenSide,
				self.castleRights.blackKingSide,
				self.castleRights.blackQueenSide
				)
			)


	def undoMove(self):
		"""
		Undo the last move, restoring the board and state to the previous turn.
		"""
		if len(self.moveLog) > 0:
			move = self.moveLog.pop()

			# Restore the board
			self.board[move.startRow][move.startCol] = move.pieceMoved
			self.board[move.endRow][move.endCol] = move.pieceCaptured

			# Update turn
			self.whiteToMove = not self.whiteToMove

			# Update king's location
			if move.pieceMoved == "wK":
				self.whiteKingLocation = (move.startRow, move.startCol)
			elif move.pieceMoved == "bK":
				self.blackKingLocation = (move.startRow, move.startCol)

			# Handle en passant undo
			if move.isEnPassantMove:
				self.board[move.endRow][move.endCol] = "--"  # Remove pawn from the target square
				captureRow = move.endRow + (1 if move.pieceMoved[0] == 'w' else -1)
				self.board[captureRow][move.endCol] = move.pieceCaptured  # Restore captured pawn

			# Restore en passant target square
			if len(self.enPassantTargetSquareLog) > 0:
				self.enPassantTargetSquareLog.pop()
				self.enPassantTargetSquare = self.enPassantTargetSquareLog[-1] if len(self.enPassantTargetSquareLog) > 0 else ()
			else:
				self.enPassantTargetSquare = ()

			# Handle castling undo
			if move.isCastleMove:
				if move.endCol - move.startCol == 2:  # Kingside castling
					self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]  # Restore rook
					self.board[move.endRow][move.endCol - 1] = "--"  # Clear the rook's square
				else:  # Queenside castling
					self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]  # Restore rook
					self.board[move.endRow][move.endCol + 1] = "--"  # Clear the rook's square

			# Restore castle rights
			self.updateCastleRightsUndo()

			# Reset game end states
			self.checkmate = False
			self.stalemate = False
	
	def updateCastleRights(self, move: Move):
		"""
		Updates the castling rights based on the given move. 
		Castling rights are invalidated in the following cases:
		- The king moves (both king-side and queen-side rights are lost for that color).
		- A rook moves from its initial position (the corresponding castling right is lost).
		- A rook is captured while in its initial position (the corresponding castling right is lost).

		Args:
			move (Move): The move that has just been played.
		"""
		# If a king moves, both king-side and queen-side castling rights are lost for that color
		if move.pieceMoved == "wK":
			self.castleRights.whiteKingSide = False
			self.castleRights.whiteQueenSide = False
		elif move.pieceMoved == "bK":
			self.castleRights.blackKingSide = False
			self.castleRights.blackQueenSide = False

		# If a white rook moves, determine which castling right is affected
		elif move.pieceMoved == "wR":
			if move.startRow == 7:
				if move.startCol == 0:
					self.castleRights.whiteQueenSide = False
				elif move.startCol == 7:
					self.castleRights.whiteKingSide = False

		# If a black rook moves, determine which castling right is affected
		elif move.pieceMoved == "bR":
			if move.startRow == 0:
				if move.startCol == 0:
					self.castleRights.blackQueenSide = False
				elif move.startCol == 7:
					self.castleRights.blackKingSide = False

		# If a white rook is captured, determine which castling right is affected
		if move.pieceCaptured == "wR":
			if move.endRow == 7:
				if move.endCol == 0:
					self.castleRights.whiteQueenSide = False
				elif move.endCol == 7:
					self.castleRights.whiteKingSide = False

		# If a black rook is captured, determine which castling right is affected
		elif move.pieceCaptured == "bR":
			if move.endRow == 0:
				if move.endCol == 0:
					self.castleRights.blackQueenSide = False
				elif move.endCol == 7:
					self.castleRights.blackKingSide = False


	def updateCastleRightsUndo(self):
		"""
		Restore the castling rights to their state before the last move.
		This is done during the undo operation.
		"""
		if len(self.castleRightsLog) > 0:
			self.castleRightsLog.pop()

			self.castleRights = self.castleRightsLog[-1]
		else:
			self.castleRights = CastleRights(True, True, True, True)

	'''
	Filters out the moves that leave the king in Check.
	'''
	def validMoveIfCheck(self):
			validMoves: list[Move] = []

			if self.whiteToMove:
				kingRow, kingCol = self.whiteKingLocation
			else:
				kingRow, kingCol = self.blackKingLocation

			if self.isChecked:
				# Double check case: only king moves are valid
				if len(self.checks) > 1:
					return self.kingValidMoves(kingRow, kingCol)
				
				# Single check case
				check = self.checks[0]
				checkRow, checkCol, checkDx, checkDy = check

				# Generate valid squares to block or capture the checking piece
				validSquares = [(checkRow, checkCol)]
				if self.board[checkRow][checkCol][1] not in ('N', 'p'):
					for i in range(1, 8):
						validSquare = (kingRow + checkDx * i, kingCol + checkDy * i)
						validSquares.append(validSquare)
						if validSquare[0] == checkRow and validSquare[1] == checkCol:
							break
				
				# Filter moves: allow king moves or moves that block/capture the check
				for move in self.validMoveIfNotCheck():
					if move.pieceMoved[1] == 'K':
						validMoves.append(move)  # King moves are handled separately
					elif (move.endRow, move.endCol) in validSquares:
						validMoves.append(move)

			else:
				# No checks: filter moves for pins
				for move in self.validMoveIfNotCheck():
					isPinned = False
					for pin in self.pins:
						pinRow, pinCol, pinDx, pinDy = pin
						if move.startRow == pinRow and move.startCol == pinCol:
							isPinned = True
							# Allow move only if it stays along the pin line
							if (move.endRow - pinRow) * pinDy == (move.endCol - pinCol) * pinDx:
								validMoves.append(move)
							break
					if not isPinned:
						validMoves.append(move)

			self.getCastlingMoves(kingRow, kingCol, validMoves)

			if len(validMoves) == 0:
				if self.isChecked:
					self.checkmate = True
				else:
					self.stalemate = True

			return validMoves


	'''
	Generate a list of moves without considering Checks.
	'''
	def validMoveIfNotCheck(self) -> list[Move]:
		moves = []
		for row in range(len(self.board)):
			for col in range(len(self.board[row])):
				piece = self.board[row][col]
				
				if piece != "--" and piece[0] == ("w" if self.whiteToMove else "b"):
					moves.extend(self.moveFunction[piece[1]](row, col))
		return moves

	'''
    Check if the king is in check and find the squares that would block or capture it.
    '''
	def checkForPinsandChecks(self):
		pins = []
		checks = []
		isChecked = False

		if self.whiteToMove:
			oppColor = "b"
			allyColor = "w"
			kingRow, kingCol = self.whiteKingLocation
		else:
			oppColor = "w"
			allyColor = "b"
			kingRow, kingCol = self.blackKingLocation
		
		DIRECTIONS = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))

		for j in range(len(DIRECTIONS)):
			dx, dy = DIRECTIONS[j]
			possiblePins = None

			for i in range(1, 8):
				endRow = kingRow + dx * i
				endCol = kingCol + dy * i

				if 0 <= endRow < 8 and 0 <= endCol < 8:
					endPiece = self.board[endRow][endCol]
					if endPiece[0] == allyColor:
						if possiblePins is None:
							possiblePins = (endRow, endCol, dx, dy)
						else:
							break
					elif endPiece[0] == oppColor:
						pieceType = endPiece[1]
						if (0 <= j <= 3 and pieceType == 'R') or \
						(4 <= j <= 7 and pieceType == 'B') or \
						(pieceType == 'Q') or \
						(i == 1 and pieceType == 'p' and
							((oppColor == 'w' and 6 <= j <= 7) or (oppColor == 'b' and 4 <= j <= 5))):
							if possiblePins is None:
								isChecked = True
								checks.append((endRow, endCol, dx, dy))
								
							else:
								pins.append(possiblePins)
								
							break
						else:
							break
				else:
					break
		
		knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
		for n in knightMoves:
			endRow, endCol = kingRow + n[0], kingCol + n[1]
			if 0 <= endRow < 8 and 0 <= endCol < 8:
				endPiece = self.board[endRow][endCol]
				if endPiece[0] == oppColor and endPiece[1] == 'N':
					isChecked = True
					checks.append((endRow, endCol, n[0], n[1]))
					

		return isChecked, pins, checks

	def inCheck(self):
		"""
		Check if the current player's king is in check.
		"""
		if self.whiteToMove:
			kingRow, kingCol = self.whiteKingLocation
		else:
			kingRow, kingCol = self.blackKingLocation
		

		return self.isSquareAttacked(kingRow, kingCol)
	
	def isSquareAttacked(self, row, col):
		"""
		Check if the square (row, col) is attacked by any opponent piece.
		"""
		oppColor = "b" if self.whiteToMove else "w"

		# Check for pawn attacks
		pawnDirection = -1 if self.whiteToMove else 1
		if 0 <= row + pawnDirection < 8:
			if (col - 1 >= 0 and self.board[row + pawnDirection][col - 1] == oppColor + "p") or \
			(col + 1 < 8 and self.board[row + pawnDirection][col + 1] == oppColor + "p"):
				return True

		# Check for knight attacks
		knightMoves = [
			(-2, -1), (-2, 1), (-1, -2), (-1, 2),
			(1, -2), (1, 2), (2, -1), (2, 1)
		]
		for kMove in knightMoves:
			knightRow, knightCol = row + kMove[0], col + kMove[1]
			if 0 <= knightRow < 8 and 0 <= knightCol < 8:
				if self.board[knightRow][knightCol] == oppColor + "N":
					return True

		# Check for sliding piece attacks
		rookDirections = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Vertical and horizontal
		bishopDirections = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Diagonal

		# Rook/Queen attacks
		slidingDirections = rookDirections + bishopDirections  # Combine all sliding directions
		for d in slidingDirections:
			for i in range(1, 8):
				checkRow, checkCol = row + d[0] * i, col + d[1] * i
				if 0 <= checkRow < 8 and 0 <= checkCol < 8:
					piece = self.board[checkRow][checkCol]
					if piece == "--":
						continue
					if piece[0] == oppColor and (piece[1] == "Q" or (piece[1] == "R" and d in rookDirections) or (piece[1] == "B" and d in bishopDirections)):
						return True
					break  # Blocked by any piece
				break  # Out of bounds


		# Check for king attacks
		kingMoves = [
			(-1, -1), (-1, 0), (-1, 1),
			(0, -1),         (0, 1),
			(1, -1), (1, 0), (1, 1)
		]
		for kMove in kingMoves:
			kingRow, kingCol = row + kMove[0], col + kMove[1]
			if 0 <= kingRow < 8 and 0 <= kingCol < 8:
				if self.board[kingRow][kingCol] == oppColor + "K":
					return True

		return False


	def threeMoveRule(self):
		if len(self.moveLog) >= 6:
			if self.moveLog[-1] == self.moveLog[-5] and self.moveLog[-2] == self.moveLog[-6]:
				return True
		return False

	'''
	Valid Moves for all types of pieces:
	'''
	def pawnValidMoves(self, row: int, col: int) -> list[Move]:
		piecePinned = False
		pinDirection = ()

		# Check if the pawn is pinned
		for i in range(len(self.pins) - 1, -1, -1):
			if self.pins[i][0] == row and self.pins[i][1] == col:
				piecePinned = True
				pinDirection = (self.pins[i][2], self.pins[i][3])
				self.pins.remove(self.pins[i])
				break

		# Determine direction, start row, and enemy color
		if self.whiteToMove:
			moveAmount = -1
			startRow = 6
			enemyColor = 'b'
			kingRow, kingCol = self.whiteKingLocation
		else:
			moveAmount = 1
			startRow = 1
			enemyColor = 'w'
			kingRow, kingCol = self.blackKingLocation

		moves = []

		# Single square move forward
		if self.board[row + moveAmount][col] == "--":
			if not piecePinned or pinDirection == (moveAmount, 0):
				moves.append(Move((row, col), (row + moveAmount, col), self.board))
				# Double square move on the first move
				if row == startRow and self.board[row + 2 * moveAmount][col] == "--":
					moves.append(Move((row, col), (row + 2 * moveAmount, col), self.board))

		# Capture to the left
		if col - 1 >= 0:
			if not piecePinned or pinDirection == (moveAmount, -1):
				if self.board[row + moveAmount][col - 1][0] == enemyColor:
					moves.append(Move((row, col), (row + moveAmount, col - 1), self.board))
				# En passant to the left
				if (row + moveAmount, col - 1) == self.enPassantTargetSquare:
					if self.isEnPassantSafe(row, col, row + moveAmount, col - 1, enemyColor):
						moves.append(Move((row, col), (row + moveAmount, col - 1), self.board, isEnPassantMove=True))

		# Capture to the right
		if col + 1 < 8:
			if not piecePinned or pinDirection == (moveAmount, 1):
				if self.board[row + moveAmount][col + 1][0] == enemyColor:
					moves.append(Move((row, col), (row + moveAmount, col + 1), self.board))
				# En passant to the right
				if (row + moveAmount, col + 1) == self.enPassantTargetSquare:
					if self.isEnPassantSafe(row, col, row + moveAmount, col + 1, enemyColor):
						moves.append(Move((row, col), (row + moveAmount, col + 1), self.board, isEnPassantMove=True))

		return moves

	def isEnPassantSafe(self, startRow, startCol, endRow, endCol, enemyColor):
		"""
		Check if performing en passant leaves the king in check.
		"""
		# Temporarily update the board to simulate the en passant move
		self.board[endRow][endCol] = self.board[startRow][startCol]
		self.board[startRow][startCol] = "--"
		self.board[startRow][endCol] = "--"  # Remove the captured pawn

		kingPosition = self.whiteKingLocation if self.whiteToMove else self.blackKingLocation
		isSafe = not self.isSquareAttacked(kingPosition[0], kingPosition[1])

		# Undo the temporary move
		self.board[startRow][startCol] = self.board[endRow][endCol]
		self.board[endRow][endCol] = "--"
		self.board[startRow][endCol] = enemyColor + "p"

		return isSafe


	def rookValidMoves(self, row: int, col: int) -> list[Move]:
		moves = []
		directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
		
		for d in directions:
			for i in range(1, 8):
				endRow, endCol = row + d[0] * i, col + d[1] * i
				
				if 0 <= endRow < 8 and 0 <= endCol < 8:  # Stay in bounds
					if self.board[endRow][endCol] == "--":  # Empty square
						moves.append(Move((row, col), (endRow, endCol), self.board))
					
					elif self.board[endRow][endCol][0] != ("w" if self.whiteToMove else "b"):  # Capture
						moves.append(Move((row, col), (endRow, endCol), self.board))
						break
				
					else:  # Blocked by own piece
						break
				else:  # Out of bounds
					break
		
		return moves
	def knightValidMoves(self, row: int, col: int) -> list[Move]:
		moves = []
		knightMoves = [
			(-2, -1), (-1, -2), (1, -2), (2, -1),  # Up-Left and Up-Right
			(-2, 1), (-1, 2), (1, 2), (2, 1)      # Down-Left and Down-Right
		]

		for move in knightMoves:
			endRow, endCol = row + move[0], col + move[1]
		
			if 0 <= endRow < 8 and 0 <= endCol < 8:  # Check if within bounds
				endPiece = self.board[endRow][endCol]
	
				if endPiece == "--" or endPiece[0] != ("w" if self.whiteToMove else "b"):
					# Empty square or enemy piece
					moves.append(Move((row, col), (endRow, endCol), self.board))
	
		return moves
	def bishopValidMoves(self, row: int, col: int) -> list[Move]:
		moves = []
		directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Diagonal directions: top-left, top-right, bottom-left, bottom-right
	
		for d in directions:
			for i in range(1, 8):
				endRow, endCol = row + d[0] * i, col + d[1] * i
		
				if 0 <= endRow < 8 and 0 <= endCol < 8:  # Stay within board
					endPiece = self.board[endRow][endCol]
				
					if endPiece == "--":  # Empty square
						moves.append(Move((row, col), (endRow, endCol), self.board))
		
					elif endPiece[0] != ("w" if self.whiteToMove else "b"):  # Capture opponent's piece
						moves.append(Move((row, col), (endRow, endCol), self.board))
						break  # Stop after capturing
		
					else:  # Friendly piece blocks the path
						break
			
				else:  # Out of bounds
					break
	
		return moves
	def queenValidMoves(self, row: int, col: int) -> list[Move]:
		moves = []
		# Combine rook and bishop moves
		
		directions = [(-1, 0), (1, 0), (0, -1), (0, 1),  # Rook directions (up, down, left, right)
				  (-1, -1), (-1, 1), (1, -1), (1, 1)]  # Bishop directions (diagonals)
	
		for d in directions:
			for i in range(1, 8):
				endRow, endCol = row + d[0] * i, col + d[1] * i
				
				if 0 <= endRow < 8 and 0 <= endCol < 8:  # Stay within board
					endPiece = self.board[endRow][endCol]
					if endPiece == "--":  # Empty square
						moves.append(Move((row, col), (endRow, endCol), self.board))
					
					elif endPiece[0] != ("w" if self.whiteToMove else "b"):  # Capture opponent's piece
						moves.append(Move((row, col), (endRow, endCol), self.board))
						break  # Stop after capturing
					
					else:  # Friendly piece blocks the path
						break
				
				else:  # Out of bounds
					break
	
		return moves
	def kingValidMoves(self, kingRow: int, kingCol: int) -> list[Move]:
		validMoves = []
		kingMoves = [
			(-1, -1), (-1, 0), (-1, 1),
			(0, -1),         (0, 1),
			(1, -1), (1, 0), (1, 1)
		]

		oppColor = "b" if self.whiteToMove else "w"  # Opponent color
		allyColor = "w" if self.whiteToMove else "b"  # Ally color

		# Check each possible king move
		for move in kingMoves:
			endRow = kingRow + move[0]
			endCol = kingCol + move[1]

			# Ensure the square is within bounds
			if 0 <= endRow < 8 and 0 <= endCol < 8:
				endPiece = self.board[endRow][endCol]

				# Ensure the square is not occupied by an ally piece
				if endPiece == "--" or endPiece[0] != allyColor:
					# Temporarily move the king to this square and check if it's attacked
					originalPiece = self.board[endRow][endCol]
					self.board[kingRow][kingCol] = "--"
					self.board[endRow][endCol] = "wK" if self.whiteToMove else "bK"

					isAttacked = self.isSquareAttacked(endRow, endCol)

					# Undo the move
					self.board[kingRow][kingCol] = "wK" if self.whiteToMove else "bK"
					self.board[endRow][endCol] = originalPiece

					# If the square is not attacked, it's a valid move
					if not isAttacked:
						validMoves.append(Move((kingRow, kingCol), (endRow, endCol), self.board))

		return validMoves



	def getCastlingMoves(self, kingRow: int, kingCol: int, moves: list[Move]):
		if self.inCheck():
			return []  # King is in check, no castling moves possible
		
		if (self.whiteToMove and self.castleRights.whiteKingSide) or (not self.whiteToMove and self.castleRights.blackKingSide):
			self.kingSideCastling(kingRow, kingCol, moves)
		
		if (self.whiteToMove and self.castleRights.whiteQueenSide) or (not self.whiteToMove and self.castleRights.blackQueenSide):
			self.queenSideCastling(kingRow, kingCol, moves)


	def kingSideCastling(self, kingRow: int, kingCol: int, moves: list[Move]):
		if self.board[kingRow][kingCol + 1] == "--" and self.board[kingRow][kingCol + 2] == "--":
			if not self.isSquareAttacked(kingRow, kingCol + 1) and not self.isSquareAttacked(kingRow, kingCol + 2):
				moves.append(Move((kingRow, kingCol), (kingRow, kingCol + 2), self.board, isCastleMove = True))
	def queenSideCastling(self, kingRow: int, kingCol: int, moves: list[Move]):
		if self.board[kingRow][kingCol - 1] == "--" and self.board[kingRow][kingCol - 2] == "--" and self.board[kingRow][kingCol - 3] == "--":
			if not self.isSquareAttacked(kingRow, kingCol - 1) and not self.isSquareAttacked(kingRow, kingCol - 2):
				moves.append(Move((kingRow, kingCol), (kingRow, kingCol - 2), self.board, isCastleMove = True))



class CastleRights():
	def __init__(self, wks, wqs, bks, bqs):
		self.whiteKingSide = wks
		self.whiteQueenSide = wqs
		self.blackKingSide = bks
		self.blackQueenSide = bqs
	
	def printCastleRights(self):
		print(f"White King Side: {self.whiteKingSide}")
		print(f"White Queen Side: {self.whiteQueenSide}")
		print(f"Black King Side: {self.blackKingSide}")
		print(f"Black Queen Side: {self.blackQueenSide}")


class BestMoveFinder:
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.data = self.load_data()

    def load_data(self) -> dict:
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r") as f:
                    content = f.read().strip()
                    if content:  # Ensure content is not empty
                        return json.loads(content)
                    else:
                        print(f"Warning: {self.json_file} is empty.")
                        return {}
            except json.JSONDecodeError:
                print(f"Error: Failed to decode JSON from {self.json_file}.")
                return {}
        else:
            print(f"Warning: {self.json_file} not found.")
            return {}

    def save_data(self):
        with open(self.json_file, "w") as f:
            json.dump(self.data, f, indent=4)

    def board_to_fen(self, board: list, whiteToMove: bool, castleRights, enPassantTargetSquare: Tuple[int, int]) -> str:
        fen = ""
        for row in board:
            empty_count = 0
            for square in row:
                if square == "--":
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen += str(empty_count)
                        empty_count = 0
                    fen += square[1].upper() if square[0] == "w" else square[1].lower()
            if empty_count > 0:
                fen += str(empty_count)
            fen += "/"
        fen = fen[:-1]  # Remove the trailing slash

        fen += " w" if whiteToMove else " b"

        castle = ""
        castle += "K" if castleRights.whiteKingSide else ""
        castle += "Q" if castleRights.whiteQueenSide else ""
        castle += "k" if castleRights.blackKingSide else ""
        castle += "q" if castleRights.blackQueenSide else ""
        fen += f" {castle if castle else '-'}"

        if enPassantTargetSquare:
            enPassant = chr(enPassantTargetSquare[1] + 97) + str(8 - enPassantTargetSquare[0])
            fen += f" {enPassant}"
        else:
            fen += " -"

        fen += " 0 1"  # Placeholder for half-move and full-move counters
        return fen

    def fen_to_custom_notation(self, startSq: Tuple[int, int], endSq: Tuple[int, int], pieceMoved: str) -> str:
        start = chr(startSq[1] + 97) + str(8 - startSq[0])
        end = chr(endSq[1] + 97) + str(8 - endSq[0])
        return f"{pieceMoved}:{start}->{end}"

    def custom_notation_to_fen_move(self, move: str) -> Tuple[Tuple[int, int], Tuple[int, int], str]:
        pieceMoved, squares = move.split(":")
        start, end = squares.split("->")
        startSq = (8 - int(start[1]), ord(start[0]) - 97)
        endSq = (8 - int(end[1]), ord(end[0]) - 97)
        return startSq, endSq, pieceMoved

    def add_best_move(self, board: list, whiteToMove: bool, castleRights, enPassantTargetSquare: Tuple[int, int], startSq: Tuple[int, int], endSq: Tuple[int, int], pieceMoved: str):
        fen = self.board_to_fen(board, whiteToMove, castleRights, enPassantTargetSquare)
        move_notation = self.fen_to_custom_notation(startSq, endSq, pieceMoved)
        
        # Append to the list of moves for that FEN, instead of overwriting
        if fen in self.data:
            self.data[fen]["best_moves"].append(move_notation)
        else:
            self.data[fen] = {"best_moves": [move_notation]}
        
        self.save_data()

    def get_best_move(self, board: list, whiteToMove: bool, castleRights, enPassantTargetSquare: Tuple[int, int]) -> Optional[dict]:
        fen = self.board_to_fen(board, whiteToMove, castleRights, enPassantTargetSquare)
        return self.data.get(fen, None)

