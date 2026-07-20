import { json, readJson, hashPassword, issueToken, publicUser, nowText } from "../_shared.js";
export async function onRequestPost({ request, env }) {
  try {
    if (!env.DB) throw new Error("D1 binding DB is missing");
    if (!env.SECRET_KEY) throw new Error("SECRET_KEY is missing");
    const data = await readJson(request), username = String(data.username || "").trim(), password = String(data.password || ""), phone = String(data.phone || "").trim();
    if (username.length < 2 || password.length < 6) return json({ error: "用户名至少 2 位，密码至少 6 位" }, 400);
    const verification = await env.DB.prepare("SELECT code,expires_at FROM verification_codes WHERE phone = ?").bind(phone).first();
    if (!/^\d{11}$/.test(phone) || !verification || verification.expires_at < Date.now() || verification.code !== String(data.code || "")) return json({ error: "验证码错误或已过期" }, 400);
    const exists = await env.DB.prepare("SELECT id FROM users WHERE username = ? OR phone = ?").bind(username, phone).first();
    if (exists) return json({ error: "用户名或手机号已注册" }, 409);
    const first = await env.DB.prepare("SELECT COUNT(*) AS count FROM users").first();
    const { salt, hash } = await hashPassword(password);
    await env.DB.prepare("INSERT INTO users (username,password,salt,credits,free_uses,is_admin,phone,created_at,total_analyses) VALUES (?,?,?,?,?,?,?,?,?)").bind(username, hash, salt, 0, 1, Number(first.count) === 0 ? 1 : 0, phone, nowText(), 0).run();
    const result = await env.DB.prepare("SELECT * FROM users WHERE username = ?").bind(username).first();
    if (!result) throw new Error("User was not created");
    await env.DB.prepare("DELETE FROM verification_codes WHERE phone = ?").bind(phone).run();
    return json({ token: await issueToken(result.id, env.SECRET_KEY), user: publicUser(result) });
  } catch (error) {
    console.error("register_failed", error?.stack || error?.message || String(error));
    return json({ error: "注册服务错误，请查看 Functions 实时日志" }, 500);
  }
}
