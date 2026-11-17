import { useState, useEffect } from 'react';
import { 
  Brain, Sparkles, CheckCircle, XCircle, RotateCcw, 
  Clock, Heart, Lightbulb, ArrowRight,
  MessageCircle, TrendingUp, Menu, X, Activity, BrainCircuit, Check,
  BookOpen, Layers, ShieldCheck, Scale
} from 'lucide-react';
import frameworkImg from './cbt-macr-framework.png';

// --- Type Definitions ---
interface DistortionResult {
  has_distortion: boolean;
  distortion_types: string[];
  explanation: string;
}

interface AnalysisResult {
  emotional_impact: string;
  underlying_beliefs: string[];
  triggers: string[];
  recommended_therapies: string[];
  therapy_rationales: Record<string, string>;
}

interface Candidate {
  therapy: string;
  reframe: string;
  rationale: string;
  evaluation?: { [key: string]: number; };
}

interface FormData {
  situation: string;
  thought: string;
}

interface FeedbackState {
  belief: number | null;
  helpfulness: number | null;
  recall: number | null;
  learning: number | null;
}

interface ReframeIteration {
  reframe: string;
  iteration: number;
}

const API_BASE_URL = '/api';
const THERAPY_FULL_NAMES: Record<string, string> = {
  "CBT": "Cognitive Behavioral Therapy",
  "ACT": "Acceptance and Commitment Therapy",
  "DBT": "Dialectical Behavior Therapy",
  "REBT": "Rational Emotive Behavior Therapy",
  "MBCT": "Mindfulness-Based Cognitive Therapy",
  "CFT": "Compassion-Focused Therapy",
  "SFBT": "Solution-Focused Brief Therapy",
  "MI": "Motivational Interviewing",
  "Schema Therapy": "Schema Therapy",
  "Narrative Therapy": "Narrative Therapy"
};

const LIKERT_OPTIONS = [
  { value: 4, label: "Strongly Agree" },
  { value: 3, label: "Somewhat Agree" },
  { value: 2, label: "Somewhat Disagree" },
  { value: 1, label: "Strongly Disagree" }
];

