/* Matches lora_driver.c gateway AT+SENSOR forwarding format. */
(function(root){
const fields=[['temperature','Temperature','°C',2],['humidity','Humidity','%RH',2],['voltage','Capacitor voltage','mV',0],['co2','CO₂','ppm',0],['tvoc','TVOC','ppb',0],['lux','Illuminance','lux',0],['rssi','RSSI','dBm',0],['snr','SNR','dB',0]];
function parse(line,time=Date.now()){
 const match=line.trim().match(/^AT\+SENSOR=([a-f\d]{8}),(-?\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(-?\d+),(-?\d+)$/i);
 if(!match) return null;
 const nums=match.slice(2).map(Number);
 const limits=[[-32768,32767],[0,65535],[0,65535],[0,65535],[0,65535],[0,65535],[-32768,32767],[-128,127]];
 if(nums.some((n,i)=>!Number.isSafeInteger(n)||n<limits[i][0]||n>limits[i][1]))return null;
 const r={time,uid:match[1].toUpperCase(),raw:line.trim()};
 fields.forEach(([key],i)=>r[key]=nums[i]/(i<2?100:1));return r;
}
class Lines{constructor(onLine){this.buffer='';this.onLine=onLine}push(chunk){this.buffer+=chunk;const parts=this.buffer.split(/[\r\n]/);this.buffer=parts.pop();parts.filter(Boolean).forEach(this.onLine);if(this.buffer.length>8192){this.onLine(this.buffer);this.buffer=''}}flush(){if(this.buffer)this.onLine(this.buffer);this.buffer=''}}
// Min/max envelope limits draw calls while retaining narrow spikes.
function envelope(rows,key,buckets,t0,t1){
 if(rows.length<=buckets*2)return rows;
 const bins=new Map();
 for(const r of rows){const n=Math.min(buckets-1,Math.max(0,Math.floor((r.time-t0)/(t1-t0||1)*buckets)));let b=bins.get(n);if(!b){bins.set(n,{min:r,max:r});continue;}if(r[key]<b.min[key])b.min=r;if(r[key]>b.max[key])b.max=r;}
 const result=[rows[0]];
 for(const b of bins.values()){if(b.min.time<=b.max.time)result.push(b.min,b.max);else result.push(b.max,b.min);}
 result.push(rows[rows.length-1]);return result;
}
const api={fields,parse,Lines,envelope};if(typeof module!=='undefined')module.exports=api;else root.Protocol=api;
})(globalThis);
