# mall 接口自动化项目介绍

- 可执行、可维护、可扩展、可接入Jenkins

- 考虑并发、mock数据、多线程、token管理

- 前后台分开

- 目录分开、Fixture分开

- API分层

- 公共能力复用

- 场景测试可以跨前后台

- 认证、API 封装、Fixture、业务测试、数据库断言、Jenkins

- 加入并发设计和Mock支持

# 设计思路

- 框架设计：四层架构（Client → API → Fixture → TestCase），职责清晰、易维护。

- 认证管理：支持前后台双 Token 自动获取、缓存和失效刷新。

- 数据管理：统一封装 MySQL、Redis 操作，支持测试数据初始化和数据库断言。

- 测试能力：参数化、数据驱动、接口场景、数据库一致性、日志、Allure 报告。

- 工程化能力：Git 管理、Jenkins 持续集成、自动生成测试报告。

## 层级设计

### 第一层 - BseClient

所有请求不直接调用 `requests.get()` 或 `requests.post()`，统一走 BaseClient，

```
class BaseClient:

    def get(self,url,**kwargs):
        ...

    def post(self,url,**kwargs):
        ...

    def put()

    def delete()
```

以后统一处理

* timeout
* retry
* log
* token
* headers
* allure
* request_id

全部只改这一层。

预保留：
```
BaseClient
      │
      ├── Retry
      ├── Token Refresh
      ├── Mock
      ├── SSL
      ├── Timeout
      ├── Upload
      ├── Download
      ├── Performance Hook
      └── Request Log
```

### 第二层 - Token管理

不在 headers 上直接写：`headers = {"Authorization":"Bearer:xxx"}`

建议： AdminAuth -> TokenManager -> BaseClient -> API 

例如

`AdminTokenManager.get_token()` 后，

在 BaseClient 中自动：

`Authorization`

不用每个接口写。

### 第三层 - API 层

例如：后台

`ProductApi`

里面只有：

* create()
* update()
* delete()
* query()
* detail()

例如
```
class ProductApi:

    def create():

    def delete():

    def update():

    def list():
```
不要写测试逻辑。

这里只负责： 调接口。

预保留：

```
Admin
Member
ThirdParty
OpenAPI
```

### 第四层 - Fixture 层 （ 参考 wazuh 的 设计 ？）

例如：

`@pytest.fixture`

负责： 管理员登录 -> 获取token -> 返回 cient

例如：
```
@pytest.fixture(scope="session")
def admin_client()：
```
返回 `ProductApi()` ?

这样，test 不用关心登录

### 第五层 - TestCase 层

这里只写： 业务。

例如：

`def test_create_product():`

里面： 调用API -> 断言 -> 数据库校验

不要：`requests.post()`

### 第六层 - 数据库层

例如：

统一： `MysqlUtil`

提供：
```
* query()
* execute()
* fetchone()
* fetchall()
```
测试直接： `mysql.query()` 即可。

### 第七层 - Redis层

统一：`RedisUtil`

以后验证：

* token
* 缓存
* 库存
* 验证码

直接：`redis.get()`

### 第八层 - Logger

不要： `print()`

统一：

`logger.info()`
`logger.error()`
`logger.warning()`

以后： Jenkins

日志： 全部统一。

### 第九层 - Allure

例如：

`BaseClient` 自动：

`allure.step()` 自动记录：

* URL
* Method
* Header
* Request
* Response
* SQL
* 耗时

以后不用每个接口写： `with allure.step():` (wazuh那边这个没有封装，有些冗余了)

### 第十层 - Jenkins

最终 Jenkins 其实非常简单。

例如： Git Pull -> pip install -> pytest -> 生成Allure -> 发送企业微信 -> 发送邮件

整个流程：GitLab -> Webhook -> Jenkins -> pytest -> Allure -> Archive -> 通知

`Jenkinsfile`：例如

```
pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                git url:'git地址'
            }
        }
        stage('Install') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Run Test') {
            steps {
                sh 'pytest testcase --alluredir=report/allure-results'
            }
        }
        stage('Generate Report') {
            steps {

                sh 'allure generate report/allure-results -o report/allure-report --clean'
            }
        }
    }
}
```

## 接口封装

一般封装四层：

```
TestCase
    │
    ▼
Business API（业务接口）
    │
    ▼
BaseClient（HTTP客户端）
    │
    ▼
requests.Session
```

这样以后接 Jenkins、重试、Token、日志、Mock 都不用改业务代码。


