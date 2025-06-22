#!/usr/bin/env python3

from flask import request, session, make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api, bcrypt
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')

        if not username:
            return {'errors': ['Username is required.']}, 400
        if not password:
            return {'errors': ['Password is required.']}, 400

        try:
            new_user = User(
                username=username,
                password_hash=password,
                bio=data.get('bio'),
                image_url=data.get('image_url')
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            session['user_id'] = new_user.id
            
            return make_response(new_user.to_dict(), 201)
        
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username must be unique']}, 422
        except ValueError as e:
            return {'errors': [str(e)]}, 400
        except Exception as e:
            db.session.rollback()
            return {'errors': ['An unexpected error occurred during signup']}, 500

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.filter_by(id=user_id).first()
            if user:
                return make_response(user.to_dict(), 200)
        return {'message': 'Not logged in'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session['user_id'] = user.id
            return make_response(user.to_dict(), 200)
        
        return {'errors': ['Invalid username or password']}, 401

class Logout(Resource):
    def delete(self):
        session['user_id'] = None
        return {'message': 'Logged out successfully'}, 204

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'errors': ['Unauthorized: Must be logged in to view recipes']}, 401 # Corrected message 
            
        recipes = Recipe.query.all()
        return make_response([recipe.to_dict() for recipe in recipes], 200)

    def post(self):
        data = request.get_json()
        user_id = session.get('user_id')

        if not user_id:
            return {'errors': ['Unauthorized: Must be logged in to create a recipe']}, 401

        # Add validation for all required fields including 'ingredients' 
        required_fields = ['title', 'ingredients', 'instructions', 'minutes_to_complete']
        for field in required_fields:
            if not data.get(field):
                return {'errors': [f"'{field}' is required."]}, 400
        
        if len(data.get('instructions', '')) < 50:
            return {'errors': ['Instructions must be at least 50 characters long.']}, 400

        try:
            new_recipe = Recipe(
                title=data['title'],
                ingredients=data['ingredients'],
                instructions=data['instructions'],
                minutes_to_complete=data['minutes_to_complete'],
                user_id=user_id
            )
            db.session.add(new_recipe)
            db.session.commit()
            return make_response(new_recipe.to_dict(), 201)
        except ValueError as e:
            return {'errors': [str(e)]}, 400
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Recipe creation failed due to data integrity issues.']}, 422
        except Exception as e:
            db.session.rollback()
            return {'errors': [f'An unexpected error occurred during recipe creation: {e}']}, 500

def register_resources(api_instance):
    api_instance.add_resource(Signup, '/signup', endpoint='signup')
    api_instance.add_resource(CheckSession, '/check_session', endpoint='check_session')
    api_instance.add_resource(Login, '/login', endpoint='login')
    api_instance.add_resource(Logout, '/logout', endpoint='logout')
    api_instance.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    register_resources(api)
    app.run(port=5555, debug=True)