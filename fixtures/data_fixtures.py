# fixtures/data_fixtures.py
import pytest

from common.utils.data_generator import DataGenerator
from common.db.mysql_util import mysql
from common.db.redis_util import redis_util


@pytest.fixture(scope="session")
def data_generator():
    return DataGenerator()


@pytest.fixture(scope="session")
def clean_database():
    tables = ["pms_product", "pms_brand", "pms_product_category",
              "oms_order", "sms_coupon", "ums_member_receive_address",
              "oms_cart_item"]

    before_count = {}

    for table in tables:
        result = mysql.query(f"select count(*) as cnt from {table}")
        before_count[table] = result[0]['cnt'] if result else 0

    yield

    for table in tables:
        result = mysql.query(f"select count(*) as cnt from {table}")
        after_count = result[0]['cnt'] if result else 0
        if after_count > before_count.get(table, 0):
            pass


@pytest.fixture
def clean_redis():
    before_keys = redis_util.get("test:*")

    yield

    after_keys = redis_util.get("test:*")
    for key in after_keys:
        if key not in before_keys:
            redis_util.decr(key)


@pytest.fixture
def ensure_test_product_exists(test_product):
    yield test_product


@pytest.fixture
def ensure_test_brand_exists(test_brand):
    yield test_brand


@pytest.fixture
def ensure_test_category_exists(test_category):
    yield test_category


@pytest.fixture
def get_existing_product():
    result = mysql.query(f"select id from pms_product where delete_status = 0 and limit 1")
    if not result:
        pytest.skip("没有可用的商品数据")
    return result[0]['id']
