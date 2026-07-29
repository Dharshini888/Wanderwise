import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import {
  IconSparkles, IconShieldCheck, IconCalculator, IconSun, IconBook, IconWifi,
  IconBell, IconHeart, IconChartBar, IconPlane, IconBus, IconCurrencyDollar,
  IconFirstAidKit, IconLock, IconBulb, IconStar, IconChevronRight, IconChevronLeft,
  IconMenu2, IconX, IconMoon, IconArrowRight, IconCheck, IconMapPin, IconClock,
  IconUsers, IconRoute, IconMessageChatbot, IconTrendingUp, IconCloud, IconBackpack,
  IconCircleCheck, IconBrandTwitter, IconBrandInstagram, IconBrandLinkedin,
  IconBrandFacebook, IconSend, IconGlobe, IconCompass, IconDeviceDesktop,
  IconDeviceTablet, IconDeviceMobile
} from "@tabler/icons-react";
import "./landing.css";

const NAV_LINKS=[{label:"Home",href:"#home"},{label:"Features",href:"#features"},{label:"Destinations",href:"#destinations"},{label:"About",href:"#how-it-works"},{label:"Contact",href:"#footer"}];
const WHY_CARDS=[{icon:IconSparkles,color:"#2563EB",bg:"#EFF6FF",title:"AI Itinerary Generator",desc:"Day-by-day personalised plans crafted by AI in seconds."},{icon:IconBulb,color:"#8B5CF6",bg:"#F5F3FF",title:"Smart Recommendations",desc:"Hyper-contextual suggestions for restaurants and attractions."},{icon:IconBus,color:"#0EA5E9",bg:"#E0F2FE",title:"Transit Assistant",desc:"Real-time transit routes, fares and offline maps."},{icon:IconCloud,color:"#10B981",bg:"#ECFDF5",title:"Weather Intelligence",desc:"Hourly forecasts integrated right into your itinerary."},{icon:IconCalculator,color:"#F59E0B",bg:"#FFFBEB",title:"Budget Planner",desc:"Set a budget, track spend and get AI savings tips."},{icon:IconChartBar,color:"#EF4444",bg:"#FEF2F2",title:"Expense Tracker",desc:"Auto-categorised logging with receipt scanning and analytics."},{icon:IconBackpack,color:"#F97316",bg:"#FFF7ED",title:"Packing Assistant",desc:"Climate-aware packing lists for every destination."},{icon:IconShieldCheck,color:"#06B6D4",bg:"#ECFEFF",title:"Safety Hub",desc:"Live risk scores, scam alerts and one-tap emergency contacts."},{icon:IconBook,color:"#84CC16",bg:"#F7FEE7",title:"Travel Journal",desc:"Beautiful auto-generated diary with photos and maps."},{icon:IconWifi,color:"#6366F1",bg:"#EEF2FF",title:"Offline Toolkit",desc:"Download maps and guides for zero-connection travel."}];
const HOW_STEPS=[{icon:IconUsers,num:"01",title:"Create Account",desc:"Sign up free in 30 seconds and set your travel personality."},{icon:IconMapPin,num:"02",title:"Enter Trip Details",desc:"Tell the AI your destination, dates, budget and interests."},{icon:IconSparkles,num:"03",title:"AI Generates Itinerary",desc:"A tailored day-by-day plan with activities, dining and transport."},{icon:IconPlane,num:"04",title:"Enjoy Your Trip",desc:"Travel confidently. Update plans on the go with AI assistance."}];
const DESTINATIONS=[{name:"Tokyo",country:"Japan",rating:4.9,budget:"$2,400",season:"Mar-May",emoji:"🗼",gradient:"linear-gradient(135deg,#ec4899,#dc2626)"},{name:"Santorini",country:"Greece",rating:4.8,budget:"$3,200",season:"Jun-Sep",emoji:"🏛️",gradient:"linear-gradient(135deg,#3b82f6,#0ea5e9)"},{name:"Bali",country:"Indonesia",rating:4.7,budget:"$1,800",season:"Apr-Oct",emoji:"🌴",gradient:"linear-gradient(135deg,#10b981,#0d9488)"},{name:"Paris",country:"France",rating:4.9,budget:"$3,800",season:"Apr-Jun",emoji:"🗺️",gradient:"linear-gradient(135deg,#f59e0b,#ea580c)"},{name:"New York",country:"USA",rating:4.8,budget:"$4,200",season:"Sep-Nov",emoji:"🗽",gradient:"linear-gradient(135deg,#475569,#1e293b)"},{name:"Maldives",country:"Maldives",rating:5.0,budget:"$5,500",season:"Nov-Apr",emoji:"🏝️",gradient:"linear-gradient(135deg,#06b6d4,#2563eb)"}];
const AI_FEATURES=[{icon:IconBulb,title:"Personalised Recs",desc:"AI learns your style to deliver spot-on recommendations."},{icon:IconSparkles,title:"AI Trip Planning",desc:"Full itineraries in under 10 seconds with one click."},{icon:IconRoute,title:"Dynamic Itinerary",desc:"Plans adapt in real-time to weather, crowds and mood."},{icon:IconCloud,title:"Weather Intelligence",desc:"Forecast-driven schedule tweaks so rain never ruins your day."},{icon:IconBackpack,title:"Packing Suggestions",desc:"Smart lists based on activities, climate and trip length."},{icon:IconTrendingUp,title:"Travel Insights",desc:"Post-trip analytics to discover your travel patterns."},{icon:IconCalculator,title:"Budget Optimisation",desc:"AI spots savings and auto-allocates your budget."}];
const COMPANION_FEATURES=[{icon:IconBus,title:"Public Transit",desc:"Step-by-step navigation in 200+ cities."},{icon:IconCurrencyDollar,title:"Currency Converter",desc:"Live rates for 170+ currencies, offline too."},{icon:IconFirstAidKit,title:"Emergency Hub",desc:"One-tap SOS with local emergency numbers."},{icon:IconLock,title:"Document Vault",desc:"Encrypted passport, visa and ticket storage."},{icon:IconBook,title:"Travel Journal",desc:"Auto-generated diary with photos and maps."},{icon:IconHeart,title:"Wishlist",desc:"Save dreams, track prices and share with friends."},{icon:IconWifi,title:"Offline Toolkit",desc:"Full functionality without internet connection."},{icon:IconChartBar,title:"Travel Analytics",desc:"Spending, routes and habits in one dashboard."},{icon:IconBell,title:"Notifications",desc:"Flight alerts, price drops and itinerary reminders."}];
const STATS=[{icon:IconRoute,raw:2400000,label:"Trips Planned",suffix:"+"},{icon:IconUsers,raw:850000,label:"Happy Travellers",suffix:"+"},{icon:IconMapPin,raw:195,label:"Countries Supported",suffix:""},{icon:IconSparkles,raw:18000000,label:"Recommendations Generated",suffix:"+"},{icon:IconGlobe,raw:12000,label:"Destinations Covered",suffix:"+"}];
const TESTIMONIALS=[{name:"Sarah Chen",role:"Digital Nomad",rating:5,text:"WanderWise planned my 3-week Japan trip in minutes. The AI knew exactly what I wanted — temples, street food and hidden gems. Absolutely magical!",avatar:"👩🏻‍💼"},{name:"Marcus Williams",role:"Adventure Traveller",rating:5,text:"The safety hub and offline maps saved me in rural Vietnam. Zero connectivity and I still navigated perfectly. This app is a game-changer.",avatar:"👨🏿‍🎒"},{name:"Priya Sharma",role:"Family Travel Blogger",rating:5,text:"Planning family trips used to take weeks. WanderWise does it in seconds and the budget planner kept us perfectly on track!",avatar:"👩🏽‍👧"},{name:"Luca Ferretti",role:"Solo Backpacker",rating:5,text:"From currency conversions to hostel picks, WanderWise is like having a local friend in every city. The journal is beautiful.",avatar:"👨🏼‍🌾"},{name:"Aisha Al-Rashid",role:"Corporate Travel Manager",rating:5,text:"I manage travel for 50+ employees. WanderWise AI cuts our planning time by 80% and keeps everyone in sync. Incredible.",avatar:"👩🏾‍💼"}];
const STYLES=["🧘 Relaxation","🏔️ Adventure","🍜 Food & Culture","🎭 Nightlife","🏛️ History","🌿 Eco Travel"];

