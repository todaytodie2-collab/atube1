/**
 * A TuBe Ultra HD v2.7 - Smart Unified Video Player Controller
 * Features:
 * - Default: Ultra-lightweight Built-in Web Video Player (HTML5 + HLS.js)
 * - Touch & TV Remote Friendly On-screen Controls (Seek, Play/Pause, 10s Skip, Volume, Fullscreen)
 * - Automatic Resolution, Stream Proxying & Error Auto-Recovery
 * - Optional External Player Integration (ASD Player, Android System, 1DM Download)
 */

const PlayerController = {
    preferredPlayer: 'internal', // 'internal' | 'asd' | 'system' | '1dm'
    currentMedia: null,
    currentServer: null,
    currentUrl: '',
    currentTitle: '',
    currentQuality: '',
    hlsInstance: null,
    controlsTimeout: null,
    isSeeking: false,
    saveProgressInterval: null,

    init() {
        // Load saved player preference or default to internal
        try {
            const saved = localStorage.getItem('atube_preferred_player');
            if (saved && ['internal', 'asd', 'system', '1dm', 'tdm'].includes(saved)) {
                this.preferredPlayer = (saved === 'tdm') ? 'internal' : saved;
            }
        } catch (e) {}

        this.syncPlayerChips();
        this.setupChipListeners();
        this.setupPlayerUI();
        this.setupKeyboardControls();
    },

    setupChipListeners() {
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
            let pName = 'المشغل الداخلي ⚡';
            if (playerType === 'easy') pName = 'Easy Player 🎬';
            else if (playerType === 'asd') pName = 'ASD Player 🚀';
            else if (playerType === 'system') pName = 'مشغل النظام 📱';
            else if (playerType === '1dm') pName = 'تحميل 1DM 📥';
            window.TVNav.showExitToast(`تم تعيين ${pName} كمشغل افتراضي`);
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

    // =========================================================================
    // 1. BUILT-IN INTERNAL LIGHTWEIGHT VIDEO PLAYER (Native HTML5 + Hls.js)
    // =========================================================================
    async playInInternalPlayer(serverUrl, mediaInfo = {}) {
        this.closeServersBottomSheet();

        const title = mediaInfo.title || (this.currentMedia ? (this.currentMedia.arabic_title || this.currentMedia.title) : 'فيديو A TuBe');
        const mediaId = mediaInfo.mediaId || (this.currentMedia ? this.currentMedia.id : null);
        const quality = mediaInfo.quality || '1080p FHD';

        this.currentUrl = serverUrl;
        this.currentTitle = title;
        this.currentQuality = quality;

        const container = document.getElementById('player-container');
        const video = document.getElementById('main-video');
        const titleEl = document.getElementById('player-video-title');
        const subEl = document.getElementById('player-video-sub');
        const qualityEl = document.getElementById('player-quality-badge');
        const loader = document.getElementById('player-loader');
        const loaderText = document.getElementById('player-loader-text');

        if (!container || !video) return;

        video.playsInline = true;
        try {
            video.setAttribute('playsinline', '');
            video.setAttribute('webkit-playsinline', '');
        } catch(e) {}

        // Display player container
        container.classList.add('active');
        if (titleEl) titleEl.textContent = title;
        if (subEl) subEl.textContent = (mediaInfo.subtitle || '');
        if (qualityEl) qualityEl.textContent = quality;

        if (loader) {
            loader.classList.add('active');
            if (loaderText) loaderText.textContent = 'جاري الاتصال بالسيرفر وتجهيز البث النظيف...';
        }

        this.showControlsTemporarily();

        // 1. Resolve direct stream URL via Backend Bridge / Resolver
        let targetStreamUrl = serverUrl;
        try {
            if (serverUrl && (serverUrl.includes('akwam') || serverUrl.includes('egydead') || serverUrl.includes('mycima') || serverUrl.includes('faselhd') || !serverUrl.match(/\.(mp4|m3u8|mkv)(\?.*)?$/i))) {
                if (loaderText) loaderText.textContent = 'جاري فك تشفير وتخطي إعلانات السيرفر ⚡...';
                const resolved = await window.API.resolveStream(serverUrl, title);
                if (resolved && resolved.success && resolved.stream_url) {
                    targetStreamUrl = resolved.abs_proxy_stream_url || resolved.proxy_stream_url || resolved.stream_url;
                }
            }
        } catch (e) {
            console.warn('[PlayerController] Stream resolve warning:', e);
        }

        // Guarantee absolute URL
        if (targetStreamUrl && targetStreamUrl.startsWith('/')) {
            const base = (window.API && window.API.BASE_URL) ? window.API.BASE_URL : window.location.origin;
            targetStreamUrl = base + targetStreamUrl;
        }

        console.log('[PlayerController] Playing Stream in Internal Player:', targetStreamUrl);

        // 2. Cleanup previous instance
        if (this.hlsInstance) {
            this.hlsInstance.destroy();
            this.hlsInstance = null;
        }
        video.pause();
        video.removeAttribute('src');
        video.load();

        // 3. Mount Stream into Video element (Hls.js or Native HTML5)
        const isHls = targetStreamUrl.includes('.m3u8') || targetStreamUrl.includes('/proxy') || targetStreamUrl.includes('m3u');

        if (isHls && window.Hls && Hls.isSupported()) {
            const hls = new Hls({
                maxBufferLength: 30,
                maxMaxBufferLength: 60,
                enableWorker: true,
                lowLatencyMode: true,
                manifestLoadingTimeOut: 12000
            });

            this.hlsInstance = hls;
            hls.loadSource(targetStreamUrl);
            hls.attachMedia(video);

            hls.on(Hls.Events.MANIFEST_PARSED, () => {
                if (loader) loader.classList.remove('active');
                video.play().catch(err => {
                    console.log('[PlayerController] Autoplay policy prevented direct playback:', err);
                    video.muted = true;
                    video.play().catch(() => {});
                });
            });

            hls.on(Hls.Events.ERROR, (event, data) => {
                console.warn('[PlayerController] HLS error:', data);
                if (data.fatal) {
                    switch (data.type) {
                        case Hls.ErrorTypes.NETWORK_ERROR:
                            console.log('[PlayerController] Recovering network error...');
                            hls.startLoad();
                            break;
                        case Hls.ErrorTypes.MEDIA_ERROR:
                            console.log('[PlayerController] Recovering media error...');
                            hls.recoverMediaError();
                            break;
                        default:
                            hls.destroy();
                            // Fallback to direct video src
                            video.src = targetStreamUrl;
                            video.play().catch(() => {});
                            break;
                    }
                }
            });
        } else {
            video.src = targetStreamUrl;
            video.oncanplay = () => {
                if (loader) loader.classList.remove('active');
            };
            video.play().catch(err => {
                console.log('[PlayerController] Direct video autoplay notice:', err);
                video.muted = true;
                video.play().catch(() => {});
            });
        }

        // Start progress auto-saver
        if (this.saveProgressInterval) clearInterval(this.saveProgressInterval);
        this.saveProgressInterval = setInterval(() => {
            if (video && !video.paused && video.currentTime > 0 && mediaId && window.ProfilesManager) {
                window.ProfilesManager.savePlaybackPosition(mediaId, Math.floor(video.currentTime));
            }
        }, 5000);
    },

    closeInternalPlayer() {
        const container = document.getElementById('player-container');
        const video = document.getElementById('main-video');
        const loader = document.getElementById('player-loader');

        if (this.saveProgressInterval) {
            clearInterval(this.saveProgressInterval);
            this.saveProgressInterval = null;
        }

        if (video) {
            video.pause();
            if (this.currentMedia && window.ProfilesManager) {
                window.ProfilesManager.savePlaybackPosition(this.currentMedia.id, Math.floor(video.currentTime || 0));
            }
            video.removeAttribute('src');
            video.load();
        }

        if (this.hlsInstance) {
            this.hlsInstance.destroy();
            this.hlsInstance = null;
        }

        if (container) {
            container.classList.remove('active');
        }

        if (loader) {
            loader.classList.remove('active');
        }

        // Exit fullscreen if active
        if (document.fullscreenElement) {
            document.exitFullscreen().catch(() => {});
        }
    },

    // =========================================================================
    // 2. PLAYER UI SETUP & INTERACTIONS
    // =========================================================================
    setupPlayerUI() {
        const container = document.getElementById('player-container');
        const video = document.getElementById('main-video');
        const backBtn = document.getElementById('player-back-btn');
        const playBtn = document.getElementById('player-btn-play');
        const playIcon = document.getElementById('player-play-icon');
        const rwdBtn = document.getElementById('player-btn-rwd');
        const fwdBtn = document.getElementById('player-btn-fwd');
        const volBtn = document.getElementById('player-btn-volume');
        const volSlider = document.getElementById('player-volume-slider');
        const volIcon = document.getElementById('player-volume-icon');
        const fullBtn = document.getElementById('player-btn-fullscreen');
        const extSwitchBtn = document.getElementById('player-ext-switch-btn');
        const progContainer = document.getElementById('player-progress-container');
        const progFill = document.getElementById('player-progress-fill');
        const progBuffered = document.getElementById('player-progress-buffered');
        const timeCurr = document.getElementById('player-time-current');
        const timeTotal = document.getElementById('player-time-duration');
        const loader = document.getElementById('player-loader');

        if (!video || !container) return;

        // Back / Close
        if (backBtn) {
            backBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.closeInternalPlayer();
            });
        }

        // Play / Pause Toggle
        const togglePlayPause = () => {
            if (video.paused) {
                video.play();
                if (playIcon) playIcon.textContent = '⏸';
                this.triggerCenterIndicator('▶');
            } else {
                video.pause();
                if (playIcon) playIcon.textContent = '▶';
                this.triggerCenterIndicator('⏸');
            }
            this.showControlsTemporarily();
        };

        if (playBtn) playBtn.addEventListener('click', (e) => { e.stopPropagation(); togglePlayPause(); });
        video.addEventListener('click', () => togglePlayPause());

        // Forward / Rewind 10s
        if (rwdBtn) {
            rwdBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                video.currentTime = Math.max(0, video.currentTime - 10);
                this.triggerCenterIndicator('↺ 10s');
                this.showControlsTemporarily();
            });
        }

        if (fwdBtn) {
            fwdBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                video.currentTime = Math.min(video.duration || 999999, video.currentTime + 10);
                this.triggerCenterIndicator('↻ 10s');
                this.showControlsTemporarily();
            });
        }

        // Volume & Mute
        if (volBtn) {
            volBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                video.muted = !video.muted;
                if (volIcon) volIcon.textContent = video.muted ? '🔇' : '🔊';
                if (volSlider) volSlider.value = video.muted ? 0 : video.volume;
                this.showControlsTemporarily();
            });
        }

        if (volSlider) {
            volSlider.addEventListener('input', (e) => {
                e.stopPropagation();
                const val = parseFloat(e.target.value);
                video.volume = val;
                video.muted = (val === 0);
                if (volIcon) volIcon.textContent = (val === 0) ? '🔇' : '🔊';
                this.showControlsTemporarily();
            });
        }

        // Fullscreen Toggle
        if (fullBtn) {
            fullBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (!document.fullscreenElement) {
                    if (container.requestFullscreen) container.requestFullscreen();
                    else if (container.webkitRequestFullscreen) container.webkitRequestFullscreen();
                } else {
                    if (document.exitFullscreen) document.exitFullscreen();
                }
                this.showControlsTemporarily();
            });
        }

        // Switch to External Player
        if (extSwitchBtn) {
            extSwitchBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const targetUrl = this.currentUrl;
                const targetTitle = this.currentTitle;
                this.closeInternalPlayer();
                this.executeLaunch(targetUrl, targetTitle, null, 'asd');
            });
        }

        // Video Progress & Time Updates
        const formatTime = (secs) => {
            if (isNaN(secs) || secs < 0) return '00:00';
            const h = Math.floor(secs / 3600);
            const m = Math.floor((secs % 3600) / 60);
            const s = Math.floor(secs % 60);
            const pad = (n) => String(n).padStart(2, '0');
            return h > 0 ? `${pad(h)}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
        };

        video.addEventListener('timeupdate', () => {
            if (!this.isSeeking && video.duration) {
                const pct = (video.currentTime / video.duration) * 100;
                if (progFill) progFill.style.width = `${pct}%`;
                if (timeCurr) timeCurr.textContent = formatTime(video.currentTime);
                if (timeTotal) timeTotal.textContent = formatTime(video.duration);
            }
        });

        video.addEventListener('progress', () => {
            if (video.buffered.length > 0 && video.duration) {
                const bufferedEnd = video.buffered.end(video.buffered.length - 1);
                const bufPct = (bufferedEnd / video.duration) * 100;
                if (progBuffered) progBuffered.style.width = `${bufPct}%`;
            }
        });

        video.addEventListener('playing', () => {
            if (loader) loader.classList.remove('active');
            if (playIcon) playIcon.textContent = '⏸';
        });

        video.addEventListener('waiting', () => {
            if (loader) loader.classList.add('active');
        });

        video.addEventListener('pause', () => {
            if (playIcon) playIcon.textContent = '▶';
        });

        // Seek Bar Click / Touch Handling
        const handleSeek = (e) => {
            if (!video.duration || !progContainer) return;
            const rect = progContainer.getBoundingClientRect();
            const clientX = e.clientX || (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
            const offsetX = Math.max(0, Math.min(rect.width, rect.right - clientX)); // RTL calculation
            const pct = offsetX / rect.width;
            video.currentTime = pct * video.duration;
            if (progFill) progFill.style.width = `${pct * 100}%`;
            this.showControlsTemporarily();
        };

        if (progContainer) {
            progContainer.addEventListener('click', (e) => handleSeek(e));
        }

        // Show controls on mouse move / touch
        container.addEventListener('mousemove', () => this.showControlsTemporarily());
        container.addEventListener('touchstart', () => this.showControlsTemporarily(), { passive: true });
    },

    showControlsTemporarily() {
        const topBar = document.getElementById('player-top-bar');
        const overlay = document.getElementById('player-controls-overlay');
        const video = document.getElementById('main-video');

        if (topBar) topBar.classList.remove('hide');
        if (overlay) overlay.classList.remove('hide');

        if (this.controlsTimeout) clearTimeout(this.controlsTimeout);

        if (video && !video.paused) {
            this.controlsTimeout = setTimeout(() => {
                if (topBar) topBar.classList.add('hide');
                if (overlay) overlay.classList.add('hide');
            }, 3500);
        }
    },

    triggerCenterIndicator(symbol) {
        const center = document.getElementById('player-center-action');
        const icon = document.getElementById('player-center-icon');
        if (!center || !icon) return;

        icon.textContent = symbol;
        center.classList.add('animate');
        setTimeout(() => {
            center.classList.remove('animate');
        }, 350);
    },

    setupKeyboardControls() {
        window.addEventListener('keydown', (e) => {
            const container = document.getElementById('player-container');
            if (!container || !container.classList.contains('active')) return;

            const video = document.getElementById('main-video');
            if (!video) return;

            if (e.key === 'Escape' || e.key === 'Back' || e.keyCode === 10009 || e.keyCode === 461) {
                e.preventDefault();
                this.closeInternalPlayer();
            } else if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                if (video.paused) video.play(); else video.pause();
                this.showControlsTemporarily();
            } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                video.currentTime = Math.min(video.duration || 999999, video.currentTime + 10);
                this.triggerCenterIndicator('↻ 10s');
                this.showControlsTemporarily();
            } else if (e.key === 'ArrowLeft') {
                e.preventDefault();
                video.currentTime = Math.max(0, video.currentTime - 10);
                this.triggerCenterIndicator('↺ 10s');
                this.showControlsTemporarily();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                video.volume = Math.min(1, video.volume + 0.1);
                this.showControlsTemporarily();
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                video.volume = Math.max(0, video.volume - 0.1);
                this.showControlsTemporarily();
            } else if (e.key.toLowerCase() === 'f') {
                e.preventDefault();
                if (!document.fullscreenElement) container.requestFullscreen?.();
                else document.exitFullscreen?.();
            }
        });
    },

    // =========================================================================
    // 3. UNIFIED DISPATCHER (INTERNAL VS EXTERNAL INTENT)
    // =========================================================================
    async requestPlayUrl(serverUrl, mediaInfo = {}) {
        if (!serverUrl) {
            if (window.TVNav) window.TVNav.showExitToast('عذراً، رابط السيرفر غير متوفر');
            return;
        }

        if (this.preferredPlayer === 'internal') {
            await this.playInInternalPlayer(serverUrl, mediaInfo);
        } else {
            await this.executeLaunch(serverUrl, mediaInfo.title, mediaInfo.mediaId, this.preferredPlayer);
        }
    },

    // External Player Intent Dispatcher (ASD Player, System Player, 1DM Download)
    async executeLaunch(sUrl, title = 'Video', mediaId = null, targetPlayer = null) {
        this.closeServersBottomSheet();
        const pType = targetPlayer || this.preferredPlayer;
        
        let pName = 'Easy Player 🎬';
        if (pType === 'asd') pName = 'ASD Player 🚀';
        else if (pType === 'system') pName = 'مشغل النظام 📱';
        else if (pType === '1dm') pName = 'مدير التحميل 1DM 📥';

        if (window.TVNav) window.TVNav.showExitToast(`جاري فتح الرابط في ${pName}...`);

        let resolvedStream = sUrl;
        let intentUrl = '';

        if (sUrl) {
            try {
                const res = await window.API.resolveStream(sUrl, title);
                if (res && res.success && res.stream_url) {
                    resolvedStream = res.abs_proxy_stream_url || res.proxy_stream_url || res.stream_url;
                }
            } catch (err) {
                console.warn('[PlayerController] Intent stream resolution warning:', err);
            }
        }

        let targetStream = resolvedStream || sUrl;
        if (targetStream && targetStream.startsWith('/')) {
            const base = (window.API && window.API.BASE_URL) ? window.API.BASE_URL : window.location.origin;
            targetStream = base + targetStream;
        }

        const scheme = targetStream.startsWith('https') ? 'https' : 'http';
        const body = targetStream.replace(/^https?:\/\//, '');
        const encTitle = encodeURIComponent(title || 'Video');

        if (pType === 'easy') {
            intentUrl = `intent://${body}#Intent;scheme=${scheme};package=com.player.easy;type=video/*;action=android.intent.action.VIEW;S.title=${encTitle};end`;
        } else if (pType === 'asd') {
            intentUrl = `intent://${body}#Intent;scheme=${scheme};package=com.app_mo.splayer;type=video/*;action=android.intent.action.VIEW;S.title=${encTitle};end`;
        } else if (pType === '1dm') {
            intentUrl = `intent://${body}#Intent;scheme=${scheme};package=idm.internet.download.manager;type=video/*;action=android.intent.action.VIEW;S.title=${encTitle};end`;
        } else {
            // Android generic system video intent
            intentUrl = `intent://${body}#Intent;scheme=${scheme};type=video/*;action=android.intent.action.VIEW;S.title=${encTitle};end`;
        }

        console.log(`[PlayerController] Dispatching ${pType} Intent:`, intentUrl);

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
            console.warn('[PlayerController] Link click failed, fallback assign:', e);
            window.location.assign(intentUrl);
        }
    },

    // Backward compatibility helpers
    requestPlay(mediaItem, serverItem = null) {
        if (window.App && window.App.openServersBottomSheet) {
            window.App.openServersBottomSheet(mediaItem);
        } else {
            const sUrl = serverItem ? (serverItem.url || serverItem.stream_url) : ((mediaItem.servers && mediaItem.servers[0] && mediaItem.servers[0].url) || '');
            this.requestPlayUrl(sUrl, { title: mediaItem.arabic_title || mediaItem.title, mediaId: mediaItem.id });
        }
    },

    launchExternalPlayer(serverUrl, mediaInfo = {}) {
        this.requestPlayUrl(serverUrl, mediaInfo);
    }
};

window.PlayerController = PlayerController;
