'use strict';
const $=id=>document.getElementById(id),{fields,parse,Lines}=Protocol;
let records=[],selected='',port=null,running=false,db=null,logs=[],renderPending=false,saveFailed=false;
const nodes=new Map();
function indexRecords(batch){for(const r of batch){if(!nodes.has(r.uid))nodes.set(r.uid,[]);nodes.get(r.uid).push(r);}}
function rebuildIndex(){nodes.clear();indexRecords(records);}
let receivedBytes=0,lastByte=0,lastRecord=0,trafficPending=false;
function updateTraffic(){trafficPending=false;$('traffic').textContent=`Serial: ${receivedBytes.toLocaleString('en-US')} bytes · Last byte: ${lastByte?formatTime(lastByte):'—'} · Last valid record: ${lastRecord?formatTime(lastRecord):'—'}`;}
function scheduleTraffic(){if(!trafficPending){trafficPending=true;setTimeout(updateTraffic,500);}}
const formatTime=t=>new Date(t).toLocaleString('en-US',{hour12:false});
const notice=t=>$('notice').textContent=t;
const request=indexedDB.open('ra08-trendlog',1);
request.onupgradeneeded=()=>request.result.createObjectStore('records',{keyPath:'id',autoIncrement:true});
request.onerror=()=>{notice('Local database unavailable. Acquisition can continue; export CSV to save your data.');$('storage').textContent='Autosave unavailable';};
request.onsuccess=()=>{db=request.result;const read=db.transaction('records').objectStore('records').getAll();read.onsuccess=()=>{for(const r of read.result)records.push(r);records.sort((a,b)=>a.time-b.time);rebuildIndex();render();};read.onerror=()=>notice('Failed to load saved records.');};
function store(batch){if(!db){saveFailed=true;notice('Database not ready. Current records are in memory only; export a backup.');return}try{const tx=db.transaction('records','readwrite');batch.forEach(r=>{const {id,...copy}=r;tx.objectStore('records').add(copy)});tx.oncomplete=()=>{$('storage').textContent=saveFailed?'Some records were not saved. Export a backup.':'Autosaved to local IndexedDB'};tx.onerror=()=>{saveFailed=true;notice('Autosave failed (storage may be full). Export a backup now.')}}catch(e){saveFailed=true;notice('Save failed: '+e.message)}}
function schedule(){if(!renderPending){renderPending=true;setTimeout(()=>{renderPending=false;render()},1000)}}
function ingest(text){const batch=[];let invalid=0;for(const line of text.split(/[\r\n]+/)){if(!line.trim())continue;logs.push(line);const r=parse(line);if(r)batch.push(r);else if(line.includes('AT+SENSOR='))invalid++}logs=logs.slice(-80);schedule();if(batch.length){for(const r of batch)records.push(r);indexRecords(batch);lastRecord=Date.now();scheduleTraffic();store(batch);schedule()}if(invalid)notice(`Ignored ${invalid} malformed SENSOR messages.`);return batch.length}
function render(){$('raw').textContent=logs.join('\n');const ids=[...nodes.keys()];if(!ids.includes(selected))selected=ids[0]||'';$('count').textContent=ids.length;$('devices').replaceChildren();for(const uid of ids){const rs=nodes.get(uid),last=rs[rs.length-1],b=document.createElement('button');b.className='device'+(selected===uid?' active':'');b.textContent=uid;const sub=document.createElement('small');sub.textContent=`${rs.length} records · ${new Date(last.time).toLocaleTimeString('en-US',{hour12:false})}`;b.append(sub);b.onclick=()=>{selected=uid;render()};$('devices').append(b)}
 const rows=(nodes.get(selected)||[]),last=rows[rows.length-1];$('selected').textContent=selected||'Waiting for sensor data';$('total').textContent=`${records.length.toLocaleString("en-US")} total records`;$('cards').replaceChildren();for(const [key,label,unit,digits] of fields){const div=document.createElement('div');div.className='card';div.innerHTML=`<small>${label}</small><strong>${last?last[key].toFixed(digits):'—'}</strong><em>${unit}</em>`;$('cards').append(div)}
 $('thead').innerHTML='<tr><th>Received at</th>'+fields.map(([,label,unit])=>`<th>${label} (${unit})</th>`).join('')+'</tr>';$('rows').innerHTML=rows.slice(-100).reverse().map(r=>'<tr><td>'+formatTime(r.time)+'</td>'+fields.map(([key,,,digits])=>`<td>${r[key].toFixed(digits)}</td>`).join('')+'</tr>').join('');draw();}
