# fixtures//admin_fixtures.py

import pytest
import allure
from typing import Any

from api.admin.product_api import ProductApi
from api.admin.brand_api import BrandApi
from api.admin.order_api import OrderApi
from api.admin.category_api import CategoryApi
from api.admin.coupon_api import CouponApi
from api.admin.admin_api import AdminApi
from common.client.admin_client import AdminClient
from common.db.mysql_util import mysql
from common.utils.data_generator import DataGenerator
from common.assertions import ApiAssertion
from common.utils.id_fetcher import IDFetcherWithAllure


@pytest.fixture(scope="session")
def admin_client():
    """ 后台客户端（已认证） """
    client = AdminClient()
    # 确保登录
    client._login()
    return client


@pytest.fixture(scope="session")
def product_api(admin_client):  # 为什么要传入admin_client
    return ProductApi()


@pytest.fixture(scope="session")
def brand_api(admin_client):
    """ 品牌API """
    return BrandApi()


@pytest.fixture(scope="session")
def category_api(admin_client):
    return CategoryApi()


@pytest.fixture(scope="session")
def order_api(admin_client):
    return OrderApi()


@pytest.fixture(scope="session")
def coupon_api(admin_client):
    return CouponApi()


@pytest.fixture(scope="session")
def admin_api(admin_client):
    """ 用户管理API """
    return AdminApi()


@pytest.fixture(scope="session")
def data_generator():
    return DataGenerator()


@pytest.fixture(scope="session")
def db_assert():
    """ 数据库断言工具 """

    class DBAssert:
        @staticmethod
        def assert_exists(table: str, condition: str, params: tuple = None):
            """ 断言数据存在 """
            sql = f"select count(*) as count from {table} where {condition}"
            result = mysql.query(sql, params)
            assert result[0].get('count', 0) > 0, f"数据不存在：{table} where {condition}"
            return result[0].get('count')

        @staticmethod
        def assert_not_exists(table: str, condition: str, params: tuple = None):
            """ 断言数据不存在 """
            sql = f"select count(*) as count from {table} where {condition}"
            result = mysql.query(sql, params)
            assert result[0].get('count', 0) == 0, f"数据存在：{table} where {condition}"

        @staticmethod
        def assert_field_value(table: str, field: str, expected: Any, condition: str, params: tuple = None):
            """ 断言字段值 """
            sql = f"select {field} from {table} where {condition}"
            result = mysql.query(sql, params)
            assert result, f"未找到数据：{table} where {condition}"
            actual = result[0].get(field)
            assert actual == expected, f"字段 {field} 期待 {expected}，实际 {actual}"

    return DBAssert


@pytest.fixture
def test_brand(brand_api, data_generator, db_assert):
    """ 创建测试品牌 """
    with allure.step("创建测试品牌"):
        data = data_generator.brand_data()
        response = brand_api.create(data)
        assert response.status_code == 200
        ApiAssertion().assert_success(response, "创建品牌失败")

        # result = response.json()
        # brand_id = result.get('data', {}).get('id')

        brand_name = data['name']
        brand_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=brand_api,
            module='brand',
            search_value=brand_name,
            page_size=10,
            max_pages=100
        )
        assert brand_id, "创建品牌失败，未返回ID"

        # 验证数据库
        db_assert.assert_exists('pms_brand', 'id = %s', (brand_id,))

        allure.attach(str(brand_id), "Brand ID", allure.attachment_type.TEXT)
        yield brand_id

    with allure.step("清理测试品牌"):
        brand_api.delete(brand_id)
        db_assert.assert_not_exists('pms_brand', 'id = %s', (brand_id,))


@pytest.fixture
def test_category(category_api, data_generator, db_assert):
    """ 创建测试分类 """
    with allure.step("创建测试分类"):
        data = data_generator.product_category_data()
        response = category_api.create(data)
        assert response.status_code == 200

        # result = response.json()
        # category_id = result.get('data', {}).get('id')
        category_name = data['name']
        category_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=category_api,
            module='category',
            search_value=category_name,
            page_size=10,
            max_pages=100,
            extra_params={'parent_id': 0}
        )
        assert category_id, "创建分类失败，未返回ID"

        # db_assert.assert_exists('pms_product_category', 'id = %s', (category_id,))

        allure.attach(str(category_id), "Category ID", allure.attachment_type.TEXT)
        yield category_id

    with allure.step("清理测试分类"):
        category_api.delete(category_id)
        db_assert.assert_not_exists('pms_product_category', 'id = %s', (category_id,))

@pytest.fixture
def test_product(product_api, data_generator, test_brand, test_category, db_assert):
    """ 创建测试商品 """
    with allure.step("创建测试商品"):
        data = data_generator.product_data(test_brand, test_category)
        response = product_api.create(data)
        assert response.status_code == 200
        result = response.json()
        product_id = result.get('data', {}).get('id')
        assert product_id, "创建商品失败，未返回ID"

        db_assert.assert_exists('pms_product', 'id = %s', (product_id,))

        allure.attach(str(product_id), "Product ID", allure.attachment_type.TEXT)
        yield product_id


@pytest.fixture
def test_coupon(coupon_api, data_generator, db_assert):
    """ 创建测试优惠券 """
    with allure.step("创建测试优惠券"):
        data = data_generator.coupon_data()
        response = coupon_api.create(data)
        assert response.status_code == 200
        result = response.json()
        coupon_id = result.get('data', {}).get('id')
        assert coupon_id, "创建优惠券失败，未返回ID"

        db_assert.assert_exists('sms_coupon', 'id = %s', (coupon_id,))

        allure.attach(str(coupon_id), "Coupon ID", allure.attachment_type.TEXT)
        yield coupon_id

    with allure.step("清理测试优惠券"):
        coupon_api.delete(coupon_id)
        db_assert.assert_not_exists('sms_coupon', 'id = %s', (coupon_id,))
