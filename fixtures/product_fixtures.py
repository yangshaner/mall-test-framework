# fixtures/product_fixtures.py - 独立的商品fixture
import pytest
import allure
import logging

from common.client.admin_client import AdminClient
from common.utils.data_generator import DataGenerator
from common.db.mysql_util import mysql
from common.assertions import DBAssertion
from common.config.config_loader import config
from common.assertions import ApiAssertion

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def admin_client_for_setup():
    """
    用于测试数据准备的后台客户端
    确保登录成功后再返回
    """
    client = AdminClient()

    # 尝试登录并验证
    with allure.step("后台客户端登录"):
        try:
            # 执行登录
            login_result= client._login()
            logger.info(f"Admin client login success: {login_result.get('user_info', {}).get('username', 'admin')}")

            # 验证登录是否成功 - 尝试获取用户信息
            info_response = client.get("/admin/info")
            if info_response.status_code == 200:
                info_data = info_response.json()
                if info_data.get('code') == 200:
                    logger.info("Admin client authentication verified")
                else:
                    logger.warning(f"Admin client authentication failed, {info_data.get('message')}")
            else:
                logger.warning(f"Admin client auth verify failed with status: {info_response.status_code}")
        except Exception as e:
            logger.error(f"Admin client logi failed: {e}")
            raise RuntimeError(f"Admin client logi failed, {e}")

    return client


@pytest.fixture
def test_product(admin_client_for_setup, data_generator):
    """
    创建测试商品 - 唯一的数据创建入口
    所有需要商品数据的测试都依赖这个fixture
    """
    with allure.step("创建测试商品"):
        # 1. 创建品牌
        brand_data = data_generator.brand_data()
        brand_response = admin_client_for_setup.post("/brand/create", json=brand_data)
        brand_result = brand_response.json()
        print("brand_result:%s" % brand_result, "type: %s" % type(brand_result))
        # brand_id = brand_result.get('data', {}).get('id')
        brand_id = brand_result.get('data', {}) # 这里是有问题的
        assert brand_id, "创建商品失败"

        # 2. 创建分类
        category_data = data_generator.product_category_data()
        category_response = admin_client_for_setup.post("/productCategory/create", json=category_data)
        category_result = category_response.json()
        print("category_result:%s" % category_result, "type: %s" % type(category_result))
        # category_id = category_result.get("data", {}).get("id")
        category_id = category_result.get("data", {})
        assert category_id, "创建分类失败"

        # 3. 创建商品
        product_data = data_generator.product_data(brand_id, category_id)
        product_response = admin_client_for_setup.post("/product/create", json=product_data)
        product_result = product_response.json()
        print("product_result:%s" % product_result, "type: %s" % type(product_result))
        # product_id = product_result.get("data", {}).get("id")
        product_id = product_result.get("data", {})
        assert product_id, "创建商品失败"

        # 4. 审核并上架（前台可见）
        admin_client_for_setup.post("/product/update/verifyStatus",
                                    params={"ids": [product_id], "verifyStatus": 1, "detail": "审核通过"})
        admin_client_for_setup.post("/product/update/publishStatus",
                                    params={"ids": [product_id], "publishStatus": 1})
        allure.attach(str(product_id), "Product ID", allure.attachment_type.TEXT)
        yield product_id

    with allure.step("清理测试商品"):
        try:
            admin_client_for_setup.post("/product/update/deleteStatus",
                                        params={"ids": [product_id], "deleteStatus": 1})
            db_assert = DBAssertion()
            db_assert.assert_not_exist("pms_product", "id = %s" % product_id)
        except Exception as e:
            allure.attach(str(e), "清理失败", allure.attachment_type.TEXT)


@pytest.fixture
def test_brand(admin_client_for_setup, data_generator): # 需要调整逻辑， 参考IDFetcher
    """ 创建测试品牌 """
    with allure.step("创建测试品牌"):
        brand_data = data_generator.brand_data()
        brand_name = brand_data.get('name')
        brand_response = admin_client_for_setup.post("/brand/create", json=brand_data)

        brand_id = mysql.get_id_by_field('pms_brand', 'name', brand_name)
        # brand_id = brand_result.get("data", {}).get("id")
        assert brand_id, "创建商品失败"

        allure.attach(str(brand_id), "Brand ID", allure.attachment_type.TEXT)
        yield brand_id

    with allure.step("清理测试品牌"):
        try:
            admin_client_for_setup.post(f"/brand/delete/{brand_id}")
        except Exception as e:
            allure.attach(str(e), "清理失败", allure.attachment_type.TEXT)


@pytest.fixture
def test_category(admin_client_for_setup, data_generator):
    """ 创建测试分类 """
    with allure.step("创建分类"):
        category_data = data_generator.product_category_data()
        category_name = category_data.get('name')
        category_response = admin_client_for_setup.post("/productCategory/create", json=category_data)
        category_result = category_response.json()
        # category_id = category_result.get("data", {}).get("id")
        category_id = mysql.get_id_by_field('pms_product_category', 'name', category_name)


        assert category_id, "创建分类失败"

        allure.attach(str(category_id), "Category ID", allure.attachment_type.TEXT)
        yield category_id

    with allure.step("清理测试分类"):
        try:
            admin_client_for_setup.post(f"/productCategory/delete/{category_id}")
        except Exception as e:
            allure.attach(str(e), "清理失败", allure.attachment_type.TEXT)
