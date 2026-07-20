# 简历专家：零代码部署工作流

最终架构是：GitHub 保存代码，Render 运行网站，Neon 保存用户数据，DeepSeek 提供真实 AI 分析。

## 一、服务说明

| 服务 | 用途 | 免费版限制 |
| --- | --- | --- |
| GitHub | 保存代码并触发部署 | 本项目够用 |
| Render | 运行网页和 Python 后端 | 闲置会休眠，首次打开可能等待约一分钟 |
| Neon | 云端 PostgreSQL 数据库 | 测试版够用 |
| DeepSeek | 真实 AI 分析 | API 按量收费，不属于免费服务 |

网站部署本身可以不花钱，但 DeepSeek API 只有在发生分析时才会消耗余额。

## 二、撤销泄露的 Key

1. 打开 DeepSeek API Keys 页面。
2. 删除曾经发到聊天里的 Key。
3. 新建一个 Key。
4. 新 Key 只在 Render 的 Environment 页面填写，不放进代码、GitHub 或聊天。

聊天或代码中的 Key 相当于公开密码，其他人拿到后可以消耗你的余额。

## 三、创建 GitHub 仓库

1. 注册并登录 GitHub。
2. 点击右上角 `+`，选择 `New repository`。
3. 仓库名填写 `resume-expert`，建议选择 `Private`。
4. 不勾选 README、.gitignore 或 License，点击 `Create repository`。
5. 进入新仓库页面，点击 `uploading an existing file`。
6. 打开本机文件夹 `resume-expert`，把项目文件拖到上传区域。
7. 不要上传 `resume_expert.db`、`__pycache__` 或任何 API Key。
8. 页面底部填写 `Initial deployment`，点击 `Commit changes`。

以后修改代码后，可以继续用 GitHub 网页的 `Add file` → `Upload files` 上传覆盖；Render 会自动重新部署。

## 四、创建 Neon 数据库

1. 注册并登录 Neon，点击 `New project`。
2. Project name 填写 `resume-expert`，区域选择离用户较近的地区。
3. 创建后在 Dashboard 点击 `Connect`。
4. 选择 `Connection string`，复制以 `postgresql://` 开头的完整地址。
5. 这个地址包含数据库密码，只填写到 Render 环境变量 `DATABASE_URL`。

数据库保存账号、积分、分析次数和历史简历，Render 重启不会清除这些数据。

## 五、在 Render 部署

1. 注册并登录 Render，建议使用 GitHub 授权。
2. 点击 `New +`，选择 `Blueprint`。
3. 选择 GitHub 中的 `resume-expert` 仓库。
4. Render 会读取项目里的 `render.yaml`。
5. 在环境变量输入页填写：
   - `DATABASE_URL`：粘贴 Neon Connection string。
   - `DEEPSEEK_API_KEY`：粘贴新生成的 DeepSeek Key。
6. 确认 `AI_MODE` 是 `deepseek`，点击部署。
7. 等待状态变成 `Live`，打开 Render 提供的 `https://resume-expert-xxxx.onrender.com` 地址。

Render 自动提供 HTTPS 临时域名，测试阶段不需要购买域名。

## 六、上线验收

1. 打开 Render 地址并注册第一个账号，第一个账号自动成为管理员。
2. 点击“使用示例数据”和“开始分析”。
3. 确认能看到九个流程页面。
4. 打开“历史简历”，确认记录可查看、可下载。
5. 管理员点击“用户数据”，确认用户数和分析次数变化。
6. 在 Render Logs 查看错误，在 DeepSeek 控制台查看 token 消耗。

## 七、环境变量解释

| 名称 | 作用 | 是否保密 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 调用 DeepSeek 的凭证 | 必须保密 |
| `DATABASE_URL` | 连接 Neon 数据库 | 必须保密 |
| `SECRET_KEY` | 签发登录令牌 | 必须保密，Render 自动生成 |
| `AI_MODE` | `mock` 使用本地结果，`deepseek` 使用真实 AI | 不保密 |
| `DEEPSEEK_MODEL` | 使用的模型，默认 `deepseek-chat` | 不保密 |
| `PRICE_MARKUP` | 用户成本加价倍率，当前为 1.4 | 不保密 |
| `DEEPSEEK_INPUT_USD_PER_M` | 每百万输入 token 单价 | 不保密，价格变化时更新 |
| `DEEPSEEK_OUTPUT_USD_PER_M` | 每百万输出 token 单价 | 不保密，价格变化时更新 |

DeepSeek 调整价格后，应同步修改两个价格变量。系统按实际 token、美元汇率和 1.4 倍倍率计算积分。

## 八、测试版边界

- 手机验证码是页面显示的模拟验证码，没有发送真实短信。
- 充值按钮只增加测试积分，没有真实支付。
- Render 免费服务会休眠，首次访问可能较慢。
- DeepSeek API 调用会产生真实费用，应在 DeepSeek 控制台设置余额提醒。
- 正式收费运营还需要短信服务、支付商户、隐私政策、用户协议和备案合规流程。

## 九、日常更新工作流

1. 在本地修改并测试。
2. 打开 GitHub 仓库，使用 `Add file` → `Upload files` 上传更新后的文件。
3. Render 自动构建并发布。
4. 打开 Render 地址验收。
5. 出现问题时先看 Render Logs，再检查 Neon 和 DeepSeek 控制台。

不要把 `.env`、数据库文件或 API Key 上传到 GitHub；项目中的 `.gitignore` 已经排除它们。
