/* Adapt the unchanged floor UI API calls to Streamlit's session-isolated channel. */
(() => {
  'use strict';
  const post=(type,fields={})=>parent.postMessage({isStreamlitMessage:true,type,...fields},'*');
  let bootstrap, readyResolve, active=null, queue=[];
  const ready=new Promise(resolve=>{readyResolve=resolve;});
  const sendNext=()=>{
    if(active || !queue.length)return;
    active=queue.shift();
    post('streamlit:setComponentValue',{value:{id:active.id,route:active.route,payload:active.payload},dataType:'json'});
  };
  window.addEventListener('message',event=>{
    if(event.source!==parent || event.data?.type!=='streamlit:render')return;
    const args=event.data.args;
    if(!bootstrap){bootstrap=args.bootstrap;readyResolve();}
    const response=args.response;
    if(active && response?.id===active.id){
      const done=active;active=null;
      done.resolve({ok:response.ok,json:async()=>response.data});
      sendNext();
    }
    post('streamlit:setFrameHeight',{height:800});
  });
  const originalFetch=window.fetch.bind(window);
  window.fetch=async(input,options={})=>{
    const url=String(input);
    if(!url.startsWith('/api/'))return originalFetch(input,options);
    await ready;
    if(url==='/api/bootstrap')return {ok:true,json:async()=>bootstrap};
    return new Promise(resolve=>{
      queue.push({id:crypto.randomUUID(),route:url.slice(5),payload:JSON.parse(options.body||'{}'),resolve});
      sendNext();
    });
  };
  post('streamlit:componentReady',{apiVersion:1});
  post('streamlit:setFrameHeight',{height:800});
})();
