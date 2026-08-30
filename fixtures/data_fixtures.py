# fixtures/data_fixtures.py
import pytest

from common.utils.data_generator import DataGenerator
from common.db.mysql_util import mysql
from common.db.redis_util import redis_util


@pytest.fixture(scope="session")
def data_generator():
    """ 数据生成器 """
    return DataGenerator()


@pytest.fixture(scope="session")
def clean_database():
    """ 清理数据库（在每个测试前后） ？ """
    # 记录测试前的状态
    tables = ["pms_product", "pms_brand", "pms_product_category",
              "oms_order", "sms_coupon", "ums_member_receive_address",
              "oms_cart_item"]

    before_count = {}

    for table in tables:
        result = mysql.query(f"select count(*) as cnt from {table}")
        before_count[table] = result[0]['cnt'] if result else 0

    yield

    # 测试后清理
    for table in tables:
        result = mysql.query(f"select count(*) as cnt from {table}")
        after_count = result[0]['cnt'] if result else 0
        if after_count > before_count.get(table, 0):
            # 删除册数数据（慎重操作）
            pass


@pytest.fixture
def clean_redis():
    """ 清理redis缓存 """
    # 记录测试前状态
    before_keys = redis_util.get("test:*")

    yield

    # 删除测试产生的key
    after_keys = redis_util.get("test:*")
    for key in after_keys:
        if key not in before_keys:
            redis_util.decr(key)


@pytest.fixture
def ensure_test_product_exists(test_product):
    """ 确保测试商品存在 """
    # test_product fixture 会自动创建
    # 如果创建失败，会抛出异常
    yield test_product


@pytest.fixture
def ensure_test_brand_exists(test_brand):
    """ 确保测试品牌存在 """
    yield test_brand


@pytest.fixture
def ensure_test_category_exists(test_category):
    """  确保测试分类存在"""
    yield test_category


@pytest.fixture
def get_existing_product():
    """ 获取一个已存在的商品 """
    result = mysql.query(f"select id from pms_product where delete_status = 0 and limit 1")
    if not result:
        pytest.skip("没有可用的商品数据")
    return result[0]['id']
