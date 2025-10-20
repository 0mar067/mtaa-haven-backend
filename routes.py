from flask import Blueprint

api = Blueprint('api', __name__)

@api.route('/test')
def test():
    return {'message': 'API is working'}