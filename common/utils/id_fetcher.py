# common/utils/id_fetcher.py
# -*- coding: utf-8 -*-

from typing import Callable, Optional, Any, Dict, List, Union
import time
import allure
import logging

logger = logging.getLogger(__name__)


class ModuleFieldConfig:
    CONFIGS = {
        'brand': {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': 'keyword',
            'list_method_name': 'list',
            'description': '品牌管理',
            'support_pagination': True
        },
        'category': {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': None,
            'list_method_name': 'list',
            'requires_parent_id': True,
            'description': '商品分类',
            'support_pagination': True,
            'max_page_size': 100
        },
        'product': {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': 'keyword',
            'list_method_name': 'simple_list',
            'description': '商品管理',
            'support_pagination': True
        },
        'coupon': {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': 'name',
            'list_method_name': 'list',
            'description': '优惠券管理',
            'support_pagination': True
        },
        'admin': {
            'name_field': 'username',
            'id_field': 'id',
            'keyword_field': 'keyword',
            'list_method_name': 'list',
            'description': '后台用户管理',
            'support_pagination': True
        },
        'order': {
            'name_field': 'orderSn',
            'id_field': 'id',
            'keyword_field': 'orderSn',
            'list_method_name': 'list',
            'description': '订单管理',
            'support_pagination': True
        },
        'flash': {
            'name_field': 'title',
            'id_field': 'id',
            'keyword_field': 'keyword',
            'list_method_name': 'list',
            'description': '限时购活动',
            'support_pagination': True
        },
        'flash_session': {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': None,
            'list_method_name': 'list',
            'description': '限时购场次',
            'support_pagination': True
        }
    }

    @classmethod
    def get_config(cls, module: str) -> Dict:
        return cls.CONFIGS.get(module, {
            'name_field': 'name',
            'id_field': 'id',
            'keyword_field': 'keyword',
            'list_method_name': 'list',
            'description': '未知模块',
            'support_pagination': True
        })

    @classmethod
    def list_module(cls) -> List[str]:
        return list(cls.CONFIGS.keys())


