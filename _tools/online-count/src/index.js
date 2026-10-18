// み旨の裏庭のホームに「いま○人が利用しています」を出すための Cloudflare Worker。
// Google アナリティクス（プロパティ 520812725）のリアルタイムの人数を、1分ごとに聞き直して返す。
// 鍵（サービスアカウント online-count の JSON）は Cloudflare の secret GA_KEY にある。リポジトリには置かない。

const PROPERTY = '520812725';
const MINUTES = 5;           // 直近何分に開いていた人を数えるか
const TTL = 60 * 1000;       // アナリティクスに聞き直す間隔

let token = null;            // { value, exp }
let cached = null;           // { value, at }
let pending = null;          // 聞いている最中のもの（同時に来ても1回で済ませる）

function b64url(bytes) {
  let s = '';
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function accessToken(key) {
  if (token && Date.now() < token.exp) return token.value;
  const now = Math.floor(Date.now() / 1000);
  const enc = (o) => b64url(new TextEncoder().encode(JSON.stringify(o)));
  const body = enc({ alg: 'RS256', typ: 'JWT' }) + '.' + enc({
    iss: key.client_email,
    scope: 'https://www.googleapis.com/auth/analytics.readonly',
    aud: 'https://oauth2.googleapis.com/token',
    iat: now,
    exp: now + 3600,
  });
  const der = Uint8Array.from(atob(key.private_key.replace(/-----[^-]+-----|\s/g, '')), (c) => c.charCodeAt(0));
  const signer = await crypto.subtle.importKey('pkcs8', der, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', signer, new TextEncoder().encode(body));
  const r = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion: body + '.' + b64url(new Uint8Array(sig)),
    }),
  });
  if (!r.ok) throw new Error(`token ${r.status}: ${await r.text()}`);
  const j = await r.json();
  token = { value: j.access_token, exp: Date.now() + (j.expires_in - 300) * 1000 };
  return token.value;
}

export async function activeUsers(key) {
  const r = await fetch(`https://analyticsdata.googleapis.com/v1beta/properties/${PROPERTY}:runRealtimeReport`, {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + (await accessToken(key)), 'Content-Type': 'application/json' },
    body: JSON.stringify({
      metrics: [{ name: 'activeUsers' }],
      minuteRanges: [{ startMinutesAgo: MINUTES - 1, endMinutesAgo: 0 }],
    }),
  });
  if (!r.ok) throw new Error(`realtime ${r.status}: ${await r.text()}`);
  const j = await r.json();
  // 誰もいないときは rows が無い
  return Number(j.rows?.[0]?.metricValues?.[0]?.value ?? 0);
}

export default {
  async fetch(req, env) {
    const headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
    };
    try {
      if (!cached || Date.now() - cached.at > TTL) {
        pending ??= activeUsers(JSON.parse(env.GA_KEY)).finally(() => { pending = null; });
        cached = { value: await pending, at: Date.now() };
      }
      return new Response(JSON.stringify({ active: cached.value, minutes: MINUTES }), {
        headers: { ...headers, 'Cache-Control': 'public, max-age=60' },
      });
    } catch (e) {
      console.error(e.message);
      return new Response(JSON.stringify({ active: null }), { status: 503, headers: { ...headers, 'Cache-Control': 'no-store' } });
    }
  },
};
