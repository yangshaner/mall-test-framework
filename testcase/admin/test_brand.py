# testcases/amdin/test_brand.py
import pytest
import allure
from common.assertions import ApiAssertion, DBAssertion
from common.utils.id_fetcher import IDFetcherWithAllure


@allure.feature("品牌管理")
class TestBrand:

    def setup_method(self):
        self.api_assert = ApiAssertion()
        self.db_assert = DBAssertion()

    @allure.story("品牌列表")
    def test_get_brand_list(self, brand_api):
        response = brand_api.list(page_num=1, page_size=10)
        result = self.api_assert.assert_success(response, "获取品牌列表失败")
        data = result.get('data', {})
        self.api_assert.assert_field_exist(data, 'list', "缺少list")
        self.api_assert.assert_field_exist(data, 'total', "缺少total")
        assert isinstance(data.get('list'), list), "list应为列表"


    @allure.story("品牌列表")
    def test_get_brand_list_with_keyword(self, brand_api):
        response = brand_api.list(page_num=1, page_size=10, keyword="手机")
        self.api_assert.assert_success(response, "关键字搜索失败")


    @allure.story("品牌列表")
    def test_get_brand_list_all(self, brand_api):
        response = brand_api.list_all()
        result = self.api_assert.assert_success(response, "获取全部品牌失败")
        data = result.get('data', [])
        assert isinstance(data, list), "返回数据应为列表"


    @allure.story("品牌创建")
    def test_create_brand(self, brand_api, data_generator):
        brand_name = f"测试品牌_{data_generator.random_string(4)}"
        data = {
            "name": brand_name,
            "logo": f"{brand_name}.png",
            "firstLetter": brand_name[0].upper(),
            "sort": 0,
            "showStatus": 1,
            "factoryStatus": 0
        }
        response = brand_api.create(data)
        self.api_assert.assert_success(response, "创建品牌失败")

        brand_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=brand_api,
            module='brand',
            search_value=brand_name,
            page_size=10,
            max_pages=100
        )
        assert brand_id, f"未找到品牌：{brand_name}"

        self.db_assert.assert_exists('pms_brand', 'id = %s', (brand_id,))
        self.db_assert.assert_field_value('pms_brand', 'name', data['name'],
                                          'id = %s', (brand_id,))
        self.db_assert.assert_field_value('pms_brand', 'show_status', data['showStatus'],
                                          'id = %s', (brand_id,))
        brand_api.delete(brand_id)
        self.db_assert.assert_not_exists('pms_brand', 'id = %s', (brand_id,))

    @allure.story("品牌更新")
    def test_update_brand(self, brand_api, data_generator):
        brand_name = f"测试品牌_{data_generator.random_string(4)}"
        data = {
            "name": brand_name,
            "logo": f"f{brand_name}.png",
            "firstLetter": brand_name[0].upper(),
            "sort": 0,
            "showStatus": 1
        }
        response = brand_api.create(data)
        self.api_assert.assert_success(response, "创建品牌失败")

        brand_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=brand_api,
            module='brand',
            search_value=brand_name,
            page_size=10,
            max_pages=100
        )
        assert brand_id, f"未找到创建的品牌:{brand_name}"

        update_data = {
            "name": f"已修改_{brand_name}",
            "logo": f"modified_logo.png",
            "sort": 50,
            "showStatus": 1
        }
        response = brand_api.update(brand_id, update_data)
        self.api_assert.assert_success(response, "更新品牌失败")

        self.db_assert.assert_field_value('pms_brand', 'name', update_data['name'],
                                          'id = %s', (brand_id,))
        self.db_assert.assert_field_value('pms_brand', 'sort', update_data['sort'],
                                          'id = %s', (brand_id,))
        brand_api.delete(brand_id)

    @allure.story("品牌详情")
    def test_get_brand_detail(self, brand_api, data_generator):
        data = data_generator.brand_data()
        response = brand_api.create(data)
        self.api_assert.assert_success(response, "品牌创建失败")
        brand_name = data['name']

        brand_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=brand_api,
            module='brand',
            search_value=brand_name,
            page_size=10,
            max_pages=100
        )
        assert brand_id, f"未找到创建的品牌:{brand_name}"

        response = brand_api.detail(brand_id)
        result = self.api_assert.assert_success(response, "获取品牌详情失败")
        detail = result.get('data', {})
        assert detail.get('id') == brand_id, "品牌ID 不匹配"
        assert detail.get('name') == brand_name, "品牌名称不匹配"
        self.api_assert.assert_field_exist(detail, 'logo', "缺少logo")
        self.api_assert.assert_field_exist(detail, 'showStatus', "缺少showStatus")

        brand_api.delete(brand_id)

    @allure.story("显示状态")
    @pytest.mark.parametrize("show_status", [0, 1])
    def test_update_show_status(self, brand_api, data_generator, show_status):
        brand_name = data_generator.brand_data()['name']
        data = {
            "name": brand_name,
            "logo": f"{brand_name}.png",
            "firstLetter": brand_name[0].upper(),
            "sort": 0,
            "showStatus": 1
        }
        response = brand_api.create(data)
        self.api_assert.assert_success(response, "创建品牌失败")

        brand_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=brand_api,
            module='brand',
            search_value=brand_name,
            page_size=10,
            max_pages=100
        )
        assert brand_id, f"未找到创建的品牌：{brand_name}"

        response = brand_api.update_show_status([brand_id], show_status)
        self.api_assert.assert_success(response, "更新显示状态失败")

        self.db_assert.assert_field_value('pms_brand', 'show_status', show_status,
                                          'id = %s', (brand_id,))

        brand_api.delete(brand_id)

    @allure.story("厂家状态")
    @pytest.mark.parametrize("factory_status", [0, 1])
    def test_update_factory_status(self, brand_api, data_generator, factory_status):
        brand_name = data_generator.brand_data()['name']
        data = {
            "name": brand_name,
            "logo": f"{brand_name}.png",
            "firstLetter": brand_name[0].upper(),
            "sort": 0,
            "showStatus": 1,
        }
        response = brand_api.create(data)
        self.api_assert.assert_success(response, "创建品牌失败")

        brand_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=brand_api,
            module='brand',
            search_value=brand_name,
            page_size=10,
            max_pages=100
        )

        assert brand_id, f"未找到创建的品牌：{brand_name}"

        response = brand_api.update_factory_status([brand_id], factory_status)
        self.api_assert.assert_success(response, "更新厂家状态失败")

        self.db_assert.assert_field_value('pms_brand', 'factory_status', factory_status,
                                          'id = %s', (brand_id,))

        brand_api.delete(brand_id)

    @allure.story("删除品牌")
    def test_delete_brand(self, brand_api, data_generator):
        brand_name = data_generator.brand_data()['name']
        data = {
            "name": brand_name,
            "logo": f"{brand_name}.png",
            "firstLetter": brand_name[0].upper(),
            "sort": 0,
            "showStatus": 1
        }
        response = brand_api.create(data)
        self.api_assert.assert_success(response, "创建品牌失败")

        brand_id = IDFetcherWithAllure.get_id_by_module(
            api_instance=brand_api,
            module='brand',
            search_value=brand_name,
            page_size=10,
            max_pages=100
        )
        assert brand_id, f"未找到创建的品牌:{brand_name}"

        self.db_assert.assert_exists('pms_brand', 'id = %s', (brand_id,))

        response = brand_api.delete(brand_id)
        self.api_assert.assert_success(response, "删除品牌失败", check_data=False)

        self.db_assert.assert_not_exists('pms_brand', 'id = %s', (brand_id,))

    @allure.story("批量删除品牌")
    def test_delete_batch_delete(self, brand_api, data_generator):
        brand_ids = []
        for i in range(2):
            brand_name = f"测试品牌_{data_generator.random_string(4)}"
            data = {
                "name": brand_name,
                "logo": f"{brand_name}.png",
                "firstLetter": brand_name[0].upper(),
                "sort": i,
                "showStatus": 1
            }
            response = brand_api.create(data)
            self.api_assert.assert_success(response, f"创建品牌{i + 1}失败")

            brand_id = IDFetcherWithAllure.get_id_by_module(
                api_instance=brand_api,
                module='brand',
                search_value=brand_name,
                page_size=10,
                max_pages=100
            )
            if brand_id:
                brand_ids.append(brand_id)

        assert len(brand_ids) == 2

        response = brand_api.delete_batch(brand_ids)
        self.api_assert.assert_success(response, "批量删除商品失败")

        for brand_id in brand_ids:
            self.db_assert.assert_not_exists('pms_brand', 'id = %s', (brand_id,))