export default function LuminaPlatform() {
  // --- States ---
  const [currentPage, setCurrentPage] = useState<string>('app');
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [step, setStep] = useState<number>(1);
  
  const [formData, setFormData] = useState<FormData>({ situation: '', thought: '' });
  const [feedback, setFeedback] = useState<FeedbackState>({ belief: null, helpfulness: null, recall: null, learning: null });
  const [isFeedbackSubmitted, setIsFeedbackSubmitted] = useState(false);

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [distortionResult, setDistortionResult] = useState<DistortionResult | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedReframe, setSelectedReframe] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [reframeHistory, setReframeHistory] = useState<ReframeIteration[]>([]);
  const [activeHistoryIndex, setActiveHistoryIndex] = useState<number>(0);
  const [selectedTherapies, setSelectedTherapies] = useState<string[]>([]);
  const [aiFeedback, setAiFeedback] = useState<string | null>(null);
  const [aiFeedback_summ, setAiFeedback_summ] = useState<string | null>(null);
  const [showExample, setShowExample] = useState(false);
  const [improveCount, setImproveCount] = useState<number>(0);
  const [isImproving, setIsImproving] = useState<boolean>(false);

  // --- Effects ---
  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/session/init`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        setSessionId(data.session_id);
      } catch (err) {
        setSessionId('demo-session-' + Date.now());
      }
    };
    initSession();
  }, []);

  useEffect(() => {
    if (analysis && analysis.recommended_therapies) {
      setSelectedTherapies(analysis.recommended_therapies);
    }
  }, [analysis]);

  useEffect(() => {
    const initializeStep5 = async () => {
      if (step === 5 && selectedReframe !== null && candidates[selectedReframe]) {
        try {
          const response = await fetch(`${API_BASE_URL}/instruction_feedback`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId, situation: formData.situation, thought: formData.thought, current_reframe: candidates[selectedReframe].reframe,
            })
          });
          if (!response.ok) throw new Error('Network response was not ok');
          const apiData = await response.json();
          setReframeHistory([{ reframe: candidates[selectedReframe].reframe, iteration: 0 }]);
          const feedbackObject = JSON.parse(apiData.ai_feedback);
          setAiFeedback_summ(feedbackObject.summary);
          setAiFeedback(apiData.ai_feedback);
          setActiveHistoryIndex(0);
          setImproveCount(0);
        } catch (error) {
          setReframeHistory([{ reframe: candidates[selectedReframe].reframe, iteration: 0 }]);
          setActiveHistoryIndex(0);
          setImproveCount(0);
        }
      }
    };
    initializeStep5();
  }, [step, selectedReframe, candidates, formData.situation, formData.thought, sessionId]); 

  // --- Logic Helpers ---
  const handleFeedbackChange = (question: keyof FeedbackState, value: number) => setFeedback(prev => ({ ...prev, [question]: value }));
  const fillExample = () => {
    setFormData({
      situation: "I sent a message to my friend 3 hours ago and saw they were online, but they haven't replied yet.",
      thought: "They are ignoring me because they find me annoying. I must have said something wrong and now they hate me."
    });
    setShowExample(false);
  };
  const toggleTherapy = (therapyKey: string) => setSelectedTherapies(prev => prev.includes(therapyKey) ? prev.filter(t => t !== therapyKey) : [...prev, therapyKey]);
  const reset = () => {
    setStep(1); setFormData({ situation: '', thought: '' }); setDistortionResult(null); setAnalysis(null); setCandidates([]);
    setSelectedReframe(null); setError(null); setSelectedTherapies([]); setFeedback({ belief: null, helpfulness: null, recall: null, learning: null });
    setIsFeedbackSubmitted(false); setImproveCount(0); setIsImproving(false); setReframeHistory([]); setActiveHistoryIndex(0); setAiFeedback(null);
  };

  // --- API Functions ---
  const detectDistortion = async () => {
    setLoading(true); setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/detect`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, situation: formData.situation, thought: formData.thought })
      });
      if (!response.ok) throw new Error('Detection failed');
      const data = await response.json();
      setDistortionResult(data);
      setStep(2);
    } catch (err) { setError('Failed to detect distortions. Please try again.'); }
    finally { setLoading(false); }
  };

  const analyzeThought = async () => {
    if (!distortionResult) return;
    setLoading(true); setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, situation: formData.situation, thought: formData.thought, distortions: distortionResult.distortion_types })
      });
      if (!response.ok) throw new Error('Analysis failed');
      const data = await response.json();
      setAnalysis(data);
      setStep(3);
    } catch (err) { setError('Failed to analyze thought. Please try again.'); }
    finally { setLoading(false); }
  };

  const generateCandidates = async () => {
    if (!selectedTherapies.length) return; 
    setLoading(true); setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/reframe`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, situation: formData.situation, thought: formData.thought, recommended_therapies: selectedTherapies })
      });
      if (!response.ok) throw new Error('Generation failed');
      const data = await response.json();
      setCandidates(data.candidates);
      setStep(4);
    } catch (err) { setError('Failed to generate reframes. Please try again.'); }
    finally { setLoading(false); }
  };

  const handleImprove = async () => {
    if (improveCount >= 5 || selectedReframe === null || reframeHistory.length === 0) return;
    setIsImproving(true);
    try {
      const currentReframeObj = reframeHistory[reframeHistory.length - 1]; 
      const response = await fetch(`${API_BASE_URL}/improve`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, situation: formData.situation, thought: formData.thought, current_reframe: currentReframeObj.reframe, history_response: reframeHistory, feedback: aiFeedback })
      });
      if (!response.ok) throw new Error('Improvement failed');
      const data = await response.json();

      const feedback_response = await fetch(`${API_BASE_URL}/instruction_feedback`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, situation: formData.situation, thought: formData.thought, current_reframe: data.new_reframe })
      });
      if (!feedback_response.ok) throw new Error('Network response was not ok');

      const feedbackData = await feedback_response.json();
      const feedbackObject = JSON.parse(feedbackData.ai_feedback);
      
      setAiFeedback_summ(feedbackObject.summary);
      setAiFeedback(feedbackData.ai_feedback);
      setReframeHistory(prev => [...prev, { reframe: data.new_reframe, iteration: improveCount + 1 }]);
      setImproveCount(prev => prev + 1);
      setActiveHistoryIndex(improveCount + 1); 
      setIsFeedbackSubmitted(false);
      setFeedback({ belief: null, helpfulness: null, recall: null, learning: null });
    } catch (err) { console.error('Failed to improve reframe:', err); } 
    finally { setIsImproving(false); }
  };

  const submitFeedback = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/feedback`, { 
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, timestamp: new Date().toISOString(), input: { situation: formData.situation, thought: formData.thought }, output: { therapy_type: candidates[selectedReframe!]?.therapy, reframe: candidates[selectedReframe!]?.reframe }, ratings: feedback })
      });
      if (!response.ok) throw new Error('Failed to save feedback');
      setIsFeedbackSubmitted(true);
    } catch (err) { alert("Could not save feedback. Please check your connection."); }
  };

  const saveSelection = async () => {
    if (selectedReframe === null) return;
    try {
      await fetch(`${API_BASE_URL}/save`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, selected_reframe: candidates[selectedReframe], original_thought: formData.thought })
      });
    } catch (err) { console.error(err); }
    finally { setStep(5); }
  };

  // --- UI Components ---
  const renderNavigation = () => (
    <nav className="bg-white/80 backdrop-blur-lg fixed w-full top-0 z-50 border-b border-blue-50/50 shadow-[0_4px_30px_rgba(0,0,0,0.02)]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          <div className="flex items-center cursor-pointer group" onClick={() => setCurrentPage('home')}>
            <div className="bg-gradient-to-tr from-blue-600 to-cyan-400 p-2 rounded-xl mr-3 group-hover:shadow-lg group-hover:shadow-blue-500/30 transition-all">
              <BrainCircuit className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-black text-slate-800 tracking-tight">Lumina</span>
          </div>
          
          <div className="hidden md:flex space-x-1 items-center bg-slate-50/80 p-1.5 rounded-full border border-slate-100">
            {['home', 'science', 'app'].map((page) => (
              <button 
                key={page} onClick={() => setCurrentPage(page)} 
                className={`px-6 py-2 rounded-full font-semibold transition-all duration-300 capitalize ${currentPage === page ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100/50'}`}
              >
                {page === 'app' ? 'Workspace' : page}
              </button>
            ))}
          </div>

          <button className="md:hidden text-slate-600 p-2" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
            {mobileMenuOpen ? <X /> : <Menu />}
          </button>
        </div>
      </div>
    </nav>
  );

  const CustomStepper = () => {
    const steps = [
      { id: 1, name: 'Input', icon: MessageCircle },
      { id: 2, name: 'Detect', icon: Activity },
      { id: 3, name: 'Analyze', icon: TrendingUp },
      { id: 4, name: 'Reframe', icon: Brain },
      { id: 5, name: 'Reflect', icon: CheckCircle }
    ];

    return (
      <div className="w-full max-w-4xl mx-auto mb-12 hidden md:block lumina-slide-down">
        <div className="flex items-center justify-between relative">
          <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-full h-1 bg-slate-100 rounded-full z-0"></div>
          <div className="absolute left-0 top-1/2 transform -translate-y-1/2 h-1 bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full z-0 transition-all duration-700 ease-in-out" style={{ width: `${((step - 1) / 4) * 100}%` }}></div>

          {steps.map((s) => {
            const isActive = step === s.id;
            const isCompleted = step > s.id;
            const Icon = s.icon;
            
            return (
              <div key={s.id} className="relative z-10 flex flex-col items-center">
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-500 ${
                  isActive ? 'bg-blue-600 text-white shadow-xl shadow-blue-500/40 scale-110 transform' : 
                  isCompleted ? 'bg-white text-blue-500 border-2 border-blue-500 shadow-md' : 
                  'bg-white text-slate-300 border-2 border-slate-100'
                }`}>
                  {isCompleted ? <Check className="w-6 h-6" /> : <Icon className="w-6 h-6" />}
                </div>
                <span className={`absolute -bottom-8 text-xs font-bold uppercase tracking-wider transition-all duration-300 ${
                  isActive ? 'text-blue-700' : isCompleted ? 'text-slate-600' : 'text-slate-400'
                }`}>{s.name}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderStep1 = () => (
    <div className="lumina-fade-in w-full max-w-3xl mx-auto">
      <div className="text-center mb-10">
        <h2 className="text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">What's on your mind?</h2>
        <p className="text-lg text-slate-500 font-light">Break down your experience into facts and thoughts. This helps create distance.</p>
      </div>

      <div className="flex justify-end mb-4">
        <button onClick={() => setShowExample(!showExample)} className="text-sm font-bold text-blue-600 bg-blue-50 hover:bg-blue-100 px-4 py-2 rounded-full transition-colors flex items-center">
          <Lightbulb className="w-4 h-4 mr-2" /> {showExample ? 'Hide Example' : 'Need an example?'}
        </button>
      </div>

      {showExample && (
        <div className="mb-8 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-3xl p-6 lumina-slide-down shadow-sm">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-sm font-bold text-blue-800 uppercase tracking-widest">Example Scenario</h3>
            <button onClick={() => setShowExample(false)} className="text-blue-400 hover:text-blue-600"><X className="w-5 h-5" /></button>
          </div>
          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <div className="bg-white/80 p-5 rounded-2xl border border-white">
              <span className="text-xs font-bold text-blue-500 uppercase block mb-2">1. The Situation</span>
              <p className="text-slate-700 text-sm">"I sent a message to my friend 3 hours ago and haven't received a reply yet."</p>
            </div>
            <div className="bg-white/80 p-5 rounded-2xl border border-white">
              <span className="text-xs font-bold text-indigo-500 uppercase block mb-2">2. The Thought</span>
              <p className="text-slate-700 text-sm">"They are ignoring me because they hate me. I always mess up relationships."</p>
            </div>
          </div>
          <button onClick={fillExample} className="w-full py-3 bg-white text-blue-600 font-bold rounded-xl shadow-sm hover:shadow-md transition-all text-sm border border-blue-100">
            Apply this example
          </button>
        </div>
      )}

      <div className="space-y-6">
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-[0_8px_30px_rgb(0,0,0,0.04)] focus-within:border-blue-400 focus-within:ring-4 focus-within:ring-blue-50 transition-all duration-300 group">
          <label className="flex items-center text-sm font-bold text-slate-800 mb-3 uppercase tracking-wider">
            <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mr-3 group-focus-within:bg-blue-100 group-focus-within:text-blue-600 transition-colors">1</div>
            Objective Situation
          </label>
          <p className="text-xs text-slate-400 mb-3 ml-9">Describe the facts as if a camera recorded them (Who, what, when, where).</p>
          <textarea
            className="w-full bg-slate-50 hover:bg-slate-100 focus:bg-white text-slate-800 rounded-2xl p-5 outline-none resize-none transition-colors border border-transparent focus:border-slate-200 text-lg"
            rows={3} placeholder="E.g., I made a mistake during my presentation..."
            value={formData.situation} onChange={(e) => setFormData({ ...formData, situation: e.target.value })}
          />
        </div>

        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-[0_8px_30px_rgb(0,0,0,0.04)] focus-within:border-indigo-400 focus-within:ring-4 focus-within:ring-indigo-50 transition-all duration-300 group">
          <label className="flex items-center text-sm font-bold text-slate-800 mb-3 uppercase tracking-wider">
            <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mr-3 group-focus-within:bg-indigo-100 group-focus-within:text-indigo-600 transition-colors">2</div>
            Subjective Thought
          </label>
          <p className="text-xs text-slate-400 mb-3 ml-9">What interpretation, fear, or judgment popped into your head?</p>
          <textarea
            className="w-full bg-slate-50 hover:bg-slate-100 focus:bg-white text-slate-800 rounded-2xl p-5 outline-none resize-none transition-colors border border-transparent focus:border-slate-200 text-lg"
            rows={3} placeholder="E.g., Everyone thinks I'm incompetent. I'll get fired..."
            value={formData.thought} onChange={(e) => setFormData({ ...formData, thought: e.target.value })}
          />
        </div>

        <div className="pt-4">
          <button onClick={detectDistortion} disabled={!formData.situation || !formData.thought || loading}
            className="w-full bg-slate-900 text-white hover:bg-blue-600 disabled:bg-slate-200 disabled:text-slate-400 font-extrabold text-lg py-5 px-6 rounded-2xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-blue-500/25 transform hover:-translate-y-1"
          >
            {loading ? <><RotateCcw className="animate-spin w-6 h-6 mr-3" /> Analyzing patterns...</> : <>Detect Distortions <ArrowRight className="w-6 h-6 ml-3" /></>}
          </button>
        </div>
      </div>
    </div>
  );

  const renderStep2 = () => {
    if (!distortionResult) return null;
    const isDistorted = distortionResult.has_distortion;

    return (
      <div className="lumina-slide-up w-full max-w-3xl mx-auto text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-8 shadow-xl relative">
           <div className={`absolute inset-0 rounded-full animate-ping opacity-20 ${isDistorted ? 'bg-amber-400' : 'bg-teal-400'}`}></div>
           <div className={`relative w-full h-full rounded-full flex items-center justify-center ${isDistorted ? 'bg-amber-100 text-amber-600' : 'bg-teal-100 text-teal-600'}`}>
              {isDistorted ? <Activity className="w-10 h-10" /> : <CheckCircle className="w-10 h-10" />}
           </div>
        </div>
        
        <h2 className="text-4xl font-extrabold text-slate-900 mb-6 tracking-tight">
          {isDistorted ? 'Cognitive Traps Detected' : 'Clear Skies Ahead'}
        </h2>

        {isDistorted ? (
          <div className="text-left">
            <p className="text-lg text-slate-500 text-center mb-8 max-w-2xl mx-auto">Your thought contains common patterns that can distort reality and heighten anxiety. Recognizing them is the first step.</p>
            
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm mb-10">
              <div className="flex flex-wrap gap-3 mb-6 justify-center">
                {distortionResult.distortion_types.map((type, idx) => (
                  <span key={idx} className="bg-amber-50 border border-amber-200 text-amber-800 px-5 py-2 rounded-xl text-sm font-bold shadow-sm">{type}</span>
                ))}
              </div>
              <div className="bg-slate-50 p-6 rounded-2xl">
                 <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center"><Brain className="w-4 h-4 mr-2"/> Clinical Explanation</h4>
                 <p className="text-slate-700 text-lg leading-relaxed">{distortionResult.explanation}</p>
              </div>
            </div>

            <button onClick={analyzeThought} disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-lg py-5 px-6 rounded-2xl transition-all shadow-lg shadow-blue-500/30 flex items-center justify-center transform hover:-translate-y-1">
              {loading ? <><RotateCcw className="animate-spin w-6 h-6 mr-3" /> Deeply analyzing...</> : <>Proceed to Deep Analysis <ArrowRight className="w-6 h-6 ml-3" /></>}
            </button>
          </div>
        ) : (
          <div>
            <p className="text-xl text-slate-600 mb-10">Your thinking appears grounded and realistic. We didn't detect major cognitive distortions.</p>
            <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm text-left mb-10">
                 <h4 className="text-xs font-bold text-teal-500 uppercase tracking-wider mb-3">AI Analysis</h4>
                 <p className="text-slate-700 text-lg leading-relaxed">{distortionResult.explanation}</p>
            </div>
            <div className="flex gap-4">
              <button onClick={() => setStep(1)} className="flex-1 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold py-4 rounded-2xl transition-all">
                Try another thought
              </button>
              <button onClick={() => setCurrentPage('home')} className="flex-1 bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-2xl transition-all">
                Return Home
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderStep3 = () => {
    if (!analysis) return null;
    return (
      <div className="lumina-fade-in w-full max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">Anatomy of a Thought</h2>
          <p className="text-lg text-slate-500 font-light">Understanding the roots and impact of your perspective.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white p-8 rounded-3xl border-t-4 border-t-sky-400 border-x border-b border-slate-200 shadow-sm hover:shadow-lg transition-all duration-300">
            <div className="bg-sky-50 w-12 h-12 rounded-full flex items-center justify-center mb-6"><Heart className="w-6 h-6 text-sky-500" /></div>
            <h3 className="text-xl font-bold text-slate-900 mb-4">Emotional Impact</h3>
            <p className="text-slate-600 leading-relaxed font-light">{analysis.emotional_impact}</p>
          </div>
          
          <div className="bg-white p-8 rounded-3xl border-t-4 border-t-indigo-400 border-x border-b border-slate-200 shadow-sm hover:shadow-lg transition-all duration-300">
            <div className="bg-indigo-50 w-12 h-12 rounded-full flex items-center justify-center mb-6"><Brain className="w-6 h-6 text-indigo-500" /></div>
            <h3 className="text-xl font-bold text-slate-900 mb-4">Core Beliefs</h3>
            <ul className="space-y-3">
              {analysis.underlying_beliefs.map((b, i) => (
                <li key={i} className="flex items-start text-slate-600 font-light"><span className="text-indigo-400 mr-3 mt-1 font-bold">•</span><span>{b}</span></li>
              ))}
            </ul>
          </div>

          <div className="bg-white p-8 rounded-3xl border-t-4 border-t-cyan-400 border-x border-b border-slate-200 shadow-sm hover:shadow-lg transition-all duration-300">
            <div className="bg-cyan-50 w-12 h-12 rounded-full flex items-center justify-center mb-6"><Clock className="w-6 h-6 text-cyan-500" /></div>
            <h3 className="text-xl font-bold text-slate-900 mb-4">Possible Triggers</h3>
            <div className="flex flex-wrap gap-2">
              {analysis.triggers.map((t, i) => (
                <span key={i} className="bg-slate-50 border border-slate-100 text-slate-700 px-4 py-2 rounded-xl text-sm font-medium">{t}</span>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-8 border border-slate-200 shadow-[0_8px_30px_rgb(0,0,0,0.04)] mb-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="text-2xl font-bold text-slate-900 mb-2">Therapeutic Lenses</h3>
              <p className="text-slate-500 text-sm">Select the psychological frameworks you want to view this thought through.</p>
            </div>
            <div className="bg-blue-50 text-blue-600 px-4 py-2 rounded-full text-sm font-bold flex items-center">
              <Sparkles className="w-4 h-4 mr-2" /> {selectedTherapies.length} Selected
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.keys(THERAPY_FULL_NAMES).map((key) => {
              const isSelected = selectedTherapies.includes(key);
              const isRecommended = analysis.recommended_therapies.includes(key);
              return (
                <button 
                  key={key} onClick={() => toggleTherapy(key)} 
                  className={`relative p-5 rounded-2xl text-left transition-all duration-300 border-2 overflow-hidden group ${
                    isSelected ? 'border-blue-500 bg-blue-50/50 shadow-md transform scale-[1.02]' : 'border-slate-100 bg-white hover:border-blue-200 hover:bg-slate-50'
                  }`}
                >
                  {isSelected && <div className="absolute top-0 right-0 w-16 h-16 bg-blue-500 rounded-bl-full -z-10 opacity-10"></div>}
                  {isRecommended && <div className="absolute top-3 right-3 w-2.5 h-2.5 bg-teal-400 rounded-full shadow-[0_0_8px_rgba(45,212,191,0.8)]"></div>}
                  
                  <div className="flex justify-between items-center mb-2">
                     <span className={`font-black text-xl tracking-tight ${isSelected ? 'text-blue-700' : 'text-slate-800'}`}>{key}</span>
                     {isSelected && <CheckCircle className="w-5 h-5 text-blue-600" />}
                  </div>
                  <span className={`text-xs block font-medium ${isSelected ? 'text-blue-600/80' : 'text-slate-400 group-hover:text-slate-500'}`}>{THERAPY_FULL_NAMES[key]}</span>
                </button>
              );
            })}
          </div>

          {analysis.recommended_therapies.some(t => selectedTherapies.includes(t)) && (
            <div className="mt-8 bg-slate-50 rounded-2xl p-6 border border-slate-100">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center"><Brain className="w-4 h-4 mr-2" /> AI Rationale for Selections</p>
              <div className="space-y-3">
                {analysis.recommended_therapies.map((therapy) => (
                  selectedTherapies.includes(therapy) && (
                    <div key={therapy} className="text-sm flex flex-col md:flex-row md:gap-3 bg-white p-3 rounded-xl shadow-sm border border-slate-100">
                      <span className="font-bold text-blue-800 whitespace-nowrap bg-blue-50 px-2 py-1 rounded-lg">{therapy}</span>
                      <span className="text-slate-600 self-center">{analysis.therapy_rationales?.[therapy]}</span>
                    </div>
                  )
                ))}
              </div>
            </div>
          )}
        </div>

        <button onClick={generateCandidates} disabled={loading || selectedTherapies.length === 0} 
          className="w-full bg-slate-900 hover:bg-blue-600 text-white font-extrabold text-xl py-6 rounded-3xl transition-all duration-300 shadow-xl hover:shadow-blue-500/25 disabled:opacity-50 flex items-center justify-center transform hover:-translate-y-1"
        >
          {loading ? <><RotateCcw className="animate-spin w-6 h-6 mr-3" /> Generating new perspectives...</> : <>Generate Reframes <ArrowRight className="w-6 h-6 ml-3" /></>}
        </button>
      </div>
    );
  };

  const renderStep4 = () => {
    if (candidates.length === 0) return null;
    return (
      <div className="lumina-slide-up w-full max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">New Perspectives</h2>
          <p className="text-lg text-slate-500 font-light">Explore these alternative viewpoints. Select the one that brings you the most relief.</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 mb-12">
          {candidates.map((candidate, idx) => {
             const isSelected = selectedReframe === idx;
             return (
              <div key={idx} onClick={() => setSelectedReframe(idx)} 
                className={`relative p-8 rounded-3xl cursor-pointer transition-all duration-300 border-2 overflow-hidden group ${
                  isSelected ? 'border-blue-500 bg-white shadow-2xl scale-[1.02] ring-4 ring-blue-500/10' : 'border-slate-200 bg-white hover:border-blue-300 hover:shadow-xl'
                }`}
              >
                {isSelected && <div className="absolute top-0 left-0 w-full h-2 bg-blue-500"></div>}
                
                <div className="flex items-center justify-between mb-6">
                  <span className={`px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${isSelected ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500 group-hover:bg-blue-50 group-hover:text-blue-600'}`}>
                    {candidate.therapy}
                  </span>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-slate-200 bg-white'}`}>
                    {isSelected && <Check className="w-5 h-5 text-blue-600" />}
                  </div>
                </div>

                <p className={`text-2xl font-medium leading-relaxed mb-8 transition-colors ${isSelected ? 'text-slate-900' : 'text-slate-700'}`}>
                  "{candidate.reframe}"
                </p>

                <div className="bg-slate-50 p-5 rounded-2xl border border-slate-100">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Why it helps</p>
                  <p className="text-sm text-slate-600">{candidate.rationale}</p>
                </div>

                {candidate.evaluation && (
                  <div className="mt-6 pt-6 border-t border-slate-100 grid grid-cols-4 gap-2">
                    {Object.entries(candidate.evaluation).map(([key, value]) => (
                      <div key={key} className="text-center">
                        <p className="text-[10px] text-slate-400 uppercase font-bold mb-2">{key}</p>
                        <div className="flex justify-center gap-0.5">
                          {[...Array(5)].map((_, i) => <div key={i} className={`w-1.5 h-1.5 rounded-full ${i < value ? (isSelected ? 'bg-blue-500' : 'bg-slate-400') : 'bg-slate-200'}`}></div>)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="flex flex-col sm:flex-row gap-4 max-w-2xl mx-auto">
          <button onClick={reset} className="flex-1 px-8 py-5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-2xl font-bold text-lg transition-all flex items-center justify-center">
             <RotateCcw className="w-5 h-5 mr-3" /> Start Over
          </button>
          <button onClick={saveSelection} disabled={selectedReframe === null} className="flex-[2] px-8 py-5 bg-slate-900 hover:bg-blue-600 text-white rounded-2xl font-bold text-lg disabled:opacity-50 transition-all flex items-center justify-center shadow-lg">
             Adopt This Perspective <ArrowRight className="ml-3 w-6 h-6" />
          </button>
        </div>
      </div>
    );
  };

  const renderStep5 = () => {
    if (selectedReframe === null || !candidates[selectedReframe]) return null;
    return (
      <div className="lumina-fade-in w-full max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-tr from-teal-400 to-emerald-400 text-white rounded-full mb-6 shadow-xl shadow-teal-500/30">
            <CheckCircle className="w-12 h-12" />
          </div>
          <h2 className="text-4xl font-extrabold text-slate-900 mb-4 tracking-tight">Perspective Shifted</h2>
          <p className="text-lg text-slate-500 font-light">Take a deep breath. Notice how this new thought feels.</p>
        </div>

        {reframeHistory.length > 0 && (
          <div className="bg-white rounded-3xl p-8 md:p-12 border border-slate-200 shadow-[0_8px_30px_rgb(0,0,0,0.06)] mb-12 relative overflow-hidden">
            {/* Background decoration */}
            <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-blue-500 via-cyan-400 to-teal-400"></div>

            <div className="grid md:grid-cols-2 gap-8 mb-12">
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Original Thought</p>
                <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 h-full">
                  <p className="text-lg text-slate-500 line-through decoration-slate-300">"{formData.thought}"</p>
                </div>
              </div>
              <div>
                 <p className="text-xs font-bold text-blue-500 uppercase tracking-widest mb-3 flex items-center justify-between">
                    New Perspective 
                    <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-[10px]">{candidates[selectedReframe].therapy}</span>
                 </p>
                 <div className="bg-blue-50/50 p-6 rounded-2xl border border-blue-100 h-full flex items-center">
                    <p className="text-2xl font-bold text-slate-800 leading-snug">"{reframeHistory[activeHistoryIndex].reframe}"</p>
                 </div>
              </div>
            </div>

            {reframeHistory.length > 1 && (
              <div className="mb-8">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Version History</p>
                <div className="flex space-x-2 overflow-x-auto pb-2 scrollbar-hide">
                  {reframeHistory.map((_, idx) => (
                    <button key={idx} onClick={() => setActiveHistoryIndex(idx)} 
                      className={`px-5 py-2.5 text-sm font-bold rounded-xl transition-all whitespace-nowrap shadow-sm border ${
                        activeHistoryIndex === idx ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      {idx === 0 ? 'Original Concept' : `Refinement ${idx}`}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-slate-50 rounded-2xl p-6 border border-slate-100 flex flex-col md:flex-row gap-6 items-start md:items-center justify-between">
              <div className="flex items-start max-w-xl">
                 <Brain className="w-6 h-6 text-indigo-500 mr-4 mt-1 flex-shrink-0" />
                 <div>
                    <p className="text-sm font-bold text-slate-900 mb-1">AI Reflection</p>
                    <p className="text-sm text-slate-600 leading-relaxed">{aiFeedback_summ}</p>
                 </div>
              </div>
              
              <button onClick={handleImprove} disabled={isImproving || improveCount >= 5 || activeHistoryIndex !== reframeHistory.length - 1} 
                className="w-full md:w-auto px-6 py-3 bg-white border border-slate-200 text-slate-700 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 rounded-xl text-sm font-bold disabled:opacity-50 transition-all flex items-center justify-center whitespace-nowrap shadow-sm"
              >
                {isImproving ? <RotateCcw className="animate-spin w-4 h-4 mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
                {improveCount >= 5 ? 'Max Refinements Reached' : 'Refine Further'}
              </button>
            </div>
          </div>
        )}

        {!isFeedbackSubmitted ? (
          <div className="bg-white rounded-3xl p-8 md:p-12 border border-slate-200 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
            <div className="mb-10 text-center max-w-xl mx-auto">
              <h3 className="text-2xl font-bold text-slate-900 mb-3">How does this feel?</h3>
              <p className="text-slate-500">Your feedback helps tailor the AI's future responses to be more effective for clinical reframing.</p>
            </div>
            
            <div className="space-y-8">
              {[
                { key: 'belief', text: "I genuinely believe in this new perspective." },
                { key: 'helpfulness', text: "This perspective helps me reduce my distress." },
                { key: 'recall', text: "I will likely recall this perspective next time." },
                { key: 'learning', text: "This exercise improved my ability to cope." }
              ].map((q, index) => (
                <div key={q.key} className="p-6 bg-slate-50 rounded-2xl border border-slate-100">
                  <p className="text-slate-800 font-bold mb-5 flex items-center"><span className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs mr-3">{index + 1}</span> {q.text}</p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {LIKERT_OPTIONS.map((opt) => {
                       const isSelected = feedback[q.key as keyof FeedbackState] === opt.value;
                       return (
                        <button key={opt.value} onClick={() => handleFeedbackChange(q.key as keyof FeedbackState, opt.value)} 
                          className={`py-3 px-2 text-xs md:text-sm font-bold rounded-xl transition-all duration-200 ${
                            isSelected ? 'bg-blue-600 text-white shadow-lg scale-105 border-transparent' : 'bg-white text-slate-600 border border-slate-200 hover:border-blue-300 hover:bg-blue-50 shadow-sm'
                          }`}
                        >
                          {opt.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-10 flex justify-center">
               <button onClick={submitFeedback} disabled={!feedback.belief || !feedback.helpfulness || !feedback.recall || !feedback.learning} 
                 className="px-12 py-5 bg-slate-900 text-white rounded-full font-extrabold text-lg disabled:opacity-50 disabled:scale-100 hover:bg-blue-600 transition-all transform hover:-translate-y-1 shadow-xl hover:shadow-blue-500/30"
               >
                  Complete Session
               </button>
            </div>
          </div>
        ) : (
          <div className="bg-teal-50 border border-teal-100 rounded-3xl p-12 text-center shadow-sm">
            <div className="inline-flex p-5 bg-teal-100 rounded-full mb-6"><Heart className="w-10 h-10 text-teal-600 fill-teal-600" /></div>
            <h3 className="text-3xl font-bold text-teal-900 mb-4">Thank You</h3>
            <p className="text-teal-700 text-lg max-w-lg mx-auto">Your feedback has been saved. We hope this tool continues to bring you clarity and peace.</p>
          </div>
        )}

        <div className="mt-12 text-center">
           <button onClick={reset} className="inline-flex items-center text-slate-500 hover:text-slate-800 font-bold transition-colors">
              <RotateCcw className="w-5 h-5 mr-2" /> Start a new reflection
           </button>
        </div>
      </div>
    );
  };

  // --- Home & Static Pages ---
  const renderHome = () => (
    <div className="pt-20 min-h-screen flex items-center justify-center bg-slate-50 relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] bg-blue-200/40 rounded-full mix-blend-multiply filter blur-[100px] animate-blob"></div>
      <div className="absolute top-[20%] right-[-10%] w-[40vw] h-[40vw] bg-cyan-200/40 rounded-full mix-blend-multiply filter blur-[100px] animate-blob animation-delay-2000"></div>
      
      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center lumina-fade-in">
        <div className="inline-flex items-center px-4 py-2 bg-white rounded-full shadow-sm border border-slate-100 mb-8">
           <Sparkles className="w-4 h-4 text-blue-500 mr-2" />
           <span className="text-sm font-bold text-slate-600 uppercase tracking-widest">Clinical-Grade Reframing</span>
        </div>
        <h1 className="text-6xl md:text-8xl font-black text-slate-900 tracking-tight leading-[1.1] mb-8">
          Clear your mind.<br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-500">Find your center.</span>
        </h1>
        <p className="text-xl md:text-2xl text-slate-500 font-light mb-12 max-w-3xl mx-auto leading-relaxed">
          An interactive, visually guided workspace designed to help you untangle cognitive distortions using clinical psychology and AI.
        </p>
        <button onClick={() => setCurrentPage('app')} className="px-12 py-6 bg-slate-900 text-white rounded-full font-bold text-xl hover:bg-blue-600 hover:shadow-2xl hover:shadow-blue-500/40 transition-all duration-300 transform hover:-translate-y-1 flex items-center justify-center mx-auto">
          Open Workspace <ArrowRight className="ml-3 w-6 h-6" />
        </button>
      </div>
    </div>
  );

  const renderScience = () => (
    <div className="lumina-fade-in w-full max-w-4xl mx-auto px-6 py-12 md:py-20">
      <div className="text-center mb-16">
        <p className="text-blue-600 font-bold tracking-widest uppercase mb-4 text-sm">The Science</p>
        <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 mb-6 tracking-tight">Built on Research. <br/>Designed for You.</h1>
        <p className="text-lg text-slate-500 font-light max-w-2xl mx-auto">
          Lumina is not just a chatbot. It is a structured environment built on advanced clinical benchmarks, designed to help you build mental flexibility.
        </p>
      </div>

      <div className="space-y-12">
        <div className="bg-white rounded-3xl p-8 md:p-10 border border-slate-200 shadow-sm">
          <div className="flex items-center mb-6">
            <div className="bg-sky-50 w-12 h-12 rounded-full flex items-center justify-center mr-4">
              <BookOpen className="w-6 h-6 text-sky-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">1. The Cognitive Model</h2>
          </div>
          <p className="text-slate-600 leading-relaxed font-light mb-4">
            At its core, this approach is grounded in the cognitive model, which posits that our emotional responses and subsequent behavioral patterns are not determined directly by objective external events, but rather by our subjective cognitive interpretations of those events[cite: 230].
          </p>
          <p className="text-slate-600 leading-relaxed font-light">
            When triggered by stressful situations, human brains often rely on flawed mental heuristics. This results in <strong>Cognitive Distortions</strong>—such as "All-or-nothing thinking" or "Personalization"—which create a chronically negative internal narrative[cite: 25, 739, 754]. Lumina uses structured Cognitive Behavioral Therapy (CBT) protocols to dismantle these logical fallacies.
          </p>
        </div>

        {/* <div className="bg-white rounded-3xl p-8 md:p-10 border border-slate-200 shadow-sm">
          <div className="flex items-center mb-6">
            <div className="bg-indigo-50 w-12 h-12 rounded-full flex items-center justify-center mr-4">
              <Layers className="w-6 h-6 text-indigo-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">2. The CBT-MACR Architecture</h2>
          </div>
          <p className="text-slate-600 leading-relaxed font-light mb-6">
            Standard Large Language Models (LLMs) often lack the deep psychological nuance required for safe interventions, occasionally validating harmful thoughts or providing generic advice[cite: 4]. To solve this, Lumina employs the <strong>CBT-MACR (CBT-based Multi-Agent Cognitive Reframing)</strong> framework[cite: 628]. 
            This decentralizes the therapeutic process into specialized AI agents:
          </p>
          <ul className="space-y-4">
            <li className="flex items-start">
              <CheckCircle className="w-5 h-5 text-indigo-400 mr-3 mt-1 flex-shrink-0" />
              <p className="text-slate-700 font-light"><strong>Subjectivity Assessment Agent:</strong> Meticulously delineates objective factual reality from subjective emotional interpretations to establish a neutral baseline[cite: 673, 675].</p>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-5 h-5 text-indigo-400 mr-3 mt-1 flex-shrink-0" />
              <p className="text-slate-700 font-light"><strong>Contrastive Reasoning Agent:</strong> Automates Socratic questioning by simultaneously constructing logical streams that both support and contradict the user's negative assumptions[cite: 693, 694].</p>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-5 h-5 text-indigo-400 mr-3 mt-1 flex-shrink-0" />
              <p className="text-slate-700 font-light"><strong>Schema Analysis Agent:</strong> Synthesizes the data to extract the latent cognitive schema, exposing the root-cause explanatory factor driving the psychological distress[cite: 726, 734].</p>
            </li>
          </ul>
        </div> */}

        <div className="bg-white rounded-3xl p-8 md:p-10 border border-slate-200 shadow-sm">
          <div className="flex items-center mb-6">
            <div className="bg-indigo-50 w-12 h-12 rounded-full flex items-center justify-center mr-4">
              <Layers className="w-6 h-6 text-indigo-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">2. The CBT-MACR Architecture</h2>
          </div>
          
          <p className="text-slate-600 leading-relaxed font-light mb-8">
            Standard Large Language Models (LLMs) often lack the deep psychological nuance required for safe interventions, occasionally validating harmful thoughts or providing generic advice. To solve this, Lumina employs the <strong>CBT-MACR (CBT-based Multi-Agent Cognitive Reframing)</strong> framework. 
            This decentralizes the therapeutic process into specialized AI agents:
          </p>

          {/* --- KHỐI HIỂN THỊ ẢNH FRAMEWORK --- */}
          <div className="mb-10 bg-slate-50 border border-slate-100 rounded-2xl p-4 md:p-6 flex justify-center shadow-inner">
            {/* Lưu ý: Đưa ảnh sơ đồ của bạn vào thư mục 'public' (nếu dùng Vite/React) và đổi tên file tương ứng */}
            <img 
              src={frameworkImg}
              alt="Overview of the CBT-MACR Framework" 
              className="max-w-full h-auto rounded-xl object-contain mix-blend-multiply hover:scale-[1.02] transition-transform duration-500"
            />
          </div>

          <ul className="space-y-5">
            <li className="flex items-start bg-white p-4 rounded-2xl border border-slate-50 hover:border-indigo-100 hover:shadow-sm transition-all">
              <CheckCircle className="w-6 h-6 text-indigo-400 mr-4 mt-0.5 flex-shrink-0" />
              <p className="text-slate-700 font-light leading-relaxed">
                <strong className="text-slate-900">Subjectivity Assessment Agent:</strong> Meticulously delineates objective factual reality from subjective emotional interpretations to establish a neutral baseline.
              </p>
            </li>
            <li className="flex items-start bg-white p-4 rounded-2xl border border-slate-50 hover:border-indigo-100 hover:shadow-sm transition-all">
              <CheckCircle className="w-6 h-6 text-indigo-400 mr-4 mt-0.5 flex-shrink-0" />
              <p className="text-slate-700 font-light leading-relaxed">
                <strong className="text-slate-900">Contrastive Reasoning Agent:</strong> Automates Socratic questioning by simultaneously constructing logical streams that both support and contradict the user's negative assumptions.
              </p>
            </li>
            <li className="flex items-start bg-white p-4 rounded-2xl border border-slate-50 hover:border-indigo-100 hover:shadow-sm transition-all">
              <CheckCircle className="w-6 h-6 text-indigo-400 mr-4 mt-0.5 flex-shrink-0" />
              <p className="text-slate-700 font-light leading-relaxed">
                <strong className="text-slate-900">Schema Analysis Agent:</strong> Synthesizes the data to extract the latent cognitive schema, exposing the root-cause explanatory factor driving the psychological distress.
              </p>
            </li>
          </ul>
        </div>

        <div className="bg-white rounded-3xl p-8 md:p-10 border border-slate-200 shadow-sm">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-6">
            <div className="flex items-center">
              <div className="bg-teal-50 w-12 h-12 rounded-full flex items-center justify-center mr-4">
                <ShieldCheck className="w-6 h-6 text-teal-500" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900">3. In-Context Refinement Feedback</h2>
            </div>
          </div>
          <p className="text-slate-600 leading-relaxed font-light mb-4">
            Lumina never gives you its first guess. Because initial generations from language models often lack perfect clinical nuance, the system employs a rigorous <strong>In-context Refinement Feedback</strong> mechanism governed by a Supervisor Agent[cite: 781, 783].
          </p>
          <p className="text-slate-600 leading-relaxed font-light mb-6">
            This agent systematically scores multiple generated candidates using a hybrid objective function before presenting the final reframe to you, focusing on three critical pillars:
          </p>
          
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-slate-50 p-5 rounded-2xl border border-slate-100">
              <Scale className="w-5 h-5 text-teal-600 mb-3" />
              <h4 className="font-bold text-slate-800 text-sm mb-2">Clinical Assessment</h4>
              <p className="text-xs text-slate-600 font-light leading-relaxed">Evaluates the reframe against Beck's principles of Socratic Questioning to ensure therapeutic safety and distortion regulation[cite: 787].</p>
            </div>
            <div className="bg-slate-50 p-5 rounded-2xl border border-slate-100">
              <Activity className="w-5 h-5 text-teal-600 mb-3" />
              <h4 className="font-bold text-slate-800 text-sm mb-2">Semantic Alignment</h4>
              <p className="text-xs text-slate-600 font-light leading-relaxed">Quantifies similarity between the input and the generated reframe to actively penalize "hallucinations"[cite: 797].</p>
            </div>
            <div className="bg-slate-50 p-5 rounded-2xl border border-slate-100">
              <Heart className="w-5 h-5 text-teal-600 mb-3" />
              <h4 className="font-bold text-slate-800 text-sm mb-2">Stylistic Alignment</h4>
              <p className="text-xs text-slate-600 font-light leading-relaxed">Ensures the response adheres to a professional therapeutic tone, matching emotional valence and subjectivity of human experts[cite: 804].</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <style>{`
        /* Custom Animations */
        @keyframes luminaFadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes luminaSlideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes luminaSlideDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        .lumina-fade-in { animation: luminaFadeIn 0.6s ease-out forwards; }
        .lumina-slide-up { animation: luminaSlideUp 0.6s ease-out forwards; }
        .lumina-slide-down { animation: luminaSlideDown 0.6s ease-out forwards; }
        
        /* Hide scrollbar for history tabs */
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>
      
      <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-blue-200 selection:text-blue-900 pb-24">
        {renderNavigation()}
        
        <main className="pt-28">
          {currentPage === 'home' && renderHome()}
          {currentPage === 'science' && renderScience()}
          {currentPage === 'app' && (
            <div className="px-4 sm:px-6 lg:px-8">
              <CustomStepper />
              {error && (
                <div className="max-w-4xl mx-auto mb-8 bg-red-50 border border-red-200 rounded-2xl p-5 flex items-start shadow-sm lumina-slide-down">
                  <XCircle className="w-6 h-6 text-red-500 mr-3 mt-0.5 flex-shrink-0" />
                  <p className="text-red-800 font-medium">{error}</p>
                </div>
              )}
              {step === 1 && renderStep1()}
              {step === 2 && renderStep2()}
              {step === 3 && renderStep3()}
              {step === 4 && renderStep4()}
              {step === 5 && renderStep5()}
            </div>
          )}
        </main>
      </div>
    </>
  );
}