fields.forEach(([key,label,unit])=>{const o=document.createElement('option');o.value=key;o.textContent=`${label} (${unit})`;$('metric').append(o)});
function draw(){const c=$('chart'),width=Math.max(320,c.clientWidth),height=330,dpr=devicePixelRatio||1;c.width=width*dpr;c.height=height*dpr;const ctx=c.getContext('2d');ctx.scale(dpr,dpr);ctx.fillStyle='#0e1b24';ctx.fillRect(0,0,width,height);const [key,label,unit,digits]=fields.find(f=>f[0]===$('metric').value);const range=Number($('range').value),cut=range?Date.now()-range:-Infinity;const rows=(nodes.get(selected)||[]).filter(r=>r.time>=cut);ctx.font='12px Segoe UI';ctx.fillStyle='#a1bfce';ctx.fillText(`${selected||'—'}  /  ${label} (${unit})`,18,25);if(!rows.length){ctx.fillText('No data in this range. Connect serial or load samples.',35,160);$('stats').textContent='';return}let lo=Infinity,hi=-Infinity,sum=0;rows.forEach(r=>{lo=Math.min(lo,r[key]);hi=Math.max(hi,r[key]);sum+=r[key]});const pad=(hi-lo)*.15||Math.max(Math.abs(hi)*.01,1),min=lo-pad,max=hi+pad;const left=70,right=width-24,top=48,bottom=280;let t0=rows[0].time,t1=rows[rows.length-1].time;if(t0===t1){t0-=1000;t1+=1000}const x=t=>left+(t-t0)/(t1-t0)*(right-left),y=v=>bottom-(v-min)/(max-min)*(bottom-top);for(let i=0;i<=4;i++){const v=min+(max-min)*i/4;ctx.strokeStyle='#243844';ctx.beginPath();ctx.moveTo(left,y(v));ctx.lineTo(right,y(v));ctx.stroke();ctx.fillStyle='#88a7b7';ctx.textAlign='right';ctx.fillText(v.toFixed(Math.min(2,digits+1)),left-9,y(v)+4)}ctx.textAlign='left';ctx.fillText(new Date(t0).toLocaleTimeString('en-US',{hour12:false}),left,305);ctx.textAlign='right';ctx.fillText(new Date(t1).toLocaleTimeString('en-US',{hour12:false}),right,305);ctx.textAlign='left';ctx.strokeStyle='#70e4bf';ctx.lineWidth=2;ctx.beginPath();const plot=Protocol.envelope(rows,key,Math.max(1,Math.floor(right-left)),t0,t1);plot.forEach((r,i)=>i?ctx.lineTo(x(r.time),y(r[key])):ctx.moveTo(x(r.time),y(r[key])));ctx.stroke();if(rows.length<150)for(const r of rows){ctx.beginPath();ctx.arc(x(r.time),y(r[key]),3,0,Math.PI*2);ctx.fillStyle='#70e4bf';ctx.fill()}$('stats').textContent=`${rows.length} points · Min ${lo.toFixed(digits)} · Max ${hi.toFixed(digits)} · Average ${(sum/rows.length).toFixed(digits)} ${unit} · ${formatTime(rows[0].time)} — ${formatTime(rows[rows.length-1].time)}`;}
$('metric').onchange=draw;$('range').onchange=draw;new ResizeObserver(draw).observe($('chart'));
function download(blob,name){const a=document.createElement('a'),url=URL.createObjectURL(blob);a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
const stamp=()=>new Date().toISOString().replace(/[:.]/g,'-');
$('export').onclick=()=>{const lines=[['received_at_iso','uid',...fields.map(([key,,unit])=>`${key}_${unit}`),'raw'],...records.map(r=>[new Date(r.time).toISOString(),r.uid,...fields.map(([k])=>r[k]),r.raw])];download(new Blob(['\uFEFF'+lines.map(row=>row.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'}),`sensor-${stamp()}.csv`)};
$('backup').onclick=()=>download(new Blob([JSON.stringify({version:1,records},null,2)],{type:'application/json'}),`sensor-${stamp()}.json`);
$('restore').onchange=async e=>{try{const file=e.target.files[0];if(!file)return;const data=JSON.parse(await file.text());if(data.version!==1||!Array.isArray(data.records))throw Error('Invalid backup format');const batch=data.records.map(r=>{if(!r||!Number.isFinite(r.time)||!Number.isFinite(new Date(r.time).getTime())||typeof r.raw!=='string')throw Error('Invalid record format');const parsed=parse(r.raw,r.time);if(!parsed)throw Error('Invalid message format');return parsed});const existing=new Set(records.map(r=>`${r.time}|${r.raw}`));const fresh=batch.filter(r=>{const k=`${r.time}|${r.raw}`;if(existing.has(k))return false;existing.add(k);return true});for(const r of fresh)records.push(r);records.sort((a,b)=>a.time-b.time);rebuildIndex();store(fresh);render();notice(`Imported ${fresh.length} records; duplicates skipped.`)}catch(err){notice('Import failed: '+err.message)}finally{e.target.value=''}};
$('png').onclick=()=>$('chart').toBlob(b=>download(b,`trend-${selected||'empty'}-${$('metric').value}-${stamp()}.png`));
$('ingest').onclick=()=>{const n=ingest($('input').value);if(!n)notice('No valid SENSOR messages found. Check the message format.')};
$('demo').onclick=()=>{const values=[[2332,5627,-94,8],[2330,5596,-94,8],[2334,5592,-98,6],[2340,5653,-97,7],[2343,5625,-97,7],[2344,5583,-97,7]],now=Date.now();const batch=values.map(([t,h,r,s],i)=>parse(`AT+SENSOR=B7180A12,${t},${h},65,390,0,13,${r},${s}`,now-(5-i)*10000));for(const r of batch)records.push(r);records.sort((a,b)=>a.time-b.time);rebuildIndex();store(batch);render();notice('Added 6 sample records with simulated reception times. Samples are saved alongside acquired records.')};
let session=null,lastSerialError='';
$('disconnect').onclick=async()=>{
 running=false;
 $('disconnect').disabled=true;
 $('status').textContent='● Disconnecting';
 if(session)await session.stop();
};
$('connect').onclick=async()=>{
 if(!('serial' in navigator)){notice('Serial access unavailable. Open this page via localhost in desktop Chrome / Edge.');return}
 $('connect').disabled=true;
 try {
  port=await navigator.serial.requestPort();
  running=true;lastSerialError='';
  $('disconnect').disabled=false;
  $('baud').disabled=true;$('idle').disabled=true;receivedBytes=0;lastByte=0;lastRecord=0;updateTraffic();
  let stream=new Lines(ingest),decoder=new TextDecoder();
  session=new SerialSession({
   idleTimeoutMs:Number($('idle').value),
   onTraffic:bytes=>{receivedBytes+=bytes;lastByte=Date.now();scheduleTraffic();},
   onDataError:error=>{notice('Message processing failed; serial reading continues. '+error.message);},
   onData:value=>stream.push(decoder.decode(value,{stream:true})),
   onState:(state,error)=>{
    if(state==='reset'){stream=new Lines(ingest);decoder=new TextDecoder();}
    if(state==='connected'){
     lastSerialError='';
     $('status').textContent='● Serial connected';
     notice('Acquiring data. Automatic recovery is enabled until you click Disconnect.');
    }
    if(state==='retrying'){
     if(error)lastSerialError=`${error.name||'Error'}: ${error.message}`;
     $('status').textContent='● Reconnecting';
     notice('Serial interrupted. Waiting for the selected device and retrying automatically. Data cannot be received while offline.'+(lastSerialError?' '+lastSerialError:''));
    }
   }
  });
  await session.run(port,{baudRate:Number($('baud').value),dataBits:8,stopBits:1,parity:'none',flowControl:'none'});
  stream.push(decoder.decode());stream.flush();
 }catch(error){if(error.name!=='NotFoundError')notice('Serial session failed: '+error.message);}
 finally {
  running=false;session=null;port=null;
  $('status').textContent='● Disconnected';
  $('disconnect').disabled=true;$('connect').disabled=false;$('baud').disabled=false;$('idle').disabled=false;
 }
};
$('clear').onclick=()=>{if(!confirm('Permanently delete all sensor records in this browser? Export a backup first.'))return;if(!db){notice('Database not ready. Records cannot be cleared yet.');return}const tx=db.transaction('records','readwrite');tx.objectStore('records').clear();tx.oncomplete=()=>{records=[];rebuildIndex();saveFailed=false;render();notice('All records cleared.')};tx.onerror=()=>notice('Failed to clear records. Please try again.')};
window.addEventListener('beforeunload',e=>{if(running){e.preventDefault();e.returnValue=''}});
render();
