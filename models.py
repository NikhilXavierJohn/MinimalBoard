from initdb import db
from sqlalchemy import UniqueConstraint

board_users = db.Table('board_users',
    db.Column('board_id', db.Integer, db.ForeignKey('boards.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)

    def __init__(self, name, email):
        self.name = name
        self.email = email


class Board(db.Model):
    __tablename__ = 'boards'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    privacy = db.Column(db.String(20), default='PUBLIC')
    url = db.Column(db.String(100), unique=True)
    users = db.relationship('User', secondary=board_users, backref=db.backref('boards', lazy='dynamic'))
    board_lists = db.relationship('BoardList', backref='parent_board', cascade='all, delete')

    def __init__(self, name, privacy='PUBLIC'):
        self.name = name
        self.privacy = privacy

    def generate_url(self):
        self.url = f'http://localhost:5000/boards/{self.id}'
        db.session.commit()

class BoardList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    board_id = db.Column(db.Integer, db.ForeignKey('boards.id'))
    board = db.relationship('Board', backref=db.backref('lists', lazy=True))
    cards = db.relationship('Card', backref='parent_board_list', cascade='all, delete')

    __table_args__ = (
        UniqueConstraint('name', 'board_id', name='uq_board_list_name_board_id'),
    )

    def __init__(self, name, board_id):
        self.name = name
        self.board_id = board_id

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    board_list_id = db.Column(db.Integer, db.ForeignKey('board_list.id'), nullable=False)
    board_list = db.relationship('BoardList', backref=db.backref('board_cards', lazy=True),overlaps='cards,parent_board_list')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('cards', lazy=True))
    

# Initialize the database
db.create_all()