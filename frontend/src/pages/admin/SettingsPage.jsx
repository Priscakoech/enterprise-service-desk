import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { Sun, Moon, ArrowLeft, Lock, Loader2, Eye, EyeOff, ShieldAlert, Camera, User } from 'lucide-react';
import api from '../../api/client';

export default function SettingsPage() {
  const navigate = useNavigate();
  const { dark, toggle } = useTheme();
  const { user, updateUser } = useAuth();
  const forced = user?.must_change_password;
  const fileInputRef = useRef(null);

  // Profile state
  const [profile, setProfile] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    username: user?.username || '',
    email: user?.email || '',
    profile_picture: user?.profile_picture || null,
  });
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg] = useState({ type: '', text: '' });
  const [avatarPreview, setAvatarPreview] = useState(null);

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [pwMsg, setPwMsg] = useState({ type: '', text: '' });

  // Auto-dismiss profile messages
  useEffect(() => {
    if (!profileMsg.text) return;
    const t = setTimeout(() => setProfileMsg({ type: '', text: '' }), 3000);
    return () => clearTimeout(t);
  }, [profileMsg]);

  // Auto-dismiss password messages
  useEffect(() => {
    if (!pwMsg.text) return;
    const t = setTimeout(() => setPwMsg({ type: '', text: '' }), 3000);
    return () => clearTimeout(t);
  }, [pwMsg]);

  // Fetch profile on mount
  useEffect(() => {
    api.get('/accounts/profile/').then((res) => {
      setProfile({
        first_name: res.data.first_name || '',
        last_name: res.data.last_name || '',
        username: res.data.username || '',
        email: res.data.email || '',
        profile_picture: res.data.profile_picture || null,
      });
    }).catch(() => {});
  }, []);

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setAvatarPreview(URL.createObjectURL(file));
    // Upload immediately
    const formData = new FormData();
    formData.append('profile_picture', file);
    setProfileSaving(true);
    api.patch('/accounts/profile/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((res) => {
      setProfile((p) => ({ ...p, profile_picture: res.data.profile_picture }));
      updateUser({ profile_picture: res.data.profile_picture });
      setProfileMsg({ type: 'success', text: 'Profile picture updated' });
    }).catch(() => {
      setProfileMsg({ type: 'error', text: 'Failed to upload picture' });
      setAvatarPreview(null);
    }).finally(() => setProfileSaving(false));
  };

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setProfileMsg({ type: '', text: '' });
    setProfileSaving(true);
    try {
      const res = await api.patch('/accounts/profile/', {
        first_name: profile.first_name,
        last_name: profile.last_name,
        username: profile.username,
        email: profile.email,
      });
      setProfile((p) => ({ ...p, ...res.data }));
      updateUser({
        first_name: res.data.first_name,
        last_name: res.data.last_name,
        username: res.data.username,
        email: res.data.email,
      });
      setProfileMsg({ type: 'success', text: 'Profile updated successfully' });
    } catch (err) {
      const data = err.response?.data;
      const msg = typeof data === 'object'
        ? Object.values(data).flat().join(', ')
        : 'Failed to update profile';
      setProfileMsg({ type: 'error', text: msg });
    } finally {
      setProfileSaving(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwMsg({ type: '', text: '' });
    if (newPassword !== confirmPassword) {
      setPwMsg({ type: 'error', text: 'New passwords do not match' });
      return;
    }
    if (newPassword.length < 4) {
      setPwMsg({ type: 'error', text: 'Password must be at least 4 characters' });
      return;
    }
    setSaving(true);
    try {
      const res = await api.post('/accounts/change-password/', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      if (res.data.token) {
        localStorage.setItem('token', res.data.token);
        api.defaults.headers.common['Authorization'] = `Token ${res.data.token}`;
      }
      setPwMsg({ type: 'success', text: 'Password changed successfully' });
      updateUser({ must_change_password: false });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      if (forced) {
        setTimeout(() => navigate('/dashboard', { replace: true }), 1000);
      }
    } catch (err) {
      setPwMsg({ type: 'error', text: err.response?.data?.error || 'Failed to change password' });
    } finally {
      setSaving(false);
    }
  };

  const avatarSrc = avatarPreview || profile.profile_picture;
  const initials = (profile.first_name?.[0] || profile.username?.[0] || 'U').toUpperCase();

  return (
    <div className="space-y-6 max-w-2xl">
      {forced && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
          <ShieldAlert className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0" />
          <p className="text-sm text-amber-800 dark:text-amber-300">
            You must change your default password before continuing. Please set a new password below.
          </p>
        </div>
      )}

      <div className="flex items-center gap-3">
        {!forced && (
          <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
        )}
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Settings</h1>
      </div>

      {/* Profile */}
      <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-white mb-5 flex items-center gap-2">
          <User className="w-4 h-4" /> Profile
        </h2>

        {profileMsg.text && (
          <div className={`mb-4 px-4 py-2.5 rounded-lg text-sm ${profileMsg.type === 'success' ? 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400' : 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400'}`}>
            {profileMsg.text}
          </div>
        )}

        {/* Avatar */}
        <div className="flex items-center gap-5 mb-6">
          <div className="relative group">
            {avatarSrc ? (
              <img
                src={avatarSrc}
                alt="Profile"
                className="w-20 h-20 rounded-full object-cover border-2 border-slate-200 dark:border-slate-700"
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-blue-600 flex items-center justify-center text-white text-2xl font-bold border-2 border-slate-200 dark:border-slate-700">
                {initials}
              </div>
            )}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="absolute inset-0 rounded-full bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
            >
              <Camera className="w-5 h-5 text-white" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleAvatarChange}
            />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-900 dark:text-white">
              {profile.first_name && profile.last_name
                ? `${profile.first_name} ${profile.last_name}`
                : profile.username}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 capitalize">{user?.role}</p>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="text-xs text-blue-600 dark:text-blue-400 hover:underline mt-1"
            >
              Change photo
            </button>
          </div>
        </div>

        {/* Profile form */}
        <form onSubmit={handleProfileSave} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1">First Name</label>
              <input
                type="text" value={profile.first_name}
                onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="First name"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1">Last Name</label>
              <input
                type="text" value={profile.last_name}
                onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Last name"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1">Username</label>
            <input
              type="text" value={profile.username}
              onChange={(e) => setProfile({ ...profile, username: e.target.value })}
              className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Username"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1">Email</label>
            <input
              type="email" value={profile.email}
              onChange={(e) => setProfile({ ...profile, email: e.target.value })}
              className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Email"
            />
          </div>
          <button type="submit" disabled={profileSaving}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium transition-colors">
            {profileSaving && <Loader2 className="w-4 h-4 animate-spin" />}
            Save Profile
          </button>
        </form>
      </div>

      {/* Appearance + System Info */}
      <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6 space-y-6">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white mb-4">Appearance</h2>
          <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/30 rounded-lg">
            <div className="flex items-center gap-3">
              {dark ? <Moon className="w-5 h-5 text-slate-400" /> : <Sun className="w-5 h-5 text-amber-500" />}
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-white">Theme</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">Currently using {dark ? 'dark' : 'light'} theme</p>
              </div>
            </div>
            <button
              onClick={toggle}
              className={`relative w-12 h-6 rounded-full transition-colors ${dark ? 'bg-blue-600' : 'bg-slate-300'}`}
            >
              <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${dark ? 'left-[26px]' : 'left-0.5'}`} />
            </button>
          </div>
        </div>

        {user?.role === 'admin' && (
        <div>
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white mb-4">System Info</h2>
          <div className="space-y-2">
            {[
              ['Application', 'Enterprise Service Desk'],
              ['Backend', 'Django REST Framework'],
              ['Frontend', 'React + Vite + Tailwind CSS'],
              ['API Base', '/api'],
            ].map(([key, val]) => (
              <div key={key} className="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-800 last:border-0">
                <span className="text-sm text-slate-500 dark:text-slate-400">{key}</span>
                <span className="text-sm font-medium text-slate-900 dark:text-white">{val}</span>
              </div>
            ))}
          </div>
        </div>
        )}
      </div>

      {/* Change Password */}
      <div className="bg-white dark:bg-[#0f1729] rounded-xl border border-slate-200 dark:border-slate-800 p-6">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
          <Lock className="w-4 h-4" /> Change Password
        </h2>

        {pwMsg.text && (
          <div className={`mb-4 px-4 py-2.5 rounded-lg text-sm ${pwMsg.type === 'success' ? 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400' : 'bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400'}`}>
            {pwMsg.text}
          </div>
        )}

        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1">Current Password</label>
            <div className="relative">
              <input
                type={showCurrent ? 'text' : 'password'} value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required
                className="w-full px-3 py-2.5 pr-10 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button type="button" onClick={() => setShowCurrent(!showCurrent)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1">New Password</label>
            <div className="relative">
              <input
                type={showNew ? 'text' : 'password'} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required
                className="w-full px-3 py-2.5 pr-10 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button type="button" onClick={() => setShowNew(!showNew)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1">Confirm New Password</label>
            <input
              type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required
              className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button type="submit" disabled={saving}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium transition-colors">
            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
            Change Password
          </button>
        </form>
      </div>
    </div>
  );
}
