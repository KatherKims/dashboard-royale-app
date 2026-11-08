/* Pure geometry: shared by the floor and Node regression checks. */
(function(root){
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  function zoomAt(camera,point,factor){
    const scale=clamp(camera.scale*factor,.35,6), ratio=scale/camera.scale;
    return {scale,x:point.x-(point.x-camera.x)*ratio,y:point.y-(point.y-camera.y)*ratio};
  }
  function worldPoint(camera,p){return {x:(p.x-camera.x)/camera.scale,y:(p.y-camera.y)/camera.scale};}
  function route(a,b,side=1){
    const dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy)||1;
    const bend=Math.min(48,Math.max(12,len*.22))*side;
    return [a,{x:(a.x+b.x)/2-dy/len*bend,y:(a.y+b.y)/2+dx/len*bend},b];
  }
  function pairedRoutes(a,b){return [route(a,b,1),route(b,a,1)];}
  function onRoute(r,t){const q=1-t;return {x:q*q*r[0].x+2*q*t*r[1].x+t*t*r[2].x,y:q*q*r[0].y+2*q*t*r[1].y+t*t*r[2].y};}
  function dropTarget(p,slots,radius=12){
    return slots.map(s=>({...s,d:Math.hypot(p.x-s.x,p.y-s.y)})).filter(s=>s.d<=radius).sort((a,b)=>a.d-b.d)[0]||null;
  }
  function blocked(p,obstacles,padding=4){return obstacles.some(o=>Math.abs(o.x-p.x)<o.w/2+padding&&Math.abs(o.y-p.y)<o.h/2+padding);}
  // A* on a free-space grid. No fallback straight line through a cabinet.
  function walkRoute(start,end,obstacles,bounds,step=8){
    const key=(x,y)=>x+','+y, snap=p=>({x:Math.round(p.x/step),y:Math.round(p.y/step)});
    const a=snap(start),b=snap(end),open=[{...a,g:0,f:0}],seen=new Map(),parents=new Map();
    seen.set(key(a.x,a.y),0);
    for(let n=0;open.length&&n<12000;n++){
      open.sort((u,v)=>v.f-u.f);const p=open.pop(),k=key(p.x,p.y);
      if(p.x===b.x&&p.y===b.y){const path=[];let cur=k;while(cur){let [x,y]=cur.split(',').map(Number);path.unshift({x:x*step,y:y*step});cur=parents.get(cur);}return path;}
      for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
        const x=p.x+dx,y=p.y+dy,point={x:x*step,y:y*step},nk=key(x,y),g=p.g+1;
        if(point.x<bounds.x||point.y<bounds.y||point.x>bounds.x+bounds.w||point.y>bounds.y+bounds.h||blocked(point,obstacles,2))continue;
        if(seen.has(nk)&&seen.get(nk)<=g)continue;
        seen.set(nk,g);parents.set(nk,k);open.push({x,y,g,f:g+Math.abs(x-b.x)+Math.abs(y-b.y)});
      }
    }return [];
  }
  root.FloorMotion={clamp,zoomAt,worldPoint,route,pairedRoutes,onRoute,dropTarget,blocked,walkRoute};
  if(typeof module!=='undefined')module.exports=root.FloorMotion;
})(typeof window==='undefined'?globalThis:window);