### BaseClient（整个框架最核心）

它不关心业务, 只负责：

* GET
* POST
* PUT
* DELETE
* Session
* Header
* Timeout
* Retry（以后）
* 日志（以后）
* Allure（以后）
* Token（以后）

所以接口统一走这里，任何接口都不能直接 requests， 而是 `client.post()`

### 配置 BaseUrl

不要写：
```
BaseClient(
    "http://localhost:8080"
)
```

建议： 例如

```common/config/config.yml

dev:
  admin_url: http://localhost:8080
  member_url: http://localhost:8085

test:
  admin_url:

prod:
```
以后： 切环境,只改 yaml。

### AdminClient

例如：

```
# common/client/admin_client.py

from common.client.base_client import BaseClient

class AdminClient(BaseClient):

    def __init__(self):
        super().__init__(admin_url)

```
以后所有后台接口都是： `AdminClient()`

### MemberClient

同理： `MemberClient` 只负责前台。

以后两套 Token 天然隔离。

###  业务API

例如：
```api/admin/product_api.py
from common.client.admin_client import AdminClient

class ProductApi:
    def __init__(self):
        self.client = AdminClient()

    def list(self,
             page_num,
             page_size):
        return self.client.get(
            "/product/list",
            params={
                "pageNum": page_num,
                "pageSize": page_size
            }
        )

    def detail(self, product_id):

        return self.client.get(
            f"/product/{product_id}"
        )

    def create(self,
               data):

        return self.client.post(
            "/product/create",
            json=data
        )
```

- 但是这样写请求的路径会不会太明显或冗余，要不提前写一个请求地址的封装（参考wazuh那样），又或者不封装

原则：一个 API 类对应一个业务模块。

例如：

* ProductApi
* BrandApi
* CategoryApi
* OrderApi
* CouponApi

不要： `MallApi` 几百个函数。


### TeseCase 

测试变得很简单。

例如：
```
def test_product_list():

    api = ProductApi()

    r = api.list(
        page_num=1,
        page_size=10
    )

    assert r.status_code == 200
```
这里测试代码不知道 `requests`, 也不知道 `BaseURL`, 更不知道 `Header`, 全部隐藏。

### 扩展Token

以后登录完成，例如：

AdminClient -> TokenManager -> Session.headers -> Authorization -> ProductApi

根本不用：
```
headers={
    Authorization
}
```
以后所有接口自动带。

注意；前台不同客户端使用不同的token，在多线程或并发的时候，token的管理

## 接口实现

不建议：`BaseClient + ProductApi` 的简单写法

建议：

TestCase
    │
Business（业务流程封装，可选）
    │
API（单接口封装）
    │
Client（HTTP客户端）
    │
requests.Session

### 第一阶段（基础框架）

* BaseClient（HTTP 请求统一入口） 
* Config（YAML 多环境）
* AdminClient / MemberClient
* Logger（日志）
* TokenManager（自动登录、缓存、刷新）

### 第二阶段（业务封装）

* ProductApi
* BrandApi
* CategoryApi
* OrderApi 
* CartApi

### 第三阶段（测试层）

* Fixture
* TestCase
* Database Assert
* Redis Assert

### 第四阶段（工程化）

* Allure
* Retry
* Jenkins
* 并发测试
* Mock

## 疑问

1. 后台不同管理员的权限不一样，在访问接口的时候如何判断
2. assert的封装
3. 请求地址封装
4. 和postman做接口测试有什么区别吗
5. 场景测试的设计呢
6. 感觉代码看起来不是很复杂，
7. 如何结合Jenkins做CI/CD呢，为什么要使用Jenkins
8. deepseek根据我的指令生成代码还是参考我的建议结合它的建议去生成代码呢
9. 并发测试和多线程要怎么实现呢
10. 配置文件config.yml有点奇怪
11. token是如何管理的
12. pruduct_api的一些接口是存在的吗，比如批量xxx
13. deepseek给的代码不全，会编造一些未实现的api
14. postman如何做接口测试，可以生成allure报告吗



## 运行命令
* 安装依赖
`pip install -r requirements.txt`

* 设置环境变量
`export TEST_ENV=dev`

* 先确保所有fixtures正确导入
`pytest --collect-only`

* 查看fixture依赖
`pytest --fixtures`

* 运行所有测试
`pytest`

* 运行冒烟测试
`pytest -m smoke`

* 运行指定模块
`pytest testcases/admin/test_product.py`

