# model/shop.py
# Model: Quản lý cửa hàng vật phẩm

class ShopItem:
    _id_counter = 1

    def __init__(self, name: str, description: str, price: float, stock: int, image: str = ""):
        self.id = ShopItem._id_counter
        ShopItem._id_counter += 1
        self.name = name
        self.description = description
        self.price = price
        self.stock = stock
        self.image = image
        self.status = "active"  # active | inactive

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock": self.stock,
            "image": self.image,
            "status": self.status
        }

    @staticmethod
    def from_dict(data: dict) -> "ShopItem":
        item = ShopItem.__new__(ShopItem)
        item.id = data["id"]
        item.name = data["name"]
        item.description = data.get("description", "")
        item.price = data.get("price", 0)
        item.stock = data.get("stock", 0)
        item.image = data.get("image", "")
        item.status = data.get("status", "active")
        return item


class ShopTransaction:
    _id_counter = 1

    def __init__(self, employee_id: int, item_id: int, item_name: str, price: float, quantity: int = 1):
        self.id = ShopTransaction._id_counter
        ShopTransaction._id_counter += 1
        self.employee_id = employee_id
        self.item_id = item_id
        self.item_name = item_name
        self.price = price
        self.quantity = quantity
        self.total = price * quantity
        self.transaction_date = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "item_id": self.item_id,
            "item_name": self.item_name,
            "price": self.price,
            "quantity": self.quantity,
            "total": self.total,
            "transaction_date": self.transaction_date
        }

    @staticmethod
    def from_dict(data: dict) -> "ShopTransaction":
        trans = ShopTransaction.__new__(ShopTransaction)
        trans.id = data["id"]
        trans.employee_id = data["employee_id"]
        trans.item_id = data["item_id"]
        trans.item_name = data["item_name"]
        trans.price = data["price"]
        trans.quantity = data.get("quantity", 1)
        trans.total = data.get("total", trans.price * trans.quantity)
        trans.transaction_date = data.get("transaction_date")
        return trans