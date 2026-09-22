const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');

const config=fs.readFileSync(path.join(root,'adsense-config.js'),'utf8');
const loader=fs.readFileSync(path.join(root,'adsense-ready.js'),'utf8');
const privacy=fs.readFileSync(path.join(root,'privacy/index.html'),'utf8');
const pages=['index.html','sports/index.html','scores/index.html','news/index.html','boxing/index.html','odds/index.html'];

assert.match(config,/enabled:false/,'AdSense must remain disabled until a real publisher ID is supplied');
assert.match(config,/publisherId:""/,'Do not commit a fake publisher ID');
assert.match(loader,/^\(\(\)=>\{/,'Loader should be self-contained');
assert.match(loader,/\^ca-pub-\\d\+\$/,'Loader must validate publisher IDs');
assert.match(loader,/pagead2\.googlesyndication\.com/,'Loader must use the official AdSense script host');
assert.match(privacy,/Google AdSense/i,'Privacy page must disclose AdSense usage');
assert.match(privacy,/consent management platform/i,'Privacy page must disclose consent handling');
assert.match(privacy,/imgglobal@imgofficial\.com/,'Privacy page must expose a contact');

for(const file of pages){
  const s=fs.readFileSync(path.join(root,file),'utf8');
  assert.match(s,/adsense-config\.js/,'Missing AdSense config on '+file);
  assert.match(s,/adsense-ready\.js/,'Missing AdSense loader on '+file);
  assert.match(s,/href="\/privacy\//,'Missing privacy link on '+file);
}

console.log('PASS: IMG is AdSense-ready and safely disabled pending a real publisher ID');
