from flask_restful import reqparse,abort
from models import *

user_parser = reqparse.RequestParser()
user_parser.add_argument('name', type=str, required=True, help="Name is required.")
user_parser.add_argument('email', type=str, required=True, help="Email is required.")

board_parser = reqparse.RequestParser()
board_parser.add_argument('name', type=str, required=True, help="Name is required.")
board_parser.add_argument('privacy', type=str, choices=['PUBLIC', 'PRIVATE'], default='PUBLIC')

board_list_parser = reqparse.RequestParser()
board_list_parser.add_argument('name', type=str, required=True, help="Name is required.")
board_list_parser.add_argument('board_id', type=int, required=True, help="Board ID is required.")

card_parser = reqparse.RequestParser()
card_parser.add_argument('name', type=str, required=True, help="Name is required.")
card_parser.add_argument('description', type=str, required=False)
card_parser.add_argument('board_list_id', type=int, required=True, help="Board List ID is required.")
card_parser.add_argument('user_id', type=int, required=False)

update_card_parser = reqparse.RequestParser()
update_card_parser.add_argument('name', type=str, required=False)
update_card_parser.add_argument('description', type=str, required=False)
update_card_parser.add_argument('board_list_id', type=int, required=False)
update_card_parser.add_argument('user_id', type=int, required=False)

def get_user(user_id):
    """
    The get_user function takes a user_id as an argument and returns the User object with that id.
    If no such user exists, it raises a 404 error.
    
    :param user_id: Get the user from the database
    :return: A user object
    """
    user = User.query.get(user_id)
    if not user:
        abort(404, message="User not found.")
    return user


def get_board(board_id):
    """
    The get_board function returns a board object from the database.
    If no board is found, it will return a 404 error.
    
    :param board_id: Get the board from the database
    :return: A board object
    """
    board = Board.query.get(board_id)
    if not board:
        abort(404, message="Board not found.")
    return board


def get_board_list(board_list_id):
    """
    The get_board_list function takes a board_list_id as an argument and returns the BoardList object with that id.
    If no such BoardList exists, it raises a 404 error.
    
    :param board_list_id: Get the board list from the database
    :return: A board list object, which is a row from the boardlist table
    """
    board_list = BoardList.query.get(board_list_id)
    if not board_list:
        abort(404, message="Board List not found.")
    return board_list


def get_card(card_id):
    """
    The get_card function returns a card object from the database.
    If no card is found, it will return a 404 error.
    
    :param card_id: Get the card from the database
    :return: A card object from the database
    """
    card = Card.query.get(card_id)
    if not card:
        abort(404, message="Card not found.")
    return card
