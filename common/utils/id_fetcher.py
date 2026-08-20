# common/utils/id_fetcher.py
# -*- coding: utf-8 -*-
"""
通用ID获取工具 - 用于在测试中获取创建记录的ID
因为mall接口创建成功后返回的data是固定值1，而不是记录ID
"""
from typing import Callable, Optional, Any, Dict, List, Union
import time
import allure
import logging

logger = logging.getLogger(__name__)
"""
# 在测试中临时调试
# 先看看都有什么参数，然后写在配置文件中
import inspect
print(inspect.signature(brand_api.list))
"""

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
            'keyword_field': None,  # 分类接口没有keyword
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
            'keyword_field': 'name',  # 注意！是name不是keyword
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
            'support_pagination': True # 场次接口返回全部数据，不分页
        }
    }

    @classmethod
    def get_config(cls, module: str) -> Dict:
        """ 获取模块配置 """
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
        """ 列出所有支持的模块 """
        return list(cls.CONFIGS.keys())


class IdFetcher:
    """ 通用ID获取工具 """

    @staticmethod
    def _extract_items(data: Any) -> List[Dict]:
        """
        从不同格式的响应数据中提取列表

        Args:
            data: 响应数据

        Returns:
            记录列表
        """
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            # 尝试多种可能的列表字段
            for field in ['list', 'records', 'items', 'data', 'rows', 'content']:
                if field in data and isinstance(data[field], list):
                    return data[field]
            # 如果数据本身是记录对象，返回包含它的列表
            if data.get('id') is not None:
                return [data]

        return []

    @staticmethod
    def _find_in_tree(items: List[Dict], name: str, name_filed: str = 'name') -> Optional[Dict]:
        """ 在树形结构中递归寻找 """
        for item in items:
            if str(item.get(name_filed)) == str(name):
                return item
            # 如果有children，递归查找
            if 'children' in item and isinstance(item['children'], list):
                found = IdFetcher._find_in_tree(item['children'], name, name_filed)
                if found:
                    return found

        return None

    @staticmethod
    def _get_total_from_response(data: Dict) -> int:
        # 从响应中获取总数
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
        """
        遍历所有分页查找记录
        Args:
            list_method: 列表查询方法
            name: 要查找的名称
            name_field: 名称字段名
            id_field: ID字段名
            page_size: 每页大小
            extra_match: 是否精确匹配
            max_pages: 最大遍历页数
            extra_params: 额外的查询参数

        Returns:
            记录ID 或 None
        """
        page_num = 1
        total_checked = 0

        while page_num <= max_pages:
            try:
                # params = {"pageNum": page_num, "pageSize": page_size}
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
                print(f"total_checked: {total_checked}")
                logger.debug(f"遍历第{page_num}页，共{len(items)}条，累计{total_checked}条")

                # 在当前页查找
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

                # 检查是否还有下一页
                total = IdFetcher._get_total_from_response(data)
                # print(f"data: {data}")
                print(f"data.total:{int(data['total'])}")
                print(f"total:{total}, page_num:{page_num}, page_size:{page_size}")
                if total > 0 and page_num * page_size >= total:
                    print("已遍历完所有的数据")
                    logger.debug(f"已遍历完所有数据，共{total}条")
                    break

                # 如果返回的数据少于page_size,说明是最后一页
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
            max_pages: int = 100, # 最大遍历页数，防止无线循环
            **kwargs
    ) -> Optional[int]:
        """
        通过名称获取记录ID

        Args:
            api_instance: API实例（用于调用list_method）
            list_method: 列表查询方法
            name: 要查找的名称
            name_field: 名称字段名（默认'name'）
            id_field: ID字段名（默认'id'）
            keyword_field: 关键字参数字段名（默认'keyword'）
            page_size: 每页大小
            max_retries: 最大重试次数
            retry_delay: 重试间隔秒数
            extra_match: 是否精确匹配
            max_pages: 最大遍历页数（默认100）

        Returns:
            记录ID 或 None

        Example:
            >>> brand_id = IDFetcher.get_id_by_name(
            ...     brand_api,
            ...     brand_api.list,
            ...     "测试品牌_ABC",
            ...     name_field='name',
            ...     keyword_field='keyword'
            ... )
            >>> print(brand_id)  # 123
        """
        for attempt in range(max_retries):
            try:
                # 构建查询参数
                params = {}

                # 添加关键字参数
                if keyword_field:
                    params[keyword_field] = name

                    # 直接使用page_num 和 page_size
                    params['page_num'] = 1
                    params['page_size'] = page_size


                    # 添加额外参数
                    params.update(kwargs)
                    logger.debug(f"查询参数：{params}")
                    print(f"查询参数：{params}")

                    # 调用列表查询方法
                    response = list_method(**params)

                    if response.status_code != 200:
                        logger.warning(f"列表查询失败：{response.status_code}， 尝试 {attempt + 1}/{max_retries}")

                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return None

                    data = response.json().get('data', {})

                    # 处理不同的数据结构
                    items = IdFetcher._extract_items(data)

                    # 查找匹配的记录
                    for item in items:
                        item_name = str(item.get(name_field, ''))
                        search_name = str(name)

                        if extra_match:
                            if item_name == search_name:
                                return item.get(id_field)
                        else:
                            if search_name in item_name:
                                return item.get(id_field)

                # 如果关键字搜索没找到，或者没有keyword字段，进行全量遍历
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

                # 如果没找到，等待后重试（可能数据还未写入）
                if attempt < max_retries - 1:
                    logger.debug(f"未找到记录：'{name}', 等待重试 {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)

            except TypeError as e:
                # 如果是参数类型错误，尝试使用不同分页参数
                if 'unexpected keyword argument' or 'page_num' or 'page_size' in str(e):
                    logger.warning(f"参数错误：{e}， 尝试不使用分页参数")
                    try:
                        # 尝试不带分页参数
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
        """
        通过任意字段值获记录ID

        Args:
            api_instance: API实例
            list_method: 列表查询方法
            field_value: 字段值
            field_name: 字段名
            id_field: ID字段名
            page_size: 每页大小
            max_retries: 最大重试次数
            retry_delay: 重试间隔

        Returns:
            记录ID 或 None

        Example:
            >>> # 通过货号获取商品ID
            >>> product_id = IDFetcher.get_id_by_field(
            ...     product_api,
            ...     product_api.list,
            ...     "PROD_001",
            ...     "productSn"
            ... )
        """
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

                # 如果没有找到，遍历所有页
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
        """
        获取最新创建的记录ID

        Args:
        api_instance: API实例
        list_method: 列表查询方法
        id_field: ID字段名
        page_size: 每页大小
        **kwargs: 其他查询参数

        Return:
             最新记录ID 或 None
        """
        params = {'pageSize': page_size, 'pageNum': 1}
        params.update(kwargs)

        try:
            response = list_method(**params)
        except TypeError:
            # 如果不支持分页参数，尝试不带
            response = list_method(**kwargs)

        if response.status_code != 200:
            return None

        data = response.json().get('data', {})
        items = IdFetcher._extract_items(data)

        if items:
            # 按ID降序排列获取最新的
            sorted_items = sorted(items, key=lambda x: x.get(id_field, 0), reverse=True)
            return sorted_items[0].get(id_field)

        return None


    @staticmethod
    def get_category_id_by_name(category_api, name: str, parent_id: int = 0) -> Optional[int]:
        """
        专门获取分类ID - 支持递归查找所有层级

        Args:
            category_api: 分类API实例
            name: 分类名称
            parent_id: 父分类ID，默认0表示一级分类

        Return:
            分类ID 或 None
        """
        try:
            # 先尝试直接查询
            response = category_api.list(parent_id=parent_id, page_num=1, page_size=100) # 要找的数据过小
            if response.status_code != 200:
                logger.warning(f"获取分类列列表失败:{response.status_code}")
                return None

            data = response.json().get('data', {})
            items = IdFetcher._extract_items(data)
            print(f"data-itemsxxx:{items}")

            # 在列表中查找
            for category in items:
                print(f"{category['name']} xxxxxxx {name}")
                if category.get('name') == name:
                    print(f"find {name} {category.get('name')} 的 id：{category.get('id')}")
                    return category.get('id')

            # 如果有children，递归查找
            for category in items:
                if 'children' in category and isinstance(category['children'], list):
                    # 在子分类中查找
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
        """
        根据模块自动适配字段配置获取ID

        Args:
            api_instance: API实例
            module: 模块名称('brand', 'product', 'coupon', 'admin', 'order', 'category')
            search_value: 搜索值
            **kwargs: 额外参数（可覆盖默认配置）

        Return:
             记录ID 或 None

        Example:
            >>> # 品牌
            >>> brand_id = IDFetcher.get_id_by_module(brand_api, 'brand', "测试品牌")
            >>>
            >>> # 优惠券（自动使用 name 作为关键字参数）
            >>> coupon_id = IDFetcher.get_id_by_module(coupon_api, 'coupon', "测试优惠券")
            >>>
            >>> # 用户（自动使用 username 作为名称字段）
            >>> user_id = IDFetcher.get_id_by_module(admin_api, 'admin', "testuser")
        """
        config = ModuleFieldConfig.get_config(module)

        # 获取对应的list方法
        list_method_name = kwargs.get('list_method_name', config.get('list_method_name', 'list'))
        list_method = getattr(api_instance, list_method_name, None)

        if list_method is None:
            raise ValueError(f"API实例没有 '{list_method_name}' 方法")

        name_field = kwargs.get('name_field', config.get('name_field', 'name'))
        id_field = kwargs.get('id_field', config.get('id_field', 'id'))
        keyword_field = kwargs.get('keyword_field', config.get('keyword_field', 'keyword'))

        # 获取额外参数
        extra_params = kwargs.get('extra_params', {})

        # 如果没有keyword字段，直接遍历
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

        # 标准查询(带分页遍历)
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
        """ 分类特殊处理 - 遍历所有分类 """
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

                # 检查子分类
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
        """ 限时购场次特殊处理 """
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
            #page_param: str = 'page_num',
            #size_param: str = 'page_size',
            page_size: int = 100,
            **kwargs
    ) -> Optional[int]:
        """ 通过遍历所有分页获取ID（用于没有keyword参数的接口） """
        page_num = 1
        while True:
            try:
                params = {}

                params.update(kwargs)

                try:
                    response = list_method(**params)
                except TypeError:
                    # 如果不支持分页参数
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

                # 检查是否还有下一页
                total = data.get('total', 0)
                if page_num * page_size >= total:
                    break

                page_num += 1

            except Exception as e:
                logger.error(f"遍历获取ID失败：{e}")
                break

        return None


class IDFetcherWithAllure:
    """ 带allure报告的ID获取器 - 组合方式而非继承 """

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
        """ 带allure报告的版本 """
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
        """ 带allure报告的模块版本 """
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
