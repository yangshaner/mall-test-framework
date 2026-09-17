# common/utils/data_generator.py

import random
import string
from datetime import datetime, timedelta
from typing import Dict
from faker import Faker


fake = Faker("zh_CN")

class DataGenerator:

    @staticmethod
    def random_string(lenght: int = 8) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=lenght))

    @staticmethod
    def random_int(min_val: int = 1, max_val: int = 100) -> int:
        return random.randint(min_val, max_val)

    @staticmethod
    def random_price(min_val: float = 0.01, max_val: float = 9999.99) -> float:
        return round(random.uniform(min_val, max_val), 2)

    @staticmethod
    def random_phone() -> str :
        return fake.phone_number()

    @staticmethod
    def random_name() -> str:
        return fake.name()

    @staticmethod
    def random_email() -> str:
        return fake.email()

    @staticmethod
    def random_data(start_days: int = 0, end_day: int = 30) -> tuple:
        start = datetime.now() + timedelta(days=start_days)
        end = datetime.now() + timedelta(days=end_day)
        return start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def random_bool() -> bool:
        return random.choice([True, False])

    @staticmethod
    def random_choice(items: list):
        return random.choice(items)

    @staticmethod
    def admin_login_data(username: str = 'admin', password: str = 'macro123') -> Dict:
        return {'username': username, 'password': password}

    @staticmethod
    def admin_register_data() -> Dict:
        username = f"test_{DataGenerator.random_string(6)}"
        return {
            'username': username,
            'password': '123456',
            'nikeName': f"测试用户_{username}",
            'email': f"{username}@test.com"
        }

    @staticmethod
    def brand_data() -> Dict:
        name = f"测试品牌_{DataGenerator.random_string(4)}"
        return {
            'name': name,
            'logo': f"{name}.png",
            'firstLetter': name[0].upper(),
            'sort': DataGenerator.random_int(0, 100),
            'showStatus': random.choice([0, 1]),
            'factoryStatus': random.choice([0, 1])
        }

    @staticmethod
    def product_category_data(parent_id: int = 0) -> Dict:
        name = f"测试分类_{DataGenerator.random_string(4)}"
        return {
            'parentId': parent_id,
            'name': name,
            'productUnit': '件',
            'sort': DataGenerator.random_int(0, 100),
            'showStatus': random.choice([0, 1]),
            'navStatus': random.choice([0, 1])
        }

    @staticmethod
    def product_data(brand_id: int, category_id: int) -> Dict:
        name = f"测试商品_{DataGenerator.random_string(6)}"
        return {
            'name': name,
            'productSn': f"TEST_{DataGenerator.random_string(8).upper()}",
            'price': DataGenerator.random_price(),
            'stock': DataGenerator.random_int(1, 100),
            'brandId': brand_id,
            'productCategoryId': category_id,
            'description': f'这是{name}的测试描述',
            'subTitle': f'测试副标题{DataGenerator.random_string(4)}',
            'publishStatus': 1,
            'verifyStatus': 1,
            'sort': DataGenerator.random_int(0, 100)
        }

    @staticmethod
    def coupon_data() -> Dict:
        start_time, end_time = DataGenerator.random_data(0, 30)
        return {
            'name': f'测试优惠卷_{DataGenerator.random_string(6)}',
            'type': random.choice([0, 1, 2, 3]),
            'amount': DataGenerator.random_price(5, 50),
            'minPoint': DataGenerator.random_price(10, 100),
            'count': DataGenerator.random_int(10, 100),
            'perLimit': DataGenerator.random_int(1, 5),
            'startTime': start_time,
            'endTime': end_time,
            'useType': random.choice([0, 1, 2]),
            'platform': random.choice([0, 1, 2]),
            'publishCount': DataGenerator.random_int(10, 100),
        }

    @staticmethod
    def order_data() -> Dict:
        return {
            'memberId': DataGenerator.random_int(1, 100),
            'couponId': DataGenerator.random_int(1, 100),
            'payAmount': DataGenerator.random_price(10, 500),
            'freightAmount': DataGenerator.random_price(0, 20),
            'receiverName': DataGenerator.random_name(),
            'receiverPhone': DataGenerator.random_phone(),
            'receiverProvince': '广东省',
            'receiverCity': '深圳市',
            'receiverRegion': '南山区',
            'receiverDetailAddress': f'测试地址_{DataGenerator.random_string(4)}'
        }

    @staticmethod
    def flash_promotion_data() -> Dict:
        start_time, end_time = DataGenerator.random_data(0, 7)
        return {
            'title': f'测试限时购_{DataGenerator.random_string(4)}',
            'startDate': start_time,
            'endDate': end_time,
            'status': random.choice([0, 1])
        }