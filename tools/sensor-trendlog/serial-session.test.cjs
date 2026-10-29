const assert=require('node:assert/strict');
const SerialSession=require('./serial-session.js');
(async()=>{
 let opens=0,closes=0,reads=0,releases=0,states=[],received=[];
 const reader={async read(){reads++;if(reads===1)throw Error('framing');if(reads===2){port.readable=null;throw Error('The device has been lost.')}await session.stop();return {value:new Uint8Array([65]),done:false}},releaseLock(){releases++},async cancel(){}};
 const port={readable:null,async open(){opens++;if(opens===2)throw Error('Device unavailable');this.readable={getReader:()=>reader}},async close(){closes++;this.readable=null}};
 const session=new SerialSession({onData:value=>received.push(...value),onState:state=>states.push(state),delay:async()=>{}});
 await session.run(port,{});
 assert.equal(opens,3);assert.equal(closes,2);assert.equal(releases,3);assert.deepEqual(received,[65]);assert.equal(session.active,false);assert.equal(states.at(-1),'stopped');assert.ok(states.includes('retrying'));
 // Stop while waiting for a missing device: no subsequent reopen.
 let attempts=0;let waiting;
 const stopped=new SerialSession({onData(){},onState(){},delay:async()=>{await stopped.stop()}});
 waiting=stopped.run({async open(){attempts++;throw Error('missing')}},{});await waiting;assert.equal(attempts,1);
 console.log('PASS: recoverable read errors, device loss, repeated open failure, reconnection, manual stop and lock cleanup');
})().catch(error=>{console.error(error);process.exitCode=1});
