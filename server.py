import hashlib
import hmac
import json
import math
import os
import secrets
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path

import requests
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import BadSignature, URLSafeTimedSerializer

ROOT = Path(__file__).resolve().parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'resume_expert.db'}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app = Flask(__name__, static_folder=None)
app.config.update(
    SQLALCHEMY_DATABASE_URI=DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.getenv("SECRET_KEY", "local-dev-secret-change-before-deploy"),
)
db = SQLAlchemy(app)
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
CODES = {}


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(64), nullable=False)
    credits = db.Column(db.Integer, default=0, nullable=False)
    free_uses = db.Column(db.Integer, default=1, nullable=False)
    is_admin = db.Column(db.Integer, default=0, nullable=False)
    phone = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.String(32))
    last_login = db.Column(db.String(32))
    total_analyses = db.Column(db.Integer, default=0, nullable=False)


class ResumeHistory(db.Model):
    __tablename__ = "resume_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    target_position = db.Column(db.String(120))
    match_score = db.Column(db.Integer)
    resume_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.String(32), nullable=False)


class UsageLog(db.Model):
    __tablename__ = "usage_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    credits_charged = db.Column(db.Integer, default=0)
    model = db.Column(db.String(80))
    created_at = db.Column(db.String(32), nullable=False)


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), 180000
    ).hex()


def public_user(user):
    return {
        "username": user.username,
        "phone": user.phone,
        "credits": user.credits,
        "freeUses": user.free_uses,
        "isAdmin": bool(user.is_admin),
    }


def issue_token(user):
    return serializer.dumps({"user_id": user.id})


def current_user():
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not token:
        token = request.args.get("token", "")
    try:
        data = serializer.loads(token, max_age=60 * 60 * 24 * 30)
    except BadSignature:
        return None
    return db.session.get(User, data.get("user_id"))


def require_user(admin=False):
    user = current_user()
    if not user:
        return None, (jsonify(error="请先登录"), 401)
    if admin and not user.is_admin:
        return None, (jsonify(error="仅管理员可访问"), 403)
    return user, None


def mock_result(data):
    position = data.get("position") or "AI 产品经理"
    return {
        "jd": {
            "responsibilities": ["负责 AI 产品规划与落地", "协同算法和工程团队交付", "开展客户调研与竞品分析"],
            "must": ["3 年以上产品经验", "具备 SQL 与数据分析能力", "理解大模型能力边界"],
            "hidden": ["将技术能力转化为客户价值", "推进 ToB 复杂项目", "通过指标验证产品效果"],
            "keywords": ["LLM", "AI 产品", "ToB SaaS", "SQL", "需求分析", "跨团队协作"],
            "persona": "具备产品基本功、技术理解力和商业落地意识的复合型产品经理。",
        },
        "diagnosis": {
            "score": 72,
            "dimensions": [{"name": "岗位关键词", "score": 68}, {"name": "经历相关性", "score": 76}, {"name": "成果量化", "score": 74}, {"name": "AI 能力证明", "score": 55}],
            "issues": ["AI 产品实战证据不足", "部分经历缺少结果指标", "已有经历与 AI 岗位映射不足"],
            "suggestions": ["补充 LLM/RAG 项目", "用场景、动作、结果重写经历", "突出数据产品与 ToB 经验"],
        },
        "matching": [
            {"requirement": "AI 产品规划", "evidence": "具备 ERP 与数据产品规划经验", "strength": "中", "supplement": True, "advice": "补充 AI 原型验证"},
            {"requirement": "数据分析", "evidence": "从 0 到 1 搭建经营报表", "strength": "强", "supplement": False, "advice": "补充指标影响"},
            {"requirement": "跨团队协作", "evidence": "主导系统集成", "strength": "强", "supplement": False, "advice": "说明协作范围"},
        ],
        "probes": ["项目服务了多少用户？", "涉及哪些协作团队？", "效率提升的统计口径是什么？", "做过哪些 AI 原型？", "权限重构后效果如何？", "如何使用 SQL 决策？"],
        "optimizations": [
            {"before": "负责 ERP 系统规划与迭代", "after": "负责企业 ERP 核心流程规划，基于业务反馈排序需求并推动研发交付。", "reason": "补充场景与动作", "risk": "确认负责范围"},
            {"before": "搭建经营报表平台", "after": "从 0 到 1 规划经营报表平台，统一指标口径并支持业务决策。", "reason": "体现业务价值", "risk": "补充用户数"},
        ],
        "finalResume": f"张三｜{position}\n\n求职意向\n{position}｜人工智能 / ToB SaaS\n\n职业摘要\n3 年 ToB 产品经验，具备企业流程和数据产品实践，擅长需求分析、方案设计与跨团队落地。\n\n核心能力\n产品规划｜需求分析｜数据产品｜SQL｜ToB SaaS｜LLM 应用\n\n工作经历\n某科技公司｜产品经理｜2021.06-至今\n• 负责企业 ERP 核心流程规划与迭代。\n• 主导审批链路集成，使平均审批时长降低 50%。\n• 从 0 到 1 规划经营数据报表平台。\n\n技能工具\nSQL、Excel、Axure、Figma、LLM、RAG\n\n教育背景\n某大学｜本科",
        "interview": {
            "intro": "我有 3 年 ToB 产品经验，擅长把复杂流程拆解成可落地方案，并用数据验证效果。",
            "questions": ["为什么转向 AI 产品？", "如何理解大模型边界？", "介绍一个从 0 到 1 的项目。", "效率提升如何计算？", "如何设计 RAG 指标？", "如何处理 ToB 定制需求？", "如何判断需求优先级？", "数据产品带来什么价值？", "如何协作算法团队？", "入职 90 天如何开展工作？"],
            "evidence": ["效率改造前后数据", "产品用户与使用频率", "需求文档和原型", "AI 原型评测记录"],
            "risks": ["不要把学习经历写成商业化经验", "指标需说明口径", "明确个人贡献"],
            "data": ["产品覆盖用户数", "活跃率", "配置耗时变化", "需求交付率"],
        },
    }


