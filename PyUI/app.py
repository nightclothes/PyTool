"""
PyUI Flask 后端服务
提供数据接口和页面渲染
"""
from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)

# 内存数据库
employees = [
    {"id": 1, "name": "张三", "age": 25, "position": "开发工程师"},
    {"id": 2, "name": "李四", "age": 30, "position": "产品经理"}
]

@app.route('/')
def index():
    """渲染前端页面"""
    return render_template('index.html')

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """获取员工数据"""
    return jsonify({
        "success": True,
        "data": employees,
        "total": len(employees)
    })

@app.route('/api/employees', methods=['POST'])
def add_employee():
    """添加新员工"""
    data = request.json
    
    # 数据验证
    if not all(key in data for key in ['name', 'age', 'position']):
        return jsonify({
            "success": False,
            "message": "缺少必要参数"
        }), 400
    
    # 生成ID并添加数据
    new_id = max(e['id'] for e in employees) + 1 if employees else 1
    new_employee = {
        "id": new_id,
        "name": data['name'],
        "age": data['age'],
        "position": data['position']
    }
    employees.append(new_employee)
    
    return jsonify({
        "success": True,
        "data": new_employee,
        "message": "添加成功"
    })

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5000)
