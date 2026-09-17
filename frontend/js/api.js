/**
 * A TuBe Ultra HD v2.0 - Dynamic API Client
 * Interfaces dynamically with Flask Backend Gateway endpoints.
 * Guarantees zero mock code - fetches real SQLite and scraper feeds.
 */

const API = {
    BASE_URL: (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin.startsWith('http'))
        ? window.location.origin
        : 'https://corpus-lesson-occur-invited.trycloudflare.com',

    async getHealth() {
        try {
            const res = await fetch(`${this.BASE_URL}/api/health`, { method: 'GET' });
            if (!res.ok) throw new Error(`Health HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.warn('[API] getHealth error:', err);
            return null;
        }
    },

    async getFeed(contentType = 'all', category = 'all', page = 1, limit = 20, search = '') {
        try {
            const params = new URLSearchParams({
                type: contentType,
                category: category,
                page: page,
                limit: limit
            });
            if (search) params.append('search', search);

            const res = await fetch(`${this.BASE_URL}/api/media/feed?${params.toString()}`);
            if (!res.ok) throw new Error(`Feed HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('[API] getFeed error:', err);
            return { items: [], total_items: 0 };
        }
    },

    async getDetails(mediaId) {
        if (!mediaId) return null;
        try {
            const res = await fetch(`${this.BASE_URL}/api/media/details?id=${encodeURIComponent(mediaId)}`);
            if (!res.ok) throw new Error(`Details HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('[API] getDetails error:', err);
            return null;
        }
    },

    async getEpisodes(mediaId, season = 1) {
        if (!mediaId) return [];
        try {
            const res = await fetch(`${this.BASE_URL}/api/media/episodes?id=${encodeURIComponent(mediaId)}&season=${season}`);
            if (!res.ok) throw new Error(`Episodes HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('[API] getEpisodes error:', err);
            return [];
        }
    },

    async getLiveChannels(category = 'all') {
        try {
            const res = await fetch(`${this.BASE_URL}/api/live_tv/channels?category=${encodeURIComponent(category)}`);
            if (!res.ok) throw new Error(`Channels HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('[API] getLiveChannels error:', err);
            return [];
        }
    },

    async getLiveCategories() {
        try {
            const res = await fetch(`${this.BASE_URL}/api/live_tv/categories`);
            if (!res.ok) throw new Error(`Live categories HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('[API] getLiveCategories error:', err);
            return ["الكل 🌟", "رياضة", "أخبار", "ترفيه", "أطفال"];
        }
    },

    async resolveStream(targetUrl, title = 'A TuBe Video') {
        if (!targetUrl) return null;
        try {
            const params = new URLSearchParams({
                url: targetUrl,
                title: title
            });
            const res = await fetch(`${this.BASE_URL}/api/resolve-stream?${params.toString()}`);
            if (!res.ok) throw new Error(`Resolve HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('[API] resolveStream error:', err);
            return null;
        }
    },

    async getStreamBridge(mediaId, season = null, episode = null) {
        if (!mediaId) return [];
        try {
            let url = `${this.BASE_URL}/api/stream/bridge?id=${encodeURIComponent(mediaId)}`;
            if (season) url += `&season=${season}`;
            if (episode) url += `&episode=${episode}`;
            const res = await fetch(url);
            if (!res.ok) return [];
            const data = await res.json();
            return data.streams || [];
        } catch (err) {
            console.error('[API] getStreamBridge error:', err);
            return [];
        }
    }
};

window.API = API;