* 运行指定测试（运行单个测试）
`pytest testcases/admin/test_product.py::TestProduct::test_create_product`

* 并行执行
`pytest -n auto`

* 运行所有member测试
`pytest testcases/member/ -v`

* 运行后台权限测试
`pytest testcases/admin/test_permission.py`

* 如果fixture找不到，检查conftest.py配置
`pytest --setup-show testcases/member/test_cart.py`

* 运行场景测试
`pytest testcases/member/test_scenario.py`

* 生成Allure报告
`pytest --alluredir=reports/allure-results`
`allure serve reports/allure-results`

* 生成HTML报告
`pytest --html=reports/report.html --self-contained-html`

* 使用run脚本
`python run_tests.py`
`python run_tests.py smoke`
`python run_tests.py module test_product`



## 版本迭代

### 第一版

框架实现：
- 四层架构： BaseClient -> API -> Fixture -> TestCase
- 自动Token管理： 支持多客户端、多线程Token隔离
- 数据库和Redis验证：支持接口返回 + 数据库双重认证
- Allure报告：自动记录 请求/响应/SQL/耗时
- 并发集成：使用pytest-xdist 并行执行
- Jenkins集成：包含Jenkinsfile和通知
- 参数化测试：使用@pytest.mark.parametrize
- 测试数据管理：统一数据生成和清理

存在的问题：
- 代码没有全部实现，只实现了部分的admin部分的api，member的api都没实现，（有些代码还没写， fixture的，testcases的）
- Jenkinsfile那里还没有理解清楚
- token是如何管理的
- 没有assert断言
- wraper是什么
- 自定义断言是什么

### 第二版

1. 增加断言模块：

* BaseAssertion: 基础断言方法
* ApiAssertion: API响应断言
* DBAssertion: 数据库断言
* RedisAssertion: Redis断言
* SoftAssertion: 软断言上下文

2. 断言的使用方式
- 强断言：立即失败 
- 软断言：收集所有错误后统一抛出
- 数据库断言：自动验证数据一致性

3. Token上下文管理
- 线程隔离的Token存储
- 自动Token刷新
- 用户切换上下文
- 临时Token上线文
- 多客户端Token隔离

4. 集成到BaseClient
- 自动从上下文中获取Token
- 支持多客户端类型

存在的问题：
1. 部分api、fixtures、testcases的代码还没实现
2. token的实现机制没有理解
3. @dataclass是什么
4. field是什么
5. 





### 第三版

add：

1. 添加角色管理模块代码和配置文件
2. 前台部分api的实现
3. 前台fixture的实现
4. 前台测试用例
5. 后台权限测试
6. 更新MemberClient支持用户切换和token的管理（从tokenManager 改为使用token_context）
7. 更新配置文件

more specific:
1. 前台完整API：登录、商品、购物车、订单、优惠券、地址、收藏、关注、浏览记录、首页
2. 角色权限管理：支持多角色、多用户、权限检查、资源服务控制
3. 权限测试：不同角色对同一接口的不同访问结果
4. 场景测试；完整购物流程、优惠券使用流程
5. Token上下文：支持多用户切换、自动刷新
6. 前后台Token隔离：AdminClient和MemberClient独立管理Token



存在的问题：
1. admin_roles.yml中的resources和menus指的什么
2. test_user.yml中的roles和status指的什么
3. 应为类型 'dict'，但实际为 'Response'  ？返回类型的设定
4. coupon_api.py 没看懂
5. 部分前台的api没有实现：brand_api 和 return_api, 不过在fixture中也没有用到
6. fixture的使用
7. allure的使用
8. tokenHead是什么
9. 在test_get_auth_code中redis验证如何实现呢
10. 前台测试用例会不会太少，且没有添加装饰器说明是回归测试还是集成测试还是其他
11. SoftAssertion导入了却没有用到
12. 在前台场景测试中优惠券可能在其他场景使用的情况要怎么办呢
13. AdminClient没有_login_with_user这个函数，但在test_permission中使用了 ？、（或许让它检查生成的饿内容）
14. 并发是用pytest写还是jmeter操作好一些呢
15. 资源是指的什么



遇到的问题：
1. 死循环：_login() → post() → request() → _login() → post() → ...：
这个错误是因为 MemberClient 的 _login 方法中调用了 self.post()，
而 self.post() 又会调用 self.request()，self.request() 中又会检查 Token 并可能再次调用 _login()，形成了递归调用