function useCountUp(target,duration,go){const[n,setN]=useState(0);useEffect(()=>{if(!go)return;let cur=0;const step=target/(duration/16);const t=setInterval(()=>{cur+=step;if(cur>=target){setN(target);clearInterval(t);}else setN(Math.floor(cur));},16);return()=>clearInterval(t);},[target,duration,go]);return n;}
function useInView(threshold){const ref=useRef(null);const[v,setV]=useState(false);useEffect(()=>{const obs=new IntersectionObserver(([e])=>{if(e.isIntersecting)setV(true);},{threshold});if(ref.current)obs.observe(ref.current);return()=>obs.disconnect();},[threshold]);return[ref,v];}
function fmtNum(n){if(n>=1000000)return(n/1000000).toFixed(1)+"M";if(n>=1000)return(n/1000).toFixed(0)+"K";return String(n);}
function StatCard({icon:Icon,raw,label,suffix,go}){const n=useCountUp(raw,2200,go);return(<div className="lp-stat"><div className="lp-stat__icon"><Icon size={26}/></div><div className="lp-stat__val">{fmtNum(n)}{suffix}</div><div className="lp-stat__lbl">{label}</div></div>);}
function Stars({n}){return(<div className="lp-stars">{Array.from({length:5}).map((_,i)=>(<IconStar key={i} size={13} fill={i<n?"#F59E0B":"none"} stroke={i<n?"#F59E0B":"#CBD5E1"}/>))}</div>);}

