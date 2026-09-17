# Mall 接口自动化测试项目

## 一、项目简介

本项目是针对 **macrozheng/mall 商城系统**的接口自动化测试框架,覆盖后台管理端(admin)与前台用户端(member)两大业务侧。

框架采用四层分层架构设计,职责清晰、易于维护与扩展:

```
TestCase  →  API  →  Client(BaseClient / AdminClient / MemberClient)  →  requests.Session
```

核心能力:

- 统一 HTTP 客户端封装,内置超时、重试、Session、Token 自动刷新
- 前后台双 Token 隔离管理,支持多用户切换与线程安全
- 接口响应 + MySQL + Redis 三重断言机制(含软断言)
- Allure 自动埋点记录请求/响应/SQL/耗时
- pytest-xdist 并发执行,支持 Jenkins CI 接入
- 多环境配置(dev / test),支持环境变量覆盖

## 二、技术栈
```
python + pytest + requests + mysql + redis + allure
```

## 三、目录说明

```
mall-test/
├── api/                      # 接口封装层(一个 API 类对应一个业务模块)
│   ├── admin/                # 后台接口:商品、品牌、分类、订单、优惠券、限时购、后台用户
│   └── member/               # 前台接口:首页、商品、购物车、订单、优惠券、地址、收藏、登录等
│
├── common/                   # 公共能力层
│   ├── client/               # HTTP 客户端 + Token 管理
│   │   ├── base_client.py    # 框架核心:统一请求入口、重试、Allure 记录、Token 刷新
│   │   ├── admin_client.py   # 后台客户端(管理员登录、Token)
│   │   ├── member_client.py  # 前台客户端(会员登录、Token)
│   │   ├── token_context.py  # 线程隔离的 Token 上下文
│   │   └── token_manager.py  # Token 缓存与失效刷新
│   │
│   ├── assertions/           # 断言体系
│   │   ├── base_assertion.py # 基础断言
│   │   ├── api_assertion.py  # 接口响应断言
│   │   ├── db_assertion.py   # 数据库断言
│   │   ├── redis_assertion.py# Redis 断言
│   │   └── soft_assertopn.py # 软断言(收集错误后统一抛出)
│   │
│   ├── config/               # 配置管理
│   │   ├── config.yml        # 多环境配置(dev/test)
│   │   └── config_loader.py  # YAML 配置加载器(支持环境变量覆盖)
│   │
│   ├── db/                   # 数据访问
│   │   ├── mysql_util.py     # MySQL 封装(query / execute)
│   │   └── redis_util.py     # Redis 封装(get / set / delete)
│   │
│   └── utils/                # 工具
│       ├── logger.py         # 日志
│       ├── data_generator.py # 测试数据生成(faker)
│       ├── id_fetcher.py     # 通用 ID 获取(API / DB 双取)
│       └── role_manager.py   # 角色权限管理
│
├── fixtures/                 # pytest fixture 层
│   ├── admin_fixtures.py     # 管理员登录、admin 客户端工厂
│   ├── member_fixtures.py    # 会员登录、购物车/订单等业务数据
│   ├── product_fixtures.py   # 商品/品牌/分类数据创建与清理
│   └── data_fixtures.py      # 数据生成器 fixture
│
├── testcase/                 # 测试用例层
│   ├── admin/                # 后台测试:登录、品牌、分类、商品、订单、权限
│   └── member/               # 前台测试:登录、商品、购物车、订单、优惠券、地址、场景流程
│
├── data/                     # 测试数据(角色配置、测试用户、业务数据)
│
├── conftest.py               # pytest 入口(注册 fixture、自定义 markers)
├── pytest.ini                # pytest 配置(测试路径、markers、默认参数)
├── run.py                    # 测试运行入口(支持全量/冒烟/模块/Allure 模式)
├── Jenkinsfile               # Jenkins CI 流水线
├── requirements.txt          # 依赖清单
└── main.py                   # PyCharm 默认入口脚本
```

## 四、How to Run

### 1. 环境准备

```bash
pip install -r requirements.txt

set TEST_ENV=dev
```

### 2. 运行测试

```bash
python run.py                 
python run.py smoke          
python run.py module test_product   
python run.py allure         

pytest                               
pytest -m smoke                      
pytest -m admin                       
pytest -m member                     
pytest testcase/member/test_scenario.py -v   
pytest testcase/admin/test_product.py::TestProduct::test_create_product -v  
pytest -n auto --dist loadscope     
```

### 3. 查看报告

```bash
start reports/test_report.html

allure serve reports/allure-results
```

### 4. 自定义 Markers

在 [pytest.ini](pytest.ini) 中已注册:`smoke`、`regression`、`admin`、`member`、`product`、`order`、`marketing`、`home`、`file`、`slow`、`skip`。

```bash
pytest -m "smoke and admin" 
pytest -m "not slow"        
```

### 5. CI/CD(Jenkins)

项目内置 [Jenkinsfile](Jenkinsfile),流水线阶段:Checkout → Health Check → API Test → Allure 报告。
