from flask import Blueprint, request, jsonify

api = Blueprint('api', __name__)

@api.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'API is working'})

@api.route('/test', methods=['POST'])
def test_post():
    try:
        data = request.get_json()
        if data is None or data == {}:
            return jsonify({'error': 'No JSON data provided'}), 400
        return jsonify({'received': data, 'message': 'Data received successfully'})
    except Exception as e:
        return jsonify({'error': 'Invalid JSON data'}), 400