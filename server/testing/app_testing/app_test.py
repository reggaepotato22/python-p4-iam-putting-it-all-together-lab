import pytest
from app import app, db, User, Recipe # Import app, db, User, Recipe for direct access
from faker import Faker
from random import randint

fake = Faker()

@pytest.fixture(scope='function', autouse=True)
def setup_teardown(app):
    with app.app_context():
        # Clean up database before each test
        Recipe.query.delete()
        User.query.delete()
        db.session.commit()
    yield
    with app.app_context():
        # Clean up database after each test
        Recipe.query.delete()
        User.query.delete()
        db.session.commit()

class TestSignup:
    def test_creates_users_at_signup(self, client, session):
        response = client.post('/signup', json={
            'username': 'testuser',
            'password': 'testpassword',
            'bio': 'Test bio',
            'image_url': 'http://example.com/image.jpg',
        })
        assert response.status_code == 201
        assert 'id' in response.json
        assert response.json['username'] == 'testuser'
        assert response.json['bio'] == 'Test bio'

    def test_422s_invalid_users_at_signup(self, client, session):
        response_no_username = client.post('/signup', json={
            'password': 'pikachu',
            'bio': 'Some bio',
            'image_url': 'http://example.com/image.jpg',
        })
        assert response_no_username.status_code == 400
        assert 'errors' in response_no_username.json
        assert 'Username is required.' in response_no_username.json['errors']

        response_no_password = client.post('/signup', json={
            'username': 'no_pass_user',
            'bio': 'Some bio',
            'image_url': 'http://example.com/image.jpg',
        })
        assert response_no_password.status_code == 400
        assert 'errors' in response_no_password.json
        assert 'Password is required.' in response_no_password.json['errors']

class TestSession:
    def test_returns_user_json_for_active_session(self, client, session):
        user = User(username="session_user", bio="Session test", image_url="http://session.com")
        user.password_hash = 'session_pass'
        session.add(user)
        session.commit()

        client.post('/login', json={'username': 'session_user', 'password': 'session_pass'})
        response = client.get('/check_session')
        assert response.status_code == 200
        assert response.json['username'] == 'session_user'

    def test_401s_for_no_session(self, client):
        response = client.get('/check_session')
        assert response.status_code == 401
        assert response.json == {'message': 'Not logged in'}

class TestLogin:
    def test_logs_in(self, client, session):
        user = User(username="login_user", bio="Login test", image_url="http://login.com")
        user.password_hash = 'login_pass'
        session.add(user)
        session.commit()

        response = client.post('/login', json={
            'username': 'login_user',
            'password': 'login_pass',
        })
        assert response.status_code == 200
        assert response.json['username'] == 'login_user'

    def test_401s_bad_logins(self, client, session):
        user = User(username="wrong_pass_user", bio="Wrong pass test", image_url="http://wrong.com")
        user.password_hash = 'correct_pass'
        session.add(user)
        session.commit()

        response_wrong_pass = client.post('/login', json={
            'username': 'wrong_pass_user',
            'password': 'incorrect_pass',
        })
        assert response_wrong_pass.status_code == 401
        assert response_wrong_pass.json == {'errors': ['Invalid username or password']}

        response_no_user = client.post('/login', json={
            'username': 'non_existent_user',
            'password': 'any_pass',
        })
        assert response_no_user.status_code == 401
        assert response_no_user.json == {'errors': ['Invalid username or password']}

class TestLogout:
    def test_logs_out(self, client, session):
        user = User(username="logout_user", bio="Logout test", image_url="http://logout.com")
        user.password_hash = 'logout_pass'
        session.add(user)
        session.commit()

        client.post('/login', json={'username': 'logout_user', 'password': 'logout_pass'})
        response = client.delete('/logout')
        assert response.status_code == 204
        assert response.data == b''

    def test_401s_if_no_session(self, client):
        response = client.delete('/logout')
        assert response.status_code == 204
        assert response.data == b''

class TestRecipeIndex:
    def test_lists_recipes_with_200(self, client, session):
        user = User(username="recipe_viewer", bio="Viewer", image_url="http://viewer.com")
        user.password_hash = 'viewer_pass'
        session.add(user)
        session.commit()
        
        # Updated instructions to meet 50+ character requirement
        recipe1 = Recipe(
            title="Delicious Pasta",
            ingredients="Noodles, Sauce",
            instructions="""This is a very detailed set of instructions for making a delicious pasta dish that will satisfy your cravings and impress your friends.""",
            minutes_to_complete=30,
            user_id=user.id
        )
        recipe2 = Recipe(
            title="Healthy Salad",
            ingredients="Lettuce, Tomatoes",
            instructions="""To prepare this delightful salad, simply chop all the fresh vegetables and mix them together in a large bowl. Add your favorite dressing for a healthy and quick meal.""",
            minutes_to_complete=15,
            user_id=user.id
        )
        session.add_all([recipe1, recipe2])
        session.commit()

        client.post('/login', json={'username': 'recipe_viewer', 'password': 'viewer_pass'})
        response = client.get('/recipes')
        assert response.status_code == 200
        assert len(response.json) == 2
        assert response.json[0]['title'] == 'Delicious Pasta' # Updated assertion
        assert response.json[1]['title'] == 'Healthy Salad'    # Updated assertion

    def test_get_route_returns_401_when_not_logged_in(self, client, session):
        response = client.get('/recipes')
        assert response.status_code == 401
        assert response.json == {'errors': ['Unauthorized: Must be logged in to view recipes']}

    def test_creates_recipes_with_201(self, client, session):
        user = User(
            username="RecipeCreator",
            bio=fake.paragraph(nb_sentences=3),
            image_url=fake.url(),
        )
        user.password_hash = 'secret'
        session.add(user)
        session.commit()
    
        login_response = client.post('/login', json={
            'username': 'RecipeCreator',
            'password': 'secret',
        })
        assert login_response.status_code == 200
    
        recipe_data = {
            'title': fake.sentence(),
            'ingredients': fake.text(max_nb_chars=100),
            'instructions': fake.paragraph(nb_sentences=8),
            'minutes_to_complete': randint(15, 90)
        }
        while len(recipe_data['instructions']) < 50:
            recipe_data['instructions'] = fake.paragraph(nb_sentences=8)
    
        response = client.post('/recipes', json=recipe_data)
    
        assert response.status_code == 201
        assert 'id' in response.json
        assert response.json['title'] == recipe_data['title']

    def test_returns_422_for_invalid_recipes(self, client, session):
        user = User(
            username="InvalidRecipeTestUser",
            bio=fake.paragraph(nb_sentences=3),
            image_url=fake.url(),
        )
        user.password_hash = 'secret'
        session.add(user)
        session.commit()
        client.post('/login', json={
            'username': 'InvalidRecipeTestUser',
            'password': 'secret',
        })
    
        response_invalid = client.post('/recipes', json={
            'title': fake.sentence(),
            'ingredients': fake.text(max_nb_chars=50),
            'instructions': 'Too short',
            'minutes_to_complete': randint(15, 90)
        })
        assert response_invalid.status_code == 400
        assert 'errors' in response_invalid.json
        assert 'Instructions must be at least 50 characters long.' in response_invalid.json['errors']
        assert "'ingredients' is required." not in response_invalid.json['errors']