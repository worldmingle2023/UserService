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