# controller/shop_controller.py
# Controller: Quản lý cửa hàng vật phẩm

from flask import Blueprint, request, jsonify, session
from model.shop import ShopItem, ShopTransaction
from model.salary import Salary
from util.file_helper import FileHelper
from util.validation import Validation
from datetime import datetime

shop_bp = Blueprint("shop", __name__)

# ========================
# UPLOAD ẢNH CHO VẬT PHẨM (Admin)
# POST /api/shop/upload-image
# ========================
@shop_bp.route("/upload-image", methods=["POST"])
def upload_image():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    image_base64 = data.get("image", "")

    if not image_base64 or not image_base64.startswith("data:image"):
        return jsonify({"success": False, "message": "Ảnh không hợp lệ"}), 400

    if len(image_base64) > 2 * 1024 * 1024 * 1.4:
        return jsonify({"success": False, "message": "Ảnh quá lớn, vui lòng chọn ảnh dưới 2MB"}), 400

    return jsonify({
        "success": True, 
        "message": "Tải ảnh thành công",
        "image": image_base64
    })


# ========================
# QUẢN LÝ VẬT PHẨM (Admin)
# ========================

# LẤY DANH SÁCH VẬT PHẨM
# GET /api/shop/items
@shop_bp.route("/items", methods=["GET"])
def get_items():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    items = FileHelper.read_all("shop_items")
    return jsonify({"success": True, "data": items})


# THÊM VẬT PHẨM (Admin)
# POST /api/shop/items
@shop_bp.route("/items", methods=["POST"])
def add_item():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    try:
        name = Validation.check_not_empty(data.get("name", ""), "Tên vật phẩm")
        price = Validation.check_money(data.get("price", 0), "Giá")
        stock = int(data.get("stock", 0))
        if stock < 0:
            raise ValueError("Số lượng tồn kho không được âm")
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    item = ShopItem(
        name=name,
        description=data.get("description", ""),
        price=price,
        stock=stock,
        image=data.get("image", "")
    )
    FileHelper.append_item("shop_items", item.to_dict())
    return jsonify({"success": True, "message": "Thêm vật phẩm thành công", "id": item.id}), 201


# CẬP NHẬT VẬT PHẨM (Admin)
# PUT /api/shop/items/<id>
@shop_bp.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    data = request.get_json()
    try:
        name = Validation.check_not_empty(data.get("name", ""), "Tên vật phẩm")
        price = Validation.check_money(data.get("price", 0), "Giá")
        stock = int(data.get("stock", 0))
        if stock < 0:
            raise ValueError("Số lượng tồn kho không được âm")
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    items = FileHelper.read_all("shop_items")
    for i, item in enumerate(items):
        if item["id"] == item_id:
            items[i]["name"] = name
            items[i]["description"] = data.get("description", "")
            items[i]["price"] = price
            items[i]["stock"] = stock
            items[i]["image"] = data.get("image", "")
            items[i]["status"] = data.get("status", "active")
            FileHelper.write_all("shop_items", items)
            return jsonify({"success": True, "message": "Cập nhật thành công"})

    return jsonify({"success": False, "message": "Không tìm thấy vật phẩm"}), 404


# XÓA VẬT PHẨM (Admin)
# DELETE /api/shop/items/<id>
@shop_bp.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Không có quyền"}), 403

    ok = FileHelper.delete_item("shop_items", item_id)
    if not ok:
        return jsonify({"success": False, "message": "Không tìm thấy vật phẩm"}), 404

    return jsonify({"success": True, "message": "Đã xóa vật phẩm"})


# ========================
# MUA HÀNG (Nhân viên)
# ========================

