import { useState, useEffect } from 'react';
import { IconMicrophone, IconVolume } from '@tabler/icons-react';

const API = 'http://localhost:8000/api';

export default function LanguageWidget({ trip, token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isListening, setIsListening] = useState(false);
  const [spokenText, setSpokenText] = useState("");
  const [translation, setTranslation] = useState("");

  useEffect(() => {
    if (!trip) return;
    const dest = trip.destination.split(',')[0];
    const cacheKey = `lang_guide_${dest}`;

    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      try { setData(JSON.parse(cached)); setLoading(false); } catch (_) {}
    }

    const fetchLang = async () => {
      try {
        const res = await fetch(`${API}/recommendations/language-guide`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ destination: dest })
        });
        if (res.ok) {
          const json = await res.json();
          if (json && json.hello) {
            setData(json);
            localStorage.setItem(cacheKey, JSON.stringify(json));
          }
        }
      } catch (e) {}
      setLoading(false);
    };
    fetchLang();
  }, [trip, token]);

  const speak = (text) => {
    if ('speechSynthesis' in window) {
      const msg = new SpeechSynthesisUtterance(text);
      window.speechSynthesis.speak(msg);
    }
  };

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech Recognition not supported in this browser.");
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
      setSpokenText("Listening...");
      setTranslation("");
    };

    recognition.onresult = async (event) => {
      const text = event.results[0][0].transcript;
      setSpokenText(text);
      
      try {
        const dest = trip.destination.split(',')[0];
        setTranslation("Translating...");
        const res = await fetch(`${API}/recommendations/translate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ text, destination: dest })
        });
        const transData = await res.json();
        setTranslation(transData.translated);
        speak(transData.translated);
      } catch (e) {
        setTranslation("Translation failed.");
      }
    };

    recognition.onerror = () => {
      setIsListening(false);
      setSpokenText("Voice error.");
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  if (!trip) return null;
  if (loading) return (
    <div className="glass-card p-6 animate-pulse">
      <div className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
        <div className="w-5 h-5 rounded-full border-2 border-[var(--color-primary-500)] border-t-transparent animate-spin"></div>
        <span>Translating cultural guides...</span>
      </div>
    </div>
  );
  if (!data || !data.hello) return null;

  const phrases = [
    { label: 'Hello', val: data.hello },
    { label: 'Thank You', val: data.thank_you },
    { label: 'Help', val: data.help },
    { label: 'How much?', val: data.how_much }
  ];

  return (
    <div className="glass-card p-6 flex flex-col gap-4">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider">
          Language Guide
        </h3>
        <span className="text-xs font-bold text-[var(--color-primary-600)] dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 px-2.5 py-1 rounded-full">
          {data.primary_language}
        </span>
      </div>
      
      {/* Mic Input Card */}
      <div className={`p-4 rounded-xl border flex flex-col gap-3 transition-colors ${
        isListening 
          ? 'bg-red-50/50 dark:bg-red-950/10 border-red-200 dark:border-red-800' 
          : 'bg-blue-50/20 dark:bg-blue-950/5 border-[var(--border-color)]'
      }`}>
        <div className="flex justify-between items-center">
          <span className="text-xs font-bold text-[var(--text-primary)]">Voice Translator</span>
          <button 
            onClick={startListening} 
            disabled={isListening}
            className={`w-9 h-9 rounded-full flex items-center justify-center cursor-pointer shadow-sm text-white transition-all transform hover:scale-105 active:scale-95 ${
              isListening ? 'bg-red-500 animate-pulse' : 'bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-700)]'
            }`}
            title="Speak to translate"
          >
            <IconMicrophone size={18} />
          </button>
        </div>
        {(spokenText || translation) && (
          <div className="text-xs bg-[var(--bg-card)] border border-[var(--border-color)] p-3 rounded-lg flex flex-col gap-1.5 shadow-sm">
            <div className="text-[var(--text-muted)] font-medium italic">"{spokenText}"</div>
            {translation && <div className="text-[var(--color-primary-600)] dark:text-blue-400 font-extrabold flex items-center gap-1">
              <IconVolume size={14} className="cursor-pointer" onClick={() => speak(translation)} />
              {translation}
            </div>}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-3">
        {phrases.map((p, i) => (
          <div key={i} className="flex justify-between items-center border-b border-[var(--border-color)] pb-2 last:border-0 last:pb-0">
            <div>
              <div className="text-[10px] text-[var(--text-muted)] font-semibold">{p.label}</div>
              <div className="text-sm font-bold text-[var(--text-primary)] font-heading">{p.val}</div>
            </div>
            <button 
              onClick={() => speak(p.val)} 
              className="text-[var(--text-muted)] hover:text-[var(--color-primary-600)] transition-colors p-1.5 hover:bg-[var(--border-color)] rounded-lg"
              title="Listen pronunciation"
            >
              <IconVolume size={18} />
            </button>
          </div>
        ))}
      </div>
      <div className="text-xs text-[var(--text-secondary)] bg-[var(--bg-app)] border border-[var(--border-color)] p-3 rounded-lg italic">
        💡 {data.cultural_tip}
      </div>
    </div>
  );
}
