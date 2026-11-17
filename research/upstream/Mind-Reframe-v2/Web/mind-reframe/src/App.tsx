// import React, { useState, useEffect } from 'react';
// import { 
//   Brain, Sparkles, CheckCircle, XCircle, ChevronRight, RotateCcw, 
//   ThumbsUp, Award, Clock, Heart, Shield, Lightbulb, ArrowRight,
//   MessageCircle, TrendingUp, Users, Menu, X
// } from 'lucide-react';

// // --- Type Definitions (Interfaces) ---
// interface DistortionResult {
//   has_distortion: boolean;
//   distortion_types: string[];
//   explanation: string;
// }

// interface AnalysisResult {
//   emotional_impact: string;
//   underlying_beliefs: string[];
//   triggers: string[];
//   recommended_therapies: string[];
// }

// interface Candidate {
//   therapy: string;
//   reframe: string;
//   rationale: string;
//   evaluation?: {
//     [key: string]: number; // Allow dynamic evaluation keys like 'empathy', 'logic'
//   };
// }

// interface FormData {
//   situation: string;
//   thought: string;
// }

// const API_BASE_URL = 'http://localhost:8000/api'; 

// const CognitiveReframingPlatform = () => {
//   const [currentPage, setCurrentPage] = useState<string>('home');
//   const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
//   const [step, setStep] = useState<number>(1);
  
//   const [formData, setFormData] = useState<FormData>({
//     situation: '',
//     thought: ''
//   });

//   // State with explicit types allowing null
//   const [sessionId, setSessionId] = useState<string | null>(null);
//   const [distortionResult, setDistortionResult] = useState<DistortionResult | null>(null);
//   const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
//   const [candidates, setCandidates] = useState<Candidate[]>([]); // Array of Candidates
//   const [selectedReframe, setSelectedReframe] = useState<number | null>(null);
//   const [loading, setLoading] = useState<boolean>(false);
//   const [error, setError] = useState<string | null>(null);

//   useEffect(() => {
//     // Initialize session
//     const initSession = async () => {
//       try {
//         const response = await fetch(`${API_BASE_URL}/session/init`, {
//           method: 'POST',
//           headers: { 'Content-Type': 'application/json' }
//         });
//         const data = await response.json();
//         setSessionId(data.session_id);
//       } catch (err) {
//         console.error('Session init failed:', err);
//         setSessionId('demo-session-' + Date.now());
//       }
//     };
//     initSession();
//   }, []);

//   const Navigation = () => (
//     <nav className="bg-white/80 backdrop-blur-md fixed w-full top-0 z-50 shadow-sm">
//       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
//         <div className="flex justify-between items-center h-16">
//           <div className="flex items-center">
//             <Brain className="w-8 h-8 text-indigo-600 mr-2" />
//             <span className="text-xl font-bold text-gray-900">MindReframe</span>
//           </div>
          
//           <div className="hidden md:flex space-x-8">
//             <button onClick={() => setCurrentPage('home')} className="text-gray-700 hover:text-indigo-600 transition">
//               Home
//             </button>
//             <button onClick={() => setCurrentPage('about')} className="text-gray-700 hover:text-indigo-600 transition">
//               About
//             </button>
//             <button onClick={() => setCurrentPage('therapies')} className="text-gray-700 hover:text-indigo-600 transition">
//               Therapies
//             </button>
//             <button onClick={() => setCurrentPage('app')} className="bg-indigo-600 text-white px-6 py-2 rounded-full hover:bg-indigo-700 transition">
//               Get Started
//             </button>
//           </div>

//           <button 
//             className="md:hidden"
//             onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
//           >
//             {mobileMenuOpen ? <X /> : <Menu />}
//           </button>
//         </div>

//         {mobileMenuOpen && (
//           <div className="md:hidden pb-4">
//             <button onClick={() => { setCurrentPage('home'); setMobileMenuOpen(false); }} className="block w-full text-left py-2 text-gray-700">
//               Home
//             </button>
//             <button onClick={() => { setCurrentPage('about'); setMobileMenuOpen(false); }} className="block w-full text-left py-2 text-gray-700">
//               About
//             </button>
//             <button onClick={() => { setCurrentPage('therapies'); setMobileMenuOpen(false); }} className="block w-full text-left py-2 text-gray-700">
//               Therapies
//             </button>
//             <button onClick={() => { setCurrentPage('app'); setMobileMenuOpen(false); }} className="block w-full text-left py-2 text-indigo-600 font-semibold">
//               Get Started
//             </button>
//           </div>
//         )}
//       </div>
//     </nav>
//   );

//   const HomePage = () => (
//     <div className="pt-16">
//       {/* Hero Section */}
//       <section className="relative min-h-screen flex items-center bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
//         <div className="absolute inset-0 overflow-hidden">
//           <div className="absolute -top-1/2 -right-1/2 w-full h-full bg-gradient-to-br from-indigo-200/30 to-transparent rounded-full blur-3xl"></div>
//           <div className="absolute -bottom-1/2 -left-1/2 w-full h-full bg-gradient-to-tr from-purple-200/30 to-transparent rounded-full blur-3xl"></div>
//         </div>

//         <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
//           <div className="grid md:grid-cols-2 gap-12 items-center">
//             <div>
//               <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
//                 Transform Your
//                 <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600"> Thoughts</span>
//               </h1>
//               <p className="text-xl text-gray-600 mb-8">
//                 Evidence-based cognitive reframing powered by AI and multiple therapeutic approaches. 
//                 Find the perspective that works for you.
//               </p>
//               <div className="flex flex-col sm:flex-row gap-4">
//                 <button 
//                   onClick={() => setCurrentPage('app')}
//                   className="bg-indigo-600 text-white px-8 py-4 rounded-full font-semibold hover:bg-indigo-700 transition shadow-lg hover:shadow-xl flex items-center justify-center"
//                 >
//                   Start Your Journey
//                   <ArrowRight className="ml-2 w-5 h-5" />
//                 </button>
//                 <button 
//                   onClick={() => setCurrentPage('about')}
//                   className="bg-white text-indigo-600 px-8 py-4 rounded-full font-semibold hover:bg-gray-50 transition shadow-lg flex items-center justify-center"
//                 >
//                   Learn More
//                 </button>
//               </div>
//             </div>

//             <div className="hidden md:block">
//               <div className="relative">
//                 <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-3xl blur-2xl opacity-20"></div>
//                 <div className="relative bg-white rounded-3xl shadow-2xl p-8">
//                   <div className="space-y-6">
//                     <div className="flex items-center space-x-4">
//                       <div className="bg-indigo-100 p-3 rounded-full">
//                         <Brain className="w-6 h-6 text-indigo-600" />
//                       </div>
//                       <div>
//                         <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
//                         <div className="h-3 bg-gray-100 rounded w-24"></div>
//                       </div>
//                     </div>
//                     <div className="flex items-center space-x-4">
//                       <div className="bg-purple-100 p-3 rounded-full">
//                         <Sparkles className="w-6 h-6 text-purple-600" />
//                       </div>
//                       <div>
//                         <div className="h-4 bg-gray-200 rounded w-40 mb-2"></div>
//                         <div className="h-3 bg-gray-100 rounded w-28"></div>
//                       </div>
//                     </div>
//                     <div className="flex items-center space-x-4">
//                       <div className="bg-pink-100 p-3 rounded-full">
//                         <Heart className="w-6 h-6 text-pink-600" />
//                       </div>
//                       <div>
//                         <div className="h-4 bg-gray-200 rounded w-36 mb-2"></div>
//                         <div className="h-3 bg-gray-100 rounded w-32"></div>
//                       </div>
//                     </div>
//                   </div>
//                 </div>
//               </div>
//             </div>
//           </div>
//         </div>
//       </section>

//       {/* Features Section */}
//       <section className="py-20 bg-white">
//         <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
//           <div className="text-center mb-16">
//             <h2 className="text-4xl font-bold text-gray-900 mb-4">Why MindReframe?</h2>
//             <p className="text-xl text-gray-600">Science-backed features designed for your well-being</p>
//           </div>

//           <div className="grid md:grid-cols-3 gap-8">
//             <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 p-8 rounded-2xl">
//               <div className="bg-indigo-600 w-14 h-14 rounded-full flex items-center justify-center mb-6">
//                 <Shield className="w-7 h-7 text-white" />
//               </div>
//               <h3 className="text-xl font-bold text-gray-900 mb-3">Evidence-Based</h3>
//               <p className="text-gray-600">
//                 Built on proven therapeutic frameworks including CBT, ACT, DBT, and 9 other modalities studied in clinical research.
//               </p>
//             </div>

//             <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-8 rounded-2xl">
//               <div className="bg-purple-600 w-14 h-14 rounded-full flex items-center justify-center mb-6">
//                 <Users className="w-7 h-7 text-white" />
//               </div>
//               <h3 className="text-xl font-bold text-gray-900 mb-3">Personalized</h3>
//               <p className="text-gray-600">
//                 Choose the therapeutic approach that resonates with you. Different perspectives for different people.
//               </p>
//             </div>

//             <div className="bg-gradient-to-br from-pink-50 to-pink-100 p-8 rounded-2xl">
//               <div className="bg-pink-600 w-14 h-14 rounded-full flex items-center justify-center mb-6">
//                 <Lightbulb className="w-7 h-7 text-white" />
//               </div>
//               <h3 className="text-xl font-bold text-gray-900 mb-3">AI-Powered</h3>
//               <p className="text-gray-600">
//                 Advanced language models trained to provide empathetic, safe, and clinically appropriate reframes.
//               </p>
//             </div>
//           </div>
//         </div>
//       </section>

//       {/* How It Works */}
//       <section className="py-20 bg-gradient-to-br from-gray-50 to-gray-100">
//         <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
//           <div className="text-center mb-16">
//             <h2 className="text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
//             <p className="text-xl text-gray-600">Your journey to healthier thinking in 5 simple steps</p>
//           </div>

//           <div className="grid md:grid-cols-5 gap-8">
//             {[
//               { icon: MessageCircle, title: 'Share', desc: 'Tell us your situation and thoughts' },
//               { icon: Brain, title: 'Detect', desc: 'We identify cognitive distortions' },
//               { icon: TrendingUp, title: 'Analyze', desc: 'Deep analysis of thought patterns' },
//               { icon: Sparkles, title: 'Reframe', desc: 'Multiple therapeutic perspectives' },
//               { icon: Heart, title: 'Choose', desc: 'Select what works for you' }
//             ].map((item, idx) => (
//               <div key={idx} className="text-center">
//                 <div className="bg-white w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
//                   <item.icon className="w-10 h-10 text-indigo-600" />
//                 </div>
//                 <h3 className="font-bold text-gray-900 mb-2">{item.title}</h3>
//                 <p className="text-sm text-gray-600">{item.desc}</p>
//               </div>
//             ))}
//           </div>
//         </div>
//       </section>

