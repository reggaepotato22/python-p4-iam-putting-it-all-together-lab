import pytest
from flask import Flask
from models import db # Import db from models, assuming db is initialized in config
from config import bcrypt # Only import bcrypt, not api
from flask_restful import Api # Import the Api class itself
from app import register_resources # Assuming this function exists in your app.py

@pytest.fixture(scope='session')
def app():
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory SQLite for testing
    test_app.config['SECRET_KEY'] = b'a\xdb\xd2\x13\x93\xc1\xe9\x97\xef2\xe3\x004U\xd1Z'
    
    with test_app.app_context():
        db.init_app(test_app) # Initialize db with the test_app
        bcrypt.init_app(test_app) # Initialize bcrypt with the test_app
        
        # Create a NEW Flask-RESTful Api instance for the test_app
        test_api = Api(test_app) 
        
        # Register resources with this new test_api instance
        register_resources(test_api) 
        
        # db.create_all() and db.drop_all() are now handled by the function-scoped fixture
        # db.create_all() # Removed from here
    
    yield test_app

    # db.drop_all() # Removed from here, now handled by the function-scoped fixture

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def session(app):
    with app.app_context():
        # Use nested transaction for function-scoped database isolation
        # This allows you to test database operations without committing them
        # to the actual in-memory database of the session scope.
        db.session.begin_nested()
        yield db.session
        db.session.rollback() # Rollback all changes made during the test
        db.session.close() # Close the session after rollback

# New fixture to ensure a clean database for EACH test function
@pytest.fixture(autouse=True)
def setup_teardown_tables(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield
        # db.drop_all() # Optional: You can drop tables again after each test, but begin_nested() rollback usually handles it.