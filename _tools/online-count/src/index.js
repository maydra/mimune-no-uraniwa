// み旨の裏庭のホームに「いま○人が利用しています」と「あなたは○人目の訪問者です」を出すための Cloudflare Worker。
// Google アナリティクス（プロパティ 520812725）に、いまの人数（サイト全体）は1分ごと、
// ホームを開いた人の累計は10分ごとに聞き直して返す。
// 鍵（サービスアカウント online-count の JSON）は Cloudflare の secret GA_KEY にある。リポジトリには置かない。

const PROPERTY = '520812725';
const MINUTES = 5;           // 直近何分に開いていた人を数えるか
const TTL = 60 * 1000;       // いまの人数を聞き直す間隔
// 累計はアナリティクスのタグをサイトに入れた日（2026-01-20、コミット 0342de9c5）から数える。
// 1回の問い合わせが重いので、聞き直すのは10分ごと（どうせアナリティクス側の集計も数十分遅れる）
const SINCE = '2026-01-20';
const TOTAL_TTL = 10 * 60 * 1000;
// ホームの URL。GitHub Pages は同じホームを3通りの形で出す（2026-11-01 の時点で / が約半分、/index、/index.html の順）
const HOME = String.raw`/mimune-no-uraniwa/?(index(\.html)?)?`;

let token = null;            // { value, exp }

// 数を1つ覚えておく入れ物。ttl ごとに聞き直し、同時に来ても1回で済ませる。
// 聞き直しに失敗したら、取れてから stale ミリ秒までの古い数を返す（無ければ null）
function memo(ttl, stale, ask) {
  let cached = null;         // { value, at }
  let pending = null;        // 聞いている最中のもの
  return async (key) => {
    if (cached && Date.now() - cached.at <= ttl) return cached.value;
    try {
      pending ??= ask(key).finally(() => { pending = null; });
      cached = { value: await pending, at: Date.now() };
      return cached.value;
    } catch (e) {
      console.error(e.message);
      return cached && Date.now() - cached.at <= stale ? cached.value : null;
    }
  };
}

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

async function report(key, kind, body) {
  const r = await fetch(`https://analyticsdata.googleapis.com/v1beta/properties/${PROPERTY}:${kind}`, {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + (await accessToken(key)), 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${kind} ${r.status}: ${await r.text()}`);
  const j = await r.json();
  // 誰もいないときは rows が無い
  return Number(j.rows?.[0]?.metricValues?.[0]?.value ?? 0);
}

// 直近 MINUTES 分に開いていた人
export function activeUsers(key) {
  return report(key, 'runRealtimeReport', {
    metrics: [{ name: 'activeUsers' }],
    minuteRanges: [{ startMinutesAgo: MINUTES - 1, endMinutesAgo: 0 }],
  });
}

// SINCE から今日までにホームを開いた人（同じ端末・ブラウザは1人。本のページだけ読みに来た人は入らない）
export function totalUsers(key) {
  return report(key, 'runReport', {
    dateRanges: [{ startDate: SINCE, endDate: 'today' }],
    metrics: [{ name: 'totalUsers' }],
    dimensionFilter: { filter: { fieldName: 'pagePath', stringFilter: { matchType: 'FULL_REGEXP', value: HOME } } },
  });
}

// いまの人数は古いと嘘になるので5分まで。累計は古くても小さく出るだけなので、いくら古くても出す
const active = memo(TTL, 5 * 60 * 1000, activeUsers);
const total = memo(TOTAL_TTL, Infinity, totalUsers);

export default {
  async fetch(req, env) {
    const headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
    };
    let key = null;
    try { key = JSON.parse(env.GA_KEY); } catch (e) { console.error('GA_KEY: ' + e.message); }
    const [a, t] = key ? await Promise.all([active(key), total(key)]) : [null, null];
    // 片方だけ取れたときは、取れたほうだけ返す（ホームは null の行を出さない）
    if (a === null && t === null) {
      return new Response(JSON.stringify({ active: null, total: null }), { status: 503, headers: { ...headers, 'Cache-Control': 'no-store' } });
    }
    return new Response(JSON.stringify({ active: a, minutes: MINUTES, total: t, since: SINCE }), {
      headers: { ...headers, 'Cache-Control': 'public, max-age=60' },
    });
  },
};