//       {/* CTA Section */}
//       <section className="py-20 bg-gradient-to-r from-indigo-600 to-purple-600">
//         <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
//           <h2 className="text-4xl font-bold text-white mb-6">Ready to Transform Your Thinking?</h2>
//           <p className="text-xl text-indigo-100 mb-8">
//             Join thousands who have discovered healthier perspectives through cognitive reframing
//           </p>
//           <button 
//             onClick={() => setCurrentPage('app')}
//             className="bg-white text-indigo-600 px-10 py-4 rounded-full font-bold text-lg hover:bg-gray-100 transition shadow-xl inline-flex items-center"
//           >
//             Start Free Today
//             <ArrowRight className="ml-2 w-5 h-5" />
//           </button>
//         </div>
//       </section>
//     </div>
//   );

//   const AboutPage = () => (
//     <div className="pt-24 pb-20 min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
//       <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
//         <h1 className="text-5xl font-bold text-gray-900 mb-8">About MindReframe</h1>
        
//         <div className="bg-white rounded-3xl shadow-xl p-8 mb-8">
//           <h2 className="text-2xl font-bold text-gray-900 mb-4">Our Mission</h2>
//           <p className="text-gray-700 mb-4">
//             MindReframe combines cutting-edge AI technology with evidence-based psychotherapy to make mental health 
//             support accessible, personalized, and effective for everyone.
//           </p>
//           <p className="text-gray-700">
//             We believe that mental well-being should be within reach for all, and that the right perspective 
//             can make a profound difference in how we experience life's challenges.
//           </p>
//         </div>

//         <div className="bg-white rounded-3xl shadow-xl p-8 mb-8">
//           <h2 className="text-2xl font-bold text-gray-900 mb-4">The Science Behind It</h2>
//           <p className="text-gray-700 mb-4">
//             Our platform is built on <strong>ReframeBench</strong>, a comprehensive benchmark evaluating large 
//             language models across 12 distinct therapeutic modalities. This research ensures that our AI 
//             provides clinically appropriate and safe cognitive reframes.
//           </p>
//           <p className="text-gray-700">
//             We integrate principles from CBT, ACT, DBT, REBT, Schema Therapy, MBCT, CFT, Narrative Therapy, 
//             SFBT, and Motivational Interviewing - giving you access to diverse therapeutic perspectives.
//           </p>
//         </div>

//         <div className="bg-white rounded-3xl shadow-xl p-8">
//           <h2 className="text-2xl font-bold text-gray-900 mb-4">Important Note</h2>
//           <p className="text-gray-700">
//             MindReframe is designed as a self-help tool and educational resource. It is not a replacement 
//             for professional mental health care. If you're experiencing severe distress, please reach out 
//             to a qualified mental health professional.
//           </p>
//         </div>
//       </div>
//     </div>
//   );

//   const TherapiesPage = () => (
//     <div className="pt-24 pb-20 min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50">
//       <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
//         <h1 className="text-5xl font-bold text-gray-900 mb-4 text-center">Therapeutic Approaches</h1>
//         <p className="text-xl text-gray-600 mb-12 text-center">
//           Explore the diverse perspectives we offer
//         </p>

//         <div className="grid md:grid-cols-2 gap-6">
//           {[
//             { name: 'CBT', full: 'Cognitive Behavioral Therapy', color: 'indigo', desc: 'Challenge and change unhelpful thoughts through evidence and logic' },
//             { name: 'ACT', full: 'Acceptance & Commitment Therapy', color: 'purple', desc: 'Accept thoughts and commit to value-driven actions' },
//             { name: 'DBT', full: 'Dialectical Behavior Therapy', color: 'pink', desc: 'Balance acceptance with change through mindfulness' },
//             { name: 'REBT', full: 'Rational Emotive Behavior Therapy', color: 'blue', desc: 'Dispute irrational beliefs with rational alternatives' },
//             { name: 'MBCT', full: 'Mindfulness-Based Cognitive Therapy', color: 'green', desc: 'Combine mindfulness with cognitive techniques' },
//             { name: 'CFT', full: 'Compassion-Focused Therapy', color: 'rose', desc: 'Cultivate self-compassion and kindness' },
//             { name: 'Schema Therapy', full: 'Schema Therapy', color: 'violet', desc: 'Identify and heal deep-rooted patterns' },
//             { name: 'Narrative', full: 'Narrative Therapy', color: 'amber', desc: 'Rewrite your story and externalize problems' },
//             { name: 'SFBT', full: 'Solution-Focused Brief Therapy', color: 'cyan', desc: 'Focus on solutions rather than problems' },
//             { name: 'MI', full: 'Motivational Interviewing', color: 'emerald', desc: 'Enhance motivation for positive change' }
//           ].map((therapy, idx) => (
//             <div key={idx} className={`bg-gradient-to-br from-${therapy.color}-50 to-${therapy.color}-100 p-6 rounded-2xl border-2 border-${therapy.color}-200`}>
//               <h3 className="text-xl font-bold text-gray-900 mb-2">{therapy.name}</h3>
//               <p className="text-sm text-gray-600 mb-3 font-medium">{therapy.full}</p>
//               <p className="text-gray-700">{therapy.desc}</p>
//             </div>
//           ))}
//         </div>
//       </div>
//     </div>
//   );

//   const detectDistortion = async () => {
//     setLoading(true);
//     setError(null);
//     try {
//       const response = await fetch(`${API_BASE_URL}/detect`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({
//           session_id: sessionId,
//           situation: formData.situation,
//           thought: formData.thought
//         })
//       });
      
//       if (!response.ok) throw new Error('Detection failed');
      
//       const data = await response.json();
//       setDistortionResult(data);
//       if (data.has_distortion) {
//         setStep(2);
//       }
//     } catch (err) {
//       setError('Failed to detect distortions. Please try again.');
//       console.error(err);
//     }
//     setLoading(false);
//   };

//   const analyzeThought = async () => {
//     if (!distortionResult) return;
    
//     setLoading(true);
//     setError(null);
//     try {
//       const response = await fetch(`${API_BASE_URL}/analyze`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({
//           session_id: sessionId,
//           situation: formData.situation,
//           thought: formData.thought,
//           distortions: distortionResult.distortion_types
//         })
//       });
      
//       if (!response.ok) throw new Error('Analysis failed');
      
//       const data = await response.json();
//       setAnalysis(data);
//       setStep(3);
//     } catch (err) {
//       setError('Failed to analyze thought. Please try again.');
//       console.error(err);
//     }
//     setLoading(false);
//   };

//   const generateCandidates = async () => {
//     if (!analysis) return;

//     setLoading(true);
//     setError(null);
//     try {
//       const response = await fetch(`${API_BASE_URL}/reframe`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({
//           session_id: sessionId,
//           situation: formData.situation,
//           thought: formData.thought,
//           recommended_therapies: analysis.recommended_therapies
//         })
//       });
      
//       if (!response.ok) throw new Error('Generation failed');
      
//       const data = await response.json();
//       setCandidates(data.candidates);
//       setStep(4);
//     } catch (err) {
//       setError('Failed to generate reframes. Please try again.');
//       console.error(err);
//     }
//     setLoading(false);
//   };

//   const saveSelection = async () => {
//     if (selectedReframe === null) return;
    
//     try {
//       await fetch(`${API_BASE_URL}/save`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({
//           session_id: sessionId,
//           selected_reframe: candidates[selectedReframe],
//           original_thought: formData.thought
//         })
//       });
//       setStep(5);
//     } catch (err) {
//       console.error('Failed to save selection:', err);
//       setStep(5); // Continue anyway
//     }
//   };

//   const reset = () => {
//     setStep(1);
//     setFormData({ situation: '', thought: '' });
//     setDistortionResult(null);
//     setAnalysis(null);
//     setCandidates([]);
//     setSelectedReframe(null);
//     setError(null);
//   };

//   const AppPage = () => (
//     <div className="pt-20 pb-12 min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
//       <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
//         {/* Progress Bar */}
//         <div className="mb-8 bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-6">
//           <div className="flex items-center justify-between">
//             {['Input', 'Detect', 'Analyze', 'Reframe', 'Select'].map((label, idx) => (
//               <React.Fragment key={idx}>
//                 <div className="flex flex-col items-center">
//                   <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold transition-all duration-300 ${
//                     step > idx + 1 ? 'bg-green-500 text-white shadow-lg scale-110' : 
//                     step === idx + 1 ? 'bg-indigo-600 text-white shadow-lg animate-pulse' : 
//                     'bg-gray-200 text-gray-400'
//                   }`}>
//                     {step > idx + 1 ? <CheckCircle className="w-6 h-6" /> : idx + 1}
//                   </div>
//                   <span className="mt-2 text-xs font-medium text-gray-700">{label}</span>
//                 </div>
//                 {idx < 4 && <div className={`flex-1 h-1 mx-2 rounded ${step > idx + 1 ? 'bg-green-500' : 'bg-gray-200'}`}></div>}
//               </React.Fragment>
//             ))}
//           </div>
//         </div>

//         {error && (
//           <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-xl p-4 flex items-center">
//             <XCircle className="w-5 h-5 text-red-600 mr-2" />
//             <p className="text-red-800">{error}</p>
//           </div>
//         )}

//         {/* Step 1: Input */}
//         {step === 1 && (
//           <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 animate-fade-in">
//             <div className="flex items-center mb-6">
//               <div className="bg-indigo-100 p-3 rounded-full mr-4">
//                 <MessageCircle className="w-6 h-6 text-indigo-600" />
//               </div>
//               <h2 className="text-3xl font-bold text-gray-900">Share Your Thoughts</h2>
//             </div>
            
//             <p className="text-gray-600 mb-8">
//               Let's start by understanding what's on your mind. Be as honest and detailed as you'd like.
//             </p>

//             <div className="mb-6">
//               <label className="block text-sm font-semibold text-gray-700 mb-3">
//                 What's the situation?
//               </label>
//               <textarea
//                 className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none resize-none transition-all"
//                 rows={4} // FIXED: number instead of string
//                 placeholder="Describe what happened or what's happening..."
//                 value={formData.situation}
//                 onChange={(e) => setFormData({ ...formData, situation: e.target.value })}
//               />
//             </div>

//             <div className="mb-8">
//               <label className="block text-sm font-semibold text-gray-700 mb-3">
//                 What thoughts came to mind?
//               </label>
//               <textarea
//                 className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none resize-none transition-all"
//                 rows={4} // FIXED: number instead of string
//                 placeholder="What were you thinking or telling yourself?"
//                 value={formData.thought}
//                 onChange={(e) => setFormData({ ...formData, thought: e.target.value })}
//               />
//             </div>

