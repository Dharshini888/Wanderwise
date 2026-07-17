import React, { useState } from 'react';

export default function ARWayfinder() {
  const [arActive, setArActive] = useState(false);

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#f4f7fa', borderRadius: '24px' }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h2 className="text-primary-dark" style={{ margin: '0 0 0.5rem 0' }}>AR Wayfinder & Translator</h2>
        <p className="text-secondary" style={{ margin: 0 }}>Point your camera at the world to navigate or translate menus instantly.</p>
      </div>

      {!arActive ? (
        <div className="glass-card" style={{ width: '100%', maxWidth: '500px', height: '400px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', borderRadius: '24px', background: 'rgba(255,255,255,0.7)', cursor: 'pointer', transition: 'all 0.3s' }} onClick={() => setArActive(true)}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem', color: '#185FA5' }}>📱</div>
          <button style={{ padding: '12px 30px', borderRadius: '30px', border: 'none', background: '#185FA5', color: '#fff', fontSize: '1.1rem', fontWeight: 'bold', cursor: 'pointer', boxShadow: '0 4px 14px rgba(24, 95, 165, 0.3)' }}>
            Launch AR Camera
          </button>
        </div>
      ) : (
        <div style={{ width: '100%', maxWidth: '500px', height: '500px', borderRadius: '24px', overflow: 'hidden', position: 'relative', background: '#000' }}>
          {/* Mock Camera Feed */}
          <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'linear-gradient(135deg, #1f4037 0%, #99f2c8 100%)', opacity: 0.6 }} />
          
          {/* AR Overlay - Navigation Arrow */}
          <div style={{ position: 'absolute', top: '40%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center', color: '#fff', textShadow: '0 2px 10px rgba(0,0,0,0.5)', animation: 'float 2s ease-in-out infinite' }}>
            <div style={{ fontSize: '4rem' }}>⬆️</div>
            <h2 style={{ margin: '0', fontSize: '1.5rem' }}>150m</h2>
            <p style={{ margin: '0', fontSize: '1rem' }}>To Kyoto Station</p>
          </div>

          {/* AR Overlay - Translation Box */}
          <div style={{ position: 'absolute', bottom: '20%', left: '50%', transform: 'translateX(-50%)', background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(10px)', padding: '1rem', borderRadius: '16px', color: '#fff', width: '80%', textAlign: 'center', border: '1px solid rgba(255,255,255,0.2)' }}>
            <div style={{ fontSize: '0.8rem', color: '#aaa', marginBottom: '5px' }}>Translating from Japanese</div>
            <strong style={{ fontSize: '1.1rem' }}>"Spicy Miso Ramen"</strong>
            <div style={{ fontSize: '0.8rem', color: '#ff4d4f', marginTop: '5px', fontWeight: 'bold' }}>⚠ Contains Gluten</div>
          </div>

          <button 
            onClick={() => setArActive(false)}
            style={{ position: 'absolute', top: '15px', right: '15px', width: '40px', height: '40px', borderRadius: '50%', border: 'none', background: 'rgba(255,255,255,0.2)', backdropFilter: 'blur(5px)', color: '#fff', fontSize: '1.2rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Adding keyframes for the float animation */}
      <style>{`
        @keyframes float {
          0% { transform: translate(-50%, -50%) translateY(0px); }
          50% { transform: translate(-50%, -50%) translateY(-15px); }
          100% { transform: translate(-50%, -50%) translateY(0px); }
        }
      `}</style>
    </div>
  );
}
