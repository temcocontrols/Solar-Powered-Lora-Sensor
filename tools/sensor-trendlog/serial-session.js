(function(root){
class SerialSession {
 constructor({onData,onState,idleTimeoutMs=120000,onTraffic=()=>{},onDataError=()=>{},delay=ms=>new Promise(resolve=>setTimeout(resolve,ms)),setTimer=(fn,ms)=>setTimeout(fn,ms),clearTimer=id=>clearTimeout(id)}){
  Object.assign(this,{onData,onState,idleTimeoutMs,onTraffic,onDataError,delay,setTimer,clearTimer});
  this.active=false;this.reader=null;this.timer=null;
 }
 clearWatchdog(){if(this.timer!==null){this.clearTimer(this.timer);this.timer=null;}}
 async stop(){this.active=false;this.clearWatchdog();if(this.reader)await this.reader.cancel().catch(()=>{});}
 async run(port,options){
  this.active=true;
  try {
   while(this.active){
    let opened=false;
    try {
     await port.open(options);opened=true;
     if(!this.active)break;
     this.onState('connected');
     while(this.active&&port.readable){
      let ended=false,stalled=false;
      const reader=port.readable.getReader();this.reader=reader;
      const arm=()=>{
       this.clearWatchdog();
       if(this.idleTimeoutMs>0)this.timer=this.setTimer(()=>{
        this.timer=null;
        if(!this.active||this.reader!==reader)return;
        stalled=true;
        this.onState('retrying',new Error('No serial bytes received within the idle timeout. Reopening the port.'));
        // Cancel the pending read before releasing its lock or reopening.
        reader.cancel().catch(()=>{});
       },this.idleTimeoutMs);
      };
      try {
       arm();
       while(this.active){
        const {value,done}=await reader.read();
        if(done){ended=true;break;}
        if(value&&value.byteLength){
         arm();this.onTraffic(value.byteLength);
         // Application/parser errors must not stop the serial read loop.
         try{this.onData(value);}catch(error){this.onDataError(error);}
        }
       }
      }catch(error){if(this.active)this.onState('retrying',error);}
      finally {this.clearWatchdog();this.reader=null;reader.releaseLock();}
      if(this.active){
       this.onState('reset');
       if(ended||stalled)break;
       await this.delay(300);
       if(this.active&&port.readable)this.onState('connected');
      }
     }
    }catch(error){if(this.active)this.onState('retrying',error);}
    finally {if(opened)await port.close().catch(()=>{});}
    if(this.active){this.onState('reset');await this.delay(2000);}
   }
  }finally {this.clearWatchdog();this.active=false;this.onState('stopped');}
 }
}
if(typeof module!=='undefined')module.exports=SerialSession;else root.SerialSession=SerialSession;
})(globalThis);