在AdminClient中也存在 _login() 调用 self.post 然后形成递归的问题，一样的解决方法


解决方案： 
1. 直接使用requests发送登录请求，然后再设置token，保存token到上下文中 
- 彻底解决递归问题：登录逻辑与业务请求完全分离
- 简单清晰：不依赖于复杂的装饰器和标记
- 易于理解：登录就是登录，请求就是请求
- 兼容性好：不依赖特定的请求拦截逻辑


## 第四版

add：

1. 后台fixture - 没写
2. 完善补充完整前台fixtures
3. 实现fixtures/部分
4. 补充后台api
6. 
7. 补全缺失的api文件，包括：

    CategoryApi - 商品分类管理  -> ok

    CouponApi - 优惠券管理   -> ok

    AdminApi - 后台用户管理   -> ok

    FlashApi - 限时购管理  -> ok

    MemberBrandApi - 前台品牌管理   -> ok

    ReturnApi - 退货申请管理  -> ok


8. 更新api/admin/__init__.py
9. 更新api/member/__init__.py
10. 更新 fixtures/member_fixtures.py

11. 修改base_assertion.py中的关于filed部分的方法
12. 完善api_assertion.py中的assert_page_response方法
13. 调整test_order.py中的

关键点：

1. 清理：每个fixture都应该有清理逻辑
2. 跳过条件：如果数据不存在，使用`pytest.skip()`跳过测试


遇到的问题：
1. 找不到fixture - 创建fixture：
例如：找不到test_product这个fixture, 
原则	    说明
单一职责	product_fixtures.py 只负责商品相关数据创建
依赖注入	member_fixtures.py 通过参数依赖 test_product，不自己创建
共享复用	test_product 可以被后台和前台测试共享使用
清晰依赖链	test_cart_item → test_product → 商品创建逻辑
易维护	修改商品创建逻辑只需要改一个文件


2. fixtures\product_fixtures.py:30: in test_product
    brand_id = brand_result.get("data", {}).get("id")
E   AttributeError: 'str' object has no attribute 'get'

说明：这个错误表明 brand_result 是一个字符串（str），而不是预期的字典对象。
当你尝试调用 .get() 方法时，字符串没有这个方法，所以报错。

这个错误表明 admin_client_for_setup 没有成功获取到有效的 token，导致调用后台API时返回了401未授权错误。
brand_result 是错误响应的字典，而不是预期的成功响应，
所以调用 .get("data", {}) 时返回的是字符串 'Full authentication is required to access this resource'，而不是字典

问题原因：

问题出在 admin_client_for_setup 的登录认证没有成功 或者 认证成功但返回值没有id这个属性

- 找 token 的设置流程，


brand_result 应该是 API 返回的 JSON 响应（字典），但实际上返回的是字符串，可能是：

- API 返回了错误信息（字符串）
- 响应没有被正确解析为 JSON
- API 返回的是纯文本而不是 JSON 格式
- 请求失败，返回了错误消息字符串



处理方式：

- 修改 common/client/base_client.py：
在 __init__ 中添加 _is_refreshing 标志，并增加 _refresh_token 和 _do_request 方法。

- 修改 common/client/admin_client.py 和 member_client.py （同样的处理方式）
确保 _login 方法返回正确的 token 信息，并且 set_token 被调用以更新上下文和 Session。

- 修改 fixture（增加健壮性）
在 fixtures/member_fixtures.py 中，我们可以简化 test_cart_item，因为 BaseClient 会自动处理 token 刷新，但为了安全，保留断言：

工作原理：

     当 cart_api.list() 被调用时，BaseClient.request 发起请求。

    如果服务端返回业务 401，request 检测到 code == 401。

    调用 _refresh_token()，该方法会调用子类的 _login() 重新登录。

    _login() 获取新 token，并通过 set_token 更新 Session 和 TokenContext。

    然后重试原始请求（_do_request），此时 token 已更新，请求成功。

    上层 fixture 得到正常响应，继续执行。

这样，所有 API 调用都能自动处理 token 过期，无需在每个测试中处理 401。


3. 区分HTTP状态码 和 业务状态码
增强 MemberClient 的自动刷新

在 MemberClient 的 request 方法中，如果检测到业务错误码 401，则刷新 token 并重试一次。

但更稳健的方式是：在 BaseClient 的 request 方法中捕获 401 业务错误，并调用刷新回调。但为了简化，我们可以在 MemberClient 中重写 request 方法。

业务错误只需要处理401吗，还有http的200呢 ？ response的具体解释和使用方式



