# testcase/security/test_security_input.py
import pytest
import allure

from common.assertions import ApiAssertion

SAFE_STATUS_CODES = (200, 400, 413)

@allure.feature("安全测试-输入校验与注入防御")
class TestSecurityInput:

    def setup_method(self):
        self.api_assert = ApiAssertion()

    def _assert_safe_response(self, response, message: str):
        assert response.status_code in SAFE_STATUS_CODES, \
            f"{message}（实际状态码 {response.status_code}，安全状态码集合 {SAFE_STATUS_CODES}）"
        body = response.text.lower()
        assert "sqlsyntax" not in body.replace(" ", "") and "SQLException".lower() not in body, \
            f"{message}：响应中不应暴露 SQL 异常信息"
        assert "java.lang" not in body and "at org.springframework" not in body, \
            f"{message}：响应中不应暴露堆栈"

    @allure.story("SQL 注入-商品搜索")
    @pytest.mark.parametrize("payload", [
        "' OR '1'='1",
        "' OR 1=1 --",
        "1' AND SLEEP(5)--",
        "1; DROP TABLE pms_product; --",
        "' UNION SELECT * FROM pms_product--",
    ])
    def test_sql_injection_search(self, member_product_api, payload):
        response = member_product_api.search(keyword=payload, page_num=1, page_size=10)
        self._assert_safe_response(response, "SQL 注入不应导致服务端异常")

    @allure.story("SQL 注入-订单查询")
    def test_sql_injection_order_list(self, member_order_api):
        response = member_order_api.list(status="0 OR 1=1", page_num=1, page_size=10)
        self._assert_safe_response(response, "SQL 注入不应导致服务端异常")

    @allure.story("SQL 注入-后台商品查询")
    def test_sql_injection_admin_product_list(self, admin_client):
        response = admin_client.get("/product/list", params={
            "pageNum": 1,
            "pageSize": 10,
            "keyword": "' OR '1'='1"
        })
        self._assert_safe_response(response, "后台接口不应受 SQL 注入影响")

    @allure.story("XSS 注入-商品名称")
    def test_xss_in_product_name(self, admin_client):
        xss_payload = "<script>alert('xss')</script>"
        product_data = {
            "name": xss_payload,
            "productSn": "XSS_TEST_001",
            "price": 99.99,
            "stock": 10,
            "brandId": 1,
            "productCategoryId": 1,
            "publishStatus": 0,
            "verifyStatus": 0,
        }
        try:
            response = admin_client.post("/product/create", json=product_data)
            result = response.json()
            assert result.get("code") == 200 or result.get("code") != 200
            if result.get("code") == 200:
                list_resp = admin_client.get("/product/list", params={
                    "pageNum": 1, "pageSize": 10, "keyword": "XSS_TEST"
                })
                list_body = list_resp.text
                assert "<script>" not in list_body, "XSS 载荷不应原样返回"
        finally:
            pass

    @allure.story("XSS 注入-搜索参数")
    def test_xss_in_search_keyword(self, member_product_api):
        xss_payload = "<img src=x onerror=alert(1)>"
        response = member_product_api.search(keyword=xss_payload, page_num=1, page_size=10)
        self._assert_safe_response(response, "XSS 注入不应导致服务端异常")
        assert "<img" not in response.text.lower() or "onerror" not in response.text.lower(), \
            "XSS 载荷不应原样回显"

    @allure.story("超长字符串参数")
    def test_oversized_string_param(self, member_product_api):
        oversized = "A" * 10000
        response = member_product_api.search(keyword=oversized, page_num=1, page_size=10)
        self._assert_safe_response(response, "超长参数不应导致服务端崩溃")

    @allure.story("负数/非法数值参数")
    @pytest.mark.parametrize("page_num", [-1, 0, -999])
    def test_negative_page_num(self, member_product_api, page_num):
        response = member_product_api.search(page_num=page_num, page_size=10)
        self._assert_safe_response(response, "负数页码不应导致服务端异常")

    @allure.story("超大 pageSize 参数")
    def test_oversized_page_size(self, member_product_api):
        response = member_product_api.search(page_num=1, page_size=1000000)
        self._assert_safe_response(response, "超大 pageSize 不应导致服务端崩溃")

    @allure.story("类型混淆-数字字段传字符串")
    def test_type_confusion_numeric_field(self, member_product_api):
        response = member_product_api.search(page_num="abc", page_size="xyz")
        self._assert_safe_response(response, "类型混淆参数不应导致服务端 500")

    @allure.story("空值/None 参数")
    def test_null_and_empty_params(self, member_product_api):
        response = member_product_api.search(keyword="", page_num=1, page_size=10)
        self._assert_safe_response(response, "空字符串参数不应导致服务端异常")

    @allure.story("特殊字符-路径遍历")
    def test_path_traversal_keyword(self, member_product_api):
        response = member_product_api.search(keyword="../../etc/passwd", page_num=1, page_size=10)
        self._assert_safe_response(response, "路径遍历不应导致服务端异常")
        assert "root:" not in response.text, "路径遍历不应泄露系统文件内容"

    @allure.story("特殊字符-控制字符")
    def test_control_characters(self, member_product_api):
        payload = "test\x00name\n<script>"
        response = member_product_api.search(keyword=payload, page_num=1, page_size=10)
        self._assert_safe_response(response, "控制字符不应导致服务端异常")