//             <button
//               onClick={detectDistortion}
//               disabled={!formData.situation || !formData.thought || loading}
//               className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl transform hover:scale-105"
//             >
//               {loading ? (
//                 <>
//                   <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
//                   Analyzing Your Thoughts...
//                 </>
//               ) : (
//                 <>
//                   Begin Analysis
//                   <ChevronRight className="w-5 h-5 ml-2" />
//                 </>
//               )}
//             </button>
//           </div>
//         )}

//         {/* Step 2: Detection */}
//         {step === 2 && distortionResult && (
//           <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 animate-fade-in">
//             <div className="flex items-center mb-6">
//               <div className="bg-yellow-100 p-3 rounded-full mr-4">
//                 <Brain className="w-6 h-6 text-yellow-600" />
//               </div>
//               <h2 className="text-3xl font-bold text-gray-900">Distortion Detection</h2>
//             </div>

//             <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border-2 border-yellow-300 rounded-xl p-6 mb-6">
//               <div className="flex items-start mb-4">
//                 <XCircle className="w-8 h-8 text-yellow-600 mr-3 flex-shrink-0 mt-1" />
//                 <div>
//                   <h3 className="text-xl font-bold text-gray-900 mb-2">Cognitive Distortions Detected</h3>
//                   <p className="text-gray-700">
//                     We've identified some thinking patterns that may be affecting your perspective.
//                   </p>
//                 </div>
//               </div>

//               <div className="mb-4">
//                 <p className="font-semibold text-gray-700 mb-3">Distortion Types:</p>
//                 <div className="flex flex-wrap gap-2">
//                   {distortionResult.distortion_types.map((type, idx) => (
//                     <span key={idx} className="bg-yellow-200 text-yellow-900 px-4 py-2 rounded-full text-sm font-semibold">
//                       {type}
//                     </span>
//                   ))}
//                 </div>
//               </div>

//               <div className="bg-white/50 rounded-lg p-4">
//                 <p className="text-sm text-gray-600 font-medium mb-1">Understanding:</p>
//                 <p className="text-gray-800">{distortionResult.explanation}</p>
//               </div>
//             </div>

//             <button
//               onClick={analyzeThought}
//               disabled={loading}
//               className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl"
//             >
//               {loading ? (
//                 <>
//                   <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
//                   Deep Analysis in Progress...
//                 </>
//               ) : (
//                 <>
//                   Continue to Deep Analysis
//                   <ChevronRight className="w-5 h-5 ml-2" />
//                 </>
//               )}
//             </button>
//           </div>
//         )}

//         {/* Step 3: Analysis */}
//         {step === 3 && analysis && (
//           <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 animate-fade-in">
//             <div className="flex items-center mb-6">
//               <div className="bg-purple-100 p-3 rounded-full mr-4">
//                 <TrendingUp className="w-6 h-6 text-purple-600" />
//               </div>
//               <h2 className="text-3xl font-bold text-gray-900">Deep Analysis</h2>
//             </div>

//             <p className="text-gray-600 mb-6">
//               Here's what we've learned about your thought pattern:
//             </p>

//             <div className="space-y-4 mb-8">
//               <div className="bg-gradient-to-r from-blue-50 to-blue-100 border-l-4 border-blue-500 rounded-lg p-5">
//                 <div className="flex items-start">
//                   <Heart className="w-5 h-5 text-blue-600 mr-3 mt-1 flex-shrink-0" />
//                   <div>
//                     <h3 className="font-bold text-gray-900 mb-2">Emotional Impact</h3>
//                     <p className="text-gray-700">{analysis.emotional_impact}</p>
//                   </div>
//                 </div>
//               </div>

//               <div className="bg-gradient-to-r from-purple-50 to-purple-100 border-l-4 border-purple-500 rounded-lg p-5">
//                 <div className="flex items-start">
//                   <Lightbulb className="w-5 h-5 text-purple-600 mr-3 mt-1 flex-shrink-0" />
//                   <div>
//                     <h3 className="font-bold text-gray-900 mb-2">Underlying Beliefs</h3>
//                     <ul className="space-y-1">
//                       {analysis.underlying_beliefs.map((belief, idx) => (
//                         <li key={idx} className="text-gray-700 flex items-start">
//                           <span className="text-purple-600 mr-2">•</span>
//                           <span>{belief}</span>
//                         </li>
//                       ))}
//                     </ul>
//                   </div>
//                 </div>
//               </div>

//               <div className="bg-gradient-to-r from-pink-50 to-pink-100 border-l-4 border-pink-500 rounded-lg p-5">
//                 <div className="flex items-start">
//                   <Clock className="w-5 h-5 text-pink-600 mr-3 mt-1 flex-shrink-0" />
//                   <div>
//                     <h3 className="font-bold text-gray-900 mb-3">Common Triggers</h3>
//                     <div className="flex flex-wrap gap-2">
//                       {analysis.triggers.map((trigger, idx) => (
//                         <span key={idx} className="bg-pink-200 text-pink-900 px-3 py-1 rounded-full text-sm font-medium">
//                           {trigger}
//                         </span>
//                       ))}
//                     </div>
//                   </div>
//                 </div>
//               </div>

//               <div className="bg-gradient-to-r from-green-50 to-green-100 border-l-4 border-green-500 rounded-lg p-5">
//                 <div className="flex items-start">
//                   <Sparkles className="w-5 h-5 text-green-600 mr-3 mt-1 flex-shrink-0" />
//                   <div>
//                     <h3 className="font-bold text-gray-900 mb-3">Recommended Therapeutic Approaches</h3>
//                     <div className="flex flex-wrap gap-2">
//                       {analysis.recommended_therapies.map((therapy, idx) => (
//                         <span key={idx} className="bg-green-200 text-green-900 px-4 py-2 rounded-full text-sm font-bold">
//                           {therapy}
//                         </span>
//                       ))}
//                     </div>
//                   </div>
//                 </div>
//               </div>
//             </div>

//             <button
//               onClick={generateCandidates}
//               disabled={loading}
//               className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl"
//             >
//               {loading ? (
//                 <>
//                   <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
//                   Generating Personalized Reframes...
//                 </>
//               ) : (
//                 <>
//                   Generate Reframes
//                   <Sparkles className="w-5 h-5 ml-2" />
//                 </>
//               )}
//             </button>
//           </div>
//         )}

//         {/* Step 4: Candidates */}
//         {step === 4 && candidates.length > 0 && (
//           <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 animate-fade-in">
//             <div className="flex items-center mb-6">
//               <div className="bg-green-100 p-3 rounded-full mr-4">
//                 <Sparkles className="w-6 h-6 text-green-600" />
//               </div>
//               <h2 className="text-3xl font-bold text-gray-900">Your Reframe Options</h2>
//             </div>

//             <p className="text-gray-600 mb-6">
//               We've generated multiple perspectives based on different therapeutic approaches. 
//               Choose the one that resonates most with you.
//             </p>

//             <div className="space-y-4 mb-8">
//               {candidates.map((candidate, idx) => (
//                 <div
//                   key={idx}
//                   onClick={() => setSelectedReframe(idx)}
//                   className={`p-6 border-2 rounded-xl cursor-pointer transition-all duration-300 transform hover:scale-102 ${
//                     selectedReframe === idx
//                       ? 'border-indigo-500 bg-gradient-to-r from-indigo-50 to-purple-50 shadow-lg'
//                       : 'border-gray-200 hover:border-indigo-300 bg-white hover:shadow-md'
//                   }`}
//                 >
//                   <div className="flex items-center justify-between mb-4">
//                     <span className="bg-indigo-600 text-white px-4 py-2 rounded-full text-sm font-bold">
//                       {candidate.therapy}
//                     </span>
//                     {selectedReframe === idx && (
//                       <div className="flex items-center text-indigo-600">
//                         <ThumbsUp className="w-5 h-5 mr-2" />
//                         <span className="font-semibold">Selected</span>
//                       </div>
//                     )}
//                   </div>

//                   <p className="text-gray-900 font-medium text-lg mb-4 leading-relaxed">
//                     "{candidate.reframe}"
//                   </p>

//                   <div className="bg-white/50 rounded-lg p-4 mb-4">
//                     <p className="text-sm text-gray-600 font-semibold mb-1">Why this works:</p>
//                     <p className="text-gray-700 text-sm">{candidate.rationale}</p>
//                   </div>

//                   {candidate.evaluation && (
//                     <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-gray-200">
//                       {Object.entries(candidate.evaluation).map(([key, value]) => (
//                         <div key={key} className="text-center">
//                           <p className="text-xs text-gray-500 uppercase font-semibold mb-1">{key}</p>
//                           <div className="flex items-center justify-center">
//                             {[...Array(5)].map((_, i) => (
//                               <Award
//                                 key={i}
//                                 className={`w-4 h-4 ${
//                                   i < value ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'
//                                 }`}
//                               />
//                             ))}
//                           </div>
//                         </div>
//                       ))}
//                     </div>
//                   )}
//                 </div>
//               ))}
//             </div>

//             <div className="flex gap-4">
//               <button
//                 onClick={reset}
//                 className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center"
//               >
//                 <RotateCcw className="w-5 h-5 mr-2" />
//                 Start Over
//               </button>

//               <button
//                 onClick={saveSelection}
//                 disabled={selectedReframe === null}
//                 className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl"
//               >
//                 Confirm Choice
//                 <CheckCircle className="w-5 h-5 ml-2" />
//               </button>
//             </div>
//           </div>
//         )}

//         {/* Step 5: Success */}
//         {step === 5 && selectedReframe !== null && candidates[selectedReframe] && (
//           <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 text-center animate-fade-in">
//             <div className="inline-block p-4 bg-green-100 rounded-full mb-6">
//               <CheckCircle className="w-20 h-20 text-green-600" />
//             </div>

//             <h2 className="text-4xl font-bold text-gray-900 mb-4">Congratulations!</h2>
//             <p className="text-xl text-gray-600 mb-8">
//               You've taken an important step toward healthier thinking
//             </p>

//             <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 rounded-2xl p-8 mb-8 text-left">
//               <div className="mb-6">
//                 <p className="text-sm text-gray-500 uppercase font-semibold mb-2">Original Thought</p>
//                 <p className="text-gray-800 italic">"{formData.thought}"</p>
//               </div>

//               <div className="flex items-center justify-center my-6">
//                 <ArrowRight className="w-8 h-8 text-indigo-600" />
//               </div>

//               <div>
//                 <p className="text-sm text-gray-500 uppercase font-semibold mb-2">
//                   Your New Perspective ({candidates[selectedReframe].therapy})
//                 </p>
//                 <p className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
//                   "{candidates[selectedReframe].reframe}"
//                 </p>
//               </div>
//             </div>