class IdFetcher:

    @staticmethod
    def _extract_items(data: Any) -> List[Dict]:
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for field in ['list', 'records', 'items', 'data', 'rows', 'content']:
                if field in data and isinstance(data[field], list):
                    return data[field]
            if data.get('id') is not None:
                return [data]

        return []

    @staticmethod
    def _find_in_tree(items: List[Dict], name: str, name_filed: str = 'name') -> Optional[Dict]:
        for item in items:
            if str(item.get(name_filed)) == str(name):
                return item
            if 'children' in item and isinstance(item['children'], list):
                found = IdFetcher._find_in_tree(item['children'], name, name_filed)
                if found:
                    return found

        return None

    @staticmethod
    def _get_total_from_response(data: Dict) -> int:
        for field in ['total', 'total', 'totalRecords', 'count']:
            if field in data:
                return int(data[field])
        return 0


    @staticmethod
    def _traverse_all_pages(
        list_method: Callable,
        name: str,
        name_field: str,
        id_field: str,
        page_size: int = 10,
        extra_match: bool = True,
        max_pages: int = 100,
        extra_params: Dict = None
    ) -> Optional[int]:

        page_num = 1
        total_checked = 0

        while page_num <= max_pages:
            try:
                params = {"page_num": page_num, "page_size": page_size}
                if extra_params:
                    params.update(extra_params)

                response = list_method(**params)

                if response.status_code != 200:
                    logger.warning(f"遍历第{page_num}页失败：{response.status_code}")
                    break

                data = response.json().get('data', {})
                items = IdFetcher._extract_items(data)

                if not items:
                    break

                total_checked += len(items)
                logger.debug(f"遍历第{page_num}页，共{len(items)}条，累计{total_checked}条")

                for item in items:
                    item_name = str(item.get(name_field, ''))
                    search_name = str(name)

                    if extra_match:
                        if item_name == search_name:
                            logger.info(f"在第{page_num}页找到记录：{item_name}, ID:{item.get(id_field)}")
                            return item.get(id_field)
                    else:
                        if search_name in item_name:
                            logger.info(f"在第{page_num}页找到记录：{item_name}, ID：{item.get(id_field)}")
                            return item.get(id_field)

                total = IdFetcher._get_total_from_response(data)

                if total > 0 and page_num * page_size >= total:
                    print("已遍历完所有的数据")
                    logger.debug(f"已遍历完所有数据，共{total}条")
                    break

                if len(item) < page_size:
                    print("这已是最后一页")
                    break

                page_num += 1

            except Exception as e:
                logger.error(f"遍历第{page_num}页失败：{e}")
                break

        return None


    @staticmethod
    def get_id_by_name(
            api_instance: Any,
            list_method: Callable,
            name: str,
            name_field: str = 'name',
            id_field: str = 'id',
            keyword_field: str = 'keyword',
            page_size: int = 10,
            max_retries: int = 3,
            retry_delay: float = 0.5,
            extra_match: bool = True,
            max_pages: int = 100,
            **kwargs
    ) -> Optional[int]:

        for attempt in range(max_retries):
            try:
                params = {}

                if keyword_field:
                    params[keyword_field] = name

                    params['page_num'] = 1
                    params['page_size'] = page_size

                    params.update(kwargs)
                    logger.debug(f"查询参数：{params}")

                    response = list_method(**params)

                    if response.status_code != 200:
                        logger.warning(f"列表查询失败：{response.status_code}， 尝试 {attempt + 1}/{max_retries}")

                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return None

                    data = response.json().get('data', {})

                    items = IdFetcher._extract_items(data)

                    for item in items:
                        item_name = str(item.get(name_field, ''))
                        search_name = str(name)

                        if extra_match:
                            if item_name == search_name:
                                return item.get(id_field)
                        else:
                            if search_name in item_name:
                                return item.get(id_field)

                result = IdFetcher._traverse_all_pages(
                    list_method=list_method,
                    name=name,
                    name_field=name_field,
                    id_field=id_field,
                    page_size=page_size,
                    extra_match=extra_match,
                    max_pages=max_pages
                )

                if result is not None:
                    return result

                if attempt < max_retries - 1:
                    logger.debug(f"未找到记录：'{name}', 等待重试 {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)

            except TypeError as e:
                if 'unexpected keyword argument' or 'page_num' or 'page_size' in str(e):
                    logger.warning(f"参数错误：{e}， 尝试不使用分页参数")
                    try:
                        params = {}
                        if keyword_field:
                            params[keyword_field] = name
                        params.update(kwargs)
                        response = list_method(**kwargs)

                        if response.status_code == 200:
                            data = response.json().get('data', {})
                            items = IdFetcher._extract_items(data)
                            for item in items:
                                if str(item.get(name_field, '')) == str(name):
                                    return item.get(id_field)
                    except Exception as e2:
                        logger.error(f"不带分页参数也失败：{e2}")

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise e

            except Exception as e:
                logger.error(f"获取ID失败：{e}，尝试 {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise e

        return None

    @staticmethod
    def get_id_by_field(
            api_instance: Any,
            list_method: Callable,
            field_value: Any,
            field_name: str,
            id_field: str = 'id',
            page_size: int = 50,
            max_retries: int = 3,
            retry_delay: float = 0.5,
    ) -> Optional[int]:

        for attempt in range(max_retries):
            try:
                params = {field_name: field_value, "pageSize": page_size, "pageNum": 1}
                params.update(params)

                response = list_method(**params)

                if response.status_code == 200:
                    data = response.json().get('data', {})
                    items = IdFetcher._extract_items(data)

                    for item in items:
                        if str(item.get(field_name)) == str(field_value):
                            return item.get(id_field)

                result = IdFetcher._traverse_all_pages(
                    list_method=list_method,
                    name=str(field_value),
                    name_field=field_name,
                    id_field=id_field,
                    page_size=page_size,
                    extra_match=True
                )

                if result is not None:
                    return result

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise e

        return None

    @staticmethod
    def get_latest_id(
            api_instance: Any,
            list_method: Callable,
            id_field: str = 'id',
            page_size: int = 1,
            **kwargs
    ) -> Optional[int]:

        params = {'pageSize': page_size, 'pageNum': 1}
        params.update(kwargs)

        try:
            response = list_method(**params)
        except TypeError:
            response = list_method(**kwargs)

        if response.status_code != 200:
            return None

        data = response.json().get('data', {})
        items = IdFetcher._extract_items(data)

        if items:
            sorted_items = sorted(items, key=lambda x: x.get(id_field, 0), reverse=True)
            return sorted_items[0].get(id_field)

        return None


    @staticmethod
    def get_category_id_by_name(category_api, name: str, parent_id: int = 0) -> Optional[int]:

        try:
            response = category_api.list(parent_id=parent_id, page_num=1, page_size=100) # 要找的数据过小
            if response.status_code != 200:
                logger.warning(f"获取分类列列表失败:{response.status_code}")
                return None

            data = response.json().get('data', {})
            items = IdFetcher._extract_items(data)

            for category in items:
                print(f"{category['name']} xxxxxxx {name}")
                if category.get('name') == name:
                    print(f"find {name} {category.get('name')} 的 id：{category.get('id')}")
                    return category.get('id')

            for category in items:
                if 'children' in category and isinstance(category['children'], list):
                    result = IdFetcher._find_in_tree(category['children'], name)
                    if result:
                        return result.get('id')

            return None
        except Exception as e:
            logger.error(f"获取分类ID失败:{e}")
            return None


    @staticmethod
    def get_id_by_module(
            api_instance: Any,
            module: str,
            search_value: str,
            **kwargs
    ) -> Optional[int]:

        config = ModuleFieldConfig.get_config(module)

        list_method_name = kwargs.get('list_method_name', config.get('list_method_name', 'list'))
        list_method = getattr(api_instance, list_method_name, None)

        if list_method is None:
            raise ValueError(f"API实例没有 '{list_method_name}' 方法")

        name_field = kwargs.get('name_field', config.get('name_field', 'name'))
        id_field = kwargs.get('id_field', config.get('id_field', 'id'))
        keyword_field = kwargs.get('keyword_field', config.get('keyword_field', 'keyword'))

        extra_params = kwargs.get('extra_params', {})

        if keyword_field is None:
            return IdFetcher._traverse_all_pages(
                list_method=list_method,
                name=search_value,
                name_field=name_field,
                id_field=id_field,
                page_size=kwargs.get('page_size',  10),
                extra_match=kwargs.get('extra_params', True),
                max_pages=kwargs.get('max_pages', 100),
                extra_params=extra_params
            )

        return IdFetcher.get_id_by_name(
            api_instance=api_instance,
            list_method=list_method,
            name=search_value,
            name_field=name_field,
            id_field=id_field,
            keyword_field=keyword_field,
            page_size=kwargs.get('page_size', 10),
            max_retries=kwargs.get('max_retries', 3),
            retry_delay=kwargs.get('retry_delay', 5),
            extra_match=kwargs.get('extra_match', True),
            max_pages=kwargs.get('max_pages', 100)
        )


    @staticmethod
    def _get_category_id_by_name(category_api, name: str, **kwargs) -> Optional[int]:
        try:
            parent_id = kwargs.get('parent_id', 0)
            response = category_api.list(parent_id=parent_id, page_num=1, page_size=100)
            if response.status_code != 200:
                return None

            data = response.json().get('data', {})
            items = IdFetcher._extract_items(data)

            for category in items:
                if category.get('name') == name:
                    return category.get('id')

                if 'children' in category:
                    for child in category['children']:
                        if child.get('name') == name:
                            return child.get('id')

            return None
        except Exception as e:
            logger.error(f"获取分类ID失败:{e}")
            return None

    @staticmethod
    def _get_flash_session_id_by_name(flash_session_api, name: str) -> Optional[int]:
        try:
            response = flash_session_api.list()
            if response.status_code != 200:
                return None

            data = response.json().get('data', [])
            items = IdFetcher._extract_items(data)

            for session in items:
                if session.get('name') == name:
                    return session.get('id')

            return None
        except Exception as e:
            logger.error(f"获取场次ID失败：{e}")
            return None

    @staticmethod
    def _get_id_by_traverse(
            api_instance: Any,
            list_method: Callable,
            search_value: str,
            name_field: str,
            id_field: str,
            page_size: int = 100,
            **kwargs
    ) -> Optional[int]:
        page_num = 1
        while True:
            try:
                params = {}

                params.update(kwargs)

                try:
                    response = list_method(**params)
                except TypeError:
                    response = list_method(**kwargs)
                    if response.status_code == 200:
                        data = response.json().get('data', {})
                        itmes = IdFetcher._extract_items(data)
                        for item in itmes:
                            if str(item.get(name_field)) == str(search_value):
                                return item.get(id_field)
                    break

                if response.status_code != 200:
                    break

                data = response.json().get('data', {})
                items = IdFetcher._extract_items(data)

                for item in items:
                    if str(item.get(name_field)) == str(search_value):
                        return item.get(id_field)

                total = data.get('total', 0)
                if page_num * page_size >= total:
                    break

                page_num += 1

            except Exception as e:
                logger.error(f"遍历获取ID失败：{e}")
                break

        return None


class IDFetcherWithAllure:

    @staticmethod
    @allure.step("通过名称获取记录ID")
    def get_id_by_name(
            api_instance: Any,
            list_method: Callable,
            name: str,
            name_field: str = 'name',
            id_field: str = 'id',
            keyword_field: str = 'keyword',
            page_size: int = 50,
            max_retries: int = 3,
            retry_delay: float = 0.5,
            extra_match: bool = True,
            max_pages: int = 100
    ) -> Optional[int]:
        allure.attach(
            f"搜索名称：{name}\n"
            f"字段名称：{name_field}\n"
            f"关键字字段：{keyword_field}\n"
            f"精确匹配：{extra_match}"
            f"最大遍历页数：{max_pages}",
            name="ID获取参数",
            attachment_type=allure.attachment_type.TEXT
        )

        result = IdFetcher.get_id_by_name(
            api_instance, list_method, name,
            name_field, id_field, keyword_field,
            page_size, max_retries, retry_delay, extra_match, max_pages
        )

        allure.attach(
            f"找到ID：{result}" if result else "未找到记录",
            name="ID获取结果",
            attachment_type=allure.attachment_type.TEXT
        )

        return result

    @staticmethod
    @allure.step("通过模块自动获取ID")
    def get_id_by_module(
            api_instance: Any,
            module: str,
            search_value: str,
            **kwargs
    ) -> Optional[int]:
        config = ModuleFieldConfig.get_config(module)
        allure.attach(
            f"模块：{module}\n"
            f"描述：{config.get('description', '')}\n"
            f"搜索值：{search_value}",
            name="模块ID获取参数",
            attachment_type=allure.attachment_type.TEXT
        )

        result = IdFetcher.get_id_by_module(api_instance, module, search_value, **kwargs)


        allure.attach(
            f"找到ID：{result}" if result else "未找到记录",
            name="模块ID获取结果",
            attachment_type=allure.attachment_type.TEXT
        )

        return result