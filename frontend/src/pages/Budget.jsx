import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, useParams } from 'react-router-dom';
import ExpenseDashboard from './ExpenseDashboard';
import { IconReceipt, IconWallet, IconMapPin } from '@tabler/icons-react';
import { getStoredUserId } from '../utils/formatters';

const API = 'http://localhost:8000/api';

export default function Budget() {
  const { tripId: paramTripId } = useParams();
  const [searchParams] = useSearchParams();
  const preTrip = searchParams.get('trip') || paramTripId;

  const [trips, setTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(preTrip || '');
  const [loading, setLoading] = useState(true);

  const token = localStorage.getItem('token');
  const userId = getStoredUserId();

  useEffect(() => {
    if (!userId || userId === 'undefined' || String(userId) === 'undefined') { setLoading(false); return; }
    fetch(`${API}/trips/user/${userId}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setTrips(data);
          if (!selectedTrip) {
            setSelectedTrip(String(data[0].id));
          }
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [userId, token]);

  if (loading) {
    return (
      <div className="p-8 text-center space-y-3">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-gray-500 font-semibold">Loading Expense Manager...</p>
      </div>
    );
  }

  if (selectedTrip) {
    return (
      <div className="space-y-4">
        {/* Trip Selector Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="flex items-center gap-2">
            <IconReceipt className="text-blue-600 dark:text-blue-400" size={24} />
            <span className="text-xs font-extrabold text-gray-700 dark:text-gray-200 uppercase tracking-wider">
              Active Trip:
            </span>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <select
              value={selectedTrip}
              onChange={(e) => setSelectedTrip(e.target.value)}
              className="px-3.5 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-xs font-bold text-gray-900 dark:text-white cursor-pointer w-full sm:w-auto"
            >
              {trips.map((t) => (
                <option key={t.id} value={t.id}>
                  📍 {t.destination} ({t.start_date} to {t.end_date})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Render v2.1 Expense Dashboard */}
        <ExpenseDashboard overrideTripId={selectedTrip} />
      </div>
    );
  }

  return (
    <div className="p-12 text-center bg-white dark:bg-gray-800 rounded-3xl border border-dashed border-gray-300 dark:border-gray-700 space-y-3">
      <IconWallet size={40} className="mx-auto text-gray-400" />
      <h3 className="text-base font-extrabold text-gray-900 dark:text-white font-heading">No Trips Found</h3>
      <p className="text-xs text-gray-500">Create a trip first to manage expenses and budget analytics.</p>
    </div>
  );
}
