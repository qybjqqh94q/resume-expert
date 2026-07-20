# resume-expert11 部署步骤

## 三个名称先记住

- GitHub 仓库：`resume-expert`
- Cloudflare Pages 项目：`resume-expert11`
- Cloudflare D1 数据库：`resume-expert-db`

## 1. 上传 GitHub 文件

打开仓库：

`https://github.com/你的用户名/resume-expert`

上传这些文件和文件夹：

```text
functions/
migrations/
wrangler.toml
CLOUDFLARE_DEPLOY.md
```

不要上传：

```text
resume_expert.db
__pycache__/
.env
任何真实 API Key
```

## 2. 创建 D1 数据库

1. 登录 Cloudflare。
2. 进入 **Workers & Pages**。
3. 点击 **D1 SQL Database**。
4. 点击 **Create database**。
5. 名称填写：`resume-expert-db`。
6. 创建后复制 **Database ID**。

打开项目里的 `wrangler.toml`，把：

```toml
database_id = "REPLACE_WITH_CLOUDFLARE_D1_DATABASE_ID"
```

替换成真实 Database ID，然后重新上传这个文件到 GitHub。

## 3. 创建数据库表

在 D1 数据库中打开 **Console / SQL Editor**。

打开项目文件：

`migrations/0001_initial.sql`

复制全部内容，粘贴到 SQL 编辑器并点击执行。

## 4. 创建 Cloudflare Pages

1. 进入 **Workers & Pages**。
2. 点击 **Create application**。
3. 选择 **Pages**。
4. 选择 **Connect to Git**。
5. 选择 GitHub 仓库：`resume-expert`。
6. 选择分支：`main`。
7. 项目名称填写：`resume-expert11`。

构建设置：

```text
Framework preset: None
Build command: 留空
Build output directory: .
Root directory: 留空
Production branch: main
```

点击 **Save and Deploy**。

## 5. 绑定 D1

进入：

**Pages 项目 resume-expert11 → Settings → Functions**

找到 **D1 database bindings**，添加：

```text
Variable name: DB
D1 database: resume-expert-db
```

保存后重新部署。

## 6. 添加环境变量

进入：

**Settings → Environment variables → Production**

添加普通变量：

```text
AI_MODE=deepseek
DEEPSEEK_MODEL=deepseek-chat
PRICE_MARKUP=1.4
```

添加 Secret：

```text
DEEPSEEK_API_KEY=你的 DeepSeek Key
SECRET_KEY=一串较长的随机字符串
```

不要把 Secret 上传到 GitHub，也不要发到聊天里。

## 7. 验证

部署完成后打开：

```text
https://你的项目.pages.dev/api/health
```

正常结果：

```json
{"ok":true,"aiMode":"deepseek","database":"d1"}
```

第一次注册成功的用户会自动成为管理员。验证码会在测试页面中显示。