//             <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6 mb-8 text-left">
//               <div className="flex items-start">
//                 <Lightbulb className="w-6 h-6 text-blue-600 mr-3 mt-1 flex-shrink-0" />
//                 <div>
//                   <h3 className="font-bold text-gray-900 mb-2">Practice Makes Progress</h3>
//                   <p className="text-gray-700 text-sm">
//                     Try using this reframe when you notice similar thoughts. It may feel unnatural at first, 
//                     but with repetition, these healthier thinking patterns will become more automatic.
//                   </p>
//                 </div>
//               </div>
//             </div>

//             <button
//               onClick={reset}
//               className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl"
//             >
//               <RotateCcw className="w-5 h-5 mr-2" />
//               Work on Another Thought
//             </button>
//           </div>
//         )}
//       </div>
//     </div>
//   );

//   return (
//     <div className="min-h-screen">
//       <Navigation />
//       {currentPage === 'home' && <HomePage />}
//       {currentPage === 'about' && <AboutPage />}
//       {currentPage === 'therapies' && <TherapiesPage />}
//       {currentPage === 'app' && <AppPage />}

//       {/* Footer */}
//       <footer className="bg-gray-900 text-white py-12">
//         <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
//           <div className="grid md:grid-cols-3 gap-8 mb-8">
//             <div>
//               <div className="flex items-center mb-4">
//                 <Brain className="w-6 h-6 text-indigo-400 mr-2" />
//                 <span className="text-lg font-bold">MindReframe</span>
//               </div>
//               <p className="text-gray-400 text-sm">
//                 Evidence-based cognitive reframing powered by AI and clinical psychology.
//               </p>
//             </div>
            
//             <div>
//               <h3 className="font-bold mb-4">Resources</h3>
//               <ul className="space-y-2 text-sm text-gray-400">
//                 <li>Crisis Hotline: 988</li>
//                 <li>NAMI Helpline: 1-800-950-6264</li>
//                 <li>Crisis Text Line: Text HOME to 741741</li>
//               </ul>
//             </div>

//             <div>
//               <h3 className="font-bold mb-4">Important</h3>
//               <p className="text-sm text-gray-400">
//                 This tool is for educational and self-help purposes. 
//                 If you're in crisis, please seek professional help immediately.
//               </p>
//             </div>
//           </div>

//           <div className="border-t border-gray-800 pt-8 text-center text-sm text-gray-400">
//             <p>&copy; 2025 MindReframe. Based on ReframeBench research.</p>
//           </div>
//         </div>
//       </footer>
//     </div>
//   );
// };

// export default CognitiveReframingPlatform;

import React, { useState, useEffect } from 'react';
import { 
  Brain, Sparkles, CheckCircle, XCircle, ChevronRight, RotateCcw, 
  ThumbsUp, Award, Clock, Heart, Shield, Lightbulb, ArrowRight,
  MessageCircle, TrendingUp, Users, Menu, X
} from 'lucide-react';

// --- Type Definitions (Interfaces) ---
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
  evaluation?: {
    [key: string]: number; // Allow dynamic evaluation keys like 'empathy', 'logic'
  };
}

