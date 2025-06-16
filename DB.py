import json
import os
from typing import Tuple, Optional

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
