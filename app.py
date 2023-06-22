from initdb import db
from flask import Flask
from sqlite3 import IntegrityError
from flask_restful import Api, Resource
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minimalboard.db'
api = Api(app)
db.init_app(app)

with app.app_context():
    from models import *
    from utilities import *


class UserResource(Resource):

    def get(self, user_id):
        """
        The get function returns a user's information.
        :param user_id: Identify the user
        :return: A dictionary of the user's id, name and email
        """
        user = get_user(user_id)
        return {'id': user.id, 'name': user.name, 'email': user.email}

    def post(self):
        """
        The post function creates a new user.
        :return: a dictionary with success/failure message along with status
        """
        args = user_parser.parse_args()
        existing_user = User.query.filter_by(email=args['email']).first()
        if existing_user:
            return {'message': 'Email already exists. Please choose a different email.'}, 409
        user = User(name=args['name'], email=args['email'])
        db.session.add(user)
        db.session.commit()
        return {'message': 'User created successfully'}, 201


class BoardResource(Resource):

    def get(self, board_id):
        """
        The get function returns a board object as a ditionary with the following structure:
        {
            'id': board.id,
            'name': board.name,
            'privacy': board.privacy, # public or private
            'url': board.url,
            'users_assigned' : [user_ids], # list of user ids assigned to this particular Board instance

        :param board_id: Get the board from the database
        :return: A dictionary with the board's id, name, privacy status (public or private), url and a list of users assigned to it
        """
        board = get_board(board_id)
        user_list = [user.id for user in board.users]
        board_data = {
            'id': board.id,
            'name': board.name,
            'privacy': board.privacy,
            'url': board.url,
            'users_assigned': user_list,
            'board_lists' : []
        }
        board_lists = BoardList.query.filter_by(board_id=board.id).all()
        for board_list in board_lists:
            board_list_data = {
                'board_list_id': board_list.id,
                'board_list_name': board_list.name,
                'cards': []
            }
            cards = Card.query.filter_by(board_list_id=board_list.id).all()
            for card in cards:
                user = card.user_id or None
                card_data = {
                    'card_id': card.id,
                    'card_name': card.name,
                    'card_description': card.description,
                    'assigned_user': user
                }
                board_list_data['cards'].append(card_data)
            board_data['board_lists'].append(board_list_data) 
        return board_data
    
    def post(self):
        """
        The post function creates a new board.
        :return: a dictionary with success/failure message along with status
        """
        args = board_parser.parse_args()
        existing_board = Board.query.filter_by(name=args['name']).first()
        if existing_board:
            return {'message': f'Board with name {args["name"]} already exists. Please choose a different name.'}, 409
        board = Board(name=args['name'], privacy=args['privacy'])
        db.session.add(board)
        db.session.flush()
        board.generate_url()
        return {'message': 'Board created successfully'}, 201

    def patch(self, board_id):
        """
        The patch function allows a user to add other users to the board.
        The function takes in a list of user IDs and adds them to the board's
        users attribute.
        :param board_id: Get the board object from the database
        :return: a dictionary with success/failure message along with status
        """
        board = get_board(board_id)
        parser = reqparse.RequestParser()
        parser.add_argument('user_ids', type=int, action='append', required=True, help="User IDs are required.")
        args = parser.parse_args()

        for user_id in args['user_ids']:
            user = get_user(user_id)
            if user not in board.users:
                board.users.append(user)

        db.session.commit()
        return {'message': 'Board users updated successfully'}, 200

    def put(self, board_id):
        """
        The put function updates the board with the given id.
        Args:
            board_id (int): The id of the board to be updated.
        :param board_id: Get the board from the database
        :return: a dictionary with success/failure message along with status
        """
        board = get_board(board_id)
        args = board_parser.parse_args()
        board.name = args['name']
        board.privacy = args['privacy']
        db.session.commit()
        return {'message': 'Board updated successfully'}, 200

    def delete(self, board_id):
        """
        The delete function deletes a board from the database. Deleting a board deletes all board lists and cards under it.
        Args:
            board_id (int): The id of the board to delete.
        :param board_id: Identify the board to be deleted
        :return: a dictionary with success/failure message along with status
        """
        board = get_board(board_id)
        db.session.delete(board)
        db.session.commit()
        return {'message': 'Board deleted successfully'}, 200


