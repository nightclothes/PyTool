from flask import Flask, send_from_directory, jsonify, redirect, url_for, request, session
from flask_cors import CORS
from user import user_bp
from trade_info import trade_bp
import os

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secure_secret_key_here')

# 注册蓝图
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(trade_bp, url_prefix='/api/trade')

# 配置CORS
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

# 全局错误处理
@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "服务器内部错误"}), 500

@app.before_request
def check_login():
    """检查用户登录状态，未登录则重定向到登录页面"""
    if 'user_id' not in session and request.path not in ['/', '/static/index.html', '/api/user/login', '/api/user/register'] and not request.path.startswith('/static/'):
        return redirect(url_for('index'))



@app.route('/')
def index():
    """主页面入口"""
    return send_from_directory('static', 'index.html')

@app.route('/trade_info.html')
def trade():
    """交易页面入口"""
    return send_from_directory('static', 'trade_info.html')

if __name__ == '__main__':
    os.makedirs('./PyUI/static', exist_ok=True)
    app.run(debug=True, port=5000)