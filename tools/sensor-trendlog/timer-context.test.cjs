const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync(require.resolve('./serial-session.js'),'utf8');
async function check(code){
 let arms=0,clears=0,reads=0,opens=0,bytes=0;
 const errors=[];
 // Browser APIs can reject a receiver that is not Window. Unlike previous
 // tests, exercise the DEFAULT timer wrappers, not injected session timers.
 const context={module:{exports:{}},setTimeout:function(){if(this?.constructor?.name==='SerialSession')throw TypeError('Illegal invocation');arms++;return arms},clearTimeout:function(){if(this?.constructor?.name==='SerialSession')throw TypeError('Illegal invocation');clears++}};
 vm.runInNewContext(code,context);
 let session;
 const reader={async read(){reads++;if(reads===1)return {value:new Uint8Array([65,66]),done:false};await session.stop();return {done:true}},async cancel(){},releaseLock(){}};
 const port={readable:null,async open(){opens++;this.readable={getReader:()=>reader}},async close(){this.readable=null}};
 session=new context.module.exports({onData:b=>bytes+=b.length,onState:(state,error)=>{if(error)errors.push(error.message)},delay:async()=>session.stop()});
 await session.run(port,{});
 return {arms,clears,reads,opens,bytes,errors};
}
(async()=>{
 const broken=source.replace('setTimer=(fn,ms)=>setTimeout(fn,ms),clearTimer=id=>clearTimeout(id)','setTimer=setTimeout,clearTimer=clearTimeout');
 const before=await check(broken);assert.equal(before.bytes,0);assert.ok(before.errors.includes('Illegal invocation'));
 const after=await check(source);assert.equal(after.bytes,2);assert.equal(after.opens,1);assert.equal(after.reads,2);assert.ok(after.arms>=2);assert.ok(after.clears>=2);assert.deepEqual(after.errors,[]);
 console.log('PASS: reproduced zero-byte timer receiver regression; fixed default timers receive data without reconnecting');
})().catch(error=>{console.error(error);process.exitCode=1});
