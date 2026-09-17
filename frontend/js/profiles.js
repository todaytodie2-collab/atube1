/**
 * A TuBe Ultra HD v2.0 - 6 Profiles & State Management
 * Features:
 * - 6 fully independent user profiles: أحمد, سارة, عمر, نورة, خالد, أطفال
 * - LocalStorage integrity guard with automatic healing fallback
 * - Independent favorites watchlist, watch history, and resume playback timestamps
 * - Live clock synchronizer
 */

const ProfilesManager = {
    PROFILES: [
        { id: 'ahmed', name: 'أحمد', role: 'الرئيسي', avatar: 'assets/app_icon.jpg', isKids: false },
        { id: 'sara', name: 'سارة', role: 'دراما وعائلي', avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150', isKids: false },
        { id: 'omar', name: 'عمر', role: 'أكشن وأنيمي', avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150', isKids: false },
        { id: 'noura', name: 'نورة', role: 'منوعات', avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150', isKids: false },
        { id: 'khaled', name: 'خالد', role: 'رياضة ووثائقي', avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150', isKids: false },
        { id: 'kids', name: 'أطفال', role: 'كرتون وترفيه', avatar: 'https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=150', isKids: true }
    ],

    activeProfileId: 'ahmed',

    init() {
        this.verifyLocalStorageIntegrity();
        this.startLiveClock();
        this.renderProfileModal();
        this.updateHeaderProfile();
    },

    verifyLocalStorageIntegrity() {
        try {
            const storedActive = localStorage.getItem('atube_active_profile');
            if (storedActive && this.PROFILES.some(p => p.id === storedActive)) {
                this.activeProfileId = storedActive;
            } else {
                this.activeProfileId = 'ahmed';
                localStorage.setItem('atube_active_profile', 'ahmed');
            }

            // Ensure profile data stores exist
            this.PROFILES.forEach(p => {
                const key = `atube_user_${p.id}`;
                const data = localStorage.getItem(key);
                if (!data) {
                    const initialData = {
                        favorites: [],
                        history: [],
                        playback_positions: {},
                        watched_episodes: []
                    };
                    localStorage.setItem(key, JSON.stringify(initialData));
                } else {
                    // Test parse
                    try {
                        JSON.parse(data);
                    } catch (e) {
                        console.warn(`[Profiles] Healing corrupted profile data for ${p.id}`);
                        localStorage.setItem(key, JSON.stringify({
                            favorites: [],
                            history: [],
                            playback_positions: {},
                            watched_episodes: []
                        }));
                    }
                }
            });
        } catch (err) {
            console.error('[Profiles] LocalStorage integrity check error:', err);
        }
    },

    getActiveProfile() {
        return this.PROFILES.find(p => p.id === this.activeProfileId) || this.PROFILES[0];
    },

    setActiveProfile(profileId) {
        if (this.PROFILES.some(p => p.id === profileId)) {
            this.activeProfileId = profileId;
            localStorage.setItem('atube_active_profile', profileId);
            this.updateHeaderProfile();
            this.renderProfileModal();
            // Dispatch event for UI re-render
            window.dispatchEvent(new CustomEvent('profileChanged', { detail: this.getActiveProfile() }));
        }
    },

    getProfileData(profileId = null) {
        const id = profileId || this.activeProfileId;
        try {
            const raw = localStorage.getItem(`atube_user_${id}`);
            return raw ? JSON.parse(raw) : { favorites: [], history: [], playback_positions: {}, watched_episodes: [] };
        } catch (e) {
            return { favorites: [], history: [], playback_positions: {}, watched_episodes: [] };
        }
    },

    saveProfileData(data, profileId = null) {
        const id = profileId || this.activeProfileId;
        try {
            localStorage.setItem(`atube_user_${id}`, JSON.stringify(data));
        } catch (e) {
            console.warn('[Profiles] Failed to save profile data:', e);
        }
    },

    // Favorites
    toggleFavorite(mediaItem) {
        const data = this.getProfileData();
        const existsIdx = data.favorites.findIndex(f => f.id === mediaItem.id);
        let added = false;
        if (existsIdx > -1) {
            data.favorites.splice(existsIdx, 1);
        } else {
            data.favorites.unshift(mediaItem);
            added = true;
        }
        this.saveProfileData(data);
        return added;
    },

    isFavorite(mediaId) {
        const data = this.getProfileData();
        return data.favorites.some(f => f.id === mediaId);
    },

    // Resume playback position
    savePlaybackPosition(mediaId, seconds) {
        if (!mediaId || seconds < 5) return;
        const data = this.getProfileData();
        data.playback_positions[mediaId] = Math.floor(seconds);
        this.saveProfileData(data);
    },

    getPlaybackPosition(mediaId) {
        const data = this.getProfileData();
        return data.playback_positions[mediaId] || 0;
    },

    // Watched episodes
    markEpisodeWatched(mediaId, season, episode) {
        const key = `${mediaId}_s${season}_e${episode}`;
        const data = this.getProfileData();
        if (!data.watched_episodes.includes(key)) {
            data.watched_episodes.push(key);
            this.saveProfileData(data);
        }
    },

    isEpisodeWatched(mediaId, season, episode) {
        const key = `${mediaId}_s${season}_e${episode}`;
        const data = this.getProfileData();
        return data.watched_episodes.includes(key);
    },

    // Header & Modal UI
    updateHeaderProfile() {
        const profile = this.getActiveProfile();
        const avatarEl = document.getElementById('header-avatar');
        const nameEl = document.getElementById('header-user-name');
        if (avatarEl) avatarEl.src = profile.avatar;
        if (nameEl) nameEl.textContent = profile.name;
    },

    renderProfileModal() {
        const container = document.getElementById('profiles-grid');
        if (!container) return;

        container.innerHTML = this.PROFILES.map(p => `
            <div class="profile-card focusable ${p.id === this.activeProfileId ? 'active-user' : ''}" 
                 data-profile-id="${p.id}" tabindex="0" role="button">
                <img src="${p.avatar}" alt="${p.name}" class="profile-card-avatar" onerror="this.src='assets/app_icon.jpg'">
                <div class="profile-card-name">${p.name}</div>
                <div style="font-size:0.75rem; color:var(--text-dim);">${p.role}</div>
            </div>
        `).join('');

        container.querySelectorAll('.profile-card').forEach(card => {
            card.addEventListener('click', () => {
                const pId = card.getAttribute('data-profile-id');
                this.setActiveProfile(pId);
                this.closeProfileModal();
            });
        });
    },

    openProfileModal() {
        const modal = document.getElementById('profiles-modal');
        if (modal) {
            modal.classList.add('active');
            const activeCard = modal.querySelector('.profile-card.active-user') || modal.querySelector('.profile-card');
            if (activeCard && window.TVNav) {
                window.TVNav.setFocus(activeCard);
            }
        }
    },

    closeProfileModal() {
        const modal = document.getElementById('profiles-modal');
        if (modal) modal.classList.remove('active');
        const btn = document.getElementById('profile-btn');
        if (btn && window.TVNav) window.TVNav.setFocus(btn);
    },

    // Live Clock (e.g. 8:30 PM)
    startLiveClock() {
        const update = () => {
            const clockEl = document.getElementById('live-clock');
            if (!clockEl) return;
            const now = new Date();
            let hours = now.getHours();
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const ampm = hours >= 12 ? 'PM' : 'AM';
            hours = hours % 12;
            hours = hours ? hours : 12;
            clockEl.textContent = `${hours}:${minutes} ${ampm}`;
        };
        update();
        setInterval(update, 10000);
    }
};

window.ProfilesManager = ProfilesManager;