def deepseek_result(data):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("服务端尚未配置 DEEPSEEK_API_KEY")
    schema = mock_result(data)
    prompt = (
        "你是严谨的中文招聘顾问。根据目标岗位信息、JD、原始简历和补充信息，输出定制化简历分析。"
        "所有结论必须基于用户材料，不得编造数字；信息不足时明确提示补充。"
        "只返回合法 JSON，不要 Markdown。JSON 字段和层级必须与下面示例完全一致，数组数量可调整：\n"
        + json.dumps(schema, ensure_ascii=False)
        + "\n用户材料：\n"
        + json.dumps(data, ensure_ascii=False)
    )
    response = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.25,
        },
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    result = json.loads(payload["choices"][0]["message"]["content"])
    return result, payload.get("usage", {})


def calculate_credits(usage):
    input_rate = float(os.getenv("DEEPSEEK_INPUT_USD_PER_M", "0.28"))
    output_rate = float(os.getenv("DEEPSEEK_OUTPUT_USD_PER_M", "0.42"))
    usd_cny = float(os.getenv("USD_CNY_RATE", "7.2"))
    markup = float(os.getenv("PRICE_MARKUP", "1.4"))
    cost_usd = usage.get("prompt_tokens", 0) / 1_000_000 * input_rate
    cost_usd += usage.get("completion_tokens", 0) / 1_000_000 * output_rate
    return max(1, math.ceil(cost_usd * usd_cny * markup * 100))


@app.get("/")
def home():
    return send_from_directory(ROOT, "index.html")


@app.get("/api/health")
def health():
    return jsonify(ok=True, aiMode=os.getenv("AI_MODE", "mock"), database="postgres" if DATABASE_URL.startswith("postgresql") else "sqlite")


@app.post("/api/send-code")
def send_code():
    phone = str(request.json.get("phone", "")).strip()
    if not phone.isdigit() or len(phone) != 11:
        return jsonify(error="请输入 11 位手机号"), 400
    code = f"{secrets.randbelow(1_000_000):06d}"
    CODES[phone] = {"code": code, "expires": time.time() + 300}
    return jsonify(message="验证码已发送", devCode=code)