class BoardListResource(Resource):

    def get(self, board_list_id):
        """
        The get function returns a board list with all of its cards.
        :param board_list_id: Get the board list by id
        :return: A dictionary with the board_list name, id and cards under it
        """
        board_list = get_board_list(board_list_id)
        board_list_data = {
            'id': board_list.id,
            'name': board_list.name,
            'board_id': board_list.board_id,
            'cards':[]
            }
        cards = Card.query.filter_by(board_list_id=board_list_id).all()
        for card in cards:
            user = card.user_id or None
            card_data = {
                'card_id': card.id,
                'card_name': card.name,
                'card_description': card.description,
                'assigned_user': user
            }
            board_list_data['cards'].append(card_data)
        return board_list_data

    def post(self):
        """
        The post function creates a new board list within the specified board.
        Args:
            name (str): The name of the new board list.
            board_id (int): The id of the parent Board object to which this BoardList belongs.
        :return: a dictionary with success/failure message along with status
        """
        args = board_list_parser.parse_args()
        existing_board = Board.query.filter_by(id=args['board_id']).first()
        if not existing_board:
            return {'message': f'Board with board id {args["board_id"]} does not exist'}, 500
        if BoardList.query.filter_by(board_id=args['board_id'], name=args['name']).first():
            return {'message': 'A board list with the same name already exists within the board.'}, 409
        board_list = BoardList(name=args['name'], board_id=args['board_id'])
        db.session.add(board_list)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {'message': 'An error occurred while creating the board list.'}, 500            
        return {'message': 'Board list created successfully.', 'board_list_id': board_list.id}, 201

    def put(self,board_list_id):
        """
        The put function allows the user to update a board list's name.
        The function takes in a board_list_id and an updated name for the board list.
        It then updates the database with this new information.
        :param board_list_id: Identify the board list that is being updated
        :return: A dictionary with the board list id and name that was updated
        """
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        args = parser.parse_args()
        board_list = BoardList.query.get(board_list_id)
        if not board_list:
            return {'message': 'Board list not found'}, 404
        board_list.name = args['name']
        db.session.commit()
        return {
            'board_list_id': board_list.id,
            'board_list_name': board_list.name
        }

    def delete(self, board_list_id):
        """
        The delete function deletes a board list from the database.
        Args:
            board_list_id (int): The id of the board list to delete.
        :param board_list_id: Identify the board list to be deleted
        :return: a dictionary with success/failure message along with status
        """
        board_list = get_board_list(board_list_id)
        db.session.delete(board_list)
        db.session.commit()
        return {'message': 'Board list deleted successfully'}, 200


