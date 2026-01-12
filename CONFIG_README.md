# 数据库配置说明

## MySQL数据库设置

### 1. 安装MySQL
确保你已经安装了MySQL服务器（版本5.7+或8.0+）

### 2. 创建数据库
在MySQL中创建数据库：
```sql
CREATE DATABASE ai_picture_gen CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 创建用户（可选）
```sql
CREATE USER 'ai_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON ai_picture_gen.* TO 'ai_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. 配置环境变量
创建 `.env` 文件或设置环境变量：

```bash
# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ai_picture_gen

# JWT配置
JWT_SECRET_KEY=your-secret-key-for-jwt
JWT_EXPIRATION_HOURS=24

# AI API配置（如果需要）
TONGYI_API_KEY=sk-your-tongyi-api-key
```

### 5. 初始化数据库
运行初始化脚本：
```bash
cd backend
python init_database.py
```

### 6. 验证配置
启动应用前，确保数据库连接正常：
```bash
cd backend
python -c "from models.database import db_connection; print('连接成功' if db_connection.test_connection() else '连接失败')"
```

## 数据库表结构

脚本会自动创建以下表：

### users（用户表）
- id: 用户ID（主键）
- username: 用户名（唯一）
- email: 邮箱（唯一）
- password_hash: 密码哈希
- created_at: 创建时间
- updated_at: 更新时间

### chat_history（聊天历史表）
- id: 记录ID（主键）
- user_id: 用户ID（外键）
- session_id: 会话ID
- message_type: 消息类型（user/system）
- content: 消息内容
- timestamp: 时间戳

### generation_records（生成记录表）
- id: 记录ID（主键）
- user_id: 用户ID（外键）
- image_url: 图片URL
- prompt: 提示词
- model: 使用的模型
- style: 生成风格
- created_at: 创建时间

## 注意事项

1. 数据库字符集使用utf8mb4以支持中文
2. 所有表都有适当的索引以提高查询性能
3. 外键约束确保数据一致性
4. 密码使用SHA256哈希存储
