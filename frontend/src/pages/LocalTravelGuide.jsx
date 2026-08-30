import React, { useState, useEffect, useCallback } from 'react';
import PageHeader from '../components/ui/PageHeader';
import StatusBadge from '../components/ui/StatusBadge';
import VerificationBadge from '../components/ui/VerificationBadge';
import GuideSearch from '../components/guide/GuideSearch';
import GuideCategories from '../components/guide/GuideCategories';
import NearbyPlaces from '../components/guide/NearbyPlaces';
import GuideMap from '../components/guide/GuideMap';
import PlaceDetailsModal from '../components/guide/PlaceDetailsModal';
import { searchGuideDestination, getNearbyGuidePlaces } from '../api/local_guide';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import {
  IconCompass,
  IconMapPin,
  IconSun,
  IconCloudStorm,
  IconMap,
  IconLayoutGrid,
  IconSparkles,
  IconBook,
  IconMessageCircle,
  IconAlertTriangle,
  IconRefresh,
} from '@tabler/icons-react';

export default function LocalTravelGuide() {
  const { user } = useAuth();
  const [destination, setDestination] = useState('Coimbatore');
  const [guideData, setGuideData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Views
  const [activeCategory, setActiveCategory] = useState('ALL');
  const [viewMode, setViewMode] = useState('split'); // 'split', 'grid', 'map'
  const [selectedPlace, setSelectedPlace] = useState(null);

  // Wishlist state map
  const [savedMap, setSavedMap] = useState({});

  // Fetch initial guide data for destination
  const fetchDestinationGuide = useCallback(async (targetDest) => {
    setLoading(true);
    setError(null);
    setGuideData(null);
    setActiveCategory('ALL');
    try {
      const data = await searchGuideDestination(targetDest);
      setGuideData(data);
      setDestination(data.destination || targetDest);
    } catch (err) {
      console.error('[LocalTravelGuide] Search error:', err);
      setError(`Unable to load destination guide for "${targetDest}". Please check network connection.`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDestinationGuide(destination);
  }, []);

  // Fetch category filtered places when category changes
  const handleCategoryChange = async (catId) => {
    setActiveCategory(catId);
    if (!guideData?.latitude || !guideData?.longitude) return;

    setLoading(true);
    try {
      const res = await getNearbyGuidePlaces({
        lat: guideData.latitude,
        lon: guideData.longitude,
        radius: 3000,
        category: catId,
        destination: guideData.destination || destination,
      });
      setGuideData((prev) => ({
        ...prev,
        places: res.places || [],
        places_count: res.count || 0,
        provider: res.provider || prev?.provider,
      }));
    } catch (err) {
      console.error('[LocalTravelGuide] Category change error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle current location trigger
  const handleUseLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        try {
          const res = await getNearbyGuidePlaces({
            lat: latitude,
            lon: longitude,
            radius: 3000,
            category: 'ALL',
          });
          setGuideData({
            destination: 'Current Location',
            display_name: `${latitude.toFixed(4)}° N, ${longitude.toFixed(4)}° E`,
            latitude,
            longitude,
            places_count: res.count || 0,
            places: res.places || [],
            weather: { status: 'Unavailable' },
            cultural_guide: null,
            provider: 'GPS Geolocation & OpenStreetMap',
          });
        } catch (err) {
          setError('Failed to fetch nearby places for current location.');
        } finally {
          setLoading(false);
        }
      },
      (err) => {
        console.error('[LocalTravelGuide] Geolocation error:', err);
        setLoading(false);
        alert('Could not access current location.');
      }
    );
  };

  // Save place to Wishlist
  const handleSaveWishlist = async (place) => {
    if (!user?.id) return;
    try {
      await api.post('/api/wishlist/add', {
        user_id: user.id,
        destination: place.name,
        country: place.address || guideData?.destination || 'Local Destination',
        notes: `Saved from Local Travel Guide (${place.category})`,
        estimated_budget: 5000,
        priority: 'someday',
      });
      setSavedMap((prev) => ({ ...prev, [place.id]: True }));
    } catch (err) {
      console.error('[LocalTravelGuide] Wishlist save error:', err);
    }
  };

  const weather = guideData?.weather;
  const tempStr =
    weather?.current?.temperature !== undefined
      ? `${weather.current.temperature}°C`
      : weather?.temp !== undefined
      ? `${weather.temp}°C`
      : null;
  const weatherDesc = weather?.current?.description || weather?.description || null;

  return (
    <div className="space-y-6 pb-12">
      {/* PAGE HEADER */}
      <PageHeader
        title="Local Travel Guide"
        subtitle="Discover useful places, attractions, services, and experiences around your destination."
        badge={<StatusBadge status="Truth-First" label="Verified Guide" />}
      />

      {/* SEARCH BAR & CONTROLS */}
      <div className="p-4 sm:p-5 rounded-3xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-xs space-y-4">
        <GuideSearch
          destination={destination}
          onSearch={fetchDestinationGuide}
          onUseLocation={handleUseLocation}
          loading={loading}
        />

        <div className="flex items-center justify-between gap-3 pt-2 border-t border-[var(--border-color)] flex-wrap">
          <GuideCategories activeCategory={activeCategory} onCategoryChange={handleCategoryChange} />

          {/* VIEW MODE TOGGLE */}
          <div className="flex items-center gap-1 bg-[var(--bg-subtle)] p-1 rounded-2xl border border-[var(--border-color)] shrink-0">
            <button
              onClick={() => setViewMode('split')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                viewMode === 'split'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              <IconCompass size={14} />
              <span className="hidden sm:inline">Split</span>
            </button>

            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                viewMode === 'grid'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              <IconLayoutGrid size={14} />
              <span className="hidden sm:inline">Grid</span>
            </button>

            <button
              onClick={() => setViewMode('map')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                viewMode === 'map'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              <IconMap size={14} />
              <span className="hidden sm:inline">Map</span>
            </button>
          </div>
        </div>
      </div>

      {/* ERROR STATE WITH RETRY */}
      {error && (
        <div className="p-5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-bold">
            <IconAlertTriangle size={18} className="shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => fetchDestinationGuide(destination)}
            className="px-3.5 py-1.5 rounded-xl bg-rose-600 text-white text-xs font-bold shadow-xs hover:bg-rose-700 transition-all flex items-center gap-1 cursor-pointer shrink-0"
          >
            <IconRefresh size={14} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* DESTINATION OVERVIEW CARD */}
      {guideData && (
        <div className="p-6 rounded-3xl bg-linear-to-br from-blue-600/10 via-indigo-600/5 to-transparent border border-blue-500/20 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-blue-600 dark:text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded-full border border-blue-500/20">
                Destination Overview
              </span>
              <VerificationBadge status="Provider Verified" size="xs" />
            </div>

            <h2 className="text-2xl font-extrabold text-[var(--text-primary)] font-heading tracking-tight">
              {guideData.destination}
            </h2>

            <div className="flex items-center gap-4 text-xs font-semibold text-[var(--text-secondary)] flex-wrap">
              {guideData.latitude && (
                <span className="flex items-center gap-1">
                  <IconMapPin size={15} className="text-blue-500" />
                  <span>
                    {guideData.latitude.toFixed(2)}° N, {guideData.longitude.toFixed(2)}° E
                  </span>
                </span>
              )}

              {tempStr ? (
                <span className="flex items-center gap-1 text-amber-500 font-bold">
                  <IconSun size={15} />
                  <span>
                    {tempStr} {weatherDesc ? `· ${weatherDesc}` : ''}
                  </span>
                </span>
              ) : (
                <span className="text-[var(--text-muted)] font-normal">⚪ Weather unavailable</span>
              )}

              <span className="text-blue-600 dark:text-blue-400 font-bold">
                {guideData.places_count || 0} places found nearby
              </span>
            </div>
          </div>

          <button
            onClick={() => setViewMode('map')}
            className="px-5 py-2.5 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-all flex items-center gap-2 cursor-pointer shrink-0"
          >
            <IconMap size={16} />
            <span>Explore Map</span>
          </button>
        </div>
      )}

      {/* MAIN VIEW CONTENT AREA */}
      {viewMode === 'split' && guideData && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* MAP COLUMN */}
          <div className="lg:col-span-5 sticky top-6">
            <GuideMap
              centerLat={guideData.latitude}
              centerLon={guideData.longitude}
              places={guideData.places || []}
              activePlace={selectedPlace}
              onSelectPlace={(p) => setSelectedPlace(p)}
              height="550px"
            />
          </div>

          {/* PLACES LIST COLUMN */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading">
                Nearby Places ({guideData.places?.length || 0})
              </h3>
              <span className="text-xs text-[var(--text-muted)] font-medium">
                Provider: {guideData.provider || 'OpenStreetMap'}
              </span>
            </div>

            <NearbyPlaces
              places={guideData.places || []}
              loading={loading}
              onViewDetails={(p) => setSelectedPlace(p)}
              onSaveWishlist={handleSaveWishlist}
              savedMap={savedMap}
            />
          </div>
        </div>
      )}

      {viewMode === 'grid' && guideData && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading">
              Nearby Places Grid ({guideData.places?.length || 0})
            </h3>
            <span className="text-xs text-[var(--text-muted)] font-medium">
              Provider: {guideData.provider || 'OpenStreetMap'}
            </span>
          </div>

          <NearbyPlaces
            places={guideData.places || []}
            loading={loading}
            onViewDetails={(p) => setSelectedPlace(p)}
            onSaveWishlist={handleSaveWishlist}
            savedMap={savedMap}
          />
        </div>
      )}

      {viewMode === 'map' && guideData && (
        <div className="space-y-4">
          <GuideMap
            centerLat={guideData.latitude}
            centerLon={guideData.longitude}
            places={guideData.places || []}
            activePlace={selectedPlace}
            onSelectPlace={(p) => setSelectedPlace(p)}
            height="650px"
          />

          <NearbyPlaces
            places={guideData.places || []}
            loading={loading}
            onViewDetails={(p) => setSelectedPlace(p)}
            onSaveWishlist={handleSaveWishlist}
            savedMap={savedMap}
          />
        </div>
      )}

      {/* RECOMMENDED NEARBY SECTION */}
      {guideData?.recommended && guideData.recommended.length > 0 && (
        <div className="p-6 rounded-3xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <IconSparkles size={20} className="text-amber-500" />
              <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading">
                Recommended Nearby Landmarks
              </h3>
            </div>
            <StatusBadge status="AI Match" label="Destination Highlights" />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {guideData.recommended.map((poi, idx) => (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-[var(--bg-subtle)] border border-[var(--border-color)] hover:border-amber-500/40 transition-all space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-[var(--text-primary)] truncate">{poi.name}</h4>
                  <span className="text-[10px] font-bold text-amber-500">★ {poi.rating || 4.7}</span>
                </div>
                <span className="text-[10px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider block">
                  {poi.category}
                </span>
                <p className="text-[11px] text-[var(--text-muted)] line-clamp-2">{poi.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CULTURAL ETIQUETTE & CUSTOMS SECTION */}
      {guideData?.cultural_guide && (
        <div className="p-6 rounded-3xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-xs space-y-5">
          <div className="flex items-center gap-2 border-b border-[var(--border-color)] pb-3">
            <IconBook size={20} className="text-blue-600 dark:text-blue-400" />
            <h3 className="text-sm font-extrabold text-[var(--text-primary)] font-heading">
              Local Customs & Cultural Etiquette — {guideData.cultural_guide.city}
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-2xl bg-[var(--bg-subtle)] border border-[var(--border-color)] space-y-1.5">
              <span className="font-extrabold text-blue-600 dark:text-blue-400 uppercase tracking-wider text-[10px] block">
                Transport Etiquette
              </span>
              <p className="text-[var(--text-secondary)] font-medium leading-relaxed">
                {guideData.cultural_guide.transport_etiquette}
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--bg-subtle)] border border-[var(--border-color)] space-y-1.5">
              <span className="font-extrabold text-blue-600 dark:text-blue-400 uppercase tracking-wider text-[10px] block">
                Tipping Guidelines
              </span>
              <p className="text-[var(--text-secondary)] font-medium leading-relaxed">
                {guideData.cultural_guide.tipping_guidelines}
              </p>
            </div>
          </div>

          {/* LOCAL CUSTOMS BULLETS */}
          {guideData.cultural_guide.local_customs && (
            <div className="space-y-2">
              <span className="font-bold text-[var(--text-primary)] text-xs block">Key Local Customs:</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {guideData.cultural_guide.local_customs.map((custom, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-[var(--bg-subtle)] border border-[var(--border-color)] text-xs text-[var(--text-secondary)] font-medium flex items-start gap-2"
                  >
                    <span className="text-blue-500 font-bold">•</span>
                    <span>{custom}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* USEFUL PHRASES */}
          {guideData.cultural_guide.useful_phrases && (
            <div className="space-y-2 pt-2">
              <span className="font-bold text-[var(--text-primary)] text-xs flex items-center gap-1">
                <IconMessageCircle size={15} className="text-blue-500" />
                <span>Useful Local Phrases:</span>
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {guideData.cultural_guide.useful_phrases.map((item, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-blue-500/5 border border-blue-500/10 text-xs flex flex-col justify-between"
                  >
                    <span className="font-extrabold text-blue-600 dark:text-blue-400">{item.phrase}</span>
                    <span className="text-[11px] text-[var(--text-muted)] mt-0.5">{item.meaning}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* PLACE DETAILS MODAL */}
      {selectedPlace && (
        <PlaceDetailsModal
          place={selectedPlace}
          originLat={guideData?.latitude}
          originLon={guideData?.longitude}
          onClose={() => setSelectedPlace(null)}
          onSaveWishlist={handleSaveWishlist}
          isSaved={!!savedMap[selectedPlace.id]}
        />
      )}
    </div>
  );
}