# MUA VẬT PHẨM
# POST /api/shop/purchase
@shop_bp.route("/purchase", methods=["POST"])
def purchase_item():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    data = request.get_json()
    try:
        item_id = int(data.get("item_id", 0))
        quantity = int(data.get("quantity", 1))
        if quantity <= 0:
            raise ValueError("Số lượng phải lớn hơn 0")
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    # Lấy thông tin nhân viên
    employees = FileHelper.read_all("employees")
    emp = next((e for e in employees if e["id"] == session["employee_id"]), None)
    if not emp:
        return jsonify({"success": False, "message": "Không tìm thấy nhân viên"}), 404

    # Lấy thông tin vật phẩm
    items = FileHelper.read_all("shop_items")
    item = next((i for i in items if i["id"] == item_id and i["status"] == "active"), None)
    if not item:
        return jsonify({"success": False, "message": "Vật phẩm không tồn tại hoặc đã ngừng bán"}), 404

    # Kiểm tra tồn kho
    if item["stock"] < quantity:
        return jsonify({"success": False, "message": f"Tồn kho không đủ. Chỉ còn {item['stock']} sản phẩm"}), 400

    # Kiểm tra số dư (tính tổng lương đã nhận)
    salaries = FileHelper.read_all("salaries")
    total_salary = sum(s.get("total", 0) for s in salaries if s["employee_id"] == session["employee_id"])

    # Tính tổng tiền đã chi tiêu từ shop_transactions
    transactions = FileHelper.read_all("shop_transactions")
    total_spent = sum(t.get("total", 0) for t in transactions if t["employee_id"] == session["employee_id"])

    balance = total_salary - total_spent
    total_cost = item["price"] * quantity

    if balance < total_cost:
        return jsonify({
            "success": False,
            "message": f"Số dư không đủ. Cần {total_cost:,.0f}₫, hiện có {balance:,.0f}₫"
        }), 400

    # ===== CẬP NHẬT BẢNG LƯƠNG =====
    # Tạo bản ghi chi tiêu trong bảng salary (dạng khấu trừ)
    # Lấy tháng hiện tại
    current_month = datetime.now().strftime("%Y-%m")
    
    # Kiểm tra xem đã có bản ghi chi tiêu trong tháng này chưa
    existing_salary = next(
        (s for s in salaries if s["employee_id"] == session["employee_id"] and s["month"] == current_month),
        None
    )
    
    if existing_salary:
        # Nếu đã có, cập nhật deduction (khấu trừ)
        for i, s in enumerate(salaries):
            if s["id"] == existing_salary["id"]:
                # Thêm tiền mua hàng vào deduction
                salaries[i]["deduction"] = s.get("deduction", 0) + total_cost
                # Tính lại total
                salaries[i]["total"] = s["base"] + s.get("bonus", 0) - salaries[i]["deduction"]
                FileHelper.write_all("salaries", salaries)
                break
    else:
        # Nếu chưa có, tạo bản ghi lương mới với deduction = total_cost
        # Lấy base_salary của nhân viên
        base_salary = emp.get("base_salary", 0)
        
        new_salary = Salary(
            employee_id=session["employee_id"],
            month=current_month,
            base=base_salary,
            bonus=0,
            deduction=total_cost
        )
        FileHelper.append_item("salaries", new_salary.to_dict())

    # Cập nhật tồn kho
    for i, it in enumerate(items):
        if it["id"] == item_id:
            items[i]["stock"] = item["stock"] - quantity
            FileHelper.write_all("shop_items", items)
            break

    # Tạo giao dịch shop
    transaction = ShopTransaction(
        employee_id=session["employee_id"],
        item_id=item_id,
        item_name=item["name"],
        price=item["price"],
        quantity=quantity
    )
    trans_dict = transaction.to_dict()
    trans_dict["transaction_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    FileHelper.append_item("shop_transactions", trans_dict)

    # Tính lại số dư sau khi mua
    new_total_salary = sum(s.get("total", 0) for s in salaries if s["employee_id"] == session["employee_id"])
    new_total_spent = sum(t.get("total", 0) for t in FileHelper.read_all("shop_transactions") 
                          if t["employee_id"] == session["employee_id"])
    new_balance = new_total_salary - new_total_spent

    return jsonify({
        "success": True,
        "message": f"Mua thành công {quantity} x {item['name']}",
        "total": total_cost,
        "balance": new_balance,
        "salary_updated": True
    })


# LẤY LỊCH SỬ MUA HÀNG
# GET /api/shop/transactions
@shop_bp.route("/transactions", methods=["GET"])
def get_transactions():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    transactions = FileHelper.read_all("shop_transactions")

    if session.get("role") != "admin":
        transactions = [t for t in transactions if t["employee_id"] == session["employee_id"]]
    else:
        emp_id = request.args.get("employee_id")
        if emp_id:
            transactions = [t for t in transactions if t["employee_id"] == int(emp_id)]

    transactions.sort(key=lambda x: x.get("transaction_date", ""), reverse=True)

    employees = FileHelper.read_all("employees")
    emp_map = {e["id"]: e["name"] for e in employees}
    for t in transactions:
        t["employee_name"] = emp_map.get(t["employee_id"], f"ID {t['employee_id']}")

    return jsonify({"success": True, "data": transactions})


# LẤY SỐ DƯ CỦA NHÂN VIÊN
# GET /api/shop/balance
@shop_bp.route("/balance", methods=["GET"])
def get_balance():
    if "employee_id" not in session:
        return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401

    employee_id = session["employee_id"]

    salaries = FileHelper.read_all("salaries")
    total_salary = sum(s.get("total", 0) for s in salaries if s["employee_id"] == employee_id)

    transactions = FileHelper.read_all("shop_transactions")
    total_spent = sum(t.get("total", 0) for t in transactions if t["employee_id"] == employee_id)

    balance = total_salary - total_spent

    # Lấy thông tin chi tiết lương theo tháng
    salary_details = []
    for s in salaries:
        if s["employee_id"] == employee_id:
            salary_details.append({
                "month": s.get("month"),
                "base": s.get("base", 0),
                "bonus": s.get("bonus", 0),
                "deduction": s.get("deduction", 0),
                "total": s.get("total", 0)
            })

    return jsonify({
        "success": True,
        "data": {
            "total_salary": total_salary,
            "total_spent": total_spent,
            "balance": balance,
            "salary_details": salary_details
        }
    })