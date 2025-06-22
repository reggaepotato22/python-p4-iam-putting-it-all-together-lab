import pytest
from sqlalchemy.exc import IntegrityError
from models import db, Recipe, User # Import User as well, since recipes need a user_id

class TestRecipe:
    def test_has_attributes(self, session): # Use the session fixture
        # Create a user for the recipe, as user_id is nullable=False
        test_user = User(
            username="RecipeTestUser",
            password_hash="securepassword",
            bio="A user for recipe tests.",
            image_url="http://example.com/user.jpg"
        )
        session.add(test_user)
        session.commit() # Commit to get an ID for the user

        recipe = Recipe(
            title="Delicious Shed Ham",
            ingredients="1 cup ham, 1/2 cup cheese, 2 slices bread", # ADDED ingredients
            instructions="""Or kind rest bred with am shed then. In""" + \
                         """ raptures building an bringing be. Elderly is detract""" + \
                         """ tedious assured private so to visited. Do travelling""" + \
                         """ companions contrasted it. Mistress strongly remember""" + \
                         """ up to. Ham him compass you proceed calling detract.""" + \
                         """ Better of always missed we person mr. September""" + \
                         """ smallness northward situation few her certainty""" + \
                         """ something.""",
            minutes_to_complete=60,
            user_id=test_user.id # ADDED user_id
        )

        session.add(recipe)
        session.commit() # Commit the recipe

        new_recipe = Recipe.query.filter(Recipe.title == "Delicious Shed Ham").first()

        assert new_recipe.title == "Delicious Shed Ham"
        assert new_recipe.ingredients == "1 cup ham, 1/2 cup cheese, 2 slices bread" # Assert ingredients
        assert new_recipe.instructions == """Or kind rest bred with am shed then. In""" + \
                                          """ raptures building an bringing be. Elderly is detract""" + \
                                          """ tedious assured private so to visited. Do travelling""" + \
                                          """ companions contrasted it. Mistress strongly remember""" + \
                                          """ up to. Ham him compass you proceed calling detract.""" + \
                                          """ Better of always missed we person mr. September""" + \
                                          """ smallness northward situation few her certainty""" + \
                                          """ something."""
        assert new_recipe.minutes_to_complete == 60
        assert new_recipe.user_id == test_user.id # Assert user_id

    def test_requires_title(self, session): # Use the session fixture
        # Create a user first for the recipe's user_id
        test_user = User(username="TitleTestUser", password_hash="testpass")
        session.add(test_user)
        session.commit()

        # Attempt to create a recipe without a title
        recipe = Recipe(
            ingredients="Sugar, spice, everything nice",
            instructions="""These instructions are definitely more than fifty characters long, so they should pass validation without any issues.""",
            minutes_to_complete=10,
            user_id=test_user.id # Provide user_id
        )
        
        with pytest.raises(IntegrityError):
            session.add(recipe)
            session.commit()
        session.rollback() # Rollback the session after the assert to clean up the failed transaction

    def test_requires_50_plus_char_instructions(self, session): # Use the session fixture
        # Create a user first for the recipe's user_id
        test_user = User(username="InstructionsTestUser", password_hash="testpass")
        session.add(test_user)
        session.commit()

        # Must raise either a sqlalchemy.exc.IntegrityError (if instructions is nullable=False and not provided)
        # or a custom validation ValueError (if you have a @validates decorator in your model).
        # Based on your current model, it should be ValueError if `instructions` length is checked.
        # If `instructions` is nullable=False but empty string is allowed, then it's ValueError.
        # If no instructions are given and it's nullable=False, it's IntegrityError.
        
        with pytest.raises( (IntegrityError, ValueError) ): # Keep both for robustness
            recipe = Recipe(
                title="Generic Ham",
                ingredients="Ham, pineapple, bread", # ADDED ingredients
                instructions="idk lol", # Too short
                minutes_to_complete=10,
                user_id=test_user.id # ADDED user_id
            )
            session.add(recipe)
            session.commit()
        session.rollback() # Rollback the session after the assert