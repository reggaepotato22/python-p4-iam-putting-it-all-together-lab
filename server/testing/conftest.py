# testing/models_testing/conftest.py
import pytest
from flask import Flask
from models import db, User, Recipe

def pytest_itemcollected(item):
    par = item.parent.obj
    node = item.obj
    pref = par.__doc__.strip() if par.__doc__ else par.__class__.__name__
    suf = node.__doc__.strip() if node.__doc__ else node.__name__
    if pref or suf:
        item._nodeid = ' '.join((pref, suf))

@pytest.fixture(scope='session')
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True

    with app.app_context():
        db.init_app(app)
        db.create_all()

        yield app

        db.drop_all()

@pytest.fixture(scope='function')
def session(app):
    with app.app_context():
        Recipe.query.delete()
        User.query.delete()
        db.session.commit()

        yield db.session

        db.session.rollback()
        db.session.remove()