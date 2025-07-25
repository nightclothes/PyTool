"""
交易信息管理模块
"""
from flask import Blueprint, request, jsonify, session
import uuid

# 交易蓝图
trade_bp = Blueprint('trade', __name__)

# 简单的内存交易数据结构
trades_db = [
    {"id": str(uuid.uuid4()), "symbol": "AAPL", "quantity": 100, "price": 175.25, "total": 17525.0, "date": "2023-10-01", "type": "buy", "status": "completed"},
    {"id": str(uuid.uuid4()), "symbol": "GOOGL", "quantity": 50, "price": 135.60, "total": 6780.0, "date": "2023-10-02", "type": "sell", "status": "completed"},
    {"id": str(uuid.uuid4()), "symbol": "MSFT", "quantity": 75, "price": 315.75, "total": 23681.25, "date": "2023-10-03", "type": "buy", "status": "pending"}
]

@trade_bp.route('/trades', methods=['GET'])
def get_trades():
    """获取交易信息列表"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "未登录"}), 401
    return jsonify({
        "success": True,
        "data": trades_db,
        "total": len(trades_db)
    })

@trade_bp.route('/trades', methods=['POST'])
def add_trade():
    """添加新交易"""
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "未登录"}), 401
    
    data = request.json
    required_fields = ['symbol', 'quantity', 'price', 'type']
    if not all(field in data for field in required_fields):
        return jsonify({"success": False, "message": "缺少必要参数"}), 400
    
    new_trade = {
        "id": str(uuid.uuid4()),
        "symbol": data['symbol'],
        "quantity": data['quantity'],
        "price": data['price'],
        "total": data['quantity'] * data['price'],
        "date": data.get('date', "2023-10-04"),  # 临时日期，实际应用应使用当前日期
        "type": data['type'],
        "status": "pending"
    }
    trades_db.append(new_trade)
    return jsonify({
        "success": True,
        "message": "交易添加成功",
        "data": new_trade
    })
