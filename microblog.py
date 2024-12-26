import sqlalchemy as sa
import sqlalchemy.orm as so
from Y import create_app, db
from Y.models import User, Post

app= create_app()
# this decorator registers the function as a 'shell context' function
# 'flask shell' command will register the items here inside the shell session
@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Post': Post}

# The flask run command will look for a Flask application instance in the module referenced 
# by the FLASK_APP environment variable, 
# which in this case is microblog.py. 
# The command sets up a web server that is configured to forward requests to 
# this application.