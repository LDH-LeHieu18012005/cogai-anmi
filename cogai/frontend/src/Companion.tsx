import { useId, useRef, type CSSProperties } from 'react';

export type CompanionState='idle'|'listening'|'thinking'|'speaking'|'support'|'unavailable';
export type CompanionTheme='sage'|'peach'|'sky';
const descriptions:Record<CompanionState,string>={idle:'Sẵn sàng nghe bạn chia sẻ',listening:'Đang ghi âm theo yêu cầu của bạn',thinking:'Đang xử lý, chưa phát phản hồi',speaking:'Đang đọc phản hồi',support:'Đang ưu tiên hỗ trợ',unavailable:'Đang tạm dừng vì lỗi dịch vụ'};

export function Companion({state,theme,motion}:{state:CompanionState;theme:CompanionTheme;motion:boolean}){
  const id=useId().replace(/:/g,'');
  const figure=useRef<HTMLDivElement>(null);
  function look(x:number,y:number){if(figure.current){figure.current.style.setProperty('--gaze-x',`${x}px`);figure.current.style.setProperty('--gaze-y',`${y}px`);}}
  return <div ref={figure} className={`companion-figure theme-${theme} state-${state} ${motion?'':'still'}`} data-state={state}
    onPointerMove={e=>{if(!motion||e.pointerType==='touch')return;const r=e.currentTarget.getBoundingClientRect();look((e.clientX-r.left-r.width/2)/r.width*8,(e.clientY-r.top-r.height/2)/r.height*5);}}
    onPointerLeave={()=>look(0,0)} style={{'--gaze-x':'0px','--gaze-y':'0px'} as CSSProperties}>
    <div className="companion-orbit orbit-one"/><div className="companion-orbit orbit-two"/>
    <svg viewBox="0 0 360 380" role="img" aria-label={`AnMi, tác nhân CogAI. ${descriptions[state]}`}>
      <defs><linearGradient id={`${id}-body`} x1="0" y1="0" x2=".8" y2="1"><stop stopColor="var(--companion-light)"/><stop offset="1" stopColor="var(--companion-body)"/></linearGradient>
        <linearGradient id={`${id}-face`} x2="0" y2="1"><stop stopColor="#153a42"/><stop offset="1" stopColor="#091d27"/></linearGradient></defs>
      <ellipse className="companion-shadow" cx="180" cy="344" rx="79" ry="12" fill="var(--companion-dark)" opacity=".1"/>
      <g className="companion-body">
        <path d="M122 290V328Q122 346 146 346Q166 346 166 329V310M194 310V329Q194 346 216 346Q239 346 239 328V290" fill={`url(#${id}-body)`} stroke="#d9dbe6" strokeWidth="2"/>
        <path d="M112 222 Q69 233 82 275 Q91 293 110 267L132 240" fill={`url(#${id}-body)`} stroke="var(--companion-dark)" strokeWidth="1.5"/>
        <path className="companion-hand" d="M246 223 Q286 216 281 250 Q276 277 252 267L230 244" fill={`url(#${id}-body)`} stroke="var(--companion-dark)" strokeWidth="1.5"/>
        <path d="M100 152Q89 105 111 78Q104 56 110 39Q125 64 144 66Q162 57 180 60Q198 57 216 66Q235 64 250 39Q256 56 249 78Q271 105 260 152L255 276Q251 319 180 320Q109 319 105 276Z" fill={`url(#${id}-body)`} stroke="#d9dbe6" strokeWidth="2"/>
        <path d="M160 63Q164 40 177 58Q182 35 192 59Q202 44 209 66" fill={`url(#${id}-body)`} stroke="#d9dbe6" strokeWidth="2" strokeLinejoin="round"/>
        <rect x="111" y="100" width="138" height="117" rx="30" fill="var(--companion-face-frame)"/>
        <rect x="123" y="114" width="114" height="85" rx="13" fill={`url(#${id}-face)`}/>
        <g className="companion-eyes"><g className="companion-gaze"><rect x="140" y="136" width="19" height="25" rx="7" fill="#70eeed"/><rect x="201" y="136" width="19" height="25" rx="7" fill="#70eeed"/></g></g>
        {state==='speaking'?<ellipse className="companion-mouth" cx="180" cy="174" rx="8" ry="5" fill="#70eeed"/>:<path d={state==='support'||state==='unavailable'?'M172 176Q180 173 188 176':'M169 171Q180 184 191 171'} stroke="#70eeed" strokeWidth="3.5" strokeLinecap="round" fill="none"/>}
        <circle cx="224" cy="265" r="4" fill="#b0b3c4"/>
      </g>
    </svg>
    <span className="companion-firefly firefly-one"/><span className="companion-firefly firefly-two"/>
  </div>;
}
