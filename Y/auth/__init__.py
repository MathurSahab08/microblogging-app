from flask import Blueprint

# blueprint creation
# Blueprint class takes the name of the blueprint and name of the base module('Y')
bp = Blueprint('auth', __name__)

from Y.auth import routes