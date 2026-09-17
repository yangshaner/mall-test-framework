# api/member/cart_api.py
import allure
from typing import Dict, List, Optional


class CartApi:

    def __init__(self, client):
        self.client = client

    @allure.step("获取购物车列表")
    def list(self) -> Dict:
        return self.client.get("/cart/list")

    @allure.step("获取购物车列表含促销信息")
    def list_promotion(self, cart_ids: Optional[List[int]] = None) -> Dict:
        params = {}
        if cart_ids:
            params["cartIds"] = cart_ids
        return self.client.get("/cart/list/promotion", params=params)

    @allure.step("添加商品到购物车")
    def add(self, data: Dict) -> Dict:
        return self.client.post("/cart/add", json=data)

    @allure.step("修改购物车中商品的数量")
    def update_quantity(self, cart_id: int, quantity: int) -> Dict:
        return self.client.get("/cart/update/quantity", params={
            "id": cart_id,
            "quantity": quantity
        })

    @allure.step("修改购物车中商品的规格")
    def update_attr(self, data: Dict) -> Dict:
        return self.client.post("/cart/update/attr", json=data)

    @allure.step("删除购物车中的指定商品")
    def delete(self, ids: List[int]) -> Dict:
        return self.client.post("/cart/delete", params={"ids": ids})

    @allure.step("清空购物车")
    def clear(self) -> Dict:
        return self.client.post("/cart/clear")

    @allure.step("获取购物车中指定商品规格")
    def get_cart_product(self, product_id: int) -> Dict:
        return self.client.get(f"/cart/getProduct/{product_id}")