登录 
获取token 
设置token：token head 和 token data 
携带token去访问其他接口

4. base_assertion.py中_assert()和assert_field_exists()方法逻辑可能有些问题：
- assert_field_exists 方法不支持字符串参数：当传入单个字段名（字符串）时，会遍历每个字符，导致错误
- 错误信息中期望值和实际值的语义混淆：在字段存在性断言中，"期望值"和"实际值"的表述不够清晰


疑问：
1. @pytest.fixture的作用
2. admin的限时购活动在member的testcases中有测试到吗
3. 直接打印response会显示<response 200> ?
4. base_assertion.py 中的_assert ？
5. token的设置和管理方式
6. 有些断言的逻辑存在问题吗
7. 为测试环境提供mock或fallback ？how

待完成：
1. fixtures/的__init__.py文件没写, 或许也不用写，应为在conftest.py文件中也会引用 ？
2. fixtures//admin_fixture.py 文件没写

心得：
1. 在debug中进一步熟悉代码的整体逻辑和流程


## 第五版

说明：

调试testcases/member部分的测试用例可以运行了

涉及到admin部分的测试用例还在开发中


思路：

1. 我们需要为每个模块编写至少覆盖主要接口的测试用例（增删改查）。同时，对于只读接口，简单验证返回即可。

2. 还需要确保每个测试文件都使用已定义的 fixtures (如 admin_client, db_assert, data_generator) 和断言工具。

3. 写关于admin模块测试用例关键点：

    所有测试使用 admin_client fixture 获取已认证的后台客户端。

    使用 ApiAssertion 进行统一断言。

    创建测试数据后尽可能清理，避免污染环境。

    对于只读接口，简单验证返回成功和数据结构即可。

    对于涉及状态修改的，注意恢复或使用临时数据

4.这些测试将覆盖核心业务模块，结合断言、数据库验证、参数化等。


补充说明

    测试依赖：部分测试依赖已有数据（如test_order.py中的test_delivery_order需要待发货订单），如果测试环境无数据，会使用pytest.skip()跳过。

    数据库清理：为了测试的独立性，建议在conftest.py中配置autouse fixture，在每个测试后回滚事务或清理测试数据（但需要谨慎，避免影响其他测试）。简单的做法是使用pytest-django的TransactionTestCase或pytest-flask的db fixture，但在纯API测试中，我们通常使用test_product、test_brand等fixture创建测试数据，并在测试后清理。

    权限测试：需要实现admin_client_factory fixture，它根据用户名登录并返回对应客户端。示例实现：
    python

    @pytest.fixture
    def admin_client_factory():
        def _create_client(username):
            client = AdminClient()
            # 登录该用户
            client._login_with_user(username)
            return client
        return _create_client

    软断言：在复杂场景中，可使用SoftAssertion收集多个断言，最后统一报告。

    Allure报告：所有测试步骤都使用了@allure.step装饰器，便于生成清晰的报告。


bugs：

现在这个bug可以作为测试报告：

1. 提交订单接口HTTP返回200，但业务创建订单失败，数据库插入异常。
```
testcase\member\test_scenario.py:97: in test_full_shopping_flow
    result = self.api_assert.assert_success(response, "生成订单失败")
common\assertions\api_assertion.py:29: in assert_success
    self.assert_response_code(response, 200, f"{message}: 业务状态码错误", soft)
common\assertions\base_assertion.py:395: in assert_response_code
    return self._assert(
common\assertions\base_assertion.py:78: in _assert
    raise AssertionError(full_message)
E   common.assertions.base_assertion.AssertionError: 生成订单失败: 业务状态码错误
E   期望业务状态码:200
E   实际业务状态码:500
```

原因分析：提交订单需要开启rabbitmq才可以去生成订单

（也不是bug，就是环境或者参数没配置合适）



疑问：
1.如何Mock数据呢，比如用户从搜索商品到下单支付最后收货完整订单，中间需要管理员那边的发货，
但是现在在member的scenario中没有写

2.Jenkins也还没有接入

3.后台接口文档中的所有 Controller 都要覆盖吗，会有很多的 ！

4.setup_method的作用



心得：
1. 感觉现在写的代码还是很初级，


callbacks:
1. admin_fixtures， ->  ok
2. 以及admin's testcases


## 第六版

add：


1. 完整的 id_fetcher.py：支持多种模块的ID获取，包括标准查询、特殊模块（分类、场次）处理、带Allure报告版本。

