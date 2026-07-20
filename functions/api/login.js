import { json, readJson, hashPassword, issueToken, publicUser, nowText } from "../_shared.js";
export async function onRequestPost({ request, env }) {
  const data = await readJson(request), user = await env.DB.prepare("SELECT * FROM users WHERE username = ?").bind(String(data.username || "").trim()).first();
  if (!user) return json({ error: "用户名或密码错误" }, 401);
  const check = await hashPassword(String(data.password || ""), user.salt);
  if (check.hash !== user.password) return json({ error: "用户名或密码错误" }, 401);
  await env.DB.prepare("UPDATE users SET last_login = ? WHERE id = ?").bind(nowText(), user.id).run();
  return json({ token: await issueToken(user.id, env.SECRET_KEY), user: publicUser(user) });
}
