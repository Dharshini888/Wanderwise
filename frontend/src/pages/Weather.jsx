import React, { useState, useEffect } from 'react';
import {
  IconSun,
  IconCloudRain,
  IconSearch,
  IconDroplet,
  IconWind,
  IconGauge,
  IconEye,
  IconAlertCircle,
  IconSunrise,
  IconSunset,
  IconSparkles,
  IconLoader,
  IconShirt,
  IconMapPin,
  IconCalendar,
  IconClock,
  IconCheck,
  IconShield,
  IconActivity,
  IconNavigation,
  IconInfoCircle,
  IconFlame,
  IconSnowflake,
  IconCloudFog,
  IconRefresh
} from '@tabler/icons-react';

const WMO_CODE_MAP = {
  0: { label: 'Clear Sky', icon: '☀️', type: 'sunny' },
  1: { label: 'Mainly Clear', icon: '🌤️', type: 'sunny' },
  2: { label: 'Partly Cloudy', icon: '⛅', type: 'cloudy' },
  3: { label: 'Overcast', icon: '☁️', type: 'cloudy' },
  45: { label: 'Foggy', icon: '🌫️', type: 'fog' },
  48: { label: 'Depositing Rime Fog', icon: '🌫️', type: 'fog' },
  51: { label: 'Light Drizzle', icon: '🌦️', type: 'rainy' },
  53: { label: 'Moderate Drizzle', icon: '🌧️', type: 'rainy' },
  55: { label: 'Dense Drizzle', icon: '🌧️', type: 'rainy' },
  56: { label: 'Freezing Drizzle', icon: '🌧️', type: 'rainy' },
  57: { label: 'Dense Freezing Drizzle', icon: '🌧️', type: 'rainy' },
  61: { label: 'Slight Rain', icon: '🌧️', type: 'rainy' },
  63: { label: 'Moderate Rain', icon: '🌧️', type: 'rainy' },
  65: { label: 'Heavy Rain', icon: '🌊', type: 'rainy' },
  66: { label: 'Freezing Rain', icon: '🌧️', type: 'rainy' },
  67: { label: 'Heavy Freezing Rain', icon: '🌊', type: 'rainy' },
  71: { label: 'Slight Snowfall', icon: '❄️', type: 'snow' },
  73: { label: 'Moderate Snowfall', icon: '❄️', type: 'snow' },
  75: { label: 'Heavy Snowfall', icon: '🌨️', type: 'snow' },
  77: { label: 'Snow Grains', icon: '🌨️', type: 'snow' },
  80: { label: 'Slight Rain Showers', icon: '🌦️', type: 'rainy' },
  81: { label: 'Moderate Rain Showers', icon: '🌧️', type: 'rainy' },
  82: { label: 'Violent Rain Showers', icon: '⛈️', type: 'rainy' },
  85: { label: 'Slight Snow Showers', icon: '🌨️', type: 'snow' },
  86: { label: 'Heavy Snow Showers', icon: '🌨️', type: 'snow' },
  95: { label: 'Thunderstorm', icon: '⛈️', type: 'rainy' },
  96: { label: 'Thunderstorm with Hail', icon: '⛈️', type: 'rainy' },
  99: { label: 'Severe Thunderstorm', icon: '⛈️', type: 'rainy' }
};