2. 完整的后台测试模块：

    test_login.py：登录认证测试

    test_brand.py：品牌管理测试

    test_category.py：分类管理测试

    test_product.py：商品管理测试

    test_order.py：订单管理测试

    test_permission.py：权限管理测试



设计思路：

ID获取方式：

    品牌：IDFetcher.get_id_by_module(brand_api, 'brand', brand_name)

    分类：IDFetcher.get_id_by_module(category_api, 'category', category_name)

    商品：IDFetcher.get_id_by_module(product_api, 'product', product_name)

    优惠券：IDFetcher.get_id_by_module(coupon_api, 'coupon', coupon_name)

    用户：IDFetcher.get_id_by_module(admin_api, 'admin', username)

测试结构：每个测试都包含创建→获取ID→验证→清理的完整流程

    
接口	                    返回格式	                获取ID方式
/brand/create	        {"code":200,"data":1}	通过名称查询品牌列表获取ID
/productCategory/create	{"code":200,"data":1}	通过名称查询分类列表获取ID
/product/create	        {"code":200,"data":1}	通过名称模糊查询商品获取ID


2.
mysql_util.py：将 query 方法改为直接返回结果列表，而不是使用上下文管理器。

db_assertion.py：新增 assert_order_status 和 assert_order_delivery 方法，封装常用数据库断言。

test_scenario.py：

    使用修复后的 mysql.query() 直接获取结果

    通过 result[0].get('status') 正确访问数据

    增加物流信息的验证




心得：
1.函数的提取（抽象）：
```原型01：
    def _get_brand_id_by_name(self, brand_api, name):
        """根据名称获取品牌ID"""
        response = brand_api.list(page_num=1, page_size=20, keyword=name)
        data = response.json().get('data', {})
        for brand in data.get('list', []):
            if brand.get('name') == name:
                return brand.get('id')
        return None
```

```原型02：
    def _get_category_id_by_name(self, category_api, name):
        """根据名称获取分类ID"""
        response = category_api.list(parent_id=0, page_num=1, page_size=50)
        data = response.json().get('data', {})
        for category in data.get('list', []):
            if category.get('name') == name:
                return category.get('id')
        return None
```

```原型03：
def _get_product_id_by_name(self, product_api, name):
        """根据名称获取商品ID"""
        response = product_api.simple_list(name)
        data = response.json().get('data', [])
        for product in data:
            if product.get('name') == name:
                return product.get('id')
        return None
```

```抽象后：
# common/utils/id_fetcher.py
from typing import Callable, Optional


class IDFetcher:
    """通用ID获取工具"""
    
    @staticmethod
    def get_id_by_name(
        api_instance,
        list_method: Callable,
        name: str,
        name_field: str = 'name',
        id_field: str = 'id',
        keyword_field: str = 'keyword',
        page_size: int = 50
    ) -> Optional[int]:
        """
        通过名称获取记录ID
        
        Args:
            api_instance: API实例
            list_method: 列表查询方法
            name: 要查找的名称
            name_field: 名称字段名
            id_field: ID字段名
            keyword_field: 关键字参数字段名
            page_size: 每页大小
        
        Returns:
            记录ID或None
        """
        response = list_method(**{keyword_field: name, 'pageSize': page_size})
        data = response.json().get('data', {})
        
        # 如果data是列表
        if isinstance(data, list):
            for item in data:
                if item.get(name_field) == name:
                    return item.get(id_field)
        
        # 如果data是字典且包含list
        if isinstance(data, dict):
            items = data.get('list', [])
            for item in items:
                if item.get(name_field) == name:
                    return item.get(id_field)
        
        return None

```
```使用方式：
from common.utils.id_fetcher import IDFetcher

brand_id = IDFetcher.get_id_by_name(
    brand_api, 
    brand_api.list, 
    brand_name,
    name_field='name',
    keyword_field='keyword'
)
```

遇到的问题：
`commandline
fixtures\product_fixtures.py:105: in test_brand
    brand_id = brand_result.get("data", {}).get("id")
E   AttributeError: 'int' object has no attribute 'get'
`

解决方式：
重写方法，不用这个fixture

或者把test_brand里面的获取id的逻辑改为`brand_id = IDFetcher.get_id_by_name`, 因为这样可以在testcases中写少一些

testcases中的用例也不应该写这么多


断点：
1.member的testcases/中的集成测试需要用到admin的api
2.admin的testcases/ -》 需要获取id -》IDFetcher.py的编写与完善 -》 具体的使用方式  -》完善代码

