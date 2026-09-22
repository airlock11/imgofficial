const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=path.resolve(__dirname,'..');

function read(name){return fs.readFileSync(path.join(base,name),'utf8')}
function routes(src){return [...src.matchAll(/url\.pathname\s*===\s*["']([^"']+)["']/g)].map(m=>m[1])}

const canonical=read('worker.js');
const cloudflare=read('worker-cloudflare.js');
const simple=read('worker-simple.js');

const required=[
  '/health','/wta-live','/scoreboard','/games','/events',
  '/boxing/meta','/boxing/rankings','/boxing/fighters','/boxing/fighter','/boxing/fights',
  '/regional-scores','/streams','/news'
];

const canonicalRoutes=routes(canonical);
const cloudflareRoutes=routes(cloudflare);

for(const route of required){
  assert.ok(canonicalRoutes.includes(route),'worker.js missing '+route);
  assert.ok(cloudflareRoutes.includes(route),'worker-cloudflare.js missing '+route);
}
assert.deepEqual(
  [...new Set(cloudflareRoutes)].sort(),
  [...new Set(canonicalRoutes)].sort(),
  'Canonical and Cloudflare workers must expose the same route contract'
);

for(const [name,src] of [['worker.js',canonical],['worker-cloudflare.js',cloudflare]]){
  assert.match(src,/request\.method !== "GET"/,name+' must reject unsupported methods');
  assert.match(src,/status\s*=\s*200/,name+' jsonResponse must support explicit status codes');
  assert.match(src,/Basketball API not configured/,name+' must handle missing BALLDONTLIE key');
  assert.match(src,/Basketball API unavailable/,name+' must handle upstream game failures');
  assert.match(src,/service:\s*"img-sports-api"/,name+' must expose health metadata');
  assert.doesNotMatch(src,/console\.log\([^\n]*(API_KEY|ACCESS_TOKEN|SECRET)/i,name+' must not log secret values');
}

// worker-simple.js is retained only as a minimal emergency fallback. It must not
// accidentally become the feature-complete deployment source.
assert.ok(routes(simple).includes('/scoreboard'),'worker-simple.js must retain emergency scoreboard fallback');
assert.ok(!routes(simple).includes('/news'),'worker-simple.js must remain clearly distinct from the canonical backend');

const sources=JSON.parse(read('live-stream-sources.json'));
assert.ok(Array.isArray(sources.sources)&&sources.sources.length>0,'live-stream-sources.json must contain sources');
const ids=new Set();
for(const source of sources.sources){
  assert.ok(source.id&&source.leagueKey,'Every live source needs id and leagueKey');
  assert.ok(source.channelId||source.handle||source.username,'Every live source needs a resolvable channel');
  assert.ok(!ids.has(source.id),'Duplicate live source id: '+source.id);
  ids.add(source.id);
}

console.log('PASS: backend route parity, health/error guards, secret hygiene, and live-source contract');