const getUvBadge = (uv) => {
  if (uv == null) return { label: 'N/A', color: 'text-slate-400 bg-slate-500/10 border-slate-500/20' };
  if (uv <= 2) return { label: `${uv} Low`, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' };
  if (uv <= 5) return { label: `${uv} Moderate`, color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' };
  if (uv <= 7) return { label: `${uv} High`, color: 'text-orange-400 bg-orange-500/10 border-orange-500/30' };
  if (uv <= 10) return { label: `${uv} Very High`, color: 'text-rose-400 bg-rose-500/10 border-rose-500/30' };
  return { label: `${uv} Extreme`, color: 'text-purple-400 bg-purple-500/10 border-purple-500/30' };
};

const getAqiBadge = (aqi) => {
  if (aqi == null) return { status: 'Unknown', color: 'text-slate-400 bg-slate-500/10', advice: 'No AQI data available for this region.' };
  if (aqi <= 50) return { status: 'Good', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30', advice: 'Air quality is satisfactory. Enjoy outdoor activities!' };
  if (aqi <= 100) return { status: 'Moderate', color: 'text-amber-400 bg-amber-500/10 border-amber-500/30', advice: 'Acceptable air quality. Sensitive individuals should take care.' };
  if (aqi <= 150) return { status: 'Unhealthy (Sensitive)', color: 'text-orange-400 bg-orange-500/10 border-orange-500/30', advice: 'Members of sensitive groups may experience health effects.' };
  if (aqi <= 200) return { status: 'Unhealthy', color: 'text-rose-400 bg-rose-500/10 border-rose-500/30', advice: 'Everyone may begin to experience health effects. Wear a mask.' };
  return { status: 'Very Unhealthy', color: 'text-purple-400 bg-purple-500/10 border-purple-500/30', advice: 'Health alert: serious health effects. Limit outdoor exposure.' };
};

export default function Weather() {
  const [cityInput, setCityInput] = useState('');
  const [locationName, setLocationName] = useState('Tokyo');
  const [countryName, setCountryName] = useState('Japan');
  const [loading, setLoading] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);
  const [error, setError] = useState('');
  const [weatherData, setWeatherData] = useState(null);
  const [airQualityData, setAirQualityData] = useState(null);
  const [recentSearches, setRecentSearches] = useState(['Tokyo', 'Paris', 'Mumbai', 'London', 'New York']);

  useEffect(() => {
    // Load default city on initial render
    handleCitySearch('Tokyo');
  }, []);

  const handleCitySearch = async (targetCity) => {
    const q = (targetCity || cityInput).trim();
    if (!q) return;

    setLoading(true);
    setError('');

    try {
      // 1. Nominatim Geocoding API
      const geoUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=1`;
      const geoRes = await fetch(geoUrl, { headers: { 'User-Agent': 'WanderWiseApp/6.0' } });
      const geoData = await geoRes.json();

      if (!geoData || geoData.length === 0) {
        setError(`City "${q}" not found. Please verify the city name.`);
        setLoading(false);
        return;
      }

      const place = geoData[0];
      const lat = parseFloat(place.lat);
      const lon = parseFloat(place.lon);
      const nameParts = place.display_name.split(',');
      const cityLabel = nameParts[0].trim();
      const countryLabel = nameParts[nameParts.length - 1].trim();

      setLocationName(cityLabel);
      setCountryName(countryLabel);

      // Save to recent searches
      setRecentSearches((prev) => {
        const filtered = prev.filter((item) => item.toLowerCase() !== cityLabel.toLowerCase());
        return [cityLabel, ...filtered].slice(0, 5);
      });

      // 2. Fetch Open-Meteo Weather Forecast
      await fetchMeteoData(lat, lon);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch weather telemetry. Please check connection.');
    } finally {
      setLoading(false);
    }
  };

  const fetchMeteoData = async (lat, lon) => {
    try {
      const meteoUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,surface_pressure,wind_speed_10m,visibility,uv_index&hourly=temperature_2m,weather_code,precipitation_probability&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max,uv_index_max,sunrise,sunset&timezone=auto`;
      const meteoRes = await fetch(meteoUrl);
      const meteo = await meteoRes.json();

      // 3. Fetch Open-Meteo Air Quality
      const aqUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}&current=us_aqi,pm2_5,pm10`;
      const aqRes = await fetch(aqUrl);
      const aq = await aqRes.json();

      setWeatherData(meteo);
      setAirQualityData(aq?.current || null);
    } catch (err) {
      console.error('Error fetching Open-Meteo payload:', err);
    }
  };

  const handleGpsLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      return;
    }

    setGpsLoading(true);
    setError('');

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;

        try {
          // Reverse geocode via Nominatim
          const revUrl = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`;
          const revRes = await fetch(revUrl, { headers: { 'User-Agent': 'WanderWiseApp/6.0' } });
          const revData = await revRes.json();

          const cityLabel = revData.address?.city || revData.address?.town || revData.address?.village || 'Current Location';
          const countryLabel = revData.address?.country || 'Local Area';

          setLocationName(cityLabel);
          setCountryName(countryLabel);

          await fetchMeteoData(lat, lon);
        } catch (err) {
          console.error(err);
          setError('Could not reverse geocode GPS location.');
        } finally {
          setGpsLoading(false);
        }
      },
      (err) => {
        setGpsLoading(false);
        setError('Location access denied or unavailable.');
      }
    );
  };

  // Helper calculations derived from current weather
  const current = weatherData?.current || {};
  const daily = weatherData?.daily || {};
  const wmoInfo = WMO_CODE_MAP[current.weather_code] || { label: 'Clear Sky', icon: '☀️', type: 'sunny' };
  const temp = current.temperature_2m ?? 24;
  const feelsLike = current.apparent_temperature ?? temp;
  const humidity = current.relative_humidity_2m ?? 65;
  const wind = current.wind_speed_10m ?? 12;
  const visibility = current.visibility ? (current.visibility / 1000).toFixed(1) : '10';
  const pressure = current.surface_pressure ? Math.round(current.surface_pressure) : 1013;
  const uvVal = current.uv_index ?? daily.uv_index_max?.[0] ?? 4;
  const uvBadge = getUvBadge(uvVal);
  const aqiVal = airQualityData?.us_aqi ?? 42;
  const pm25Val = airQualityData?.pm2_5 ? airQualityData.pm2_5.toFixed(1) : '8.4';
  const pm10Val = airQualityData?.pm10 ? airQualityData.pm10.toFixed(1) : '18.2';
  const aqiInfo = getAqiBadge(aqiVal);

  const rainProbMax = daily.precipitation_probability_max?.[0] ?? (wmoInfo.type === 'rainy' ? 75 : 15);

  // Dynamic Weather Alerts generator
  const alerts = [];
  if (rainProbMax >= 60 || current.precipitation > 2) alerts.push({ label: 'Heavy Rain Warning', icon: '☔', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' });
  if (current.weather_code >= 95) alerts.push({ label: 'Thunderstorm Warning', icon: '⛈️', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' });
  if (temp >= 35) alerts.push({ label: 'Heatwave Alert', icon: '🔥', color: 'bg-rose-500/20 text-rose-300 border-rose-500/30' });
  if (wind >= 35) alerts.push({ label: 'High Wind Advisory', icon: '💨', color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' });
  if (wmoInfo.type === 'snow') alerts.push({ label: 'Snowfall Alert', icon: '❄️', color: 'bg-sky-500/20 text-sky-300 border-sky-500/30' });
  if (wmoInfo.type === 'fog') alerts.push({ label: 'Dense Fog Advisory', icon: '🌫️', color: 'bg-slate-500/20 text-slate-300 border-slate-500/30' });
  if (alerts.length === 0) alerts.push({ label: 'Favorable Conditions', icon: '✨', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' });

  // Dynamic Clothing Recommendations
  const clothingItems = [];
  if (temp >= 28) {
    clothingItems.push({ text: '☀️ Wear light cotton clothes', tag: 'Lightwear' });
    clothingItems.push({ text: '🧢 Use sunglasses and a cap', tag: 'Sun Protection' });
  } else if (temp <= 12) {
    clothingItems.push({ text: '🧥 Carry a warm jacket or coat', tag: 'Outerwear' });
    clothingItems.push({ text: '🧤 Wear winter clothing & gloves', tag: 'Thermal' });
  } else {
    clothingItems.push({ text: '👕 Comfortable casual layers', tag: 'Regular' });
    clothingItems.push({ text: '🧥 Carry a light windbreaker', tag: 'Light Layer' });
  }

  if (wmoInfo.type === 'rainy' || rainProbMax > 40) {
    clothingItems.push({ text: '☔ Carry a compact umbrella', tag: 'Rainproof' });
    clothingItems.push({ text: '🥾 Waterproof shoes recommended', tag: 'Footwear' });
  }

  // Dynamic Activity Recommendations
  const activityCategories = {
    sunny: [
      { name: 'Beach & Coastal Walk', desc: 'Enjoy sunny shores and gentle ocean breezes.' },
      { name: 'City Sightseeing Tour', desc: 'Explore historical landmarks and outdoor monuments.' },
      { name: 'Mountain Hiking Trail', desc: 'Clear visibility makes for scenic panoramic views.' },
      { name: 'Outdoor Photography', desc: 'Perfect natural lighting for landscape shots.' }
    ],
    cloudy: [
      { name: 'Historical Walking Tour', desc: 'Mild temperatures ideal for urban walking.' },
      { name: 'Museum & Art Gallery Visit', desc: 'Discover indoor culture and exhibitions.' },
      { name: 'Shopping District Stroll', desc: 'Explore outdoor shopping avenues comfortably.' },
      { name: 'Cozy Cafe Hopping', desc: 'Relax at local coffee houses and bakeries.' }
    ],
    rainy: [
      { name: 'Indoor Art Galleries', desc: 'Stay dry while exploring world-class art collections.' },
      { name: 'Shopping Malls & Arcades', desc: 'Covered retail hubs with dining and entertainment.' },
      { name: 'Specialty Cafes & Bistro', desc: 'Enjoy hot drinks listening to rain outside.' },
      { name: 'Science Center & Planetarium', desc: 'Interactive indoor exhibits for all ages.' }
    ],
    snow: [
      { name: 'Skiing & Alpine Resort', desc: 'Take advantage of fresh snow slopes.' },
      { name: 'Snowboarding & Sledding', desc: 'Fun winter sports action on the hills.' },
      { name: 'Winter Photography Tour', desc: 'Capture snow-covered landscapes and architecture.' },
      { name: 'Thermal Bath & Hot Springs', desc: 'Unwind in heated natural thermal waters.' }
    ],
    fog: [
      { name: 'Indoor Thermal Spa', desc: 'Escape mist with warm wellness treatments.' },
      { name: 'Museum Cultural Tour', desc: 'Immerse in local indoor historical exhibits.' },
      { name: 'Local Culinary Market', desc: 'Taste regional delicacies at indoor food halls.' }
    ]
  };

  const recommendedActivities = activityCategories[wmoInfo.type] || activityCategories.sunny;

  // Dynamic Travel Advice
  const travelTips = [];
  if (temp >= 30) travelTips.push('Hydration Notice: Carry enough bottled water throughout the day.');
  if (uvVal >= 6) travelTips.push('Sun Protection: Apply SPF 50+ sunscreen every 2 hours.');
  if (rainProbMax >= 50) travelTips.push('Gear Protection: Keep electronics in waterproof dry bags.');
  if (temp >= 28) travelTips.push('Early Sightseeing: Start outdoor tours early to beat peak heat.');
  if (wmoInfo.type === 'rainy' || current.weather_code >= 95) travelTips.push('Safety Advisory: Avoid outdoor trekking during heavy downpours or storms.');
  if (travelTips.length < 3) travelTips.push('Local Currency: Keep small change for local transport and cafes.');

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto min-h-screen pb-24 text-[var(--text-primary)]">
      
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl text-white shadow-lg shadow-blue-500/20">
            <IconSun size={32} />
          </div>
          <div>
            <h1 className="text-3xl font-black tracking-tight font-heading flex items-center gap-2">
              🌦️ Weather Intelligence
            </h1>
            <p className="text-xs text-[var(--text-muted)] mt-1 max-w-2xl font-medium">
              Live weather forecasts powered by Open-Meteo. Discover clothing recommendations, weather alerts, and travel-friendly activity suggestions.
            </p>
          </div>
        </div>
      </div>

      {/* Search Section */}
      <div className="glass-card p-5 rounded-2xl mb-8 bg-gradient-to-r from-blue-900/20 via-indigo-900/10 to-purple-900/20 border border-blue-500/20 shadow-xl">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-purple-400">
              <IconSearch size={18} />
            </span>
            <input
              type="text"
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCitySearch()}
              placeholder="Search any city (Tokyo, Paris, Mumbai...)"
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-purple-500/30 bg-[var(--bg-glass)] text-sm text-[var(--text-primary)] outline-none focus:border-purple-400 transition-all placeholder:text-[var(--text-muted)]"
            />
          </div>

          <button
            onClick={() => handleCitySearch()}
            disabled={loading}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold px-6 py-3 rounded-xl text-sm shadow-lg shadow-purple-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {loading ? <IconLoader className="animate-spin" size={18} /> : <IconSearch size={18} />}
            <span>Search</span>
          </button>

          <button
            onClick={handleGpsLocation}
            disabled={gpsLoading}
            className="bg-purple-900/40 hover:bg-purple-800/60 border border-purple-500/30 text-purple-200 font-bold px-4 py-3 rounded-xl text-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
            title="Use current GPS location"
          >
            {gpsLoading ? <IconLoader className="animate-spin" size={18} /> : <IconMapPin size={18} className="text-purple-400" />}
            <span className="hidden md:inline">GPS Location</span>
          </button>
        </div>

        {/* Recent Searches Pills */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-[10px] text-purple-300 font-bold uppercase tracking-wider">Recent Searches:</span>
          {recentSearches.map((s, idx) => (
            <button
              key={idx}
              onClick={() => handleCitySearch(s)}
              className="text-xs bg-purple-900/30 hover:bg-purple-800/50 text-purple-200 border border-purple-500/20 px-3 py-1 rounded-lg transition-all"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="glass-card p-4 rounded-xl mb-8 bg-rose-950/20 border border-rose-500/30 text-rose-300 text-sm font-semibold flex items-center gap-3">
          <IconAlertCircle size={22} className="text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Skeleton Loading State */}
      {loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-pulse">
          <div className="lg:col-span-2 glass-card h-64 rounded-2xl bg-purple-900/10"></div>
          <div className="glass-card h-64 rounded-2xl bg-purple-900/10"></div>
        </div>
      )}

      {/* Main Weather Telemetry Content */}
      {!loading && weatherData && (
        <div className="space-y-8 animate-fadeIn">
          
          {/* Current Weather Hero Card */}
          <div className="glass-card p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-blue-900/40 via-purple-900/30 to-indigo-900/40 border border-purple-500/30 shadow-2xl relative overflow-hidden">
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-8">
              
              {/* City & Temperature */}
              <div className="flex items-center gap-6">
                <div className="text-7xl drop-shadow-xl animate-bounce duration-1000">{wmoInfo.icon}</div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-3xl sm:text-4xl font-black text-white font-heading">{locationName}</h2>
                    <span className="text-xs bg-purple-900/50 border border-purple-500/30 text-purple-300 px-2.5 py-1 rounded-lg font-bold">
                      {countryName}
                    </span>
                  </div>
                  <div className="text-xs text-[var(--text-muted)] mt-1 font-medium">
                    {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })} • {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div className="text-sm font-bold text-purple-300 mt-2 capitalize flex items-center gap-2">
                    <span>{wmoInfo.label}</span>
                  </div>
                </div>
              </div>

              {/* Main Temp & Metrics Grid */}
              <div className="flex flex-wrap gap-8 items-center border-t lg:border-t-0 lg:border-l border-purple-500/20 pt-6 lg:pt-0 lg:pl-8 w-full lg:w-auto">
                <div className="text-center lg:text-left">
                  <div className="text-5xl sm:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-300 via-purple-200 to-white font-heading">
                    {Math.round(temp)}°C
                  </div>
                  <div className="text-xs text-purple-300 mt-1 font-semibold">Feels like {Math.round(feelsLike)}°C</div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 flex-1">
                  <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                    <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase flex items-center gap-1">
                      <IconDroplet size={14} className="text-blue-400" /> Humidity
                    </div>
                    <div className="text-sm font-extrabold text-white mt-1">{humidity}%</div>
                  </div>

                  <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                    <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase flex items-center gap-1">
                      <IconWind size={14} className="text-teal-400" /> Wind
                    </div>
                    <div className="text-sm font-extrabold text-white mt-1">{wind} km/h</div>
                  </div>

                  <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                    <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase flex items-center gap-1">
                      <IconEye size={14} className="text-pink-400" /> Visibility
                    </div>
                    <div className="text-sm font-extrabold text-white mt-1">{visibility} km</div>
                  </div>

                  <div className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)]">
                    <div className="text-[10px] text-[var(--text-muted)] font-bold uppercase flex items-center gap-1">
                      <IconGauge size={14} className="text-purple-400" /> Pressure
                    </div>
                    <div className="text-sm font-extrabold text-white mt-1">{pressure} hPa</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 7-Day Forecast & Weather Alerts */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* 7-Day Forecast Cards */}
            <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-[var(--border-color)]">
              <h3 className="text-base font-bold text-white font-heading mb-4 flex items-center gap-2">
                <IconCalendar size={20} className="text-purple-400" /> 7-Day Weather Forecast
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-7 gap-2">
                {(daily.time || []).slice(0, 7).map((d, i) => {
                  const dayCode = daily.weather_code?.[i] ?? 0;
                  const dayWmo = WMO_CODE_MAP[dayCode] || { icon: '☀️' };
                  const maxT = daily.temperature_2m_max?.[i] ?? 25;
                  const minT = daily.temperature_2m_min?.[i] ?? 18;
                  const dayRain = daily.precipitation_probability_max?.[i] ?? 10;
                  const dayWind = daily.wind_speed_10m_max?.[i] ?? 10;

                  return (
                    <div key={i} className="bg-[var(--bg-glass)] p-3 rounded-xl border border-[var(--border-color)] text-center flex flex-col justify-between">
                      <div className="text-xs font-bold text-purple-300">
                        {i === 0 ? 'Today' : new Date(d + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short' })}
                      </div>
                      <div className="text-3xl my-2">{dayWmo.icon}</div>
                      <div className="text-sm font-black text-white">{Math.round(maxT)}° / <span className="text-[var(--text-muted)] text-xs">{Math.round(minT)}°</span></div>
                      <div className="mt-2 pt-2 border-t border-purple-500/10 text-[10px] space-y-1">
                        <div className="text-blue-400 font-bold">{dayRain}% 💧</div>
                        <div className="text-[var(--text-muted)]">{Math.round(dayWind)} km/h</div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Sunrise & Sunset Block */}
              {daily.sunrise?.[0] && (
                <div className="grid grid-cols-2 gap-4 mt-6 pt-4 border-t border-[var(--border-color)]">
                  <div className="bg-amber-950/20 border border-amber-500/30 p-3.5 rounded-xl flex items-center gap-3">
                    <IconSunrise className="text-amber-400" size={28} />
                    <div>
                      <div className="text-[10px] text-amber-300 font-bold uppercase">Sunrise</div>
                      <div className="text-sm font-extrabold text-white">
                        {new Date(daily.sunrise[0]).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>

                  <div className="bg-indigo-950/20 border border-indigo-500/30 p-3.5 rounded-xl flex items-center gap-3">
                    <IconSunset className="text-indigo-400" size={28} />
                    <div>
                      <div className="text-[10px] text-indigo-300 font-bold uppercase">Sunset</div>
                      <div className="text-sm font-extrabold text-white">
                        {new Date(daily.sunset[0]).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Weather Alerts & Air Quality Card */}
            <div className="space-y-6">
              
              {/* Weather Alerts Card */}
              <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)]">
                <h3 className="text-base font-bold text-white font-heading mb-4 flex items-center gap-2">
                  <IconAlertCircle className="text-rose-400" /> Active Weather Warnings
                </h3>
                <div className="space-y-2.5">
                  {alerts.map((alt, idx) => (
                    <div key={idx} className={`p-3 rounded-xl border flex items-center gap-3 font-semibold text-xs ${alt.color}`}>
                      <span className="text-lg">{alt.icon}</span>
                      <span>{alt.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Air Quality Card */}
              <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)]">
                <h3 className="text-base font-bold text-white font-heading mb-4 flex items-center gap-2">
                  <IconActivity className="text-emerald-400" /> Air Quality Telemetry
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)]">
                    <span className="text-xs text-[var(--text-muted)] font-bold uppercase">US AQI Status</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-extrabold border ${aqiInfo.color}`}>
                      {aqiVal} • {aqiInfo.status}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)]">
                      <span className="text-[10px] text-[var(--text-muted)] font-bold block">PM2.5</span>
                      <span className="font-extrabold text-white text-sm">{pm25Val} µg/m³</span>
                    </div>
                    <div className="p-3 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)]">
                      <span className="text-[10px] text-[var(--text-muted)] font-bold block">PM10</span>
                      <span className="font-extrabold text-white text-sm">{pm10Val} µg/m³</span>
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-purple-950/20 border border-purple-500/20 text-xs text-purple-200">
                    💡 {aqiInfo.advice}
                  </div>
                </div>
              </div>

            </div>
          </div>

          {/* Clothing & Activity Recommendations Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Clothing Recommendation Card */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)]">
              <h3 className="text-base font-bold text-white font-heading mb-4 flex items-center gap-2">
                <IconShirt className="text-purple-400" /> AI Clothing Recommendations
              </h3>
              <div className="space-y-3">
                {clothingItems.map((item, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] flex justify-between items-center">
                    <span className="text-xs font-bold text-white">{item.text}</span>
                    <span className="text-[10px] bg-purple-900/40 text-purple-300 px-2.5 py-1 rounded-md font-bold uppercase border border-purple-500/20">
                      {item.tag}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Travel Tips Card */}
            <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)]">
              <h3 className="text-base font-bold text-white font-heading mb-4 flex items-center gap-2">
                <IconSparkles className="text-amber-400" /> Smart Travel Advice & Tips
              </h3>
              <div className="space-y-3">
                {travelTips.map((tip, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/30 flex items-start gap-3">
                    <IconCheck size={18} className="text-amber-400 shrink-0 mt-0.5" />
                    <span className="text-xs font-medium text-amber-100">{tip}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Activity Recommendations Section */}
          <div className="glass-card p-6 rounded-2xl border border-[var(--border-color)]">
            <h3 className="text-base font-bold text-white font-heading mb-4 flex items-center gap-2">
              <IconActivity className="text-blue-400" /> Weather-Matched Activity Suggestions ({wmoInfo.type.toUpperCase()})
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {recommendedActivities.map((act, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-[var(--bg-glass)] border border-[var(--border-color)] hover:border-purple-500/40 transition-all">
                  <div className="text-sm font-extrabold text-white mb-1 font-heading">{act.name}</div>
                  <div className="text-xs text-[var(--text-muted)]">{act.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Page Footer */}
          <div className="pt-8 border-t border-[var(--border-color)] text-center text-xs text-[var(--text-muted)] space-y-1">
            <div>Powered by <strong>Open-Meteo Weather API</strong> • <strong>OpenStreetMap Geocoding</strong> • <strong>WanderWise AI Intelligence</strong></div>
            <div>© {new Date().getFullYear()} WanderWise AI Travel Assistant. All live meteorological telemetry updated in real time.</div>
          </div>

        </div>
      )}
    </div>
  );
}
