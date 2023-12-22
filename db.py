# http://flask.pocoo.org/docs/1.0/tutorial/database/
import click
import os
from flask import current_app, g
from flask.cli import with_appcontext
from pymongo import MongoClient

def get_db():
    if "db" not in g:
        mongo_uri = os.environ.get('MONGO_URI')
        client = MongoClient(mongo_uri)
        g.db = client.users
    return g.db

def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def update_user_profile(user_id, new_name):
    db = get_db()
    users_collection = db.users
    # Update user's data. '$set' is used to update only the specified fields
    result = users_collection.update_one(
        {"_id": user_id},
        {"$set": {"name": new_name}}
    )
    return result.modified_count  # Returns the number of documents modified

def delete_user_profile(user_id):
    db = get_db()
    users_collection = db.users
    # Delete the user document from the database
    result = users_collection.delete_one({"_id": user_id})
    return result.deleted_count  # Returns the number of documents deleted