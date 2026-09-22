const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const pages=[
['index.html','https://www.imgofficial.com/'],
['sports/index.html','https://www.imgofficial.com/sports/'],
['scores/index.html','https://www.imgofficial.com/scores/'],
['news/index.html','https://www.imgofficial.com/news/'],
['boxing/index.html','https://www.imgofficial.com/boxing/'],
['odds/index.html','https://www.imgofficial.com/odds/']
];
for(const [file,url] of pages){
 const s=fs.readFileSync(path.join(root,file),'utf8');
 assert.match(s,/<title>[^<]{8,}<\/title>/);
 assert.match(s,/<meta name="description" content="[^"]{50,}">/);
 assert.ok(s.includes('rel="canonical" href="'+url+'"'));
 assert.match(s,/name="robots" content="index,follow/);
 assert.match(s,/property="og:title"/);
 assert.match(s,/application\/ld\+json/);
}
const robots=fs.readFileSync(path.join(root,'robots.txt'),'utf8');
assert.match(robots,/Sitemap:/i);
const sitemap=fs.readFileSync(path.join(root,'sitemap.xml'),'utf8');
for(const [,url] of pages) assert.ok(sitemap.includes('<loc>'+url+'</loc>'));
console.log('PASS: SEO metadata, canonicals, robots, structured data and sitemap');