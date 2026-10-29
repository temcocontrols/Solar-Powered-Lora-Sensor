const assert=require('node:assert/strict');
const SerialSession=require('./serial-session.js');
(async()=>{
 let timer=null,opens=0,closes=0,cancels=0,reads=0,traffic=0,appErrors=0;
 let unblock;
 const states=[];
 const reader={
  async read(){reads++;if(reads===1)return new Promise(resolve=>{unblock=resolve;queueMicrotask(()=>timer())});if(reads===2)return {value:new Uint8Array([65]),done:false};await session.stop();return {done:true}},
  async cancel(){cancels++;if(unblock){unblock({done:true});unblock=null}},releaseLock(){}
 };
 const port={readable:null,async open(){opens++;this.readable={getReader:()=>reader}},async close(){closes++;this.readable=null}};
 const session=new SerialSession({idleTimeoutMs:100,onData(){throw Error('parser failed')},onDataError(){appErrors++},onTraffic:n=>traffic+=n,onState:s=>states.push(s),delay:async()=>{},setTimer:fn=>{timer=fn;return 1},clearTimer:()=>{timer=null}});
 await session.run(port,{});
 assert.equal(opens,2);assert.equal(closes,2);assert.ok(cancels>=1);assert.equal(traffic,1);assert.equal(appErrors,1);assert.equal(reads,3);assert.equal(timer,null);assert.ok(states.includes('retrying'));
 console.log('PASS: silent pending read is cancelled and reopened; parser errors do not stop reading; manual stop clears watchdog');
 const {envelope}=require('./protocol.js');
 const data=Array.from({length:100000},(_,i)=>({time:i,value:i===55555?9999:Math.sin(i)}));
 const plotted=envelope(data,'value',800,0,99999);
 assert.ok(plotted.length<=1602);assert.ok(plotted.some(r=>r.value===9999));assert.equal(plotted[0],data[0]);assert.equal(plotted.at(-1),data.at(-1));
 console.log('PASS: 100,000-point chart is bounded to 1,602 points while preserving spike and endpoints');
})().catch(error=>{console.error(error);process.exitCode=1});