@app.post("/api/register")
def register():
    data = request.json or {}
    username, password = str(data.get("username", "")).strip(), str(data.get("password", ""))
    phone, code = str(data.get("phone", "")).strip(), str(data.get("code", "")).strip()
    saved = CODES.get(phone)
    if len(username) < 2 or len(password) < 6:
        return jsonify(error="用户名至少 2 位，密码至少 6 位"), 400
    if not saved or saved["expires"] < time.time() or not hmac.compare_digest(saved["code"], code):
        return jsonify(error="验证码错误或已过期"), 400
    if User.query.filter((User.username == username) | (User.phone == phone)).first():
        return jsonify(error="用户名或手机号已注册"), 409
    salt = secrets.token_hex(16)
    user = User(username=username, password=password_hash(password, salt), salt=salt, phone=phone, created_at=now_text(), is_admin=1 if User.query.count() == 0 else 0)
    db.session.add(user)
    db.session.commit()
    CODES.pop(phone, None)
    return jsonify(token=issue_token(user), user=public_user(user))


@app.post("/api/login")
def login():
    data = request.json or {}
    user = User.query.filter_by(username=str(data.get("username", "")).strip()).first()
    password = str(data.get("password", ""))
    if not user or not hmac.compare_digest(user.password, password_hash(password, user.salt)):
        return jsonify(error="用户名或密码错误"), 401
    user.last_login = now_text()
    db.session.commit()
    return jsonify(token=issue_token(user), user=public_user(user))


@app.get("/api/me")
def me():
    user, error = require_user()
    return error or jsonify(user=public_user(user))


@app.post("/api/topup")
def topup():
    user, error = require_user()
    if error:
        return error
    user.credits += max(0, min(int((request.json or {}).get("credits", 0)), 100000))
    db.session.commit()
    return jsonify(user=public_user(user))


@app.post("/api/analyze")
def analyze():
    user, error = require_user()
    if error:
        return error
    if not user.is_admin and user.free_uses <= 0 and user.credits < 100:
        return jsonify(error="积分不足，请先充值"), 402
    data = request.json or {}
    try:
        if os.getenv("AI_MODE", "mock") == "deepseek":
            result, usage = deepseek_result(data)
        else:
            result, usage = mock_result(data), {"prompt_tokens": 0, "completion_tokens": 0}
    except (requests.RequestException, RuntimeError, ValueError, KeyError) as exc:
        return jsonify(error=f"AI 分析失败：{exc}"), 502
    charge = calculate_credits(usage) if usage.get("total_tokens") else 0
    if not user.is_admin:
        if user.free_uses > 0:
            user.free_uses -= 1
            charge = 0
        else:
            user.credits = max(0, user.credits - charge)
    user.total_analyses += 1
    position = data.get("position") or "目标岗位"
    history = ResumeHistory(user_id=user.id, title=f"{position} 定制简历", target_position=position, match_score=result["diagnosis"]["score"], resume_text=result["finalResume"], created_at=now_text())
    log = UsageLog(user_id=user.id, prompt_tokens=usage.get("prompt_tokens", 0), completion_tokens=usage.get("completion_tokens", 0), credits_charged=charge, model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"), created_at=now_text())
    db.session.add_all([history, log])
    db.session.commit()
    return jsonify(result=result, user=public_user(user), usage={"creditsCharged": charge})


@app.get("/api/history")
def history():
    user, error = require_user()
    if error:
        return error
    rows = ResumeHistory.query.filter_by(user_id=user.id).order_by(ResumeHistory.id.desc()).all()
    return jsonify(items=[{"id": row.id, "title": row.title, "target_position": row.target_position, "match_score": row.match_score, "resume_text": row.resume_text, "created_at": row.created_at} for row in rows])


@app.get("/api/history/<int:history_id>/download")
def download_history(history_id):
    user, error = require_user()
    if error:
        return error
    row = ResumeHistory.query.filter_by(id=history_id, user_id=user.id).first()
    if not row:
        return jsonify(error="历史记录不存在"), 404
    output = BytesIO(row.resume_text.encode("utf-8"))
    return send_file(output, as_attachment=True, download_name=f"resume-{history_id}.txt", mimetype="text/plain")


@app.get("/api/admin/stats")
def admin_stats():
    user, error = require_user(admin=True)
    if error:
        return error
    users = User.query.order_by(User.id.desc()).limit(50).all()
    return jsonify(
        summary={"users": User.query.count(), "analyses": sum(item.total_analyses or 0 for item in users), "credits": sum(item.credits or 0 for item in users), "resumes": ResumeHistory.query.count()},
        users=[{"username": item.username, "phone": item.phone, "credits": item.credits, "free_uses": item.free_uses, "total_analyses": item.total_analyses, "created_at": item.created_at, "last_login": item.last_login, "is_admin": item.is_admin} for item in users],
    )


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5463")), debug=False)
