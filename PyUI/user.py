"""
用户管理模块
"""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# 用户蓝图
user_bp = Blueprint('user', __name__)

# 简单的内存用户数据结构
users_db = {
    "admin": {
        "id": str(uuid.uuid4()),
        "username": "admin",
        "password": generate_password_hash("admin123"),
        "email": "admin@example.com",
        "role": "admin"
    }
}

@user_bp.route('/register', methods=['POST'])
def register():
    """用户注册接口"""
    # 禁用注册功能
    return jsonify({
        "success": False,
        "message": "注册功能已禁用",
    })

    data = request.json
    required_fields = ['username', 'password', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({"success": False, "message": "缺少必要参数"}), 400
    if data['username'] in users_db:
        return jsonify({"success": False, "message": "用户名已存在"}), 400
    user_id = str(uuid.uuid4())
    users_db[data['username']] = {
        "id": user_id,
        "username": data['username'],
        "password": generate_password_hash(data['password']),
        "email": data['email'],
        "role": "user"
    }
    return jsonify({
        "success": True,
        "message": "注册成功",
        "data": {
            "id": user_id,
            "username": data['username'],
            "email": data['email']
        }
    })

@user_bp.route('/login', methods=['POST'])
def login():
    """用户登录接口"""
    data = request.json
    if 'username' not in data or 'password' not in data:
        return jsonify({"success": False, "message": "需要用户名和密码"}), 400
    user = users_db.get(data['username'])
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({"success": False, "message": "用户名或密码错误"}), 401
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    return jsonify({
        "success": True,
        "message": "登录成功",
        "data": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "role": user['role']
        }
    })

@user_bp.route('/logout', methods=['POST'])
def logout():
    """用户注销接口"""
    session.clear()
    return jsonify({"success": True, "message": "注销成功"})
# FIXME 检查session通过 但是拿不到信息 因为用户信息是内存的导致 uid变化 而session的uid没有变化
@user_bp.route('/user', methods=['GET'])
def get_user_info():
    """获取当前用户信息"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "未登录"}), 401
    user = next((u for u in users_db.values() if u['id'] == session['user_id']), None)
    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 404
    return jsonify({
        "success": True,
        "data": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "role": user['role']
        }
    })