class CardResource(Resource):

    def get(self, card_id):
        """
        The get function returns a card object with the following fields:
        id: The unique identifier for the card.
        name: The name of the card.
        description: A short description of what is on this card.
        board_list_id: The list that this card belongs to (foreign key).
        :param card_id: Get the card with that id
        :return: A dictionary of the card object
        """
        card = get_card(card_id)
        return {
            'id': card.id,
            'name': card.name,
            'description': card.description,
            'board_list_id': card.board_list_id,
            'user_id': card.user_id
        }

    def post(self):
        """
        The post function creates a new card using given board list id and card name and description that is part of the
        request body
        :return: A tuple of the message and a status code
        """
        args = card_parser.parse_args()
        board_list = get_board_list(args['board_list_id'])
        board_id = board_list.board_id
        board = get_board(board_id)
        card = Card(name=args['name'], description=args['description'], board_list=board_list)
        if args['user_id']:
            user = get_user(args['user_id'])
            if user not in board.users:
                return {'message': f'Add user to {board.name} board to access within card'}, 500
            card.user = user
        db.session.add(card)
        db.session.commit()
        return {'message': 'Card created successfully'}, 201

    def put(self, card_id):
        """
        The put function updates a card with the given id.
        The function takes in the following parameters:
        - name (string): The new name of the card. If not provided, then it will remain unchanged.
        - description (string): The new description of the card. If not provided, then it will remain unchanged. 
        - board_list_id (int): The id of a board_list that is in this same board as this card's current list to move to that list instead.
        :param card_id: Get the card from the database
        :return: a dictionary with success/failure message along with status
        """
        card = get_card(card_id)
        if not card:
            return {'message': f'Card with card id {card_id} does not exist'}, 500
        board_list_id = card.board_list_id
        board_list = get_board_list(board_list_id)
        board_id = board_list.board_id
        board = get_board(board_id)
        args = update_card_parser.parse_args()
        if args['name']:
            card.name = args['name']

        if args['description']:
            card.description = args['description']

        if args['board_list_id']:
            board_list = get_board_list(args['board_list_id'])
            if board_list in board.board_lists:
                card.board_list_id = board_list.id
            else:
                return {'message': f'Cannot assign card to board list that is not in the same board'}, 500 

        if args['user_id']:
            if args['user_id'] != -1:
                user = get_user(args['user_id'])
                if user not in board.users:
                    return {'message': f'Add user to {board.name} board to access within card'}, 500
                card.user = user
                card.user_id = user.id
            else:
                card.user = None
                card.user_id = None
        db.session.commit()
        return {'message': 'Card updated successfully'}, 200

    def delete(self, card_id):
        """
        The delete function deletes a card from the database.
        Args: card_id (int): The id of the card to be deleted.
        :param card_id: Identify the card to be deleted
        :return: a dictionary with success/failure message along with status
        """
        card = get_card(card_id)
        db.session.delete(card)
        db.session.commit()
        return {'message': 'Card deleted successfully'}, 200
    
class AllBoardsDataResource(Resource):
    def get(self):
        """
        The get function returns a list of boards, each board containing a list of lists,
        each list containing a list of cards. Each card contains the following information:
        card_id, card_name, card_description and assigned user.
        :return: A list of dictionaries
        """
        boards = Board.query.all()
        result = []
        for board in boards:
            board_data = {
                'board_id': board.id,
                'board_name': board.name,
                'users': [user.id for user in board.users],
                'board_lists': []
            }
            board_lists = BoardList.query.filter_by(board_id=board.id).all()
            for board_list in board_lists:
                board_list_data = {
                    'board_list_id': board_list.id,
                    'board_list_name': board_list.name,
                    'cards': []
                }
                cards = Card.query.filter_by(board_list_id=board_list.id).all()
                for card in cards:
                    user = card.user_id or None
                    card_data = {
                        'card_id': card.id,
                        'card_name': card.name,
                        'card_description': card.description,
                        'assigned_user': user
                    }
                    board_list_data['cards'].append(card_data)
                board_data['board_lists'].append(board_list_data)
            result.append(board_data)
        return result

class AllBoardsResource(Resource):
    def get(self):
        """
        The get function returns a list of all boards in the database.
        The function queries the Board table and creates a list of dictionaries, each dictionary containing information about
        one board and its child board list and cards respectively.
        The function then returns this list as JSON data.
        :return: A dictionary with the key 'boards' and a list of dictionaries as its value
        """
        boards = Board.query.all()
        boards_data = []
        for board in boards:
            board_data = {
                'id': board.id,
                'name': board.name,
                'privacy': board.privacy,
                'url': board.url
            }
            boards_data.append(board_data)
        return {'boards': boards_data}

api.add_resource(AllBoardsResource, '/all_boards')
api.add_resource(AllBoardsDataResource, '/all_boards_data')
api.add_resource(UserResource, '/users/<int:user_id>', '/users')
api.add_resource(BoardResource, '/boards/<int:board_id>', '/boards')
api.add_resource(BoardListResource, '/boardlists/<int:board_list_id>', '/boardlists')
api.add_resource(CardResource, '/cards/<int:card_id>', '/cards')



if __name__ == '__main__':
    app.run(debug=True)