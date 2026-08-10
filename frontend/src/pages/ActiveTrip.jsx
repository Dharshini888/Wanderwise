import React, { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import {
  OverviewTab,
  RouteOptionsTab,
  AIAnalysisTab,
  TimelineTab,
  WeatherSafetyTab,
  BudgetAnalyticsTab,
  NearbyTab,
  FloatingAIAssistant
} from '../components/transit/TransitComponentsV6';
import { IconSparkles } from '@tabler/icons-react';

const API = 'http://localhost:8000/api';

export default function ActiveTrip() {
  const { tripId } = useParams();
  const location = useLocation();
  
  const [loading, setLoading] = useState(true);
  const [routeData, setRouteData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);
  
  useEffect(() => {
    fetchV4RouteData();
  }, [tripId, location]);

  const fetchV4RouteData = async () => {
    setLoading(true);
    try {
      let origin = "Coimbatore";
      let destination = "Erode";
      let preferred_mode = "fastest";
      let budget = 50000;
      
      if (location.state) {
         origin = location.state.origin || origin;
         destination = location.state.destination || destination;
         budget = location.state.budget || budget;
      }
      
      const res = await fetch(`${API}/transit/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ origin, destination, preferred_mode, budget, date: "Tomorrow" })
      });
      
      const data = await res.json();
      setRouteData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !routeData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-purple-400">
        <IconSparkles size={48} className="animate-pulse mb-4" />
        <p className="font-bold">Loading WanderWise v6.0 AI Travel Platform...</p>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: '🗺️ Overview & Map' },
    { id: 'routes', label: '🚗 Route Options' },
    { id: 'ai', label: '🧠 AI Analysis' },
    { id: 'timeline', label: '⏱️ Timeline' },
    { id: 'weather', label: '🌤️ Weather & Safety' },
    { id: 'budget', label: '💰 Budget & Analytics' },
    { id: 'nearby', label: '📍 Nearby Essentials' }
  ];

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto min-h-screen pb-24 relative">
      {/* Navigation Bar */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-6 border-b border-[var(--border-color)] scrollbar-none">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/30'
                : 'bg-[var(--bg-glass)] text-[var(--text-muted)] hover:text-white border border-[var(--border-color)]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Workspaces */}
      <div>
        {activeTab === 'overview' && <OverviewTab routeData={routeData} />}
        {activeTab === 'routes' && <RouteOptionsTab routeData={routeData} />}
        {activeTab === 'ai' && <AIAnalysisTab routeData={routeData} />}
        {activeTab === 'timeline' && <TimelineTab routeData={routeData} />}
        {activeTab === 'weather' && <WeatherSafetyTab routeData={routeData} />}
        {activeTab === 'budget' && <BudgetAnalyticsTab routeData={routeData} />}
        {activeTab === 'nearby' && <NearbyTab routeData={routeData} />}
      </div>

      {/* Global Floating AI Travel Assistant Overlay */}
      <FloatingAIAssistant routeData={routeData} isOpen={isAssistantOpen} setIsOpen={setIsAssistantOpen} />
    </div>
  );
}
