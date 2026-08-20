# confest.py

import pytest
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入所有fixture
# from fixtures.admin_fixture import *
# from fixtures.member_fixture import *
# from fixtures.data_fixture import *
# from fixtures.product_fixtures import *

# 也可以使用 pytest_plugins 方式
pytest_plugins = [
    'fixtures.product_fixtures',
    'fixtures.admin_fixtures',
    'fixtures.member_fixtures',
    'fixtures.data_fixtures'
]


def pytest_configure(config):
    """ pytest配置勾子 """
    # 创建报告目录
    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "allure-results").mkdir(exist_ok=True)

    # 添加自定义标记
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "regression: 回归测试")
    config.addinivalue_line("markers", "admin: 后台管理测试")
    config.addinivalue_line("markers", "member: 前台用户测试")
    config.addinivalue_line("markers", "product: 商品管理测试")
    config.addinivalue_line("markers", "order: 订单管理测试")

    @pytest.fixture(scope="session", autouse=True)
    def test_session_setup():
        """ 测试会话设置 """
        print("\n" + "=" * 30)
        print("Mall API Test Framework Started")
        print("=" * 30)
        yield
        print("\n" + "=" * 30)
        print("Mall API Test Framework Finished")
        print("=" * 30)
