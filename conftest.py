# confest.py

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

pytest_plugins = [
    'fixtures.product_fixtures',
    'fixtures.admin_fixtures',
    'fixtures.member_fixtures',
    'fixtures.data_fixtures'
]

def pytest_configure(config):

    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "allure-results").mkdir(exist_ok=True)

    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "regression: 回归测试")
    config.addinivalue_line("markers", "admin: 后台管理测试")
    config.addinivalue_line("markers", "member: 前台用户测试")
    config.addinivalue_line("markers", "product: 商品管理测试")
    config.addinivalue_line("markers", "order: 订单管理测试")

    @pytest.fixture(scope="session", autouse=True)
    def test_session_setup():
        print("\n" + "=" * 30)
        print("Mall API Test Framework Started")
        print("=" * 30)
        yield
        print("\n" + "=" * 30)
        print("Mall API Test Framework Finished")
        print("=" * 30)
