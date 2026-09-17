/**
 * A TuBe Ultra HD v2.0 - External Video Player Intent Dispatcher
 * Directly launches external mobile/TV players without any internal web player:
 * - TDM Player (com.tdm.manager)
 * - ASD Player (com.app_mo.splayer)
 * - Android System Player Chooser (Generic Video Intent)
 */

const PlayerController = {
    preferredPlayer: 'tdm',
    currentMedia: null,
    currentServer: null,

    init() {
        // Load saved player preference or default to TDM
        try {
            const saved = localStorage.getItem('atube_preferred_player');
            if (saved && ['tdm', 'asd', 'system'].includes(saved)) {
                this.preferredPlayer = saved;
            }
        } catch (e) {}

        this.syncPlayerChips();

        // Setup bottom sheet chips
        document.querySelectorAll('.player-chip').forEach(chip => {
            chip.addEventListener('click', (e) => {
                const target = chip.dataset.player;
                if (target) {
                    this.setPreferredPlayer(target);
                }
            });
        });

        // Close bottom sheet button
        const closeBtn = document.getElementById('sheet-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeServersBottomSheet());
        }

        const sheetOverlay = document.getElementById('servers-bottom-sheet');
        if (sheetOverlay) {
            sheetOverlay.addEventListener('click', (e) => {
                if (e.target === sheetOverlay) {
                    this.closeServersBottomSheet();
                }
            });
        }
    },

    setPreferredPlayer(playerType) {
        this.preferredPlayer = playerType;
        try {
            localStorage.setItem('atube_preferred_player', playerType);
        } catch (e) {}
        this.syncPlayerChips();
        if (window.TVNav) {
            const pName = playerType === 'tdm' ? 'TDM Player ⚡' : (playerType === 'asd' ? 'ASD Player 🚀' : 'مشغل النظام 📱');
            window.TVNav.showExitToast(`تم اختيار ${pName} كمشغل افتراضي`);
        }
    },

    syncPlayerChips() {
        document.querySelectorAll('.player-chip').forEach(chip => {
            if (chip.dataset.player === this.preferredPlayer) {
                chip.classList.add('active');
            } else {
                chip.classList.remove('active');
            }
        });
    },

    closeServersBottomSheet() {
        const sheet = document.getElementById('servers-bottom-sheet');
        if (sheet) sheet.classList.remove('active');
    },

    // Main entry point for playing a stream directly via external player
    async launchExternalPlayer(serverUrl, mediaInfo = {}) {
        this.closeServersBottomSheet();

        const title = mediaInfo.title || (this.currentMedia ? (this.currentMedia.arabic_title || this.currentMedia.title) : 'فيديو A TuBe');
        const mediaId = mediaInfo.mediaId || (this.currentMedia ? this.currentMedia.id : null);

        await this.executeLaunch(serverUrl, title, mediaId);
    },

    // Direct Intent Execution
    async executeLaunch(sUrl, title, mediaId = null) {
        const pName = this.preferredPlayer === 'tdm' ? 'TDM Player ⚡' : (this.preferredPlayer === 'asd' ? 'ASD Player 🚀' : 'مشغل النظام 📱');
        if (window.TVNav) window.TVNav.showExitToast(`جاري فتح البث المباشر في ${pName}...`);

        let resolvedStream = sUrl;
        let intentUrl = '';
        let genericIntentUrl = '';

        if (sUrl) {
            try {
                const res = await window.API.resolveStream(sUrl, title);
                if (res && res.success === false) {
                    if (window.TVNav) {
                        window.TVNav.showExitToast(res.error || 'عذراً، هذا السيرفر غير متاح حالياً، يرجى اختيار سيرفر آخر.');
                    }
                    return;
                }
                if (res) {
                    resolvedStream = res.abs_proxy_stream_url || res.proxy_stream_url || res.stream_url || sUrl;
                    if (this.preferredPlayer === 'asd' && res.asdplayer_intent) {
                        intentUrl = res.asdplayer_intent;
                    }
                    genericIntentUrl = res.generic_intent || '';
                }
            } catch (err) {
                console.warn('[PlayerController] resolveStream warning, using direct url:', err);
            }
        }

        // Guarantee absolute URL for external mobile player
        let targetStream = resolvedStream || sUrl;
        if (targetStream && targetStream.startsWith('/')) {
            const base = (window.API && window.API.BASE_URL) ? window.API.BASE_URL : window.location.origin;
            targetStream = base + targetStream;
        }

        const scheme = (targetStream && targetStream.startsWith('https')) ? 'https' : 'http';
        const body = (targetStream || '').replace(/^https?:\/\//, '');
        const encTitle = encodeURIComponent(title || 'Video');

        // Build target intent URL based on user preference
        if (!intentUrl) {
            if (this.preferredPlayer === 'tdm') {
                // Support both TDM and 1DM Video Player Intent
                intentUrl = `intent://${body}#Intent;scheme=${scheme};package=idm.internet.download.manager;type=video/*;action=android.intent.action.VIEW;S.title=${encTitle};end`;
            } else if (this.preferredPlayer === 'asd') {
                // Support ASD / SPlayer Intent
                intentUrl = `intent://${body}#Intent;scheme=${scheme};package=com.app_mo.splayer;type=video/*;action=android.intent.action.VIEW;S.title=${encTitle};end`;
            } else {
                intentUrl = `intent://${body}#Intent;scheme=${scheme};type=video/*;action=android.intent.action.VIEW;S.title=${encTitle};end`;
            }
        }

        if (!genericIntentUrl) {
            genericIntentUrl = `intent://${body}#Intent;scheme=${scheme};type=video/*;action=android.intent.action.VIEW;S.title=${encTitle};end`;
        }

        console.log(`[PlayerController] Dispatching ${this.preferredPlayer} Intent:`, intentUrl);

        // Save playback progress
        if (window.ProfilesManager && mediaId) {
            window.ProfilesManager.savePlaybackPosition(mediaId, 10);
        }

        // Method 1: DOM link click (preserves user gesture activation on Android Chrome)
        try {
            const link = document.createElement('a');
            link.href = intentUrl;
            link.rel = 'noreferrer';
            document.body.appendChild(link);
            link.click();
            setTimeout(() => {
                if (document.body.contains(link)) document.body.removeChild(link);
            }, 1000);
        } catch (e) {
            console.warn('[PlayerController] link click failed:', e);
        }

        // Method 2: Fallback direct assign after brief timeout
        setTimeout(() => {
            try {
                window.location.assign(intentUrl);
            } catch (e) {
                if (genericIntentUrl && genericIntentUrl !== intentUrl) {
                    try { window.location.assign(genericIntentUrl); } catch (err) {}
                }
            }
        }, 300);

        if (window.TVNav) {
            setTimeout(() => {
                window.TVNav.showExitToast(`تم إرسال أمر التشغيل إلى ${pName}`);
            }, 1000);
        }
    },

    // Backward-compatibility stubs for external calls
    requestPlay(mediaItem, serverItem = null) {
        if (window.App && window.App.openServersBottomSheet) {
            window.App.openServersBottomSheet(mediaItem);
        } else {
            const sUrl = serverItem ? (serverItem.url || serverItem.stream_url) : (mediaItem.servers && mediaItem.servers[0] && mediaItem.servers[0].url) || '';
            this.launchExternalPlayer(sUrl, { title: mediaItem.arabic_title || mediaItem.title, mediaId: mediaItem.id });
        }
    },

    launchASDPlayer() {
        this.setPreferredPlayer('asd');
        if (this.currentServer) {
            this.launchExternalPlayer(this.currentServer.url, { title: this.currentMedia.arabic_title || this.currentMedia.title });
        }
    },

    playInInternalPlayer(serverUrl, mediaInfo = {}) {
        // Redirect to external player as user requested removal of internal player
        this.launchExternalPlayer(serverUrl, mediaInfo);
    }
};

window.PlayerController = PlayerController;
