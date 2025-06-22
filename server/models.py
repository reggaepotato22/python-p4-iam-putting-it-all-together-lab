from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import validates # ADDED: Import validates
from config import db, bcrypt # Ensure bcrypt is imported from config

class User(db.Model, SerializerMixin):
    __tablename__ = 'users' # Explicitly set table name

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    _password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.String(255))
    image_url = db.Column(db.String(255))

    recipes = db.relationship('Recipe', backref='user', lazy=True, cascade='all, delete-orphan')

    serialize_rules = ('-_password_hash', '-recipes.user') # Exclude password and avoid circular reference

    @hybrid_property
    def password_hash(self):
        return self._password_hash

    @password_hash.setter
    def password_hash(self, password):
        # Ensure the password is encoded to bytes before hashing
        self._password_hash = bcrypt.generate_password_hash(
            password.encode('utf-8')).decode('utf-8')

    @hybrid_method
    def authenticate(self, password):
        # Ensure the provided password is encoded to bytes for checking
        return bcrypt.check_password_hash(
            self._password_hash, password.encode('utf-8'))

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'bio': self.bio,
            'image_url': self.image_url
        }

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes' # Explicitly set table name

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    minutes_to_complete = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    serialize_rules = ('-user.recipes',) # Avoid circular serialization

    # ADDED: Validation for instructions length
    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if not instructions or len(instructions) < 50:
            raise ValueError("Instructions must be at least 50 characters long.")
        return instructions

    def __repr__(self):
        return f'<Recipe {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'ingredients': self.ingredients,
            'instructions': self.instructions,
            'minutes_to_complete': self.minutes_to_complete,
            'user_id': self.user_id
        }