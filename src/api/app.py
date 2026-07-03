import logging
from flask import Flask, jsonify, request
from src.data_engine.storage import get_engine, read_table

logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/data')
def get_data():
    table = request.args.get('table', 'rel_razao')
    limit = request.args.get('limit')
    try:
        df = read_table(table, limit=limit)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        logger.exception('Error reading table %s', table)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