interface FormData {
  situation: string;
  thought: string;
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

const CognitiveReframingPlatform = () => {
  const [currentPage, setCurrentPage] = useState<string>('home');
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [step, setStep] = useState<number>(1);
  
  const [formData, setFormData] = useState<FormData>({
    situation: '',
    thought: ''
  });
  
  // ... các state cũ (step, formData, etc.)
  

  // // --- NEW: State cho Feedback (Demo Mode) ---
  // const [feedback, setFeedback] = useState({
  //   relevance: 0,   // Sát với situation
  //   suitability: 0, // Phù hợp với cá nhân
  //   realism: 0,     // Tính thực tế
  // });
  // const [isFeedbackSubmitted, setIsFeedbackSubmitted] = useState(false);

  // // Hàm xử lý chọn sao
  // const handleRate = (criteria: keyof typeof feedback, rating: number) => {
  //   setFeedback(prev => ({ ...prev, [criteria]: rating }));
  // };

  // // Helper render ngôi sao
  // const renderStars = (criteria: keyof typeof feedback) => {
  //   return (
  //     <div className="flex gap-1">
  //       {[1, 2, 3, 4, 5].map((star) => (
  //         <button
  //           key={star}
  //           onClick={() => handleRate(criteria, star)}
  //           className={`transition-all duration-200 focus:outline-none ${
  //             star <= feedback[criteria] 
  //               ? "text-yellow-400 fill-yellow-400 scale-110" 
  //               : "text-gray-300 hover:text-yellow-200 hover:scale-105"
  //           }`}
  //           type="button"
  //         >
  //           <Star className="w-6 h-6" />
  //         </button>
  //       ))}
  //     </div>
  //   );
  // };

  // --- NEW: State cho Feedback (Likert Scale) ---
  // Định nghĩa kiểu dữ liệu cho Feedback mới
  interface FeedbackState {
    belief: number | null;      // Tin tưởng vào reframe
    helpfulness: number | null; // Giúp ích cho cảm xúc
    recall: number | null;      // Khả năng nhớ lại
    learning: number | null;    // Bài học rút ra
  }

  const [feedback, setFeedback] = useState<FeedbackState>({
    belief: null,
    helpfulness: null,
    recall: null,
    learning: null
  });

  const [isFeedbackSubmitted, setIsFeedbackSubmitted] = useState(false);

  // Các lựa chọn trả lời (Likert Scale)
  const LIKERT_OPTIONS = [
    { value: 4, label: "Strongly Agree" },
    { value: 3, label: "Somewhat Agree" },
    { value: 2, label: "Somewhat Disagree" },
    { value: 1, label: "Strongly Disagree" }
  ];

  // Helper xử lý chọn đáp án
  const handleFeedbackChange = (question: keyof FeedbackState, value: number) => {
    setFeedback(prev => ({ ...prev, [question]: value }));
  };

  

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [distortionResult, setDistortionResult] = useState<DistortionResult | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedReframe, setSelectedReframe] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/session/init`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        setSessionId(data.session_id);
      } catch (err) {
        console.error('Session init failed:', err);
        setSessionId('demo-session-' + Date.now());
      }
    };
    initSession();
  }, []);

  // --- API Functions ---
  const detectDistortion = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          situation: formData.situation,
          thought: formData.thought
        })
      });
      if (!response.ok) throw new Error('Detection failed');
      const data = await response.json();
      setDistortionResult(data);
      setStep(2);
    } catch (err) {
      setError('Failed to detect distortions. Please try again.');
      console.error(err);
    }
    setLoading(false);
  };

  const analyzeThought = async () => {
    if (!distortionResult) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          situation: formData.situation,
          thought: formData.thought,
          distortions: distortionResult.distortion_types
        })
      });
      
      if (!response.ok) throw new Error('Analysis failed');
      
      const data = await response.json();
      setAnalysis(data);
      setStep(3);
    } catch (err) {
      setError('Failed to analyze thought. Please try again.');
      console.error(err);
    }
    setLoading(false);
  };

  // ... các state cũ
  interface ReframeIteration {
    reframe: string;
    iteration: number;
  }

  const [reframeHistory, setReframeHistory] = useState<ReframeIteration[]>([]);
  const [activeHistoryIndex, setActiveHistoryIndex] = useState<number>(0); // Trỏ tới phiên bản đang xem

  const [selectedTherapies, setSelectedTherapies] = useState<string[]>([]);
  const [aiFeedback, setAiFeedback] = useState<string | null>(null);
  const [aiFeedback_summ, setAiFeedback_summ] = useState<string | null>(null);
  const [showExample, setShowExample] = useState(false);
  const [improveCount, setImproveCount] = useState<number>(0);
  const [isImproving, setIsImproving] = useState<boolean>(false);

  // Thêm useEffect này để khi có kết quả phân tích (Step 3), 
  // ta tự động điền các liệu pháp AI gợi ý vào danh sách chọn.
  useEffect(() => {
    if (analysis && analysis.recommended_therapies) {
      setSelectedTherapies(analysis.recommended_therapies);
    }
  }, [analysis]);

  const fillExample = () => {
    setFormData({
      ...formData,
      situation: "I sent a message to my friend 3 hours ago and saw they were online, but they haven't replied yet.",
      thought: "They are ignoring me because they find me annoying. I must have said something wrong and now they hate me."
    });
    setShowExample(false);
  };

  // Hàm xử lý chọn/bỏ chọn liệu pháp
  const toggleTherapy = (therapyKey: string) => {
    setSelectedTherapies(prev => {
      if (prev.includes(therapyKey)) {
        // Nếu đã có thì bỏ đi (nhưng cảnh báo hoặc chặn nếu muốn giữ ít nhất 1 cái)
        return prev.filter(t => t !== therapyKey);
      } else {
        // Nếu chưa có thì thêm vào
        return [...prev, therapyKey];
      }
    });
  };
  // const generateCandidates = async () => {
  //   if (!analysis) return;

  //   setLoading(true);
  //   setError(null);
  //   try {
  //     const response = await fetch(`${API_BASE_URL}/reframe`, {
  //       method: 'POST',
  //       headers: { 'Content-Type': 'application/json' },
  //       body: JSON.stringify({
  //         session_id: sessionId,
  //         situation: formData.situation,
  //         thought: formData.thought,
  //         recommended_therapies: analysis.recommended_therapies
  //       })
  //     });
      
  //     if (!response.ok) throw new Error('Generation failed');
      
  //     const data = await response.json();
  //     setCandidates(data.candidates);
  //     setStep(4);
  //   } catch (err) {
  //     setError('Failed to generate reframes. Please try again.');
  //     console.error(err);
  //   }
  //   setLoading(false);
  // };

  // Khởi tạo lịch sử khi vừa bước vào Step 5
  // useEffect(() => {
  //   if (step === 5 && selectedReframe !== null && candidates[selectedReframe]) {
  //     const initialReframe: ReframeIteration = {
  //       reframe: candidates[selectedReframe].reframe,
  //       iteration: 0
  //     };
  //     setReframeHistory([initialReframe]);
  //     setActiveHistoryIndex(0);
  //     setImproveCount(0);
  //   }
  // }, [step, selectedReframe, candidates]);

  useEffect(() => {
    // 1. Khai báo một hàm async bên trong
    const initializeStep5 = async () => {
      // 2. Vẫn giữ nguyên điều kiện kiểm tra
      if (step === 5 && selectedReframe !== null && candidates[selectedReframe]) {
        
        try {
          // Bạn có thể bật một state loading ở đây nếu cần (ví dụ: setIsImproving(true))

          // 3. Thực hiện gọi API
          const response = await fetch(`${API_BASE_URL}/instruction_feedback`, {
            method: 'POST', // Hoặc GET tùy thiết kế backend của bạn
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId, // Gửi kèm session_id nếu cần
              situation: formData.situation,
              thought: formData.thought,
              current_reframe: candidates[selectedReframe].reframe,
            })
          });

          if (!response.ok) {
            throw new Error('Network response was not ok');
          }

          const apiData = await response.json();

          // 4. Khởi tạo state với dữ liệu từ API kết hợp với dữ liệu local
          const initialReframe: ReframeIteration = {
            reframe: candidates[selectedReframe].reframe,
            iteration: 0
          };
          
          setReframeHistory([initialReframe]);
          const feedbackObject = JSON.parse(apiData.ai_feedback);
          setAiFeedback_summ(feedbackObject.summary);
          setAiFeedback(apiData.ai_feedback);
          setActiveHistoryIndex(0);
          setImproveCount(0);

        } catch (error) {
          console.error('Lỗi khi khởi tạo dữ liệu ở step 5:', error);
          
          // 5. Luôn có phương án dự phòng (fallback) nếu gọi API thất bại
          // Để UI không bị treo hoặc trắng trang
          const fallbackReframe: ReframeIteration = {
            reframe: candidates[selectedReframe].reframe,
            iteration: 0
          };
          setReframeHistory([fallbackReframe]);
          setActiveHistoryIndex(0);
          setImproveCount(0);
          
        } finally {
        }
      }
    };

    initializeStep5();

  }, [step, selectedReframe, candidates]); 

  const handleImprove = async () => {
    if (improveCount >= 5 || selectedReframe === null || reframeHistory.length === 0) return;
    
    setIsImproving(true);
    try {
      const currentReframeObj = reframeHistory[reframeHistory.length - 1]; 

      const response = await fetch(`${API_BASE_URL}/improve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          situation: formData.situation,
          thought: formData.thought,
          current_reframe: currentReframeObj.reframe,
          history_response: reframeHistory,
          feedback: aiFeedback
        })
      });
      
      if (!response.ok) throw new Error('Improvement failed');
      
      const data = await response.json();

      const feedback_response = await fetch(`${API_BASE_URL}/instruction_feedback`, {
        method: 'POST', // Hoặc GET tùy thiết kế backend của bạn
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId, // Gửi kèm session_id nếu cần
          situation: formData.situation,
          thought: formData.thought,
          current_reframe: data.new_reframe,
        })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const feedbackData = await feedback_response.json();

      const feedbackObject = JSON.parse(feedbackData.ai_feedback);
      setAiFeedback_summ(feedbackObject.summary);
      setAiFeedback(feedbackData.ai_feedback);
      
      // Tạo object mới và đưa vào lịch sử
      const newIteration: ReframeIteration = {
        reframe: data.new_reframe,
        iteration: improveCount + 1
      };

      setReframeHistory(prev => [...prev, newIteration]);
      setImproveCount(prev => prev + 1);
      setActiveHistoryIndex(improveCount + 1); // Tự động chuyển view sang tab mới nhất 
      
      // Reset form đánh giá Likert
      setIsFeedbackSubmitted(false);
      setFeedback({ belief: null, helpfulness: null, recall: null, learning: null });
      
    } catch (err) {
      console.error('Failed to improve reframe:', err);
    } finally {
      setIsImproving(false);
    }
  };

  const generateCandidates = async () => {
    // Kiểm tra selectedTherapies thay vì analysis
    if (!selectedTherapies.length) return; 

    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/reframe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          situation: formData.situation,
          thought: formData.thought,
          recommended_therapies: selectedTherapies
        })
      });
      
      if (!response.ok) throw new Error('Generation failed');
      
      const data = await response.json();
      setCandidates(data.candidates);
      setStep(4);
    } catch (err) {
      setError('Failed to generate reframes. Please try again.');
      console.error(err);
    }
    setLoading(false);
  };

  const submitFeedback = async () => {
    // 1. Chuẩn bị payload dữ liệu
    const feedbackPayload = {
      session_id: sessionId,
      timestamp: new Date().toISOString(),
      input: {
        situation: formData.situation,
        thought: formData.thought,
      },
      output: {
        therapy_type: candidates[selectedReframe!]?.therapy,
        reframe: candidates[selectedReframe!]?.reframe,
      },
      ratings: feedback // { relevance, suitability, realism }
    };

    try {
      // 2. Gửi về Backend
      const response = await fetch(`${API_BASE_URL}/feedback`, { // API endpoint mới
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedbackPayload)
      });

      if (!response.ok) throw new Error('Failed to save feedback');

      // 3. Cập nhật UI
      console.log("✅ Feedback saved to server");
      setIsFeedbackSubmitted(true);
    } catch (err) {
      console.error("❌ Error saving feedback:", err);
      // Có thể hiển thị thông báo lỗi nhẹ ở đây nếu cần
      alert("Could not save feedback. Please check your connection.");
    }
  };

  const saveSelection = async () => {
    if (selectedReframe === null) return;
    
    try {
      await fetch(`${API_BASE_URL}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          selected_reframe: candidates[selectedReframe],
          original_thought: formData.thought
        })
      });
      setStep(5);
    } catch (err) {
      console.error('Failed to save selection:', err);
      setStep(5); 
    }
  };
  
  // const reset = () => {
  //   // 1. Reset các luồng chính
  //   setStep(1);
  //   setFormData({ situation: '', thought: '' });
    
  //   // 2. Xóa kết quả phân tích cũ
  //   setDistortionResult(null);
  //   setAnalysis(null);
  //   setCandidates([]);
  //   setSelectedReframe(null);
  //   setError(null);

  //   // 3. Reset danh sách liệu pháp đã chọn (QUAN TRỌNG: để lần sau AI tự gợi ý lại từ đầu)
  //   setSelectedTherapies([]);

  //   // 4. Reset Feedback về null (trạng thái chưa chọn)
  //   setFeedback({
  //     belief: null,
  //     helpfulness: null,
  //     recall: null,
  //     learning: null
  //   });
  //   setIsFeedbackSubmitted(false);
  // };
  const reset = () => {
    setStep(1);
    setFormData({ situation: '', thought: '' });
    setDistortionResult(null);
    setAnalysis(null);
    setCandidates([]);
    setSelectedReframe(null);
    setError(null);
    setSelectedTherapies([]);
    setFeedback({ belief: null, helpfulness: null, recall: null, learning: null });
    setIsFeedbackSubmitted(false);
    
    // Clear state improve
    setImproveCount(0);
    setIsImproving(false);

    setReframeHistory([]);
    setActiveHistoryIndex(0);
    setAiFeedback(null);
  };


  const renderNavigation = () => (
    <nav className="bg-white/80 backdrop-blur-md fixed w-full top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Brain className="w-8 h-8 text-indigo-600 mr-2" />
            <span className="text-xl font-bold text-gray-900">MindReframe</span>
          </div>
          
          <div className="hidden md:flex space-x-8">
            <button onClick={() => setCurrentPage('home')} className="text-gray-700 hover:text-indigo-600 transition">
              Home
            </button>
            <button onClick={() => setCurrentPage('about')} className="text-gray-700 hover:text-indigo-600 transition">
              About
            </button>
            <button onClick={() => setCurrentPage('therapies')} className="text-gray-700 hover:text-indigo-600 transition">
              Therapies
            </button>
            <button onClick={() => setCurrentPage('app')} className="bg-indigo-600 text-white px-6 py-2 rounded-full hover:bg-indigo-700 transition">
              Get Started
            </button>
          </div>

          <button 
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X /> : <Menu />}
          </button>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden pb-4">
            <button onClick={() => { setCurrentPage('home'); setMobileMenuOpen(false); }} className="block w-full text-left py-2 text-gray-700">
              Home
            </button>
            <button onClick={() => { setCurrentPage('about'); setMobileMenuOpen(false); }} className="block w-full text-left py-2 text-gray-700">
              About
            </button>
            <button onClick={() => { setCurrentPage('therapies'); setMobileMenuOpen(false); }} className="block w-full text-left py-2 text-gray-700">
              Therapies
            </button>
            <button onClick={() => { setCurrentPage('app'); setMobileMenuOpen(false); }} className="block w-full text-left py-2 text-indigo-600 font-semibold">
              Get Started
            </button>
          </div>
        )}
      </div>
    </nav>
  );

  const renderHomePage = () => (
    <div className="pt-16">
      <section className="relative min-h-screen flex items-center bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-1/2 -right-1/2 w-full h-full bg-gradient-to-br from-indigo-200/30 to-transparent rounded-full blur-3xl"></div>
          <div className="absolute -bottom-1/2 -left-1/2 w-full h-full bg-gradient-to-tr from-purple-200/30 to-transparent rounded-full blur-3xl"></div>
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
                Transform Your
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600"> Thoughts</span>
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                Evidence-based cognitive reframing powered by AI and multiple therapeutic approaches. 
                Find the perspective that works for you.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <button 
                  onClick={() => setCurrentPage('app')}
                  className="bg-indigo-600 text-white px-8 py-4 rounded-full font-semibold hover:bg-indigo-700 transition shadow-lg hover:shadow-xl flex items-center justify-center"
                >
                  Start Your Journey
                  <ArrowRight className="ml-2 w-5 h-5" />
                </button>
                <button 
                  onClick={() => setCurrentPage('about')}
                  className="bg-white text-indigo-600 px-8 py-4 rounded-full font-semibold hover:bg-gray-50 transition shadow-lg flex items-center justify-center"
                >
                  Learn More
                </button>
              </div>
            </div>

            <div className="hidden md:block">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-3xl blur-2xl opacity-20"></div>
                <div className="relative bg-white rounded-3xl shadow-2xl p-8">
                  <div className="space-y-6">
                    <div className="flex items-center space-x-4">
                      <div className="bg-indigo-100 p-3 rounded-full">
                        <Brain className="w-6 h-6 text-indigo-600" />
                      </div>
                      <div className="space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-32"></div>
                        <div className="h-3 bg-gray-100 rounded w-24"></div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="bg-purple-100 p-3 rounded-full">
                        <Sparkles className="w-6 h-6 text-purple-600" />
                      </div>
                      <div className="space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-40"></div>
                        <div className="h-3 bg-gray-100 rounded w-28"></div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="bg-pink-100 p-3 rounded-full">
                        <Heart className="w-6 h-6 text-pink-600" />
                      </div>
                      <div className="space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-36"></div>
                        <div className="h-3 bg-gray-100 rounded w-32"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Why MindReframe?</h2>
            <p className="text-xl text-gray-600">Science-backed features designed for your well-being</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 p-8 rounded-2xl">
              <div className="bg-indigo-600 w-14 h-14 rounded-full flex items-center justify-center mb-6">
                <Shield className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Evidence-Based</h3>
              <p className="text-gray-600">
                Built on proven therapeutic frameworks including CBT, ACT, DBT, and 9 other modalities studied in clinical research.
              </p>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-8 rounded-2xl">
              <div className="bg-purple-600 w-14 h-14 rounded-full flex items-center justify-center mb-6">
                <Users className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Personalized</h3>
              <p className="text-gray-600">
                Choose the therapeutic approach that resonates with you. Different perspectives for different people.
              </p>
            </div>

            <div className="bg-gradient-to-br from-pink-50 to-pink-100 p-8 rounded-2xl">
              <div className="bg-pink-600 w-14 h-14 rounded-full flex items-center justify-center mb-6">
                <Lightbulb className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">AI-Powered</h3>
              <p className="text-gray-600">
                Advanced language models trained to provide empathetic, safe, and clinically appropriate reframes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-xl text-gray-600">Your journey to healthier thinking in 5 simple steps</p>
          </div>

          <div className="grid md:grid-cols-5 gap-8">
            {[
              { icon: MessageCircle, title: 'Share', desc: 'Tell us your situation and thoughts' },
              { icon: Brain, title: 'Detect', desc: 'We identify cognitive distortions' },
              { icon: TrendingUp, title: 'Analyze', desc: 'Deep analysis of thought patterns' },
              { icon: Sparkles, title: 'Reframe', desc: 'Multiple therapeutic perspectives' },
              { icon: Heart, title: 'Choose', desc: 'Select what works for you' }
            ].map((item, idx) => (
              <div key={idx} className="text-center">
                <div className="bg-white w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <item.icon className="w-10 h-10 text-indigo-600" />
                </div>
                <h3 className="font-bold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-sm text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-indigo-600 to-purple-600">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-white mb-6">Ready to Transform Your Thinking?</h2>
          <p className="text-xl text-indigo-100 mb-8">
            Join thousands who have discovered healthier perspectives through cognitive reframing
          </p>
          <button 
            onClick={() => setCurrentPage('app')}
            className="bg-white text-indigo-600 px-10 py-4 rounded-full font-bold text-lg hover:bg-gray-100 transition shadow-xl inline-flex items-center"
          >
            Start Free Today
            <ArrowRight className="ml-2 w-5 h-5" />
          </button>
        </div>
      </section>
    </div>
  );

  const renderAboutPage = () => (
    <div className="pt-24 pb-20 min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-5xl font-bold text-gray-900 mb-8">About MindReframe</h1>
        
        <div className="bg-white rounded-3xl shadow-xl p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Our Mission</h2>
          <p className="text-gray-700 mb-4">
            MindReframe combines cutting-edge AI technology with evidence-based psychotherapy to make mental health 
            support accessible, personalized, and effective for everyone.
          </p>
          <p className="text-gray-700">
            We believe that mental well-being should be within reach for all, and that the right perspective 
            can make a profound difference in how we experience life's challenges.
          </p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">The Science Behind It</h2>
          <p className="text-gray-700 mb-4">
            Our platform is built on <strong>ReframeBench</strong>, a comprehensive benchmark evaluating large 
            language models across 12 distinct therapeutic modalities. This research ensures that our AI 
            provides clinically appropriate and safe cognitive reframes.
          </p>
          <p className="text-gray-700">
            We integrate principles from CBT, ACT, DBT, REBT, Schema Therapy, MBCT, CFT, Narrative Therapy, 
            SFBT, and Motivational Interviewing - giving you access to diverse therapeutic perspectives.
          </p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Important Note</h2>
          <p className="text-gray-700">
            MindReframe is designed as a self-help tool and educational resource. It is not a replacement 
            for professional mental health care. If you're experiencing severe distress, please reach out 
            to a qualified mental health professional.
          </p>
        </div>
      </div>
    </div>
  );

  const renderTherapiesPage = () => (
    <div className="pt-24 pb-20 min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-5xl font-bold text-gray-900 mb-4 text-center">Therapeutic Approaches</h1>
        <p className="text-xl text-gray-600 mb-12 text-center">
          Explore the diverse perspectives we offer
        </p>

        <div className="grid md:grid-cols-2 gap-6">
          {[
            { name: 'CBT', full: 'Cognitive Behavioral Therapy', color: 'indigo', desc: 'Challenge and change unhelpful thoughts through evidence and logic' },
            { name: 'ACT', full: 'Acceptance & Commitment Therapy', color: 'purple', desc: 'Accept thoughts and commit to value-driven actions' },
            { name: 'DBT', full: 'Dialectical Behavior Therapy', color: 'pink', desc: 'Balance acceptance with change through mindfulness' },
            { name: 'REBT', full: 'Rational Emotive Behavior Therapy', color: 'blue', desc: 'Dispute irrational beliefs with rational alternatives' },
            { name: 'MBCT', full: 'Mindfulness-Based Cognitive Therapy', color: 'green', desc: 'Combine mindfulness with cognitive techniques' },
            { name: 'CFT', full: 'Compassion-Focused Therapy', color: 'rose', desc: 'Cultivate self-compassion and kindness' },
            { name: 'Schema Therapy', full: 'Schema Therapy', color: 'violet', desc: 'Identify and heal deep-rooted patterns' },
            { name: 'Narrative', full: 'Narrative Therapy', color: 'amber', desc: 'Rewrite your story and externalize problems' },
            { name: 'SFBT', full: 'Solution-Focused Brief Therapy', color: 'cyan', desc: 'Focus on solutions rather than problems' },
            { name: 'MI', full: 'Motivational Interviewing', color: 'emerald', desc: 'Enhance motivation for positive change' }
          ].map((therapy, idx) => (
            <div key={idx} className={`bg-gradient-to-br from-${therapy.color}-50 to-${therapy.color}-100 p-6 rounded-2xl border-2 border-${therapy.color}-200`}>
              <h3 className="text-xl font-bold text-gray-900 mb-2">{therapy.name}</h3>
              <p className="text-sm text-gray-600 mb-3 font-medium">{therapy.full}</p>
              <p className="text-gray-700">{therapy.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderAppPage = () => (
    <div className="pt-20 pb-12 min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Progress Bar */}
        <div className="mb-8 bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            {['Input', 'Detect', 'Analyze', 'Reframe', 'Select'].map((label, idx) => (
              <React.Fragment key={idx}>
                <div className="flex flex-col items-center">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold transition-all duration-300 ${
                    step > idx + 1 ? 'bg-green-500 text-white shadow-lg scale-110' : 
                    step === idx + 1 ? 'bg-indigo-600 text-white shadow-lg animate-pulse' : 
                    'bg-gray-200 text-gray-400'
                  }`}>
                    {step > idx + 1 ? <CheckCircle className="w-6 h-6" /> : idx + 1}
                  </div>
                  <span className="mt-2 text-xs font-medium text-gray-700">{label}</span>
                </div>
                {idx < 4 && <div className={`flex-1 h-1 mx-2 rounded ${step > idx + 1 ? 'bg-green-500' : 'bg-gray-200'}`}></div>}
              </React.Fragment>
            ))}
          </div>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-xl p-4 flex items-center">
            <XCircle className="w-5 h-5 text-red-600 mr-2" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Step 1: Input */}
        {step === 1 && (
  <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 animate-fade-in">
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center">
        <div className="bg-indigo-100 p-3 rounded-full mr-4">
          <MessageCircle className="w-6 h-6 text-indigo-600" />
        </div>
        <h2 className="text-3xl font-bold text-gray-900">Share Your Thoughts</h2>
      </div>
      
      {/* Nút bật/tắt ví dụ */}
      <button
        onClick={() => setShowExample(!showExample)}
        className="text-sm font-medium text-indigo-600 hover:text-indigo-800 flex items-center transition-colors"
      >
        <Lightbulb className="w-4 h-4 mr-1" />
        {showExample ? 'Hide Example' : 'See Example'}
      </button>
    </div>

    {/* Khu vực hiển thị Example */}
    {showExample && (
      <div className="mb-8 bg-blue-50 border border-blue-100 rounded-xl p-5 relative animate-fade-in">
        <button 
          onClick={() => setShowExample(false)}
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
        >
          <X className="w-4 h-4" />
        </button>
        <h3 className="text-sm font-bold text-blue-800 uppercase tracking-wide mb-3">Example Scenario</h3>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-1">THE SITUATION (Facts only)</p>
            <p className="text-sm text-gray-700 bg-white p-3 rounded-lg border border-blue-100 italic">
              "I sent a message to my friend 3 hours ago and haven't received a reply yet."
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-1">THE THOUGHT (Interpretation)</p>
            <p className="text-sm text-gray-700 bg-white p-3 rounded-lg border border-blue-100 italic">
              "They are ignoring me because they hate me. I always mess up relationships."
            </p>
          </div>
        </div>
        <button
          onClick={fillExample}
          className="mt-4 text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline"
        >
          Click to use this example
        </button>
      </div>
    )}
    
    <p className="text-gray-600 mb-8">
      Let's start by understanding what's on your mind. Be as honest and detailed as you'd like.
    </p>

    <div className="mb-6">
      <div className="flex justify-between items-baseline mb-3">
        <label className="block text-sm font-semibold text-gray-700">
          What's the situation?
        </label>
        <span className="text-xs text-gray-400 font-medium">Objective facts (Who, what, where)</span>
      </div>
      <textarea
        className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none resize-none transition-all placeholder:text-gray-400"
        rows={3}
        placeholder="E.g., I made a mistake during my presentation..."
        value={formData.situation}
        onChange={(e) => setFormData({ ...formData, situation: e.target.value })}
        key="situation-input"
      />
    </div>

    <div className="mb-8">
      <div className="flex justify-between items-baseline mb-3">
        <label className="block text-sm font-semibold text-gray-700">
          What thoughts came to mind?
        </label>
        <span className="text-xs text-gray-400 font-medium">Your interpretation or feeling</span>
      </div>
      <textarea
        className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none resize-none transition-all placeholder:text-gray-400"
        rows={3}
        placeholder="E.g., Everyone thinks I'm incompetent. I'll get fired..."
        value={formData.thought}
        onChange={(e) => setFormData({ ...formData, thought: e.target.value })}
        key="thought-input"
      />
    </div>

    <button
      onClick={detectDistortion}
      disabled={!formData.situation || !formData.thought || loading}
      className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
    >
      {loading ? (
        <>
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
          Analyzing Your Thoughts...
        </>
      ) : (
        <>
          Begin Analysis
          <ChevronRight className="w-5 h-5 ml-2" />
        </>
      )}
    </button>
  </div>
)}

        {/* Step 2: Detection */}
        {step === 2 && distortionResult && (
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 animate-fade-in">
            <div className="flex items-center mb-6">
              <div className={`${distortionResult.has_distortion ? 'bg-yellow-100' : 'bg-green-100'} p-3 rounded-full mr-4`}>
                {distortionResult.has_distortion ? (
                  <Brain className="w-6 h-6 text-yellow-600" />
                ) : (
                  <CheckCircle className="w-6 h-6 text-green-600" />
                )}
              </div>
              <h2 className="text-3xl font-bold text-gray-900">
                {distortionResult.has_distortion ? 'Distortion Detection' : 'Great News!'}
              </h2>
            </div>

            {distortionResult.has_distortion ? (
              <>
                {/* Distortion Detected - Original UI */}
                <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border-2 border-yellow-300 rounded-xl p-6 mb-6">
                  <div className="flex items-start mb-4">
                    <XCircle className="w-8 h-8 text-yellow-600 mr-3 flex-shrink-0 mt-1" />
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 mb-2">Cognitive Distortions Detected</h3>
                      <p className="text-gray-700">
                        We've identified some thinking patterns that may be affecting your perspective.
                      </p>
                    </div>
                  </div>

                  <div className="mb-4">
                    <p className="font-semibold text-gray-700 mb-3">Distortion Types:</p>
                    <div className="flex flex-wrap gap-2">
                      {distortionResult.distortion_types.map((type, idx) => (
                        <span key={idx} className="bg-yellow-200 text-yellow-900 px-4 py-2 rounded-full text-sm font-semibold">
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white/50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 font-medium mb-1">Understanding:</p>
                    <p className="text-gray-800">{distortionResult.explanation}</p>
                  </div>
                </div>

                <button
                  onClick={analyzeThought}
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Deep Analysis in Progress...
                    </>
                  ) : (
                    <>
                      Continue to Deep Analysis
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </>
                  )}
                </button>
              </>
            ) : (
              <>
                {/* No Distortion Detected - New UI */}
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl p-6 mb-6">
                  <div className="flex items-start mb-4">
                    <CheckCircle className="w-8 h-8 text-green-600 mr-3 flex-shrink-0 mt-1" />
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 mb-2">Healthy Thinking Pattern</h3>
                      <p className="text-gray-700">
                        Your thought appears to be balanced and realistic. We didn't detect any cognitive distortions.
                      </p>
                    </div>
                  </div>

                  <div className="bg-white/50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 font-medium mb-1">Analysis:</p>
                    <p className="text-gray-800">{distortionResult.explanation}</p>
                  </div>
                </div>

                <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6 mb-6">
                  <div className="flex items-start">
                    <Lightbulb className="w-6 h-6 text-blue-600 mr-3 mt-1 flex-shrink-0" />
                    <div>
                      <h3 className="font-bold text-gray-900 mb-2">Keep It Up!</h3>
                      <p className="text-gray-700 text-sm">
                        Your thinking seems clear and grounded. This is a sign of good mental health. 
                        If you're still feeling distressed about the situation, consider whether the 
                        situation itself needs attention rather than your thoughts about it.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={() => setStep(1)}
                    className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center"
                  >
                    <RotateCcw className="w-5 h-5 mr-2" />
                    Try Another Thought
                  </button>

                  <button
                    onClick={() => setCurrentPage('home')}
                    className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl"
                  >
                    <CheckCircle className="w-5 h-5 mr-2" />
                    Back to Home
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* Step 3: Analysis */}
        {/* Step 3: Analysis */}
        {step === 3 && analysis && (
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 animate-fade-in">
            <div className="flex items-center mb-6">
              <div className="bg-purple-100 p-3 rounded-full mr-4">
                <TrendingUp className="w-6 h-6 text-purple-600" />
              </div>
              <h2 className="text-3xl font-bold text-gray-900">Deep Analysis</h2>
            </div>

            {/* ... (Giữ nguyên phần hiển thị Emotional Impact, Beliefs, Triggers cũ) ... */}
            <div className="space-y-4 mb-8">
              {/* Code hiển thị Emotional Impact, Beliefs, Triggers giữ nguyên như cũ... */}
              <div className="bg-gradient-to-r from-blue-50 to-blue-100 border-l-4 border-blue-500 rounded-lg p-5">
                  {/* ... nội dung Emotional Impact ... */}
                  <div className="flex items-start">
                      <Heart className="w-5 h-5 text-blue-600 mr-3 mt-1 flex-shrink-0" />
                      <div>
                        <h3 className="font-bold text-gray-900 mb-2">Emotional Impact</h3>
                        <p className="text-gray-700">{analysis.emotional_impact}</p>
                      </div>
                    </div>
              </div>
              
              {/* ... Các block Underlying Beliefs và Triggers giữ nguyên ... */}
                <div className="bg-gradient-to-r from-purple-50 to-purple-100 border-l-4 border-purple-500 rounded-lg p-5">
                  {/* ... nội dung Beliefs ... */}
                    <div className="flex items-start">
                          <Lightbulb className="w-5 h-5 text-purple-600 mr-3 mt-1 flex-shrink-0" />
                          <div>
                            <h3 className="font-bold text-gray-900 mb-2">Underlying Beliefs</h3>
                            <ul className="space-y-1">
                              {analysis.underlying_beliefs.map((belief, idx) => (
                                <li key={idx} className="text-gray-700 flex items-start">
                                  <span className="text-purple-600 mr-2">•</span>
                                  <span>{belief}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                </div>
                
                <div className="bg-gradient-to-r from-pink-50 to-pink-100 border-l-4 border-pink-500 rounded-lg p-5">
                    {/* ... nội dung Triggers ... */}
                    <div className="flex items-start">
                          <Clock className="w-5 h-5 text-pink-600 mr-3 mt-1 flex-shrink-0" />
                          <div>
                            <h3 className="font-bold text-gray-900 mb-3">Common Triggers</h3>
                            <div className="flex flex-wrap gap-2">
                              {analysis.triggers.map((trigger, idx) => (
                                <span key={idx} className="bg-pink-200 text-pink-900 px-3 py-1 rounded-full text-sm font-medium">
                                  {trigger}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                </div>
            </div>

            {/* --- NEW SECTION: CUSTOMIZE THERAPIES --- */}
            <div className="mb-8">
              <div className="flex items-center mb-4">
                <Sparkles className="w-5 h-5 text-indigo-600 mr-2" />
                <h3 className="text-xl font-bold text-gray-900">Select Perspectives</h3>
              </div>
              
              <p className="text-gray-600 text-sm mb-4">
                Based on your analysis, we've selected the best approaches (highlighted). 
                You can tap to add or remove other perspectives you'd like to explore.
              </p>

              {/* Grid lựa chọn liệu pháp */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {Object.entries(THERAPY_FULL_NAMES).map(([key, fullName]) => {
                  const isSelected = selectedTherapies.includes(key);
                  const isRecommended = analysis.recommended_therapies.includes(key);

                  return (
                    <button
                      key={key}
                      onClick={() => toggleTherapy(key)}
                      className={`
                        relative p-3 rounded-xl border-2 text-left transition-all duration-200
                        ${isSelected 
                          ? 'border-indigo-500 bg-indigo-50 shadow-md' 
                          : 'border-gray-200 bg-white hover:border-indigo-200 hover:bg-gray-50 text-gray-400'
                        }
                      `}
                    >
                      {/* Badge "Recommended" nếu AI gợi ý */}
                      {isRecommended && (
                        <span className="absolute -top-2 -right-2 bg-green-100 text-green-700 text-[10px] font-bold px-2 py-0.5 rounded-full border border-green-200 shadow-sm">
                          Recommended
                        </span>
                      )}

                      <div className="flex items-center justify-between mb-1">
                        <span className={`font-bold text-sm ${isSelected ? 'text-indigo-900' : 'text-gray-500'}`}>
                          {key}
                        </span>
                        {isSelected && <CheckCircle className="w-4 h-4 text-indigo-600" />}
                      </div>
                      <p className={`text-[10px] leading-tight line-clamp-2 ${isSelected ? 'text-indigo-700' : 'text-gray-400'}`}>
                        {fullName}
                      </p>
                    </button>
                  );
                })}
              </div>
              
              {/* Hiển thị lý do tại sao AI chọn liệu pháp (chỉ hiện cho những cái AI recommend) */}
              <div className="mt-4 bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-xs font-bold text-gray-500 uppercase mb-2">Why these were recommended:</p>
                <div className="space-y-2">
                  {analysis.recommended_therapies.map((therapy) => (
                    selectedTherapies.includes(therapy) && ( // Chỉ hiện nếu user vẫn đang chọn nó
                      <div key={therapy} className="text-sm">
                        <span className="font-bold text-gray-800">{therapy}: </span>
                        <span className="text-gray-600">{analysis.therapy_rationales?.[therapy]}</span>
                      </div>
                    )
                  ))}
                </div>
              </div>
            </div>

            {/* Button Generate */}
            <button
              onClick={generateCandidates}
              disabled={loading || selectedTherapies.length === 0} // Disable nếu không chọn liệu pháp nào
              className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Generating {selectedTherapies.length} Perspectives...
                </>
              ) : (
                <>
                  Generate Reframes ({selectedTherapies.length} Selected)
                  <Sparkles className="w-5 h-5 ml-2" />
                </>
              )}
            </button>
          </div>
        )}

        {/* Step 4: Candidates */}
        {step === 4 && candidates.length > 0 && (
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 animate-fade-in">
            <div className="flex items-center mb-6">
              <div className="bg-green-100 p-3 rounded-full mr-4">
                <Sparkles className="w-6 h-6 text-green-600" />
              </div>
              <h2 className="text-3xl font-bold text-gray-900">Your Reframe Options</h2>
            </div>

            <p className="text-gray-600 mb-6">
              We've generated multiple perspectives based on different therapeutic approaches. 
              Choose the one that resonates most with you.
            </p>

            <div className="space-y-4 mb-8">
              {candidates.map((candidate, idx) => (
                <div
                  key={idx}
                  onClick={() => setSelectedReframe(idx)}
                  className={`p-6 border-2 rounded-xl cursor-pointer transition-all duration-300 transform hover:scale-102 ${
                    selectedReframe === idx
                      ? 'border-indigo-500 bg-gradient-to-r from-indigo-50 to-purple-50 shadow-lg'
                      : 'border-gray-200 hover:border-indigo-300 bg-white hover:shadow-md'
                  }`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className="bg-indigo-600 text-white px-4 py-2 rounded-full text-sm font-bold">
                      {candidate.therapy}
                    </span>
                    {selectedReframe === idx && (
                      <div className="flex items-center text-indigo-600">
                        <ThumbsUp className="w-5 h-5 mr-2" />
                        <span className="font-semibold">Selected</span>
                      </div>
                    )}
                  </div>

                  <p className="text-gray-900 font-medium text-lg mb-4 leading-relaxed">
                    "{candidate.reframe}"
                  </p>

                  <div className="bg-white/50 rounded-lg p-4 mb-4">
                    <p className="text-sm text-gray-600 font-semibold mb-1">Why this works:</p>
                    <p className="text-gray-700 text-sm">{candidate.rationale}</p>
                  </div>

                  {candidate.evaluation && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-gray-200">
                      {Object.entries(candidate.evaluation).map(([key, value]) => (
                        <div key={key} className="text-center">
                          <p className="text-xs text-gray-500 uppercase font-semibold mb-1">{key}</p>
                          <div className="flex items-center justify-center">
                            {[...Array(5)].map((_, i) => (
                              <Award
                                key={i}
                                className={`w-4 h-4 ${
                                  i < value ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'
                                }`}
                              />
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex gap-4">
              <button
                onClick={reset}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center"
              >
                <RotateCcw className="w-5 h-5 mr-2" />
                Start Over
              </button>

              <button
                onClick={saveSelection}
                disabled={selectedReframe === null}
                className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl"
              >
                Confirm Choice
                <CheckCircle className="w-5 h-5 ml-2" />
              </button>
            </div>
          </div>
        )}

        {/* Step 5: Success */}
{step === 5 && selectedReframe !== null && candidates[selectedReframe] && (
  <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-8 text-center animate-fade-in max-w-2xl mx-auto">
    <div className="inline-block p-4 bg-green-100 rounded-full mb-6">
      <CheckCircle className="w-20 h-20 text-green-600" />
    </div>

    <h2 className="text-4xl font-bold text-gray-900 mb-4">Congratulations!</h2>
    <p className="text-xl text-gray-600 mb-8">
      You've taken an important step toward healthier thinking
    </p>

    {/* Reframe Result Card */}
    {reframeHistory.length > 0 && (
      <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 rounded-2xl p-8 mb-8 text-left relative transition-all duration-500">
        
        {/* --- NEW: History Navigation Tabs --- */}
        {reframeHistory.length > 1 && (
          <div className="mb-6 flex space-x-2 overflow-x-auto pb-2 scrollbar-hide">
            {reframeHistory.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setActiveHistoryIndex(idx)}
                className={`px-4 py-1.5 text-xs font-bold rounded-full transition-all whitespace-nowrap ${
                  activeHistoryIndex === idx
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'bg-white text-indigo-600 border border-indigo-200 hover:bg-indigo-50'
                }`}
              >
                {idx === 0 ? 'Original' : `Version ${idx + 1}`}
              </button>
            ))}
          </div>
        )}

        <div className="mb-6">
          <p className="text-sm text-gray-500 uppercase font-semibold mb-2">Situation</p>
          <p className="text-gray-800 italic">"{formData.situation}"</p>
        </div>
        <div className="mb-6">
          <p className="text-sm text-gray-500 uppercase font-semibold mb-2">Original Thought</p>
          <p className="text-gray-800 italic">"{formData.thought}"</p>
        </div>

        <div className="flex items-center justify-center my-6">
          <ArrowRight className="w-8 h-8 text-indigo-600" />
        </div>

        <div>
          <p className="text-sm text-gray-500 uppercase font-semibold mb-2 flex justify-between items-center">
            <span>Your New Perspective ({candidates[selectedReframe].therapy})</span>
            {/* Hiển thị version đang xem ở góc phải */}
            <span className="text-xs bg-purple-200 text-purple-800 px-2 py-0.5 rounded-md">
              {activeHistoryIndex === 0 ? 'Original' : `Iteration ${activeHistoryIndex}`}
            </span>
          </p>
          <p className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600 min-h-[3rem]">
            "{reframeHistory[activeHistoryIndex].reframe}"
          </p>
        </div>

        {/* LLM Insight & Improve Button */}
        <div className="mt-8 pt-6 border-t border-purple-200/50">
          <div className="flex items-start mb-6 bg-white/60 p-4 rounded-xl">
            <Brain className="w-5 h-5 text-purple-600 mr-3 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-bold text-gray-800 mb-1">AI Feedback</p>
              <p className="text-sm text-gray-700 leading-relaxed">
                {aiFeedback_summ}
              </p>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleImprove}
              // Vô hiệu hoá nút nếu đang loading, đã tới giới hạn 5 lần, hoặc đang xem lại lịch sử cũ (chỉ cho phép improve từ bản mới nhất)
              disabled={isImproving || improveCount >= 5 || activeHistoryIndex !== reframeHistory.length - 1}
              className={`text-sm font-bold py-2.5 px-5 rounded-xl flex items-center transition-all shadow-sm
                ${(isImproving || improveCount >= 5 || activeHistoryIndex !== reframeHistory.length - 1)
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-white border-2 border-purple-200 text-purple-600 hover:bg-purple-50 hover:border-purple-400 hover:shadow-md'
                }`}
            >
              {isImproving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600 mr-2"></div>
                  Refining...
                </>
              ) : activeHistoryIndex !== reframeHistory.length - 1 ? (
                <>
                  <RotateCcw className="w-4 h-4 mr-2" />
                  View Latest to Improve
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  {improveCount >= 5 ? 'Max Refinements Reached' : `Improve Reframe (${improveCount}/5)`}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    )}

    {/* --- NEW: FEEDBACK UI (Likert Scale) --- */}
    {!isFeedbackSubmitted ? (
      <div className="bg-white border border-gray-200 shadow-sm rounded-xl p-6 mb-8 text-left animate-fade-in transition-all">
        <div className="mb-6 border-b border-gray-100 pb-4">
          <h3 className="text-lg font-bold text-gray-800 flex items-center">
            <MessageCircle className="w-5 h-5 mr-2 text-indigo-600" />
            Evaluation
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            How strongly do you agree with the following statements regarding your chosen perspective?
          </p>
        </div>
        
        <div className="space-y-8">
          {/* Question 1: Belief */}
          <div>
            <p className="text-gray-800 font-medium mb-3 text-sm">
              1. I genuinely believe in this new perspective.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {LIKERT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleFeedbackChange('belief', opt.value)}
                  className={`py-2 px-3 text-xs rounded-lg border transition-all duration-200 ${
                    feedback.belief === opt.value
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-md font-semibold'
                      : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:bg-indigo-50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Question 2: Helpfulness */}
          <div>
            <p className="text-gray-800 font-medium mb-3 text-sm">
              2. This perspective helps me reduce my distress.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {LIKERT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleFeedbackChange('helpfulness', opt.value)}
                  className={`py-2 px-3 text-xs rounded-lg border transition-all duration-200 ${
                    feedback.helpfulness === opt.value
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-md font-semibold'
                      : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:bg-indigo-50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Question 3: Memorability */}
          <div>
            <p className="text-gray-800 font-medium mb-3 text-sm">
              3. I will likely recall this perspective next time I feel this way.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {LIKERT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleFeedbackChange('recall', opt.value)}
                  className={`py-2 px-3 text-xs rounded-lg border transition-all duration-200 ${
                    feedback.recall === opt.value
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-md font-semibold'
                      : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:bg-indigo-50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Question 4: Learning */}
          <div>
            <p className="text-gray-800 font-medium mb-3 text-sm">
              4. This exercise improved my ability to cope with negative thoughts.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {LIKERT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleFeedbackChange('learning', opt.value)}
                  className={`py-2 px-3 text-xs rounded-lg border transition-all duration-200 ${
                    feedback.learning === opt.value
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-md font-semibold'
                      : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:bg-indigo-50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Nút Submit chỉ hiện khi đã trả lời hết (hoặc ít nhất 1 câu tùy bạn) */}
        <div className="mt-8 text-center animate-fade-in">
          <button 
            onClick={submitFeedback}
            disabled={!feedback.belief || !feedback.helpfulness || !feedback.recall || !feedback.learning}
            className="text-sm bg-indigo-50 text-indigo-600 hover:bg-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed px-8 py-3 rounded-full font-bold transition-all shadow-sm hover:shadow-md"
          >
            Submit Evaluation
          </button>
        </div>
      </div>
    ) : (
      // UI sau khi đã submit (Cảm ơn)
      <div className="bg-green-50 border border-green-100 rounded-xl p-6 mb-8 flex flex-col items-center justify-center animate-fade-in">
        <div className="bg-green-100 p-3 rounded-full mb-3">
          <ThumbsUp className="w-8 h-8 text-green-600" />
        </div>
        <p className="text-green-800 font-bold text-lg">Thank You!</p>
        <p className="text-green-600 text-sm mt-1 text-center max-w-md">
          Your feedback is invaluable for improving our therapeutic models. 
          Keep practicing this reframe whenever you need it.
        </p>
      </div>
    )}
    {/* --- END FEEDBACK UI --- */}

    <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6 mb-8 text-left">
      <div className="flex items-start">
        <Lightbulb className="w-6 h-6 text-blue-600 mr-3 mt-1 flex-shrink-0" />
        <div>
          <h3 className="font-bold text-gray-900 mb-2">Practice Makes Progress</h3>
          <p className="text-gray-700 text-sm">
            Try using this reframe when you notice similar thoughts. It may feel unnatural at first, 
            but with repetition, these healthier thinking patterns will become more automatic.
          </p>
        </div>
      </div>
    </div>

    <button
      onClick={reset}
      className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-center shadow-lg hover:shadow-xl"
    >
      <RotateCcw className="w-5 h-5 mr-2" />
      Work on Another Thought
    </button>
  </div>
)}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen">
      {renderNavigation()}
      {currentPage === 'home' && renderHomePage()}
      {currentPage === 'about' && renderAboutPage()}
      {currentPage === 'therapies' && renderTherapiesPage()}
      {currentPage === 'app' && renderAppPage()}

      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            <div>
              <div className="flex items-center mb-4">
                <Brain className="w-6 h-6 text-indigo-400 mr-2" />
                <span className="text-lg font-bold">MindReframe</span>
              </div>
              <p className="text-gray-400 text-sm">
                Evidence-based cognitive reframing powered by AI and clinical psychology.
              </p>
            </div>
            
            {/* <div> */}
              {/* <h3 className="font-bold mb-4">About & Contact</h3> */}
              {/* <ul className="space-y-2 text-sm text-gray-400"> */}
                {/* <li>Affiliation: Anonymous</li> */}
                {/* <li>Contact Email: alpha.utehy@gmail.com</li> */}
                {/* <li>Crisis Text Line: Text HOME to 741741</li> */}
              {/* </ul> */}
            {/* </div> */}

            <div>
              <h3 className="font-bold mb-4">Important</h3>
              <p className="text-sm text-gray-400">
                This tool is for educational and self-help purposes. 
                If you're in crisis, please seek professional help immediately.
              </p>
            </div>
          </div>

          <div className="border-t border-gray-800 pt-8 text-center text-sm text-gray-400">
            <p>&copy; 2026 MindReframe. Based on MindReframe research.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default CognitiveReframingPlatform;