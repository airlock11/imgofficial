const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const base = path.resolve(__dirname, '..');
const app = fs.readFileSync(path.join(base, 'app.js'), 'utf8');
const home = fs.readFileSync(path.join(base, 'index.html'), 'utf8');

// Theme preferences must not prevent mobile page initialization.
for (const mode of ['normal', 'malformed', 'blocked']) {
  function context() {
    const button = {style:{},offsetWidth:44,offsetHeight:44,setAttribute(){},addEventListener(){}};
    const storage = {getItem(key){return key==='img-theme-position'?(mode==='malformed'?'broken-json':'{"x":20,"y":30}'):'dark'},setItem(){if(mode==='blocked')throw new Error('Storage disabled')}};
    return vm.createContext({
      document:{documentElement:{dataset:{}},createElement(){return button},body:{append(){}}},
      get localStorage(){if(mode==='blocked')throw new Error('Storage disabled');return storage},
      matchMedia:()=>({matches:true}),innerWidth:390,innerHeight:844,addEventListener(){}
    });
  }
  const appContext = context();
  vm.runInContext(app.slice(0, app.indexOf('const navIcons=')), appContext);
  vm.runInContext("writePreference('img-theme','light')", appContext);
  const homeContext = context();
  const scripts = [...home.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
  vm.runInContext(scripts[0], homeContext);
  vm.runInContext(scripts[1].slice(0,scripts[1].indexOf('const reduced='))+'})();', homeContext);
  vm.runInContext("writePreference('img-theme','light')", homeContext);
}

let shown = 0;
const host = {innerHTML:'',querySelector(){return null}};
const streamContext = vm.createContext({
  URL,location:{href:'https://www.imgofficial.com/scores/'},
  allGames:[],liveNowItems:[],esc:String,
  ensureLiveDialog:()=>({querySelector:()=>host,showModal(){shown++}}),
  window:{open(){throw new Error('Unexpected external navigation')}}
});
vm.runInContext(app.slice(app.indexOf('function liveStreamsForGame('),app.indexOf('async function hydrateLiveStreams(')),streamContext);
const specific = {watchUrl:'https://www.youtube.com/watch?v=abcdefghijk'};
for (const [state,stream,expected] of [
  ['live',specific,1],['final',specific,0],['scheduled',specific,0],
  ['live',{watchUrl:'https://www.youtube.com/@OneSportsPHL/streams'},0],
  ['live',{watchUrl:'javascript:alert(1)'},0],
  ['live',{embedUrl:'https://www.youtube-nocookie.com/embed/abcdefghijk'},1],
  ['live',{watchUrl:'https://youtu.be/abcdefghijk'},1],
  ['live',{watchUrl:'https://youtube.com/watch?v=bad'},0]
]) {
  streamContext.game={state,streams:[stream]};
  assert.equal(vm.runInContext('liveStreamsForGame(game).length',streamContext),expected);
}
streamContext.allGames=[{eventId:'test',state:'live',streams:[]}];
streamContext.liveNowItems=[{eventId:'test',state:'live',streams:[specific]}];
vm.runInContext("openLiveStream('test')",streamContext);
assert.equal(shown,1,'A streamless league copy must not mask the Live Now stream');
assert.match(host.innerHTML,/youtube.com\/embed\/abcdefghijk/);
assert.doesNotMatch(host.innerHTML,/data-close-live|live-dialog-close/,'The redundant inline close button must not be rendered');
assert.doesNotMatch(host.innerHTML,/Watch on YouTube|<h2>|One Sports/,'The simplified player must not show redundant stream labels or external-link text');
assert.match(app,/class="live-close"/,'The main dialog close button must remain available');
assert.equal((app.match(/\(g\.streams\?\.length\?/g)||[]).length,0,'All live buttons must use the eligibility check');
console.log('PASS: mobile preferences, live stream eligibility, stream lookup, and simplified live dialog');
