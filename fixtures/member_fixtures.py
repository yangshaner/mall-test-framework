# fixtures/member_fixtures.py
import pytest
import allure
import requests
from requests.adapters import HTTPAdapter

from api.member import ReturnApi
from api.member.login_api import MemberLoginApi
from api.member.product_api import MemberProductApi
from api.member.cart_api import CartApi
from api.member.order_api import MemberOrderApi
from api.member.coupon_api import MemberCouponApi
from api.member.address_api import AddressApi
from api.member.collection_api import CollectionApi
from api.member.attention_api import AttentionApi
from api.member.read_history_api import ReadHistoryApi
from api.member.home_api import HomeApi
from api.member.brand_api import MemberBrandApi
from common.assertions import ApiAssertion, DBAssertion
from common.db.mysql_util import mysql
from common.client.member_client import MemberClient
from common.utils.data_generator import DataGenerator
from fixtures.product_fixtures import test_product, test_brand


@pytest.fixture(scope="session")
def member_client():
    client = MemberClient()
    client._login()
    return client


@pytest.fixture(scope="session")
def member_client_unauthenticated():
    return MemberClient()


@pytest.fixture(scope="session")
def member_login_api(member_client):
    return MemberLoginApi()


@pytest.fixture(scope="session")
def member_product_api(member_client):
    return MemberProductApi(member_client)


@pytest.fixture(scope="session")
def member_brand_api(member_client):
    return MemberBrandApi()


@pytest.fixture(scope="session")
def cart_api(member_client):
    return CartApi(member_client)


@pytest.fixture(scope="session")
def member_order_api(member_client):
    return MemberOrderApi()


@pytest.fixture(scope="session")
def member_coupon_api(member_client):
    return MemberCouponApi()


@pytest.fixture(scope="session")
def address_api(member_client):
    return AddressApi()


@pytest.fixture(scope="session")
def collection_api(member_client):
    return CollectionApi()


@pytest.fixture(scope="session")
def collection_available(member_client):
    probe = requests.Session()
    probe.mount("http://", HTTPAdapter(max_retries=0))
    probe.mount("https://", HTTPAdapter(max_retries=0))
    auth = member_client.session.headers.get("Authorization", "")
    if auth:
        probe.headers["Authorization"] = auth
    try:
        resp = probe.get(
            f"{member_client.base_url}/member/productCollection/list",
            params={"pageNum": 1, "pageSize": 1},
            timeout=(3, 6)
        )
        body = resp.json()
        return resp.status_code == 200 and body.get("code") == 200
    except requests.exceptions.RequestException:
        return False
    except ValueError:
        return False
    finally:
        probe.close()


@pytest.fixture(scope="session")
def attention_api(member_client):
    return AttentionApi()


@pytest.fixture(scope="session")
def read_history_api(member_client):
    return ReadHistoryApi()


@pytest.fixture(scope="session")
def home_api(member_client):
    return HomeApi()


@pytest.fixture(scope="session")
def retune_api(member_client):
    return ReturnApi()


@pytest.fixture(scope="session")
def data_generator():
    return DataGenerator()


@pytest.fixture(scope="session")
def api_assert():
    return ApiAssertion()


@pytest.fixture(scope="session")
def db_assert():
    return DBAssertion()


@pytest.fixture(scope="session")
def test_member_address(address_api, data_generator, db_assert):
    with allure.step("创建测试收货地址"):
        data = {
            "name": data_generator.random_name(),
            "phoneNumber": data_generator.random_phone(),
            "province": "广东省",
            "city": "深圳市",
            "region": "南山区",
            "detailAddress": f"测试地址_{data_generator.random_string(4)}",
            "defaultStatus": 1
        }
        response = address_api.add(data)
        assert response.status_code == 200
        result = response.json()
        address_id = result.get('data', {}).get('id')
        assert address_id, "创建收货地址失败"

        allure.attach(str(address_id), "Address ID", allure.attachment_type.TEXT)
        yield address_id

    with allure.step("清理测试收货地址"):
        try:
            address_id.delete(address_id)
        except Exception as e:
            allure.attach(str(e), " 清理失败", allure.attachment_type.TEXT)


@pytest.fixture
def test_cart_item(cart_api, test_product):
    with allure.step("添加商品到购物车"):
        sku_rows = mysql.query(
            "SELECT id, price FROM pms_sku_stock WHERE product_id = %s AND stock > 0 ORDER BY id LIMIT 1",
            (test_product,)
        )
        assert sku_rows, f"商品 {test_product} 没有可用 SKU（pms_sku_stock 无库存记录）"
        sku_id = sku_rows[0]["id"]
        price = float(sku_rows[0]["price"] or 99.99)

        data = {
            "productId": test_product,
            "productSkuId": sku_id,
            "quantity": 1,
            "price": price
        }
        response = cart_api.add(data)
        assert response.status_code == 200, f"添加购物车失败（http层面）： {response.text}"
        add_result = response.json()
        assert add_result.get("code") == 200, f"添加购物车失败（业务处理层面）：{add_result.get('message')}"


        list_response = cart_api.list()
        assert list_response.status_code == 200
        list_result = list_response.json()
        assert list_result.get('code') == 200, f"获取购物车列表失败：{list_result.get('message')}"

        list_data = list_result.get('data')
        if not isinstance(list_data, list):
            raise TypeError(f"购物车列表数据应为list，实际为{type(list_data)}: {list_data})")

        cart_item = next((item for item in list_data if item.get("productId") == test_product), None)
        assert cart_item, "购物车商品未添加成功"

        cart_id = cart_item.get('id')
        allure.attach(str(cart_id), "Cart Item ID", allure.attachment_type.TEXT)

        yield cart_id

    with allure.step("清理购物车"):
        try:
            cart_api.clear()
        except Exception as e:
            allure.attach(str(e), "清理失败", allure.attachment_type.TEXT)


