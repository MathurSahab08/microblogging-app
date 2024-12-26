from flask import Blueprint

bp = Blueprint('main', __name__)

from Y.main import routes