(deepseek有时提供的代码东一块西一块的，上下文也对不太上，看似能用，实则还需自己整合与调试)
(感觉deepseek也是有点拟人，你觉得它给出的东西不能直接上手用时，提出要更完整的整体逻辑时，它就会库库输出，上下文也对上了，总结也给你整好)




to do lists:
1.项目代码的完善和测试：
    id_fetcher.py -> ok, test_login.py -> ok, test_brand.py -> ok, 
    test_category.py -> ok, test_product.py -> ok(感觉逻辑有点奇怪),


    

2.接入jenkins
3.zentao的管理
4.注意一个只读用户：username：readonly_user, password: readonly1234



心得：
1.使用fixtures可以省去导入定义，实例化的过程



## 第七版

add：

1. 主要是整体的调试 :tesecases/member -> 测试ok

2. 测试代码的提取与优化



关键改进

    软断言处理：在 test_get_order_list_by_status 中使用 SoftAssertion，避免单个订单状态不匹配导致整个测试失败

    数据准备：在测试前获取实际存在的订单，而不是假设存在特定状态的订单

    状态验证：使用更灵活的方式验证状态，考虑测试环境的实际情况

    错误信息：提供更详细的错误信息，便于调试

    清理机制：使用 fixture 和 finally 确保测试数据被正确清理

    参数化测试：覆盖更多测试场景

    数据库验证：每个操作后验证数据库状态一致性






遇到的问题：
1. pytest测试隔离性问题 - pytest fixture 作用域冲突

最可能的原因：事务隔离级别和自动提交, 数据库连接在多个测试间共享，事务未提交。 

在 mysql_util.py 中，query() 方法使用了 _get_connection() 获取连接，
但这个连接可能在不同的测试用例中被复用， 且 autocommit=False。
当订单在前面的步骤中创建后，如果没有显式提交，后续的查询可能看不到数据。

为什么单独运行测试时能查到，批量运行时查不到？

- 单独运行：测试执行完成后，连接自动关闭并提交事务，数据可见。

- 批量运行：多个测试共享同一个连接，事务未提交，数据对其他查询不可见

解决方法：`启用 autocommit=True**`

```# common/db/mysql_util.py

def get_connection(self):
        """获取数据库连接 - 启用自动提交"""
        if self._connection is None or not self._connection.open:
            self._connection = pymysql.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 3306),
                user=self.db_config.get('user', 'root'),
                password=self.db_config.get('password', ''),
                database=self.db_config.get('database', ''),
                charset='utf8mb4',
                autocommit=True,  # ✅ 启用自动提交(修改这里，将原来的False 改为 True)
                connect_timeout=10
            )
        return self._connectio

```

