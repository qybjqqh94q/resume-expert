const enc = new TextEncoder();

export const json = (body, status = 200, headers = {}) => new Response(JSON.stringify(body), {
  status,
  headers: { "content-type": "application/json; charset=utf-8", ...headers },
});

export async function readJson(request) {
  try { return await request.json(); } catch { return {}; }
}

function b64(bytes) {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}
function unb64(s) {
  s = s.replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  const raw = atob(s); return Uint8Array.from(raw, c => c.charCodeAt(0));
}
function textB64(value) { return b64(enc.encode(value)); }
function b64Text(value) { return new TextDecoder().decode(unb64(value)); }

export async function hashPassword(password, salt = crypto.randomUUID()) {
  const key = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", salt: enc.encode(salt), iterations: 120000, hash: "SHA-256" }, key, 256);
  return { salt, hash: b64(new Uint8Array(bits)) };
}

export async function issueToken(userId, secret) {
  const payload = textB64(JSON.stringify({ userId, exp: Date.now() + 30 * 86400000 }));
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = b64(new Uint8Array(await crypto.subtle.sign("HMAC", key, enc.encode(payload))));
  return `${payload}.${sig}`;
}

export async function currentUser(request, env) {
  const token = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "") || new URL(request.url).searchParams.get("token");
  if (!token || !env.SECRET_KEY) return null;
  const [payload, sig] = token.split(".");
  if (!payload || !sig) return null;
  const key = await crypto.subtle.importKey("raw", enc.encode(env.SECRET_KEY), { name: "HMAC", hash: "SHA-256" }, false, ["verify"]);
  if (!await crypto.subtle.verify("HMAC", key, unb64(sig), enc.encode(payload))) return null;
  try {
    const data = JSON.parse(b64Text(payload));
    if (!data.exp || data.exp < Date.now()) return null;
    return await env.DB.prepare("SELECT * FROM users WHERE id = ?").bind(data.userId).first();
  } catch { return null; }
}

export function publicUser(user) {
  return { username: user.username, phone: user.phone, credits: user.credits, freeUses: user.free_uses, isAdmin: !!user.is_admin };
}
export function nowText() { return new Date().toISOString().replace("T", " ").slice(0, 19); }
export function requireUser(user, admin = false) { return !user ? json({ error: "请先登录" }, 401) : (admin && !user.is_admin ? json({ error: "仅管理员可访问" }, 403) : null); }
export function credits(usage, env) {
  const input = Number(env.DEEPSEEK_INPUT_USD_PER_M || .28), output = Number(env.DEEPSEEK_OUTPUT_USD_PER_M || .42);
  const usdCny = Number(env.USD_CNY_RATE || 7.2), markup = Number(env.PRICE_MARKUP || 1.4);
  const cost = ((usage.prompt_tokens || 0) / 1e6 * input + (usage.completion_tokens || 0) / 1e6 * output) * usdCny * markup;
  return Math.max(1, Math.ceil(cost * 100));
}
export function mockResult(data) {
  const position = data.position || "AI 产品经理";
  return { jd: { responsibilities: ["负责目标岗位规划与落地", "协同算法和工程团队交付"], must: ["具备产品和数据分析能力", "理解大模型应用边界"], hidden: ["能把技术转化为业务价值"], keywords: ["AI", "SQL", "ToB SaaS"], persona: "能以数据驱动产品决策的候选人" }, diagnosis: { score: 78, dimensions: [{ name: "岗位匹配", score: 80 }, { name: "成果表达", score: 76 }], issues: ["部分经历缺少量化结果"], suggestions: ["补充项目指标和业务影响"] }, matching: [], probes: ["介绍一个最有影响力的项目", "如何验证产品效果"], optimizations: [], finalResume: `目标岗位：${position}\n\n建议补充量化成果与业务影响。`, interview: { intro: "我有产品规划、数据分析和跨团队交付经验。", questions: ["为什么应聘该岗位？"], evidence: ["项目指标", "用户反馈"], risks: ["避免夸大成果"], data: ["覆盖用户数", "转化率"] } };
}
export async function analyzeWithAI(data, env) {
  if ((env.AI_MODE || "mock") !== "deepseek") return [mockResult(data), {}];
  if (!env.DEEPSEEK_API_KEY) throw new Error("服务端尚未配置 DEEPSEEK_API_KEY");
  const schema = mockResult(data);
  const prompt = `你是严谨的中文招聘顾问。根据岗位、JD、原始简历和补充信息，严格只返回 JSON，字段结构必须与示例一致，不要 Markdown。示例：${JSON.stringify(schema)}\n用户材料：${JSON.stringify(data)}`;
  const response = await fetch("https://api.deepseek.com/chat/completions", { method: "POST", headers: { Authorization: `Bearer ${env.DEEPSEEK_API_KEY}`, "Content-Type": "application/json" }, body: JSON.stringify({ model: env.DEEPSEEK_MODEL || "deepseek-chat", messages: [{ role: "user", content: prompt }], response_format: { type: "json_object" }, temperature: .25 } ) });
  if (!response.ok) throw new Error(`DeepSeek 请求失败 (${response.status})`);
  const payload = await response.json();
  return [JSON.parse(payload.choices?.[0]?.message?.content || "{}"), payload.usage || {}];
}