export default function Home(){
  const[dark,setDark]=useState(()=>document.documentElement.classList.contains("dark"));
  const[mNav,setMNav]=useState(false);
  const[scrolled,setScrolled]=useState(false);
  const[dIdx,setDIdx]=useState(0);
  const[tIdx,setTIdx]=useState(0);
  const[plan,setPlan]=useState({dest:"",budget:"$1,000-$3,000",dur:"7 days",style:""});
  const[shown,setShown]=useState(false);
  const[email,setEmail]=useState("");
  const[subbed,setSubbed]=useState(false);
  const[sRef,sVis]=useInView(0.3);

  useEffect(()=>{const fn=()=>setScrolled(window.scrollY>60);window.addEventListener("scroll",fn,{passive:true});return()=>window.removeEventListener("scroll",fn);},[]);
  useEffect(()=>{const t=setInterval(()=>setTIdx(i=>(i+1)%TESTIMONIALS.length),5000);return()=>clearInterval(t);},[]);
  const toggleDark=()=>{document.documentElement.classList.toggle("dark");setDark(d=>!d);};
  const VIS=3,maxD=DESTINATIONS.length-VIS;

  return (
    <div className="lp" id="home">
      <header className={"lp-nav"+(scrolled?" lp-nav--stuck":"")}>
        <div className="lp-nav__wrap">
          <a href="#home" className="lp-logo"><span className="lp-logo__icon"><IconCompass size={20} stroke={2.5}/></span><span className="lp-logo__text">WanderWise</span></a>
          <nav className="lp-nav__links">{NAV_LINKS.map(l=><a key={l.label} href={l.href} className="lp-nav__link">{l.label}</a>)}</nav>
          <div className="lp-nav__right">
            <button className="lp-icon-btn" onClick={toggleDark} aria-label="Toggle dark mode">{dark?<IconSun size={19}/>:<IconMoon size={19}/>}</button>
            <Link to="/login" className="lp-btn lp-btn--ghost">Log In</Link>
            <Link to="/register" className="lp-btn lp-btn--primary"><IconSparkles size={15}/> Get Started</Link>
            <button className="lp-icon-btn lp-ham" onClick={()=>setMNav(o=>!o)} aria-label="Menu">{mNav?<IconX size={22}/>:<IconMenu2 size={22}/>}</button>
          </div>
        </div>
        {mNav&&(<div className="lp-mnav">{NAV_LINKS.map(l=><a key={l.label} href={l.href} className="lp-mnav__link" onClick={()=>setMNav(false)}>{l.label}</a>)}<div className="lp-mnav__btns"><Link to="/login" className="lp-btn lp-btn--ghost" onClick={()=>setMNav(false)}>Log In</Link><Link to="/register" className="lp-btn lp-btn--primary" onClick={()=>setMNav(false)}>Get Started</Link></div></div>)}
      </header>

      <section className="lp-hero" aria-label="Hero">
        <div className="lp-hero__blob lp-hero__blob--a"/><div className="lp-hero__blob lp-hero__blob--b"/><div className="lp-hero__blob lp-hero__blob--c"/>
        <div className="lp-dots-grid" aria-hidden="true">{Array.from({length:60}).map((_,i)=><span key={i} className="lp-dot"/>)}</div>
        <div className="lp-hero__body">
          <div className="lp-hero__text">
            <div className="lp-badge"><span className="lp-badge__pill">NEW</span>WanderWise AI 2.0 is here<IconChevronRight size={14}/></div>
            <h1 className="lp-hero__h1">Plan Smarter.<br/>Travel Better.<br/><span className="lp-grad">Explore with AI.</span></h1>
            <p className="lp-hero__sub">Your AI-powered travel companion that builds hyper-personalised itineraries, manages your budget, and keeps you safe.</p>
            <div className="lp-hero__ctas">
              <Link to="/register" className="lp-btn lp-btn--primary lp-btn--lg" id="hero-start"><IconSparkles size={20}/> Start Planning Free</Link>
              <a href="#destinations" className="lp-btn lp-btn--outline lp-btn--lg" id="hero-explore"><IconCompass size={20}/> Explore Destinations</a>
            </div>
            <div className="lp-trust">
              <div className="lp-trust__avs">{["👩🏻","👨🏿","👩🏽","👨🏼","👩🏾"].map((e,i)=><span key={i} className="lp-trust__av" style={{zIndex:5-i}}>{e}</span>)}</div>
              <div className="lp-trust__txt"><strong>850K+</strong> happy travellers &nbsp;·&nbsp; <Stars n={5}/> <strong>4.9/5</strong></div>
            </div>
          </div>
          <div className="lp-hero__card-wrap">
            <div className="lp-ai-card">
              <div className="lp-ai-card__hd"><div className="lp-ai-card__av"><IconMessageChatbot size={18}/></div><div><p className="lp-ai-card__name">WanderWise AI</p><p className="lp-ai-card__status">● Online</p></div><span className="lp-ai-card__tag">AI</span></div>
              <div className="lp-ai-chat">
                <div className="lp-bubble lp-bubble--bot">✈️ Ready to plan your perfect trip! Where are we going?</div>
                <div className="lp-bubble lp-bubble--user">Tokyo, 10 days, $3000, food and culture 🍜</div>
                <div className="lp-bubble lp-bubble--bot lp-typing"><span className="lp-tdot"/><span className="lp-tdot" style={{animationDelay:"0.2s"}}/><span className="lp-tdot" style={{animationDelay:"0.4s"}}/></div>
              </div>
              <div className="lp-itin-prev">
                <p className="lp-itin-prev__lbl">✨ AI Itinerary Preview</p>
                {["Day 1 · Shibuya & Harajuku","Day 2 · Tsukiji + Asakusa","Day 3 · Mt. Fuji Day Trip"].map((d,i)=><div key={i} className="lp-iday"><IconCircleCheck size={14} className="lp-iday__ic"/> {d}</div>)}
                <div className="lp-ibudget"><span>Est. cost</span><strong>$2,847 / $3,000</strong></div>
              </div>
            </div>
            <div className="lp-float lp-float--tr"><IconShieldCheck size={13}/> Safety Verified</div>
            <div className="lp-float lp-float--bl"><IconCloud size={13}/> Sunny 24°C Tokyo</div>
          </div>
        </div>
      </section>

      <section className="lp-sec lp-planner-sec" id="planner">
        <div className="lp-sec__in">
          <div className="lp-sec__chip">AI Trip Planner</div>
          <h2 className="lp-sec__h2">Build Your Perfect Trip in <span className="lp-grad">10 Seconds</span></h2>
          <p className="lp-sec__sub">Enter details and watch AI craft a full personalised itinerary instantly.</p>
          <div className="lp-planner">
            <div className="lp-planner__form glass-card">
              <div className="lp-field"><label htmlFor="p-dest" className="lp-lbl"><IconMapPin size={14}/> Destination</label><input id="p-dest" type="text" className="lp-input" placeholder="e.g. Tokyo, Japan" value={plan.dest} onChange={e=>setPlan(p=>({...p,dest:e.target.value}))}/></div>
              <div className="lp-row">
                <div className="lp-field"><label htmlFor="p-budget" className="lp-lbl"><IconCalculator size={14}/> Budget</label><select id="p-budget" className="lp-input" value={plan.budget} onChange={e=>setPlan(p=>({...p,budget:e.target.value}))}>{["Under $500","$500-$1,000","$1,000-$3,000","$3,000-$6,000","$6,000+"].map(o=><option key={o}>{o}</option>)}</select></div>
                <div className="lp-field"><label htmlFor="p-dur" className="lp-lbl"><IconClock size={14}/> Duration</label><select id="p-dur" className="lp-input" value={plan.dur} onChange={e=>setPlan(p=>({...p,dur:e.target.value}))}>{["3 days","5 days","7 days","10 days","14 days","21 days"].map(o=><option key={o}>{o}</option>)}</select></div>
              </div>
              <div className="lp-field"><label className="lp-lbl"><IconSparkles size={14}/> Travel Style</label><div className="lp-styles">{STYLES.map(s=><button key={s} type="button" className={"lp-style"+(plan.style===s?" lp-style--on":"")} onClick={()=>setPlan(p=>({...p,style:p.style===s?"":s}))}>{s}</button>)}</div></div>
              <button className="lp-btn lp-btn--primary lp-btn--block" id="gen-btn" onClick={()=>setShown(true)}><IconSparkles size={16}/> Generate My Itinerary</button>
              <p className="lp-planner__note">Free · No credit card · Ready in seconds</p>
            </div>
            <div className={"lp-planner__prev glass-card"+(shown?" lp-prev--on":"")}>
              {!shown?(<div className="lp-empty"><div className="lp-empty__icon"><IconRoute size={36}/></div><p>Fill in your trip details and click <b>Generate</b> to see your AI itinerary here.</p></div>):(
                <div className="lp-itin">
                  <div className="lp-itin__hd"><h3 className="lp-itin__dest">{plan.dest||"Your Destination"}</h3><div className="lp-itin__meta"><span><IconClock size={11}/> {plan.dur}</span><span><IconCalculator size={11}/> {plan.budget}</span>{plan.style&&<span>{plan.style}</span>}</div></div>
                  {["Arrival & City Overview","Cultural Immersion & Landmarks","Local Markets & Hidden Gems","Day Trip to Countryside","Food & Nightlife Experience"].map((d,i)=><div key={i} className="lp-itin__day"><span className="lp-itin__dnum">Day {i+1}</span><div><p className="lp-itin__dtitle">{d}</p><p className="lp-itin__ddesc">AI-curated activities, dining and transport planned for you.</p></div><IconChevronRight size={14}/></div>)}
                  <div className="lp-itin__ft"><Link to="/register" className="lp-btn lp-btn--primary lp-btn--sm">Full Itinerary <IconArrowRight size={13}/></Link><span className="lp-itin__ftnote">Sign up to save and customise</span></div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="lp-sec lp-why-sec" id="features">
        <div className="lp-sec__in">
          <div className="lp-sec__chip">Why WanderWise?</div>
          <h2 className="lp-sec__h2">Everything You Need for <span className="lp-grad">Smarter Travel</span></h2>
          <p className="lp-sec__sub">10 powerful AI-driven tools in one beautiful app.</p>
          <div className="lp-why-grid">{WHY_CARDS.map((c,i)=><div key={i} className="lp-wcard glass-card"><div className="lp-wcard__icon" style={{background:c.bg,color:c.color}}><c.icon size={22}/></div><h3 className="lp-wcard__title">{c.title}</h3><p className="lp-wcard__desc">{c.desc}</p><span className="lp-wcard__arr"><IconArrowRight size={14}/></span></div>)}</div>
        </div>
      </section>

      <section className="lp-sec lp-how-sec" id="how-it-works">
        <div className="lp-sec__in">
          <div className="lp-sec__chip">How It Works</div>
          <h2 className="lp-sec__h2">From <span className="lp-grad">Idea to Itinerary</span> in Four Steps</h2>
          <p className="lp-sec__sub">Getting started is as easy as 1-2-3-4.</p>
          <div className="lp-steps">{HOW_STEPS.map((s,i)=><div key={i} className="lp-step">{i<HOW_STEPS.length-1&&<div className="lp-step__line"/>}<div className="lp-step__circle"><s.icon size={24}/></div><div className="lp-step__num">{s.num}</div><h3 className="lp-step__title">{s.title}</h3><p className="lp-step__desc">{s.desc}</p></div>)}</div>
          <div className="lp-how-cta"><Link to="/register" className="lp-btn lp-btn--primary lp-btn--lg" id="how-cta"><IconSparkles size={17}/> Get Started Free</Link></div>
        </div>
      </section>

      <section className="lp-sec lp-dest-sec" id="destinations">
        <div className="lp-sec__in">
          <div className="lp-sec__chip">Popular Destinations</div>
          <h2 className="lp-sec__h2">Trending <span className="lp-grad">Around the World</span></h2>
          <p className="lp-sec__sub">Handpicked destinations with AI insights and budget estimates.</p>
          <div className="lp-dest-wrap">
            <button className="lp-cbtn lp-cbtn--l" onClick={()=>setDIdx(i=>Math.max(0,i-1))} disabled={dIdx===0} aria-label="Previous"><IconChevronLeft size={20}/></button>
            <div className="lp-dest-grid">{DESTINATIONS.map((d,i)=><div key={d.name} className={"lp-dcard"+(i<dIdx||i>=dIdx+VIS?" lp-dcard--hide":"")}><div className="lp-dcard__img" style={{background:d.gradient}}><span className="lp-dcard__emoji">{d.emoji}</span></div><div className="lp-dcard__body"><div className="lp-dcard__top"><div><h3 className="lp-dcard__name">{d.name}</h3><p className="lp-dcard__country"><IconMapPin size={11}/> {d.country}</p></div><div className="lp-dcard__rating"><IconStar size={12} fill="#F59E0B" stroke="#F59E0B"/> {d.rating}</div></div><div className="lp-dcard__meta"><span><IconCalculator size={11}/> {d.budget}</span><span><IconSun size={11}/> {d.season}</span></div><Link to="/register" className="lp-btn lp-btn--outline lp-btn--sm lp-btn--block">View Details <IconArrowRight size={12}/></Link></div></div>)}</div>
            <button className="lp-cbtn lp-cbtn--r" onClick={()=>setDIdx(i=>Math.min(maxD,i+1))} disabled={dIdx>=maxD} aria-label="Next"><IconChevronRight size={20}/></button>
          </div>
        </div>
      </section>

      <section className="lp-sec lp-aif-sec" id="ai-features">
        <div className="lp-sec__in">
          <div className="lp-sec__chip">AI Features</div>
          <h2 className="lp-sec__h2">Powered by <span className="lp-grad">Next-Gen AI</span></h2>
          <p className="lp-sec__sub">Seven intelligent systems working together to make your trip extraordinary.</p>
          <div className="lp-aif-grid">{AI_FEATURES.map((f,i)=><div key={i} className="lp-aif-card glass-card"><div className="lp-aif-card__icon"><f.icon size={22}/></div><h3 className="lp-aif-card__title">{f.title}</h3><p className="lp-aif-card__desc">{f.desc}</p><span className="lp-aif-card__tag">AI-Powered</span></div>)}</div>
        </div>
      </section>

      <section className="lp-sec lp-comp-sec" id="companion">
        <div className="lp-sec__in">
          <div className="lp-sec__chip">Smart Companion</div>
          <h2 className="lp-sec__h2">Your <span className="lp-grad">All-in-One</span> Travel Toolkit</h2>
          <p className="lp-sec__sub">Nine essential tools that keep you covered from booking to touchdown.</p>
          <div className="lp-comp-grid">{COMPANION_FEATURES.map((f,i)=><div key={i} className="lp-ccomp glass-card"><div className="lp-ccomp__icon"><f.icon size={20}/></div><h3 className="lp-ccomp__title">{f.title}</h3><p className="lp-ccomp__desc">{f.desc}</p></div>)}</div>
        </div>
      </section>

      <section className="lp-stats-bg" id="stats" ref={sRef}>
        <div className="lp-stats-bg__blob lp-stats-bg__blob--a"/><div className="lp-stats-bg__blob lp-stats-bg__blob--b"/>
        <div className="lp-stats-wrap">
          <div className="lp-sec__chip lp-sec__chip--light">Our Impact</div>
          <h2 className="lp-sec__h2 lp-sec__h2--light">Trusted by <span className="lp-grad-light">Millions</span> of Travellers</h2>
          <div className="lp-stats-grid">{STATS.map((s,i)=><StatCard key={i} {...s} go={sVis}/>)}</div>
        </div>
      </section>

      <section className="lp-sec lp-testi-sec" id="testimonials">
        <div className="lp-sec__in">
          <div className="lp-sec__chip">Testimonials</div>
          <h2 className="lp-sec__h2">What Travellers <span className="lp-grad">Are Saying</span></h2>
          <p className="lp-sec__sub">Real stories from real travellers who explored the world with WanderWise.</p>
          <div className="lp-testi-outer"><div className="lp-testi-track" style={{transform:"translateX(-"+(tIdx*100)+"%)"}}>{TESTIMONIALS.map((t,i)=><div key={i} className="lp-tcard glass-card"><Stars n={t.rating}/><p className="lp-tcard__txt">"{t.text}"</p><div className="lp-tcard__auth"><span className="lp-tcard__av">{t.avatar}</span><div><p className="lp-tcard__name">{t.name}</p><p className="lp-tcard__role">{t.role}</p></div></div></div>)}</div></div>
          <div className="lp-testi-dots">{TESTIMONIALS.map((_,i)=><button key={i} className={"lp-tdot-btn"+(tIdx===i?" lp-tdot-btn--on":"")} onClick={()=>setTIdx(i)} aria-label={"Testimonial "+(i+1)}/>)}</div>
          <div className="lp-testi-nav"><button className="lp-cbtn" onClick={()=>setTIdx(i=>Math.max(0,i-1))} aria-label="Prev"><IconChevronLeft size={18}/></button><button className="lp-cbtn" onClick={()=>setTIdx(i=>Math.min(TESTIMONIALS.length-1,i+1))} aria-label="Next"><IconChevronRight size={18}/></button></div>
        </div>
      </section>

      <section className="lp-sec lp-screens-sec" id="screenshots">
        <div className="lp-sec__in">
          <div className="lp-sec__chip">App Preview</div>
          <h2 className="lp-sec__h2">Beautiful on <span className="lp-grad">Every Device</span></h2>
          <p className="lp-sec__sub">A seamless experience across desktop, tablet and mobile.</p>
          <div className="lp-devices">
            <div className="lp-device lp-device--desktop"><div className="lp-device__frame"><div className="lp-device__bar"><span/><span/><span/></div><div className="lp-device__screen"><div className="lp-mk-row"/><div className="lp-mk-hero"/><div className="lp-mk-cols"><div className="lp-mk-col"/><div className="lp-mk-col"/><div className="lp-mk-col"/></div></div></div><p className="lp-device__lbl"><IconDeviceDesktop size={14}/> Desktop</p></div>
            <div className="lp-device lp-device--tablet"><div className="lp-device__frame lp-device__frame--tab"><div className="lp-device__cam"/><div className="lp-device__screen lp-device__screen--tab"><div className="lp-mk-row"/><div className="lp-mk-hero lp-mk-hero--sm"/><div className="lp-mk-cols"><div className="lp-mk-col"/><div className="lp-mk-col"/></div></div><div className="lp-device__home"/></div><p className="lp-device__lbl"><IconDeviceTablet size={14}/> Tablet</p></div>
            <div className="lp-device lp-device--mobile"><div className="lp-device__frame lp-device__frame--mob"><div className="lp-device__notch"/><div className="lp-device__screen lp-device__screen--mob"><div className="lp-mk-row"/><div className="lp-mk-hero lp-mk-hero--xs"/><div className="lp-mk-cols lp-mk-cols--col"><div className="lp-mk-col"/><div className="lp-mk-col"/></div></div></div><p className="lp-device__lbl"><IconDeviceMobile size={14}/> Mobile</p></div>
          </div>
        </div>
      </section>

      <section className="lp-cta" id="cta">
        <div className="lp-cta__blob lp-cta__blob--a"/><div className="lp-cta__blob lp-cta__blob--b"/>
        <div className="lp-cta__in">
          <div className="lp-cta__ring"><IconPlane size={30}/></div>
          <h2 className="lp-cta__h2">Start Your Smart Travel<br/>Journey <span className="lp-grad-light">Today</span></h2>
          <p className="lp-cta__sub">Join 850,000+ travellers who plan smarter, spend less and experience more.</p>
          <div className="lp-cta__btns"><Link to="/register" className="lp-btn lp-btn--white lp-btn--lg" id="cta-signup"><IconSparkles size={19}/> Sign Up Free</Link><Link to="/register" className="lp-btn lp-btn--outline-w lp-btn--lg" id="cta-plan"><IconRoute size={19}/> Plan Your First Trip</Link></div>
          <div className="lp-perks">{["Free forever plan","No credit card","AI-powered itineraries","195 countries"].map((p,i)=><span key={i} className="lp-perk"><IconCheck size={13}/> {p}</span>)}</div>
        </div>
      </section>

      <footer className="lp-footer" id="footer">
        <div className="lp-footer__in">
          <div className="lp-footer__brand">
            <div className="lp-logo lp-logo--ft"><span className="lp-logo__icon"><IconCompass size={18}/></span><span className="lp-logo__text">WanderWise</span></div>
            <p className="lp-footer__tag">Your AI-powered travel companion. Plan smarter, travel better.</p>
            <div className="lp-footer__social">{[[IconBrandTwitter,"Twitter"],[IconBrandInstagram,"Instagram"],[IconBrandFacebook,"Facebook"],[IconBrandLinkedin,"LinkedIn"]].map(([Ic,lbl])=><a key={lbl} href="#" className="lp-social" aria-label={lbl}><Ic size={17}/></a>)}</div>
          </div>
          <div className="lp-footer__cols">{[{t:"Company",ls:["About Us","Careers","Blog","Press Kit","Partners"]},{t:"Features",ls:["AI Planner","Budget Tracker","Transit Guide","Safety Hub","Travel Journal"]},{t:"Resources",ls:["Help Center","API Docs","Community","Status Page","Changelog"]},{t:"Legal",ls:["Privacy Policy","Terms of Service","Cookie Policy","GDPR"]}].map(col=><div key={col.t} className="lp-footer__col"><h4 className="lp-footer__col-h">{col.t}</h4>{col.ls.map(l=><a key={l} href="#" className="lp-footer__lnk">{l}</a>)}</div>)}</div>
          <div className="lp-footer__news">
            <h4 className="lp-footer__col-h">Travel Inspiration</h4>
            <p className="lp-footer__news-sub">Weekly destination guides and AI travel tips in your inbox.</p>
            <form className="lp-news-form" onSubmit={e=>{e.preventDefault();if(email)setSubbed(true);}}>
              {!subbed?(<><input type="email" className="lp-input lp-news-input" placeholder="your@email.com" value={email} onChange={e=>setEmail(e.target.value)} aria-label="Email" required/><button type="submit" className="lp-btn lp-btn--primary lp-news-btn"><IconSend size={15}/></button></>):(<div className="lp-news-ok"><IconCircleCheck size={16}/> Subscribed! ✈️</div>)}
            </form>
          </div>
        </div>
        <div className="lp-footer__btm"><p>© 2026 WanderWise Inc. All rights reserved. Designed with ❤️ and AI.</p><p>Made for adventurers, by adventurers 🌍</p></div>
      </footer>
    </div>
  );
}
