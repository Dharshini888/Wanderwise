import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import EmailVerification from "./pages/EmailVerification";
import AuthCallback from "./pages/AuthCallback";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Weather from "./pages/Weather";
import AISuggestions from "./pages/AISuggestions";
import Transit from "./pages/Transit";
import ActiveTrip from "./pages/ActiveTrip";
import Packing from "./pages/Packing";
import Safety from "./pages/Safety";
import Budget from "./pages/Budget";
import Currency from "./pages/Currency";
import Journal from "./pages/Journal";
import Wishlist from "./pages/Wishlist";
import Analytics from "./pages/Analytics";
import Companion from "./pages/Companion";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import GroupConsensus from "./pages/GroupConsensus";
import HealthAndDocs from "./pages/HealthAndDocs";
import DocumentsVault from "./pages/DocumentsVault";
import SmartBudget from "./pages/SmartBudget";
import TripList from "./pages/TripList";
import TripDetails from "./pages/TripDetails";
import ExpenseDashboard from "./pages/ExpenseDashboard";
import SmartChecklist from "./pages/SmartChecklist";
import LocalTravelGuide from "./pages/LocalTravelGuide";
import ProtectedRoute from "./components/ProtectedRoute";

import Layout from "./components/Layout";

import { AuthProvider } from "./context/AuthContext";

function App() {
  useEffect(() => {
    try {
      const stored = localStorage.getItem('ww_settings');
      if (stored) {
        const settings = JSON.parse(stored);
        if (settings.theme === 'Dark (Coming Soon)' || settings.theme === 'Dark') {
          document.documentElement.classList.add('dark');
        } else if (settings.theme === 'Auto (Coming Soon)' || settings.theme === 'Auto') {
          if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.classList.add('dark');
          }
        } else {
          document.documentElement.classList.remove('dark');
        }
      }
    } catch (_) {}
  }, []);

  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/verify-email" element={<EmailVerification />} />
          <Route path="/auth/callback" element={<AuthCallback />} />

          {/* Protected Routes inside Layout */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
            <Route path="/trips" element={<Layout><TripList /></Layout>} />
            <Route path="/trips/:tripId" element={<Layout><TripDetails /></Layout>} />
            <Route path="/checklist" element={<Layout><SmartChecklist /></Layout>} />
            <Route path="/guide" element={<Layout><LocalTravelGuide /></Layout>} />
            <Route path="/companion" element={<Layout><TripList /></Layout>} />
            <Route path="/chat" element={<Layout><Chat /></Layout>} />
            <Route path="/weather" element={<Layout><Weather /></Layout>} />
            <Route path="/recommendations" element={<Layout><AISuggestions /></Layout>} />
            <Route path="/transit" element={<Layout><Transit /></Layout>} />
            <Route path="/trips/:tripId/transit" element={<Layout><Transit /></Layout>} />
            <Route path="/trips/:tripId/live" element={<Layout><ActiveTrip /></Layout>} />
            <Route path="/packing" element={<Layout><Packing /></Layout>} />
            <Route path="/safety" element={<Layout><Safety /></Layout>} />
            <Route path="/budget" element={<Layout><Budget /></Layout>} />
            <Route path="/smart-budget" element={<Layout><SmartBudget /></Layout>} />
            <Route path="/expenses/:tripId" element={<Layout><ExpenseDashboard /></Layout>} />
            <Route path="/currency" element={<Layout><Currency /></Layout>} />

            <Route path="/journal" element={<Layout><Journal /></Layout>} />
            <Route path="/journal/:tripId" element={<Layout><Journal /></Layout>} />
            <Route path="/wishlist" element={<Layout><Wishlist /></Layout>} />
            <Route path="/analytics" element={<Layout><Analytics /></Layout>} />
            <Route path="/profile" element={<Layout><Profile /></Layout>} />
            <Route path="/settings" element={<Layout><Settings /></Layout>} />
            <Route path="/group-consensus" element={<Layout><GroupConsensus /></Layout>} />
            <Route path="/health-docs" element={<Layout><HealthAndDocs /></Layout>} />
            <Route path="/documents" element={<Layout><DocumentsVault /></Layout>} />
            <Route path="/documents/:docId" element={<Layout><DocumentsVault /></Layout>} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;