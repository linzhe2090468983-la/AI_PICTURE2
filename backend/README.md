# AI电商宣传图生成器 - 后端

## 📁 代码结构说明

### 目录结构
```
backend/
├── main.py                 # 主应用文件（替换原来的app.py）
├── config.py               # 配置管理
├── requirements.txt        # 依赖包列表
├── README.md              # 说明文档
├── __init__.py            # 包初始化
├── models/                # 数据模型层
│   ├── database.py        # MySQL数据库连接
│   ├── mysql_user_model.py    # 用户认证模型
│   ├── mysql_history_model.py # 历史记录模型
│   ├── task_manager.py    # 任务管理器
│   └── __init__.py
├── routes/                # 路由层
│   ├── auth_routes.py     # 认证相关路由
│   ├── image_routes.py    # 图片生成路由
│   ├── history_routes.py  # 历史记录路由
│   └── __init__.py
├── services/              # 服务层
│   ├── ai_service.py      # AI生成服务
│   ├── image_service.py   # 图片处理服务
│   └── __init__.py
├── utils/                 # 工具层
│   ├── ai_utils.py        # AI相关工具函数
│   ├── image_utils.py     # 图片处理工具函数
│   └── __init__.py
├── uploads/               # 上传文件目录
├── outputs/               # 输出文件目录
└── *.db                  # 数据库文件（如果使用SQLite）
```

### 🏗️ 架构分层

#### 1. **路由层** (`routes/`)
- **职责**：处理HTTP请求，路由分发，参数验证
- **文件说明**：
  - `auth_routes.py`：用户注册、登录、个人资料
  - `image_routes.py`：图片生成、上传、处理
  - `history_routes.py`：聊天历史、生成记录查询

#### 2. **服务层** (`services/`)
- **职责**：核心业务逻辑，外部API调用
- **文件说明**：
  - `ai_service.py`：通义万相AI生成服务
  - `image_service.py`：图片上传、处理、本地效果应用

#### 3. **工具层** (`utils/`)
- **职责**：通用工具函数，代码复用
- **文件说明**：
  - `ai_utils.py`：提示词生成、增强、上下文构建
  - `image_utils.py`：图片验证、效果应用、预处理

#### 4. **数据模型层** (`models/`)
- **职责**：数据库操作，数据持久化
- **文件说明**：
  - `database.py`：MySQL连接管理
  - `mysql_user_model.py`：用户认证相关数据库操作
  - `mysql_history_model.py`：历史记录数据库操作

#### 5. **配置层** (`config.py`)
- **职责**：环境变量、数据库配置、API密钥等

### 🚀 启动方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（创建.env文件）
# 参考 .env.example

# 3. 初始化数据库
python models/database.py  # 或运行初始化脚本

# 4. 启动服务
python main.py
```

### 📡 API端点

#### 认证相关 (`/auth`)
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `GET /auth/profile` - 获取用户信息

#### 图片生成 (`/image`)
- `POST /image/generate` - 上传图片生成宣传图
- `POST /image/generate-from-text` - 文字描述生成图片
- `POST /image/simple-test` - 简单图片效果测试

#### 历史记录 (`/history`)
- `GET /history/chat-history` - 获取会话列表
- `GET /history/chat-history/<session_id>` - 获取聊天历史
- `DELETE /history/chat-history/<session_id>` - 删除聊天历史
- `GET /history/generation-records` - 获取生成记录

#### 系统状态
- `GET /health` - 健康检查
- `GET /` - API信息

### 🔧 开发规范

#### 1. **代码注释**
- 每个函数都有详细的中文docstring
- 关键参数和返回值都有说明
- 复杂的业务逻辑有注释解释

#### 2. **错误处理**
- 统一的异常捕获和处理
- 详细的错误日志记录
- 用户友好的错误信息返回

#### 3. **数据库操作**
- 使用参数化查询防止SQL注入
- 统一的连接管理和释放
- 事务处理确保数据一致性

#### 4. **API设计**
- RESTful风格的URL设计
- 统一的响应格式
- 详细的API文档注释

### 🗄️ 数据库设计

#### users表
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### chat_history表
```sql
CREATE TABLE chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    message_type ENUM('user', 'system') NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### generation_records表
```sql
CREATE TABLE generation_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    image_url LONGTEXT NOT NULL,
    prompt TEXT,
    model VARCHAR(50),
    style VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 🔐 安全考虑

1. **密码安全**：使用SHA256哈希存储密码
2. **JWT认证**：使用JWT进行用户身份验证
3. **输入验证**：严格验证用户输入，防止注入攻击
4. **文件上传**：限制文件类型和大小，防止恶意上传

### 📈 扩展性

1. **模块化设计**：每个功能模块独立，便于扩展
2. **服务分离**：业务逻辑与路由分离，便于测试
3. **配置集中**：所有配置集中管理，便于部署
4. **数据库抽象**：使用统一的数据库接口，便于切换数据库类型

### 🐛 故障排除

#### 常见问题：
1. **数据库连接失败**：检查MySQL配置和网络连接
2. **依赖安装失败**：使用虚拟环境或更新pip
3. **端口占用**：检查5000端口是否被其他程序占用
4. **权限问题**：确保MySQL用户有适当的权限

#### 日志位置：
- 应用日志：控制台输出
- 数据库日志：`models/database.py`中的logger输出

### 📝 更新日志

#### v2.0.0 (2025-01-XX)
- 🏗️ 重构代码结构，实现模块化设计
- 💾 迁移到MySQL数据库
- 🔐 添加JWT用户认证系统
- 📊 添加用户历史记录管理
- 🤖 优化AI生成服务，支持多种尺寸
- 📱 改进API设计和错误处理
