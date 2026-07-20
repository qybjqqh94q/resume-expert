import { json, readJson } from "../_shared.js";
export async function onRequestPost({ request, env }) {
  const { phone = "" } = await readJson(request);
  if (!/^\d{11}$/.test(String(phone))) return json({ error: "请输入 11 位手机号" }, 400);
  const devCode = String(Math.floor(Math.random() * 1000000)).padStart(6, "0");
  await env.DB.prepare("INSERT INTO verification_codes (phone,code,expires_at) VALUES (?,?,?) ON CONFLICT(phone) DO UPDATE SET code=excluded.code, expires_at=excluded.expires_at").bind(String(phone), devCode, Date.now() + 300000).run();
  return json({ message: "验证码已生成", devCode });
}