2. testcase\admin\test_brand.py:53: in test_create_brand
    brand_id = IDFetcherWithAllure.get_id_by_module(
common\utils\id_fetcher.py:527: in get_id_by_module
    result = super().get_id_by_module(api_instance, module, search_value, **kwargs)
E   TypeError: super(type, obj): obj must be an instance or subtype of type ？

原因分析：
这个错误是因为 IDFetcherWithAllure 继承 IDFetcher 后，
调用 super().get_id_by_module() 时参数传递方式有问题。在静态方法中使用 super() 需要特别注意。

静态方法不能使用 super() 调用。

解决方法：
```原来：# common/utils/id_fetcher.py
class IDFetcherWithAllure(IDFetcher):
    ...
     result = super().get_id_by_name(
            api_instance, list_method, name,
            name_field, id_field, keywork_field,
            page_size, max_retries, retry_delay, extra_match
        )
    ...
```
修改后：
```# common/utils/id_fetcher.py
class IDFetcherWithAllure:
    # 带Allure报告的ID获取器 - 组合方式而非继承
    
    # 使用组合方式，委托给IDFetcher
    _fetcher = IDFetcher()
    
    ...
     result = IDFetcher.get_id_by_name(
            api_instance, list_method, name,
            name_field, id_field, keywork_field,
            page_size, max_retries, retry_delay, extra_match
        )
    ...   
```
然后也检查 API 封装的实际参数
```
# 在测试中临时添加调试代码
def test_debug_brand_api(self, brand_api):
    import inspect
    print("brand_api.list 参数:", inspect.signature(brand_api.list))
    print("brand_api.list 文档:", brand_api.list.__doc__)
```

然后也修改修改id_fetcher.py中的ModuleFieldConfig和IdFetcher中的参数适配问题

二者结合


3.testcase\admin\test_category.py:59: in test_create_category
    assert category_id, f"未找到创建的分类：{category_name}"
E   AssertionError: 未找到创建的分类：测试分类_ejcU
E   assert None

问题分析：

问题在于分类接口的列表查询方式特殊——它需要 parentId 参数，而且分类可能有层级结构。

且`response = category_api.list(parent_id=parent_id, page_num=1, page_size=100)`表示数据只对比了前100个，后面的数据没有对比，
但又新建的数据都在后面，所以就没有对比到，所以结果显示没有找到

解决方法：修复 id_fetcher.py 中分类的ID获取方法， 以及其他需要遍历的接口， 遍历所有分页来查找目标数据


3. 获取id可以直接从数据库中获取，避免分页遍历的问题，为什么还要重新请求一遍然后再根据返回的数据去获取id呢（id_fetcher.py）
或者说双重验证

添加mysql获取id的方法，同时修复id_fetcher.py中获取id的方式，然后具体使用的方法也修改


获取id的方式：
- 直接从数据库中获取
- 写fixture去获取, 但是在fixture中方法中，也是要用到数据库或者从请求返回的结果中去获取，所以还是直接用写sql去数据库中获取吧，看情况结合使用
- 写id_fetcher.py去获取



4. 请求参数的值有为0的可能，在判断的时候不建议`if xxx`, 而是用`if xxx is not None`，
在请求订单状态为0的时候用`if status`就会跳过设置这个参数，返回的也就是默认全部的值

5. 角色、用户、资源分不清 ？



心得：
1.要么传入参数有问题（传入错误的值，参数的名称错误，在json=data中data没有传入需要的参数, 传入了不需要的参数）， 要么参数的名称设置错误，要么请求的连接错误
2.修改代码逻辑，发现盲点，重新写代码，优化代码
3.deepseek把新的改了，把旧的错误也改了进去
4.重试配置：对于500错误不应该重试，因为重试也无法解决
5.测试策略：如果接口确实有问题，使用pytest.skip()跳过该测试，避免阻塞其他测试
6.就有一种感觉，虽然代码的数量看起来很多，但有一大部分是重复的东西，断言覆盖率也不高
用、 with，finally 或许
7.回溯或许要花费些时间




## 第八版

bug：
1. 标题：商品创建接口返回异常，但商品数据已成功入库 ，
    严重级别：P1
    原因：导致用户认为创建失败，重复提交，产生重复数据
    描述：在创建商品点击提交后，返回400，界面重新刷新到填写商品信息的界面，但是创建的数据又会显示在界面上，
也就是：后端创建商品已经成功，但前端在后续请求/响应处理阶段又发生了400，导致前端认为创建失败并刷新/返回表单。

这是为什么？哪个服务没开启吗

可能：商品创建成功，pms_product插入成功（商品主表插入成功），但是pms_sku_stock  或 pms_product_attribute_value失败（SKU失败），
事务没有完全回滚，这属于`数据一致性缺陷`，（高价值bug）

分析过程：
先F12：

勾选：
✓ Preserve log（保留日志）
✓ Disable cache（禁用缓存）

或用Charles 或 Fiddler抓包：


好像也不是bug，在代码中请求的参数把data=改为json=就行，在前端请示也突然可以正常运行和显示了 ？ 偶发性的错误吗 （还是请求参数类型错误？）


2. 数据的比较判断：
类型判断，可能一个是float，另一个是str或Decimal  
-> 修复 DBAssertion - 添加数值比较支持，修复 ApiAssertion - 添加字段值比较， 修复 BaseAssertion - 增强比较方法
-> 更新 test_product.py - 使用增强的断言

-> 或者在断言传入参数的时候修改数据的类型和数据库中的一致(但是这样测试用例就显得很复杂，没那么简练)
->要么在断言函数中再进行修改（这样在后台操作会好一些）

心得：
1. 请求返回400也不一定代表错误，数据库中金额能也会有数据，请求的数据也会显示在界面上，就是请求的过程不是预期的那样

问题：
1.在assertion中，把actual和expected弄反了吧？或许也没反，从数据库中取出来的才是actual的，创建的数据才是expected的

2. 数据库中有新创建的商品数据，但是后台管理界面没有显示 ？


断点：
1.testcases/admin中的test_product.py中的simpleList的查询有点问题，和数据库对不上，不知道是什么原因，用postman也查询不出







