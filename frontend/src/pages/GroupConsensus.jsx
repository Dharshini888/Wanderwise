import React, { useState } from 'react';

export default function GroupConsensus() {
  const [activities, setActivities] = useState([
    { id: '1', name: 'Morning Beach Trip', image: '🏖️', description: 'Relax by the ocean.', votes: { yes: 3, no: 2 }, aiSuggestion: 'Split group or find a compromise time slot.' },
    { id: '2', name: 'Museum of Modern Art', image: '🖼️', description: 'Explore contemporary art.', votes: { yes: 2, no: 3 }, aiSuggestion: 'Consider alternative activity due to low group interest.' },
    { id: '3', name: 'Local Food Tour', image: '🍜', description: 'Taste authentic street food.', votes: { yes: 5, no: 0 }, aiSuggestion: 'Approved by majority.' }
  ]);
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleSwipe = (vote) => {
    // In a real app, send vote to API
    if (currentIndex < activities.length) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const currentActivity = activities[currentIndex];

  return (
    <div style={{ minHeight: '100vh', padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#f4f7fa' }}>
      <h1 className="text-primary-dark" style={{ marginBottom: '1rem' }}>Group Consensus Engine</h1>
      <p className="text-secondary" style={{ marginBottom: '2rem' }}>Swipe to vote on activities for the upcoming trip.</p>

      {currentActivity ? (
        <div className="glass-card" style={{ padding: '2rem', borderRadius: '24px', maxWidth: '400px', width: '100%', textAlign: 'center', position: 'relative', overflow: 'hidden', transition: 'transform 0.3s ease', boxShadow: '0 10px 30px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '5rem', marginBottom: '1rem' }}>{currentActivity.image}</div>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: '#333' }}>{currentActivity.name}</h2>
          <p style={{ color: '#666', marginBottom: '2rem' }}>{currentActivity.description}</p>
          
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem' }}>
            <button 
              onClick={() => handleSwipe(false)}
              style={{ padding: '15px 30px', borderRadius: '30px', border: 'none', background: '#ff4d4f', color: '#fff', fontSize: '1.2rem', fontWeight: 'bold', cursor: 'pointer', transition: 'transform 0.2s', boxShadow: '0 4px 10px rgba(255, 77, 79, 0.3)' }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
            >
              Nope
            </button>
            <button 
              onClick={() => handleSwipe(true)}
              style={{ padding: '15px 30px', borderRadius: '30px', border: 'none', background: '#52c41a', color: '#fff', fontSize: '1.2rem', fontWeight: 'bold', cursor: 'pointer', transition: 'transform 0.2s', boxShadow: '0 4px 10px rgba(82, 196, 26, 0.3)' }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
            >
              Yeah
            </button>
          </div>
        </div>
      ) : (
        <div className="glass-card" style={{ padding: '2rem', borderRadius: '24px', maxWidth: '600px', width: '100%' }}>
          <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>Voting Complete!</h2>
          <h3 style={{ marginBottom: '1rem', color: '#185FA5' }}>AI Compromise Suggestions</h3>
          {activities.map(act => (
            <div key={act.id} style={{ padding: '1rem', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <strong style={{ fontSize: '1.1rem' }}>{act.name}</strong>
                <p style={{ fontSize: '0.9rem', color: '#666', margin: '5px 0 0 0' }}>{act.aiSuggestion}</p>
              </div>
              <div style={{ display: 'flex', gap: '10px', fontSize: '0.9rem' }}>
                <span style={{ color: '#52c41a', fontWeight: 'bold' }}>Yes: {act.votes.yes}</span>
                <span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>No: {act.votes.no}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
