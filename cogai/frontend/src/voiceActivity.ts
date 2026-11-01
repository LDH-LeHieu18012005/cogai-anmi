/** Local energy gate, not an emotion, safety or linguistic classifier. */
export class VoiceActivity {
  private attackAt:number|null=null;
  private lastVoice=0;
  private talking=false;
  private floor=0; // Background level, kept across resets so fans or machines do not count as speech.
  constructor(private threshold=.018,private attackMs=220,private silenceMs=1300){}
  get detecting(){return this.attackAt!==null||this.talking;}
  reset(){this.attackAt=null;this.lastVoice=0;this.talking=false;}
  feed(level:number,now:number):'start'|'end'|null{
    if(!this.talking&&this.attackAt===null)this.floor=this.floor?this.floor*.97+level*.03:level;
    const threshold=Math.max(this.threshold,Math.min(this.floor*2.5,.08));
    const audible=level>=(this.talking?threshold*.7:threshold);
    if(audible){
      this.lastVoice=now;
      if(this.attackAt===null)this.attackAt=now;
      if(!this.talking&&now-this.attackAt>=this.attackMs){this.talking=true;return 'start';}
    }else{
      if(!this.talking)this.attackAt=null;
      if(this.talking&&now-this.lastVoice>=this.silenceMs){this.reset();return 'end';}
    }
    return null;
  }
}
