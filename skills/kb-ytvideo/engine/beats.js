// NODE_PATH=<work>/node_modules node beats.js dist/clip.html out/sheet.png t1 t2 ... -> contact sheet of stills at those times
// Works at any clip size (16:9, 9:16, 4:5). Transparent clips are shown on black, or on --bg=path.png (e.g. the footage frame).
const {chromium}=require('playwright');const path=require('path');const {execFileSync}=require('child_process');const fs=require('fs');const os=require('os');
(async()=>{let args=process.argv.slice(2);let bgImg=null;args=args.filter(a=>{if(a.startsWith('--bg=')){bgImg=a.slice(5);return false}return true});
 const [html,out,...ts]=args;
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.goto('file://'+path.resolve(html)+'?render');await p.evaluate(()=>document.fonts.ready);
 const info=await p.evaluate(()=>({W:document.getElementById('stage').offsetWidth,H:document.getElementById('stage').offsetHeight}));
 await p.setViewportSize({width:info.W,height:info.H});
 const bg=bgImg?'data:image/png;base64,'+fs.readFileSync(bgImg).toString('base64'):null;
 await p.evaluate(bg=>{if(document.documentElement.classList.contains('alpha')){const s=bg?`#000 url(${bg}) center/cover`:'#000';document.documentElement.style.background=s;document.body.style.background=s;}},bg);
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'beats'));
 for(let i=0;i<ts.length;i++){await p.evaluate(t=>seek(t),+ts[i]);await p.screenshot({path:`${dir}/${String(i).padStart(3,'0')}.png`});}
 await b.close();
 const vertical=info.H>info.W, cols=Math.min(vertical?6:4,ts.length),rows=Math.ceil(ts.length/cols), tw=vertical?360:640;
 execFileSync('ffmpeg',['-loglevel','error','-y','-i',`${dir}/%03d.png`,'-vf',`scale=${tw}:-1,tile=${cols}x${rows}:padding=4:color=white`,'-frames:v','1',out]);
 console.log('sheet',out,ts.length,'stills');if(errs.length) console.log('ERR',errs);})();