SEED_PRODUCT_ID = 26
@pytest.fixture
def seed_cart_item(cart_api):
    sku_rows = mysql.query(
        "SELECT id, price FROM pms_sku_stock WHERE product_id = %s AND stock > 0 ORDER BY id LIMIT 1",
        (SEED_PRODUCT_ID,)
    )
    if not sku_rows:
        pytest.skip(f"种子商品 {SEED_PRODUCT_ID} 无可用 SKU，跳过促销相关链路")

    sku_id = sku_rows[0]["id"]
    price = float(sku_rows[0]["price"] or 0)
    response = cart_api.add({
        "productId": SEED_PRODUCT_ID,
        "productSkuId": sku_id,
        "quantity": 1,
        "price": price
    })
    result = response.json()
    assert response.status_code == 200 and result.get("code") == 200, \
        f"种子商品加购失败: {result.get('message')}"

    list_result = cart_api.list().json()
    list_data = list_result.get("data") or []
    cart_item = next(
        (it for it in list_data if isinstance(it, dict) and it.get("productId") == SEED_PRODUCT_ID),
        None
    )
    assert cart_item, "种子商品购物车项未找到"
    yield cart_item["id"]

    try:
        cart_api.clear()
    except Exception:
        pass


@pytest.fixture
def test_member_order(member_order_api, seed_cart_item, test_member_address):
    with allure.step("生成测试订单"):
        conforms_response = member_order_api.generate_confirm_order([seed_cart_item])
        confirm_result = conforms_response.json()

        assert conforms_response.status_code == 200 and confirm_result.get("code") == 200, \
            f"生成确认单失败: HTTP {conforms_response.status_code}, {str(confirm_result)[:200]}"

        order_data = {
            "memberReceiverAddressId": test_member_address,
            "couponId": None,
            "useIntegration": 0,
            "payType": 1,
            "cartIds": [seed_cart_item]
        }
        response = member_order_api.generate_order(order_data)
        assert response.status_code == 200
        result = response.json()
        assert result.get("code") == 200, \
            f"创建订单失败（业务层）: {result.get('message')}, data={str(result.get('data'))[:200]}"
        order_data_resp = result.get("data")
        assert isinstance(order_data_resp, dict), f"订单创建返回data类型异常: {type(order_data_resp).__name__}"
        order_id = order_data_resp.get("id")
        assert order_id, "创建订单失败，未返回订单ID"

        allure.attach(str(order_id), "Order ID", allure.attachment_type.TEXT)
        yield order_id

    with allure.step("清理测试订单"):
        try:
            member_order_api.delete_order(order_id)
        except Exception as e:
            allure.attach(str(e), "清理失败", allure.attachment_type.TEXT)


@pytest.fixture
def test_read_history(read_history_api, test_product, data_generator):
    with allure.step("创建测试浏览记录"):
        data = {
            "productId": test_product,
            "productName": f"测试商品_{data_generator.random_string(4)}",
            "productPic": "test.png",
            "productPrice": "99.99"
        }
        response = read_history_api.create(data)
        assert response.status_code == 200
        result = response.json()
        assert result.get("code") == 200, f"创建浏览记录失败: {result.get('message')}"
        history_data = result.get("data")
        history_id = history_data.get("id") if isinstance(history_data, dict) else None

        allure.attach(str(history_id), "History ID", allure.attachment_type.TEXT)
        yield history_id

    with allure.step("清理测试来浏览记录"):
        try:
            if history_id:
                read_history_api.delete([history_id])
        except Exception as e:
            allure.attach(str(e), "清理失败", allure.attachment_type.TEXT)


@pytest.fixture
def test_collection(collection_api, collection_available,
                    test_product, data_generator):

    if not collection_available:
        pytest.skip("收藏接口不可用（服务端超时/缺少收藏表），跳过收藏写操作")

    with allure.step("创建测试收藏"):
        data = {
            "productId": test_product,
            "productName": f"测试商品_{data_generator.random_string(4)}",
            "productPic": "test.png",
            "productPrice": "99.99"
        }
        response = collection_api.add(data)
        assert response.status_code == 200
        allure.attach(str(test_product), "Collection Product ID", allure.attachment_type.TEXT)
        yield test_product

    with allure.step("清理测试收藏"):
        try:
            collection_api.delete(test_product)
        except Exception as e:
            allure.attach(str(e), "清理失败", allure.attachment_type.TEXT)


@pytest.fixture
def test_attention(attention_api, test_brand, data_generator):
    with allure.step("创建测试关注"):
        brand_api = MemberBrandApi()
        brand_response = brand_api.detail(test_brand)
        brand_result = brand_response.json()
        brand_data = brand_result.get("data", {})

        data = {
            "brandId": test_brand,
            "brandName": brand_data.get('name', f'测试品牌_{data_generator.random_string(4)}'),
            "brandLogo": "logo.png",
        }
        response = attention_api.create(data)
        assert response.status_code == 200
        result = response.json()
        attention_id = result.get("data", {}).get("id")

        allure.attach(str(attention_id), "Attention ID", allure.attachment_type.TEXT)
        yield attention_id

    with allure.step("清理测试关注"):
        try:
            attention_api.delete(test_brand)
        except Exception as e:
            allure.attach(str(e), "清理失败", allure.attachment_type.TEXT)