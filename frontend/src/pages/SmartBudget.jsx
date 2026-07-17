import React from 'react';

export default function SmartBudget() {
  const splits = [
    { from: 'Alice', to: 'Bob', amount: 45.50 },
    { from: 'Charlie', to: 'Bob', amount: 12.00 }
  ];

  return (
    <div style={{ minHeight: '100vh', padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#f4f7fa' }}>
      <h1 className="text-primary-dark" style={{ marginBottom: '1rem' }}>Smart Group Budget</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', width: '100%', maxWidth: '1000px' }}>
        
        {/* Settlement Suggestions */}
        <div className="glass-card" style={{ padding: '2rem', borderRadius: '24px' }}>
          <h2 style={{ fontSize: '1.3rem', marginBottom: '1.5rem', color: '#185FA5' }}>Settle-Up Suggestions</h2>
          <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1.5rem' }}>Optimized transactions to balance the group.</p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {splits.map((s, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: '#fff', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '35px', height: '35px', borderRadius: '50%', background: '#ff7a45', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>{s.from[0]}</div>
                  <span style={{ color: '#8c8c8c' }}>→</span>
                  <div style={{ width: '35px', height: '35px', borderRadius: '50%', background: '#36cfc9', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>{s.to[0]}</div>
                </div>
                <div style={{ fontWeight: 'bold', fontSize: '1.1rem', color: '#333' }}>${s.amount.toFixed(2)}</div>
              </div>
            ))}
          </div>
          <button style={{ marginTop: '1.5rem', padding: '10px 20px', width: '100%', background: '#52c41a', color: '#fff', border: 'none', borderRadius: '10px', cursor: 'pointer', fontWeight: 'bold' }}>
            Settle All
          </button>
        </div>

        {/* Auto Categorization OCR */}
        <div className="glass-card" style={{ padding: '2rem', borderRadius: '24px' }}>
          <h2 style={{ fontSize: '1.3rem', marginBottom: '1.5rem', color: '#185FA5' }}>Add Expense</h2>
          <div style={{ padding: '2rem', border: '2px dashed #185FA5', borderRadius: '12px', textAlign: 'center', background: 'rgba(24, 95, 165, 0.05)', cursor: 'pointer' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🧾</div>
            <p style={{ color: '#185FA5', margin: 0, fontWeight: 500 }}>Scan Receipt</p>
            <p style={{ fontSize: '0.8rem', color: '#666', marginTop: '5px' }}>AI will extract amount and category</p>
          </div>
          
          <div style={{ marginTop: '2rem' }}>
            <input type="text" placeholder="Amount" style={{ width: '100%', padding: '12px', marginBottom: '1rem', borderRadius: '8px', border: '1px solid #d9d9d9', boxSizing: 'border-box' }} />
            <select style={{ width: '100%', padding: '12px', marginBottom: '1rem', borderRadius: '8px', border: '1px solid #d9d9d9', boxSizing: 'border-box' }}>
              <option>Split Equally</option>
              <option>Exact Amounts</option>
            </select>
            <button style={{ padding: '12px', width: '100%', background: '#185FA5', color: '#fff', border: 'none', borderRadius: '10px', cursor: 'pointer' }}>Add Expense</button>
          </div>
        </div>

      </div>
    </div>
  );
}
