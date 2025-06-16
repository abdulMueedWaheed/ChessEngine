from pymongo import MongoClient
import hashlib

class GameStateDatabase:
    def __init__(self, db_name='chess_db', collection_name='game_states'):
        # Connect to MongoDB
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def generate_state_hash(self, board_state):
        """
        Generate a hash for the given board state to use as a unique identifier.
        This helps in reducing the size of the data stored and quickly checking game states.
        """
        # You could use a more sophisticated method to serialize the board state if needed
        return hashlib.sha256(board_state.encode()).hexdigest()

    def store_game_state(self, board_state, best_move):
        """
        Check if the board state is already stored. If not, store the state and the best move.
        """
        state_hash = self.generate_state_hash(board_state)
        
        # Check if the game state already exists
        existing_state = self.collection.find_one({"gameState": state_hash})
        
        if existing_state:
            # If the state exists, return the best move
            return existing_state["bestMove"]
        else:
            # If the state doesn't exist, store the new game state with the best move
            self.collection.insert_one({
                "gameState": state_hash,
                "bestMove": best_move
            })
            return best_move

    def get_best_move(self, board_state):
        """
        Retrieve the best move for a given board state.
        """
        state_hash = self.generate_state_hash(board_state)
        
        # Find the game state in the database
        existing_state = self.collection.find_one({"gameState": state_hash})
        
        if existing_state:
            return existing_state["bestMove"]
        else:
            return None  # State not found, no best move available
