const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const repos=['Mind-Reframe','Mind-Reframe-v2','Lumina'];
(async()=>{
for(const repo of repos){
const api='https://huggingface.co/api/spaces/Anonymous-EmpathyAI/'+repo;
const meta=await (await fetch(api,{signal:AbortSignal.timeout(30000)})).json();
if(!meta.sha)throw new Error('Missing revision '+repo);
const tree=await (await fetch(api+'/tree/'+meta.sha+'?recursive=true&limit=1000',{signal:AbortSignal.timeout(30000)})).json();
const base=path.resolve('research','upstream',repo);fs.mkdirSync(base,{recursive:true});
const selected=tree.filter(f=>f.type==='file'&&!/(^|\/)(\.env(?:\..*)?|__pycache__|dist|logs|node_modules)(\/|$)/.test(f.path)&&!/dataset_feedback|\.pyc$/.test(f.path)&&/\.(py|tsx?|jsx?|css|json|md|txt|ya?ml|conf|html)$|(^|\/)(Dockerfile|LICENSE[^/]*|COPYING[^/]*|AGENTS\.md)$/.test(f.path));
const records=[];
for(let i=0;i<selected.length;i+=6){await Promise.all(selected.slice(i,i+6).map(async f=>{
const target=path.resolve(base,f.path);if(!target.startsWith(base+path.sep))throw new Error('Invalid path');
const url='https://huggingface.co/spaces/Anonymous-EmpathyAI/'+repo+'/resolve/'+meta.sha+'/'+f.path.split('/').map(encodeURIComponent).join('/');
const r=await fetch(url,{signal:AbortSignal.timeout(30000)});if(!r.ok)throw new Error(r.status+' '+f.path);
const data=Buffer.from(await r.arrayBuffer());fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,data);
records.push({path:f.path,sha256:crypto.createHash('sha256').update(data).digest('hex'),bytes:data.length});
}));}
fs.writeFileSync(path.join(base,'SOURCE_MANIFEST.json'),JSON.stringify({repo:'Anonymous-EmpathyAI/'+repo,revision:meta.sha,license:meta.cardData?.license??null,excluded:'Environment files, runtime logs, feedback data, compiled files and assets',files:records.sort((a,b)=>a.path.localeCompare(b.path))},null,2));
console.log(JSON.stringify({repo,revision:meta.sha,license:meta.cardData?.license??null,downloaded:records.length,paths:records.map(f=>f.path)}));
}
})().catch(e=>{console.error(e.message);process.exitCode=1});
