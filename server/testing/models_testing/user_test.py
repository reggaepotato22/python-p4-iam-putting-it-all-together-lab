import pytest
from models import User, Recipe, db # Ensure db is imported if you're using it directly
from sqlalchemy.exc import IntegrityError

class TestUser:
    def test_has_attributes(self, session):
        user = User(
            username="Liz",
            image_url="https://prod-images.tcm.com/Master-Profile-Images/ElizabethTaylor.jpg",
            bio="""Dame Elizabeth Rosemond Taylor DBE (February 27, 1932""" + \
                """ - March 23, 2011) was a British-American actress. """ + \
                """She began her career as a child actress in the early""" + \
                """ 1940s and was one of the most popular stars of """ + \
                """classical Hollywood cinema in the 1950s. She then""" + \
                """ became the world's highest paid movie star in the """ + \
                """1960s, remaining a well-known public figure for the """ + \
                """rest of her life. In 1999, the American Film Institute""" + \
                """ named her the seventh-greatest female screen legend """ + \
                """of Classic Hollywood cinema."""
        )
        user.password_hash = "whosafraidofvirginiawoolf"

        session.add(user)
        session.commit()

        created_user = User.query.filter(User.username == "Liz").first()

        assert(created_user.username == "Liz")
        assert(created_user.image_url == "https://prod-images.tcm.com/Master-Profile-Images/ElizabethTaylor.jpg")
        assert(created_user.bio == \
            """Dame Elizabeth Rosemond Taylor DBE (February 27, 1932""" + \
            """ - March 23, 2011) was a British-American actress. """ + \
            """She began her career as a child actress in the early""" + \
            """ 1940s and was one of the most popular stars of """ + \
            """classical Hollywood cinema in the 1950s. She then""" + \
            """ became the world's highest paid movie star in the """ + \
            """1960s, remaining a well-known public figure for the """ + \
            """rest of her life. In 1999, the American Film Institute""" + \
            """ named her the seventh-greatest female screen legend """ + \
            """of Classic Hollywood cinema.""")

    def test_requires_username(self, session):
        user = User()
        user.password_hash = "somepassword"

        session.add(user)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_requires_unique_username(self, session):
        user_1 = User(username="Ben")
        user_1.password_hash = "pass1"

        user_2 = User(username="Ben")
        user_2.password_hash = "pass2"

        session.add(user_1)
        session.commit()
        session.add(user_2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_has_list_of_recipes(self, session):
        user = User(username="Prabhdip")
        user.password_hash = "testpassword123"
        session.add(user)
        session.commit() # Commit user to get an ID

        recipe_1 = Recipe(
            title="Delicious Shed Ham",
            ingredients="Ham, pineapple, bread, glaze", # ADDED: ingredients are required
            instructions="""Or kind rest bred with am shed then. In""" + \
                """ raptures building an bringing be. Elderly is detract""" + \
                """ tedious assured private so to visited. Do travelling""" + \
                """ companions contrasted it. Mistress strongly remember""" + \
                """ up to. Ham him compass you proceed calling detract.""" + \
                """ Better of always missed we person mr. September""" + \
                """ smallness northward situation few her certainty""" + \
                """ something.""",
            minutes_to_complete=60,
            user=user # LINKED: recipe to user
        )
        recipe_2 = Recipe(
            title="Hasty Party Ham",
            ingredients="Bread, cheese, tomato, herbs", # ADDED: ingredients are required
            instructions="""As am hastily invited settled at limited""" + \
                """ civilly fortune me. Really spring in extent""" + \
                """ an by. Judge but built gay party world. Of""" + \
                """ so am he remember although required. Bachelor""" + \
                """ unpacked be advanced at. Confined in declared""" + \
                """ marianne is vicinity.""",
            minutes_to_complete=30,
            user=user # LINKED: recipe to user
        )

        user.recipes.append(recipe_1)
        user.recipes.append(recipe_2)

        session.add_all([recipe_1, recipe_2]) # Only add recipes here, user already added and committed
        session.commit()

        assert(user.id)
        assert(recipe_1.id)
        assert(recipe_2.id)

        assert(recipe_1 in user.recipes)
        assert(recipe_2 in user.recipes)
        assert recipe_1.user_id == user.id # Verify user linkage
        assert recipe_2.user_id == user.id # Verify user linkage

    def test_recipe_attributes(self, session):
        # Create a user first for the recipe's user_id
        test_user = User(username="RecipeUser", password_hash="recipepass")
        session.add(test_user)
        session.commit()

        recipe = Recipe(
            title="Test Recipe",
            ingredients="Test ingredients for the recipe.", # ADDED: ingredients are required
            instructions="Test instructions here and make sure they are long enough for the validation.",
            minutes_to_complete=15,
            user=test_user # LINKED: recipe to user
        )
        session.add(recipe)
        session.commit()
        
        assert hasattr(recipe, 'title')
        assert hasattr(recipe, 'instructions')
        assert hasattr(recipe, 'minutes_to_complete')
        assert hasattr(recipe, 'ingredients') # Assert presence of ingredients attribute
        assert hasattr(recipe, 'user_id') # Assert presence of user_id attribute

    def test_recipe_requires_title(self, session):
        # Create a user first for the recipe's user_id
        test_user = User(username="NoTitleUser", password_hash="notitlepass")
        session.add(test_user)
        session.commit()

        recipe = Recipe(
            ingredients="Required ingredients here.", # ADDED: ingredients are required
            instructions="Some instructions that are long enough to pass validation here.",
            minutes_to_complete=10,
            user=test_user # LINKED: recipe to user
        )
        session.add(recipe)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_requires_50_plus_char_instructions(self, session):
        user = User(username="ValidatorTestUser")
        user.password_hash = "testpass"
        session.add(user)
        session.commit()

        # Moved Recipe instantiation inside pytest.raises as ValueError is raised immediately
        with pytest.raises(ValueError, match="Instructions must be at least 50 characters long."):
            Recipe(
                title="Short Instructions",
                ingredients="Some ingredients here.", # ADDED: ingredients are required
                instructions="Too short", # This will trigger the ValueError on instantiation
                minutes_to_complete=10,
                user=user
            )
        # No session.add() or session.commit() here, as the error occurs before it.
        # No session.rollback() needed here as no transaction was started by add/commit.