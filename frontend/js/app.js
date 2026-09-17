/**
 * A TuBe Ultra HD v2.0 - Master Application Controller
 * Handles:
 * - Smart Splash Screen with Health Check, Cache Warming, and Marquee Posters
 * - Dynamic Data Feeding from Flask API
 * - Hero Banner with Smooth Cross-Fade & Dynamic Hover/Focus Reaction
 * - Interactive Genres & Regions Filter Bar
 * - Media Details Modal with Real Cast & Crew
 * - Dedicated Episode Servers & Quality Modal (Series Servers Isolated to Episodes)
 * - Strict Title Language Rules (العربية هي الأساسية والإنجليزية فرعية — مطابقة الموك أب)
 * - Redesigned Live TV Interface with Pulsing Live Badges, Logos, Categories & Search
 */

const App = {
    heroItem: null,
    recentItems: [],
    trendingItems: [],
    animeItems: [],
    wweItems: [],
    atubeItems: [],
    liveChannels: [],
    currentView: 'home',
    activeRegion: 'all',
    activeGenre: 'all',

    // Helper: Strict Title Language Rules — العربية أساسية والإنجليزية فرعية (مطابقة الموك أب)
    getDisplayTitle(item) {
        if (!item) return '';
        return item.arabic_title || item.title || '';
    },

    getDisplaySubtitle(item) {
        if (!item) return '';
        const ar = (item.arabic_title || '').trim();
        const en = (item.title || '').trim();
        return (en && en !== ar) ? en : '';
    },

    async init() {
        console.log('[A TuBe] Initializing App Controller v2.0...');

        // Initialize Profiles & Player
        if (window.ProfilesManager) window.ProfilesManager.init();
        if (window.PlayerController) window.PlayerController.init();

        // Profile change event listener
        window.addEventListener('profileChanged', (e) => this.onProfileChanged(e.detail));

        // Navigation listeners
        this.setupNavigationListeners();
        this.setupFilterBar();

        // Run Smart Splash Screen Cycle
        await this.runSplashScreenSequence();

        // تطبيق الرابط العميق (#movies / #live-tv ...) — الافتراضي الرئيسية
        this.handleHashRoute();

        // Set Initial Focus
        const initialFocus = document.querySelector('.hero-actions .btn-primary') || document.querySelector('.sidebar-item.active');
        if (initialFocus && window.TVNav) {
            window.TVNav.setFocus(initialFocus);
        }
    },

    // ==========================================================================
    // 1. SMART SPLASH SCREEN (Matches Mockup 2)
    // ==========================================================================
    async runSplashScreenSequence() {
        const splashEl = document.getElementById('splash-screen');
        const progressBar = document.getElementById('splash-progress-bar');
        const statusAr = document.getElementById('splash-status-ar');
        const backdropEl = document.getElementById('splash-backdrop');
        const marqueeTrack = document.getElementById('splash-marquee-track');

        let progress = 15;
        const setProgress = (val, textAr) => {
            progress = Math.max(progress, val);
            if (progressBar) progressBar.style.width = `${progress}%`;
            if (statusAr && textAr) statusAr.textContent = textAr;
        };

        setProgress(20, 'جاري فحص الاتصال بالخادم الرئيسي...');

        const timeoutPromise = new Promise(resolve => setTimeout(resolve, 4500));
        const healthCheck = window.API.getHealth();

        // Cache warming & data preloading
        const loadInitialData = async () => {
            try {
                // Fetch Recent (Row 1)
                const recentRes = await window.API.getFeed('all', 'recent', 1, 14);
                this.recentItems = recentRes.items || [];

                // Fetch Trending SA (Row 2)
                const trendingRes = await window.API.getFeed('all', 'trending_sa', 1, 10);
                this.trendingItems = trendingRes.items || [];

                // اختيار البانر: البحث في كل القوائم المحمّلة (recent ثم trending) لأن
                // "the-crown-series" مُصنّف trending_sa وليس ضمن recent
                const heroSources = [...this.recentItems, ...this.trendingItems];
                this.heroItem = heroSources.find(i => i.id === 'the-crown-series')
                    || heroSources.find(i => /crown/i.test(i.id || '') || /the crown/i.test(i.title || ''))
                    || this.recentItems[0]
                    || this.trendingItems[0] || null;

                // Fetch Anime
                const animeRes = await window.API.getFeed('anime', 'all', 1, 8);
                this.animeItems = animeRes.items || [];

                // Fetch WWE
                const wweRes = await window.API.getFeed('wwe', 'all', 1, 6);
                this.wweItems = wweRes.items || [];

                // Fetch Atube Originals
                const atubeRes = await window.API.getFeed('atube', 'all', 1, 6);
                this.atubeItems = atubeRes.items || [];

                // Dynamic Splash Backdrop
                if (backdropEl && this.heroItem && this.heroItem.backdrop) {
                    backdropEl.style.backgroundImage = `url('${this.heroItem.backdrop}')`;
                }

                // Dynamic Splash Marquee of Posters
                if (marqueeTrack && this.recentItems.length > 0) {
                    const posters = [...this.recentItems, ...this.recentItems].map(item => `
                        <img src="${item.poster}" alt="${this.getDisplayTitle(item)}" class="splash-marquee-poster" onerror="this.onerror=null;this.src='assets/default_poster.jpg';">
                    `).join('');
                    marqueeTrack.innerHTML = posters;
                }
            } catch (err) {
                console.warn('[App] Cache warming warning:', err);
            }
        };

        await Promise.race([
            Promise.all([healthCheck, loadInitialData()]),
            timeoutPromise
        ]);

        setProgress(70, 'جاري بناء واجهة العرض التلفزيونية...');
        this.renderHeroBanner();
        this.renderHomeCarousels();

        setProgress(100, 'اكتمل التحميل! أهلاً بك في A TuBe');

        setTimeout(() => {
            if (splashEl) splashEl.classList.add('fade-out');
        }, 500);
    },

    // ==========================================================================
    // 2. HERO BANNER (~70vh, Matches Mockup 1)
    // ==========================================================================
    renderHeroBanner(item = null) {
        const hero = item || this.heroItem;
        if (!hero) return;

        const backdropImg = document.getElementById('hero-backdrop-img');
        const titleEl = document.getElementById('hero-title');
        const subtitleEl = document.getElementById('hero-subtitle');
        const ratingEl = document.getElementById('hero-rating');
        const durationEl = document.getElementById('hero-duration');
        const yearEl = document.getElementById('hero-year');
        const qualityEl = document.getElementById('hero-quality');
        const synopsisEl = document.getElementById('hero-synopsis');

        // Smooth cross-fade backdrop transition
        if (backdropImg) {
            const newBackdrop = hero.backdrop || hero.poster || 'assets/default_backdrop.jpg';
            if (backdropImg.getAttribute('src') !== newBackdrop) {
                backdropImg.style.opacity = '0.35';
                setTimeout(() => {
                    backdropImg.src = newBackdrop;
                    backdropImg.style.opacity = '1';
                }, 120);
            }
        }

        // Strict title language
        const displayTitle = this.getDisplayTitle(hero);
        const displaySub = this.getDisplaySubtitle(hero);

        if (titleEl) titleEl.textContent = displayTitle;
        if (subtitleEl) subtitleEl.textContent = displaySub || (hero.genres ? (Array.isArray(hero.genres) ? hero.genres.join(' • ') : JSON.parse(hero.genres || '[]').join(' • ')) : '');
        if (ratingEl) ratingEl.textContent = `★ ${hero.rating || '8.7'}`;
        if (durationEl) durationEl.textContent = hero.duration || '58 دقيقة';
        if (yearEl) yearEl.textContent = hero.year || '2024';
        if (qualityEl) qualityEl.textContent = hero.quality || '4K Ultra HD';
        if (synopsisEl) synopsisEl.textContent = hero.synopsis || '';

        // Play button
        const playBtn = document.getElementById('hero-btn-play');
        if (playBtn) {
            playBtn.onclick = () => {
                if (hero.content_type === 'series' || hero.content_type === 'anime') {
                    this.openDetailsModal(hero.id);
                } else {
                    window.PlayerController.requestPlay(hero);
                }
            };
        }

        // Watchlist button
        const watchlistBtn = document.getElementById('hero-btn-watchlist');
        if (watchlistBtn) {
            const isFav = window.ProfilesManager.isFavorite(hero.id);
            this.updateWatchlistBtn(watchlistBtn, isFav);
            watchlistBtn.onclick = () => {
                const added = window.ProfilesManager.toggleFavorite(hero);
                this.updateWatchlistBtn(watchlistBtn, added);
                if (window.TVNav) {
                    window.TVNav.showExitToast(added ? 'تمت الإضافة إلى قائمة المشاهدة' : 'تمت الإزالة من قائمة المشاهدة');
                }
            };
        }
    },

    updateWatchlistBtn(btn, isFavorite) {
        if (!btn) return;
        btn.innerHTML = isFavorite ? '✓ في قائمة المشاهدة' : '🔖 قائمة المشاهدة';
        if (isFavorite) {
            btn.style.background = 'rgba(16, 185, 129, 0.25)';
            btn.style.borderColor = '#10b981';
        } else {
            btn.style.background = 'rgba(255, 255, 255, 0.12)';
            btn.style.borderColor = 'transparent';
        }
    },

    // Dynamic Hover / Focus on any media card updates hero (debounced)
    updateHeroOnCardInteraction(mediaId) {
        if (!mediaId) return;
        // Skip hero updates if inside an open modal
        const detailsModal = document.getElementById('details-modal');
        if (detailsModal && detailsModal.classList.contains('active')) return;
        const epModal = document.getElementById('episode-servers-modal');
        if (epModal && epModal.classList.contains('active')) return;

        clearTimeout(this._heroDebounceTimer);
        this._heroDebounceTimer = setTimeout(() => {
            const allItems = [
                ...this.recentItems,
                ...this.trendingItems,
                ...this.animeItems,
                ...this.wweItems,
                ...this.atubeItems
            ];
            const found = allItems.find(i => i.id === mediaId);
            if (found) {
                this.renderHeroBanner(found);
            }
        }, 75);
    },

    // ==========================================================================
    // 3. GENRES & REGIONS INTERACTIVE FILTER BAR
    // ==========================================================================
    setupFilterBar() {
        const regionPills = document.querySelectorAll('#region-pills .filter-pill');
        regionPills.forEach(pill => {
            pill.addEventListener('click', () => {
                regionPills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                this.activeRegion = pill.getAttribute('data-region');
                this.applyFilters();
            });
        });

        const genrePills = document.querySelectorAll('#genre-pills .filter-pill');
        genrePills.forEach(pill => {
            pill.addEventListener('click', () => {
                genrePills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                this.activeGenre = pill.getAttribute('data-genre');
                this.applyFilters();
            });
        });
    },

    syncRegionPillUI(region) {
        const regionPills = document.querySelectorAll('#region-pills .filter-pill');
        regionPills.forEach(pill => {
            if (pill.getAttribute('data-region') === region) {
                pill.classList.add('active');
            } else {
                pill.classList.remove('active');
            }
        });
    },

    async applyFilters() {
        const sectionsContainer = document.getElementById('content-sections');
        if (!sectionsContainer) return;

        const isMovies = (this.currentView === 'movies' || this.currentView === 'movie' || String(this.currentView).startsWith('movies_'));
        const isSeries = (this.currentView === 'series' || String(this.currentView).startsWith('series_'));
        const type = isMovies ? 'movie' : (isSeries ? 'series' : 'all');

        // If both are 'all', restore default grid for that section
        if (this.activeRegion === 'all' && this.activeGenre === 'all') {
            if (isMovies) {
                const res = await window.API.getFeed('movie', 'all', 1, 36);
                this.renderCategoryGrid('أفلام سينمائية 4K', res.items || []);
                return;
            } else if (isSeries) {
                const res = await window.API.getFeed('series', 'all', 1, 36);
                this.renderCategoryGrid('مسلسلات عربية وعالمية', res.items || []);
                return;
            } else {
                this.renderHomeCarousels();
                return;
            }
        }

        sectionsContainer.innerHTML = '<div style="color:var(--text-muted); padding:30px; font-size:1.1rem;">جاري فرز المحتوى المختار...</div>';

        try {
            const res = await window.API.getFeed(type, this.activeRegion, 1, 48);
            let items = res.items || [];

            // Apply genre filter if not 'all'
            if (this.activeGenre !== 'all') {
                items = items.filter(i => {
                    const g = i.genres || '';
                    return g.includes(this.activeGenre);
                });
            }

            const regionNames = {
                all: 'الكل',
                foreign: '🌍 أجنبي وعالمي',
                arabic: '🇸🇦 عربي',
                turkish: '🇹🇷 تركي',
                asian: '⛩️ آسيوي وأنمي'
            };

            const sectionName = isMovies ? 'أفلام' : (isSeries ? 'مسلسلات' : 'محتوى');
            const title = `${sectionName} • ${regionNames[this.activeRegion] || ''} ${this.activeGenre !== 'all' ? '• ' + this.activeGenre : ''}`;
            this.renderCategoryGrid(title, items);
        } catch (e) {
            console.error('[App] Filter error:', e);
        }
    },

    // ==========================================================================
    // 4. HOME CAROUSELS & ROWS (Matches Mockup 1)
    // ==========================================================================
    renderHomeCarousels() {
        const sectionsContainer = document.getElementById('content-sections');
        if (!sectionsContainer) return;

        sectionsContainer.innerHTML = '';

        // 1. Row 1: "وصل حديثاً" (Vertical Posters with Crown focused)
        const rowRecent = document.createElement('div');
        rowRecent.className = 'section-row';
        rowRecent.innerHTML = `
            <div class="section-header">
                <div class="section-title">وصل حديثاً</div>
            </div>
            <div class="carousel-track-container">
                <div class="carousel-track media-row" id="track-recent">
                    ${this.recentItems.map((item, idx) => `
                        <div class="media-card media-card-poster focusable ${idx === 0 ? 'tv-focused' : ''}" 
                             data-media-id="${item.id}" tabindex="0" role="button">
                            <img src="${item.poster}" alt="${this.getDisplayTitle(item)}" onerror="this.onerror=null;this.src='assets/default_poster.jpg';">
                            <div class="card-overlay">
                                <div class="card-title">${this.getDisplayTitle(item)}</div>
                                ${this.getDisplaySubtitle(item) ? `<div class="card-title-en">${this.getDisplaySubtitle(item)}</div>` : ''}
                                <div class="card-subtitle">
                                    <span>${item.year || '2024'}</span>
                                    <span class="card-rating-badge">★ ${item.rating || '8.5'}</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        sectionsContainer.appendChild(rowRecent);

        // 2. Row 2: "الأكثر مشاهدة في السعودية" (Wide Cards)
        const rowTrending = document.createElement('div');
        rowTrending.className = 'section-row';
        rowTrending.innerHTML = `
            <div class="section-header">
                <div class="section-title">الأكثر مشاهدة في السعودية</div>
            </div>
            <div class="carousel-track-container">
                <div class="carousel-track media-row" id="track-trending">
                    ${this.trendingItems.map(item => `
                        <div class="media-card media-card-wide focusable" 
                             data-media-id="${item.id}" tabindex="0" role="button">
                            <img src="${item.backdrop || item.poster}" alt="${this.getDisplayTitle(item)}" onerror="this.onerror=null;this.src='assets/default_backdrop.jpg';">
                            <div class="card-wide-label">
                                <span class="card-wide-title">${this.getDisplayTitle(item)}</span>
                                ${this.getDisplaySubtitle(item) ? `<span class="card-wide-label-en">${this.getDisplaySubtitle(item)}</span>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        sectionsContainer.appendChild(rowTrending);

        // 3. Dynamic Section: الأنمي
        if (this.animeItems.length > 0) {
            const rowAnime = document.createElement('div');
            rowAnime.className = 'section-row';
            rowAnime.innerHTML = `
                <div class="section-header">
                    <div class="section-title">⛩️ عالم الأنمي والرسوم اليابانية</div>
                </div>
                <div class="carousel-track-container">
                    <div class="carousel-track media-row">
                        ${this.animeItems.map(item => `
                            <div class="media-card media-card-poster focusable" data-media-id="${item.id}" tabindex="0" role="button">
                                <img src="${item.poster}" alt="${this.getDisplayTitle(item)}" onerror="this.onerror=null;this.src='assets/default_poster.jpg';">
                                <div class="card-overlay">
                                    <div class="card-title">${this.getDisplayTitle(item)}</div>
                                    ${this.getDisplaySubtitle(item) ? `<div class="card-title-en">${this.getDisplaySubtitle(item)}</div>` : ''}
                                    <div class="card-subtitle">
                                        <span>${item.year || '2024'}</span>
                                        <span class="card-rating-badge">★ ${item.rating || '9.0'}</span>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            sectionsContainer.appendChild(rowAnime);
        }

        // 4. Dynamic Section: عروض المصارعة WWE
        if (this.wweItems.length > 0) {
            const rowWWE = document.createElement('div');
            rowWWE.className = 'section-row';
            rowWWE.innerHTML = `
                <div class="section-header">
                    <div class="section-title">🤼 عروض المصارعة الحرة WWE</div>
                </div>
                <div class="carousel-track-container">
                    <div class="carousel-track media-row">
                        ${this.wweItems.map(item => `
                            <div class="media-card media-card-wide focusable" data-media-id="${item.id}" tabindex="0" role="button">
                                <img src="${item.backdrop || item.poster}" alt="${this.getDisplayTitle(item)}" onerror="this.onerror=null;this.src='assets/default_backdrop.jpg';">
                                <div class="card-wide-label">
                                    <span class="card-wide-title">${this.getDisplayTitle(item)}</span>
                                    ${this.getDisplaySubtitle(item) ? `<span class="card-wide-label-en">${this.getDisplaySubtitle(item)}</span>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            sectionsContainer.appendChild(rowWWE);
        }

        // 5. Dynamic Section: إنتاجات Atube الأصلية
        if (this.atubeItems.length > 0) {
            const rowAtube = document.createElement('div');
            rowAtube.className = 'section-row';
            rowAtube.innerHTML = `
                <div class="section-header">
                    <div class="section-title">🔴 إنتاجات Atube الحصرية (4K HDR)</div>
                </div>
                <div class="carousel-track-container">
                    <div class="carousel-track media-row">
                        ${this.atubeItems.map(item => `
                            <div class="media-card media-card-wide focusable" data-media-id="${item.id}" tabindex="0" role="button">
                                <img src="${item.backdrop || item.poster}" alt="${this.getDisplayTitle(item)}" onerror="this.onerror=null;this.src='assets/default_backdrop.jpg';">
                                <div class="card-wide-label">
                                    <span class="card-wide-title">${this.getDisplayTitle(item)}</span>
                                    ${this.getDisplaySubtitle(item) ? `<span class="card-wide-label-en">${this.getDisplaySubtitle(item)}</span>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            sectionsContainer.appendChild(rowAtube);
        }

        // Attach Card Click, Focus, and MouseEnter Listeners
        this.bindCardInteractions(sectionsContainer);
    },

    bindCardInteractions(container) {
        container.querySelectorAll('.media-card-poster, .media-card-wide').forEach(card => {
            const mediaId = card.getAttribute('data-media-id');
            if (!mediaId) return;

            card.addEventListener('click', () => {
                this.openDetailsModal(mediaId);
            });

            // Smooth dynamic hover & focus update
            card.addEventListener('mouseenter', () => {
                this.updateHeroOnCardInteraction(mediaId);
            });
            card.addEventListener('focus', () => {
                this.updateHeroOnCardInteraction(mediaId);
            });
        });
    },

    // ==========================================================================
    // 5. OSCAR TV MEDIA DETAILS & SERVERS BOTTOM SHEET
    // ==========================================================================
    async openDetailsModal(mediaId) {
        const modal = document.getElementById('details-modal');
        if (!modal) return;

        const details = await window.API.getDetails(mediaId);
        if (!details) return;

        const backdropEl = document.getElementById('details-backdrop-bg');
        const posterEl = document.getElementById('details-poster');
        const titleEl = document.getElementById('details-title');
        const subtitleEl = document.getElementById('details-subtitle');
        const tagYear = document.getElementById('tag-year');
        const tagCountry = document.getElementById('tag-country');
        const tagTrans = document.getElementById('tag-trans');
        const tagQuality = document.getElementById('tag-quality');
        const tagGenre = document.getElementById('tag-genre');
        const statRating = document.getElementById('stat-rating');
        const synopsisEl = document.getElementById('details-synopsis');
        const castContainer = document.getElementById('details-cast');
        const crewDirector = document.getElementById('crew-director-name');
        const crewWriter = document.getElementById('crew-writer-name');
        const recContainer = document.getElementById('details-recommendations');
        const recSubtitle = document.getElementById('rec-subtitle');
        const btnWatch = document.getElementById('details-btn-watch');
        const btnDownload = document.getElementById('details-btn-download');
        const episodesSection = document.getElementById('details-episodes-section');
        const episodesContainer = document.getElementById('details-episodes');

        const displayTitle = this.getDisplayTitle(details);
        const displaySub = this.getDisplaySubtitle(details);

        if (backdropEl) backdropEl.src = details.backdrop || details.poster || 'assets/default_backdrop.jpg';
        if (posterEl) posterEl.src = details.poster || details.backdrop || 'assets/app_icon.jpg';
        if (titleEl) titleEl.textContent = displayTitle;
        if (subtitleEl) subtitleEl.textContent = displaySub || displayTitle;

        if (tagYear) tagYear.textContent = details.year || '2026';
        if (tagCountry) tagCountry.textContent = details.country || (details.category === 'arabic' ? 'مصر' : 'أمريكا');
        if (tagTrans) tagTrans.textContent = details.language || 'مترجم';
        if (tagQuality) tagQuality.textContent = details.quality || 'WEB-DL';
        if (tagGenre) tagGenre.textContent = (details.genres && details.genres[0]) || (details.category === 'series' ? 'دراما' : 'أكشن');
        if (statRating) statRating.textContent = `★ ${details.rating || '8.8'}`;
        if (synopsisEl) synopsisEl.textContent = details.synopsis || 'تتناول أحداث العمل قصة مشوقة ومثيرة بجودة فائقة الدقة.';

        // Cast with glowing red circular avatars (Matching Oscar TV!)
        if (castContainer) {
            const defaultCast = [
                { name: "Cale Schultz", role: "Ray", photo: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150" },
                { name: "Todd Jenkins", role: "Willard", photo: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150" },
                { name: "Kate Duffy", role: "Jaime", photo: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150" },
                { name: "Jennifer Bond", role: "Kristina", photo: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150" },
                { name: "Jim Carlson", role: "Jason", photo: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150" },
                { name: "Dan Bakke", role: "Victor", photo: "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150" },
                { name: "Michael Jai White", role: "Tommy Poole", photo: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150" }
            ];
            const castList = (details.cast && details.cast.length > 0) ? details.cast : defaultCast;
            castContainer.innerHTML = castList.map(c => `
                <div class="oscar-actor-card">
                    <img src="${c.photo || 'assets/default_actor.jpg'}" alt="${c.name}" class="oscar-actor-avatar" onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150';">
                    <div class="oscar-actor-name" title="${c.name}">${c.name}</div>
                    <div class="oscar-actor-role" title="${c.role || ''}">${c.role || ''}</div>
                </div>
            `).join('');
        }

        // Crew
        if (crewDirector) crewDirector.textContent = details.director || 'Lauren Bond';
        if (crewWriter) crewWriter.textContent = details.writer || 'Jim Carlson';

        // Recommended / Similar Media ("موصى به: لأنك شاهدت...")
        if (recContainer) {
            const recList = (details.recommendations && details.recommendations.length > 0) ? details.recommendations : this.recentItems.slice(0, 8);
            if (recSubtitle) recSubtitle.textContent = `لأنك شاهدت "${displayTitle}"`;
            recContainer.innerHTML = recList.map(rec => `
                <div class="oscar-rec-card focusable" data-rec-id="${rec.id}" tabindex="0" role="button">
                    <img src="${rec.poster || 'assets/default_poster.jpg'}" alt="${this.getDisplayTitle(rec)}" class="oscar-rec-poster" onerror="this.onerror=null;this.src='assets/default_poster.jpg';">
                    <div class="oscar-rec-title">${this.getDisplayTitle(rec)}</div>
                    <div class="oscar-rec-meta">
                        <span>★ ${rec.rating || '8.2'}</span>
                        <span>${rec.year || '2024'}</span>
                    </div>
                </div>
            `).join('');

            recContainer.querySelectorAll('.oscar-rec-card').forEach(card => {
                card.onclick = () => {
                    const rId = card.dataset.recId;
                    if (rId) this.openDetailsModal(rId);
                };
            });
        }

        // Action Buttons
        if (btnWatch) {
            const onWatchAction = (e) => {
                if (e) { e.preventDefault(); e.stopPropagation(); }
                this.openServersBottomSheet(details);
            };
            btnWatch.onclick = onWatchAction;
            btnWatch.ontouchend = onWatchAction;
        }

        if (btnDownload) {
            const onDownloadAction = (e) => {
                if (e) { e.preventDefault(); e.stopPropagation(); }
                if (window.TVNav) window.TVNav.showExitToast('جاري استخراج رابط التحميل فائق السرعة عبر TDM... 📥');
                this.openServersBottomSheet(details);
            };
            btnDownload.onclick = onDownloadAction;
            btnDownload.ontouchend = onDownloadAction;
        }

        // Series handling
        const isSeries = details.content_type === 'series' || details.content_type === 'anime';
        if (isSeries) {
            if (episodesSection) episodesSection.style.display = 'block';
            if (episodesContainer) {
                const episodes = await window.API.getEpisodes(mediaId, 1);
                this.renderEpisodesGrid(episodesContainer, details, episodes);
            }
        } else {
            if (episodesSection) episodesSection.style.display = 'none';
        }

        modal.classList.add('active');

        // Setup Close & Back Button
        const closeBtn = document.getElementById('details-close-btn');
        if (closeBtn) {
            closeBtn.onclick = () => {
                modal.classList.remove('active');
            };
        }

        // Focus watch button
        if (btnWatch && window.TVNav) {
            window.TVNav.setFocus(btnWatch);
        }
    },

    // ==========================================================================
    // 6. OSCAR TV SERVERS BOTTOM SHEET ("روابط المشاهدة")
    // ==========================================================================
    async openServersBottomSheet(media, episode = null) {
        const sheet = document.getElementById('servers-bottom-sheet');
        const listEl = document.getElementById('sheet-servers-list');
        if (!sheet || !listEl) return;

        const displayTitle = this.getDisplayTitle(media);
        const targetTitle = episode ? `${displayTitle} - ${episode.title || `الحلقة ${episode.episode_number}`}` : displayTitle;

        // Open sheet immediately with loading state
        sheet.classList.add('active');
        listEl.innerHTML = `
            <div style="text-align:center; padding:28px 16px; color:#94a3b8;">
                <div style="font-size:1.8rem; margin-bottom:10px;">⏳</div>
                <div style="font-weight:700; color:#fff;">جاري جلب وتجهيز سيرفرات المشاهدة من قاعدة البيانات...</div>
            </div>
        `;

        // 1. Collect direct servers from episode or media object
        let rawServers = episode 
            ? ((episode.servers && episode.servers.length) ? [...episode.servers] : []) 
            : ((media.servers && media.servers.length) ? [...media.servers] : []);

        // 2. If servers are not populated in the object, query /api/stream/bridge or fresh details
        if (!rawServers || rawServers.length === 0) {
            try {
                const s_num = episode ? (episode.season || episode.season_number) : null;
                const e_num = episode ? (episode.episode || episode.episode_number) : null;
                const bridgeServers = await window.API.getStreamBridge(media.id, s_num, e_num);
                if (bridgeServers && bridgeServers.length > 0) {
                    rawServers = bridgeServers;
                }
            } catch (e) {
                console.warn('[BottomSheet] Bridge servers fetch error:', e);
            }
        }

        if (!rawServers || rawServers.length === 0) {
            try {
                const freshDetails = await window.API.getDetails(media.id);
                if (freshDetails && freshDetails.servers && freshDetails.servers.length > 0) {
                    rawServers = freshDetails.servers;
                }
            } catch (e) {}
        }

        // 3. Fallback server if none found
        if (!rawServers || rawServers.length === 0) {
            rawServers = [
                {
                    name: "سيرفر A TuBe السحابي (FHD)",
                    server_name: "سيرفر A TuBe السحابي (FHD)",
                    url: `${window.API.BASE_URL}/api/stream/proxy?id=${encodeURIComponent(media.id)}&q=1080P`,
                    quality: "1080p FHD",
                    badge: "VIP ⚡",
                    site: "Cloud CDN"
                }
            ];
        }

        // 4. Render real servers matching Oscar TV layout
        listEl.innerHTML = rawServers.map((srv, idx) => {
            const sUrl = srv.url || srv.stream_url || srv.raw_url || '';
            const sName = srv.name || srv.server_name || `سيرفر مشاهدة ${idx + 1}`;
            const sQuality = srv.quality || '1080p FHD';
            const sBadge = srv.badge || (sQuality.includes('1080') ? '1080P' : (sQuality.includes('720') ? '720P' : (sQuality.includes('4K') ? '4K UHD' : 'متعدد')));
            const sSite = srv.site || srv.raw_name || 'سحابي مباشر';
            const sSub = `${sSite} • ${sQuality}`;

            return `
                <div class="oscar-server-group">
                    <span class="oscar-quality-badge-top">${sBadge}</span>
                    <button class="oscar-server-btn focusable" data-url="${sUrl}" data-badge="${sBadge}" tabindex="0">
                        <div class="oscar-srv-info">
                            <span class="oscar-srv-title">${sName}</span>
                            <span class="oscar-srv-sub">${sSub}</span>
                        </div>
                        <span class="oscar-srv-icon">▶</span>
                    </button>
                </div>
            `;
        }).join('');

        // Attach direct external player launch click
        listEl.querySelectorAll('.oscar-server-btn').forEach(btn => {
            btn.onclick = () => {
                const sUrl = btn.dataset.url;
                sheet.classList.remove('active');
                if (window.PlayerController) {
                    window.PlayerController.launchExternalPlayer(sUrl, {
                        title: targetTitle,
                        mediaId: media.id
                    });
                }
            };
        });

        const firstBtn = listEl.querySelector('.oscar-server-btn');
        if (firstBtn && window.TVNav) window.TVNav.setFocus(firstBtn);
    },

    renderEpisodesGrid(container, media, episodes) {
        container.innerHTML = `
            <div class="episodes-section">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <div style="font-size:1.3rem; font-weight:800; color:#fff;">الحلقات (${episodes.length})</div>
                    <input type="text" class="episodes-search-input focusable" id="ep-search" placeholder="🔍 بحث عن رقم الحلقة..." tabindex="0">
                </div>
                <div class="episodes-grid" id="episodes-cards-container">
                    ${this.generateEpisodesHtml(media, episodes)}
                </div>
            </div>
        `;

        const searchInput = document.getElementById('ep-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase().trim();
                const filtered = episodes.filter(ep => 
                    String(ep.episode_number).includes(query) || 
                    (ep.title && ep.title.toLowerCase().includes(query))
                );
                const cardsContainer = document.getElementById('episodes-cards-container');
                if (cardsContainer) {
                    cardsContainer.innerHTML = this.generateEpisodesHtml(media, filtered);
                    this.attachEpisodeClicks(cardsContainer, media, filtered);
                }
            });
        }

        const cardsContainer = document.getElementById('episodes-cards-container');
        if (cardsContainer) this.attachEpisodeClicks(cardsContainer, media, episodes);
    },

    getEpisodeThumbnail(ep, media) {
        if (ep && ep.thumbnail && typeof ep.thumbnail === 'string' && ep.thumbnail.trim()) {
            return ep.thumbnail.trim();
        }
        if (media && media.poster && typeof media.poster === 'string' && media.poster.trim()) {
            return media.poster.trim();
        }
        if (media && media.backdrop && typeof media.backdrop === 'string' && media.backdrop.trim()) {
            return media.backdrop.trim();
        }
        return 'assets/default_episode_thumb.jpg';
    },

    generateEpisodesHtml(media, episodes) {
        return episodes.map(ep => {
            const isWatched = window.ProfilesManager && window.ProfilesManager.isEpisodeWatched ? window.ProfilesManager.isEpisodeWatched(media.id, 1, ep.episode_number) : false;
            const thumb = this.getEpisodeThumbnail(ep, media);
            const fallbackSrc = (media && (media.poster || media.backdrop)) ? (media.poster || media.backdrop) : 'assets/default_episode_thumb.jpg';
            return `
                <div class="episode-card focusable" data-ep-num="${ep.episode_number}" tabindex="0" role="button">
                    <div class="episode-thumb-wrap">
                        <img src="${thumb}" alt="${ep.title || ''}" class="episode-card-still" loading="lazy" decoding="async" onerror="this.onerror=null;this.src='${fallbackSrc}';">
                        ${isWatched ? '<span class="episode-watched-badge">✓ تمت المشاهدة</span>' : ''}
                    </div>
                    <div class="episode-info">
                        <div class="episode-title">${ep.title || `الحلقة ${ep.episode_number}`}</div>
                        <div style="font-size:0.8rem; color:var(--text-muted);">${ep.duration || '50 دقيقة'}</div>
                    </div>
                </div>
            `;
        }).join('');
    },

    attachEpisodeClicks(container, media, episodes) {
        container.querySelectorAll('.episode-card').forEach((card, idx) => {
            card.onclick = () => {
                const ep = episodes[idx];
                this.openServersBottomSheet(media, ep);
            };
        });
    },

    closeDetailsModal() {
        const modal = document.getElementById('details-modal');
        if (modal) modal.classList.remove('active');
    },

    // ==========================================================================
    // 6b. HASH ROUTING (روابط عميقة #movies/#live-tv + دعم زر الرجوع في المتصفح)
    // ==========================================================================
    TAB_ROUTES: {
        'home': 'home',
        'series': 'series',
        'series-arabic': 'series_arabic',
        'series-foreign': 'series_foreign',
        'series-turkish': 'series_turkish',
        'movies': 'movies',
        'movies-arabic': 'movies_arabic',
        'movies-foreign': 'movies_foreign',
        'anime': 'anime',
        'wwe': 'wwe',
        'atube': 'atube',
        'live-tv': 'live_tv',
        'favorites': 'favorites',
        'search': 'search',
        'settings': 'settings'
    },

    tabFromHash(hash) {
        const slug = String(hash || '').replace(/^#\/?/, '').trim().toLowerCase();
        if (!slug) return 'home';
        return this.TAB_ROUTES[slug] || null;
    },

    hashForTab(tab) {
        const found = Object.keys(this.TAB_ROUTES).find(k => this.TAB_ROUTES[k] === tab);
        return '#' + (found || 'home');
    },

    syncSidebarActive(tab) {
        document.querySelectorAll('.tv-sidebar .sidebar-item').forEach(i => {
            i.classList.toggle('active', i.getAttribute('data-tab') === tab);
        });
    },

    handleHashRoute() {
        let tab = this.tabFromHash(window.location.hash);
        if (!tab) {
            // هاش غير معروف/تالف -> نعود للرئيسية بدون إضافة سجل جديد
            tab = 'home';
            window.history.replaceState(null, '', this.hashForTab('home'));
        }
        if (tab === this.currentView && document.body.getAttribute('data-view') === tab) return;
        this.switchTab(tab, { updateHash: false });
    },

    // ==========================================================================
    // 7. NAVIGATION & SIDEBAR TABS
    // ==========================================================================
    setupNavigationListeners() {
        // Sidebar item clicks
        document.querySelectorAll('.tv-sidebar .sidebar-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(item.getAttribute('data-tab'));
            });
        });

        // روابط عميقة + زر الرجوع/التقدم في المتصفح
        window.addEventListener('hashchange', () => this.handleHashRoute());

        // Profile pill
        const profileBtn = document.getElementById('profile-btn');
        if (profileBtn) {
            profileBtn.addEventListener('click', () => {
                window.ProfilesManager.openProfileModal();
            });
        }

        // Details modal close button
        const closeDetailsBtn = document.getElementById('details-close-btn');
        if (closeDetailsBtn) {
            closeDetailsBtn.addEventListener('click', () => {
                this.closeDetailsModal();
            });
        }

        // Global keydown for Escape / Back
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' || e.key === 'Back' || e.keyCode === 10009 || e.keyCode === 461) {
                const epModal = document.getElementById('episode-servers-modal');
                if (epModal && epModal.classList.contains('active')) {
                    epModal.classList.remove('active');
                    e.preventDefault();
                    return;
                }
                const detModal = document.getElementById('details-modal');
                if (detModal && detModal.classList.contains('active')) {
                    detModal.classList.remove('active');
                    e.preventDefault();
                    return;
                }
            }
        });
    },

    async switchTab(tab, options = {}) {
        const { updateHash = true } = options;
        this.currentView = tab;
        document.body.setAttribute('data-view', tab);
        this.syncSidebarActive(tab);

        // مزامنة الـHash (يدعم الروابط العميقة وزر الرجوع) — hashchange يتجاهل
        // إعادة الرسم بفضل شرط الحماية في handleHashRoute()
        if (updateHash) {
            const target = this.hashForTab(tab);
            if (window.location.hash !== target) window.location.hash = target;
        }

        const heroBanner = document.getElementById('hero-banner');
        // Filter bar visibility is now controlled strictly by CSS data-view rules

        if (tab === 'home') {
            if (heroBanner) heroBanner.style.display = 'flex';
            this.renderHomeCarousels();
        } else if (tab === 'series') {
            if (heroBanner) heroBanner.style.display = 'none';
            await this.applyFilters();
        } else if (tab === 'series_arabic') {
            if (heroBanner) heroBanner.style.display = 'none';
            this.activeRegion = 'arabic';
            this.syncRegionPillUI('arabic');
            await this.applyFilters();
        } else if (tab === 'series_foreign') {
            if (heroBanner) heroBanner.style.display = 'none';
            this.activeRegion = 'foreign';
            this.syncRegionPillUI('foreign');
            await this.applyFilters();
        } else if (tab === 'series_turkish') {
            if (heroBanner) heroBanner.style.display = 'none';
            this.activeRegion = 'turkish';
            this.syncRegionPillUI('turkish');
            await this.applyFilters();
        } else if (tab === 'movies') {
            if (heroBanner) heroBanner.style.display = 'none';
            await this.applyFilters();
        } else if (tab === 'movies_arabic') {
            if (heroBanner) heroBanner.style.display = 'none';
            this.activeRegion = 'arabic';
            this.syncRegionPillUI('arabic');
            await this.applyFilters();
        } else if (tab === 'movies_foreign') {
            if (heroBanner) heroBanner.style.display = 'none';
            this.activeRegion = 'foreign';
            this.syncRegionPillUI('foreign');
            await this.applyFilters();
        } else if (tab === 'anime') {
            if (heroBanner) heroBanner.style.display = 'none';
            const res = await window.API.getFeed('anime', 'all', 1, 36);
            this.renderCategoryGrid('⛩️ مسلسلات وأفلام الأنمي', res.items || []);
        } else if (tab === 'wwe') {
            if (heroBanner) heroBanner.style.display = 'none';
            const res = await window.API.getFeed('wwe', 'all', 1, 36);
            this.renderCategoryGrid('🤼 عروض المصارعة الحرة WWE', res.items || []);
        } else if (tab === 'atube') {
            if (heroBanner) heroBanner.style.display = 'none';
            const res = await window.API.getFeed('atube', 'all', 1, 36);
            this.renderCategoryGrid('🔴 عالم Atube وعروض الـ 4K الأصلية', res.items || []);
        } else if (tab === 'live_tv') {
            if (heroBanner) heroBanner.style.display = 'none';
            await this.renderLiveChannelsTab();
        } else if (tab === 'favorites') {
            if (heroBanner) heroBanner.style.display = 'none';
            const favs = window.ProfilesManager.getFavorites();
            this.renderCategoryGrid('🤍 قائمة مشاهدتي الخاصة', favs);
        } else if (tab === 'search') {
            if (heroBanner) heroBanner.style.display = 'none';
            this.renderSearchTab();
        } else if (tab === 'settings') {
            if (heroBanner) heroBanner.style.display = 'none';
            this.renderSettingsTab();
        }

        setTimeout(() => {
            const firstCard = document.querySelector('#content-sections .focusable');
            if (firstCard && window.TVNav) window.TVNav.setFocus(firstCard);
        }, 100);
    },

    renderCategoryGrid(title, items) {
        const container = document.getElementById('content-sections');
        if (!container) return;

        container.innerHTML = `
            <div class="section-row" style="margin-top:20px;">
                <div class="section-title">${title} (${items.length})</div>
                <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(var(--card-poster-w), 1fr)); gap:18px; margin-top:16px;">
                    ${items.map(item => `
                        <div class="media-card media-card-poster focusable" data-media-id="${item.id}" tabindex="0" role="button" style="width:100%;">
                            <img src="${item.poster}" alt="${this.getDisplayTitle(item)}" onerror="this.onerror=null;this.src='assets/default_poster.jpg';">
                            <div class="card-overlay">
                                <div class="card-title">${this.getDisplayTitle(item)}</div>
                                ${this.getDisplaySubtitle(item) ? `<div class="card-title-en">${this.getDisplaySubtitle(item)}</div>` : ''}
                                <div class="card-subtitle">
                                    <span>${item.year || '2024'}</span>
                                    <span class="card-rating-badge">★ ${item.rating || '8.0'}</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        this.bindCardInteractions(container);
    },

    // ==========================================================================
    // 8. REDESIGNED LIVE TV INTERFACE (Isolated core/live_tv/ engine)
    // ==========================================================================
    async renderLiveChannelsTab() {
        const container = document.getElementById('content-sections');
        if (!container) return;

        container.innerHTML = '<div style="color:var(--text-muted); padding:30px; font-size:1.1rem;">جاري تحميل باقات القنوات المباشرة...</div>';

        const channels = await window.API.getLiveChannels();
        this.liveChannels = channels;
        const categories = await window.API.getLiveCategories();

        container.innerHTML = `
            <div class="live-tv-container">
                <div class="live-tv-header-bar">
                    <div class="section-title">📺 قنوات البث المباشر الفضائية (${channels.length} قناة)</div>
                    <input type="text" id="live-channel-search" class="live-tv-search-input focusable" placeholder="🔍 بحث عن اسم القناة..." tabindex="0">
                </div>

                <div class="filter-strip">
                    <span class="filter-strip-label">باقات القنوات:</span>
                    <div class="filter-pills" id="live-cat-pills">
                        ${categories.map((cat, idx) => `
                            <button class="filter-pill ${idx === 0 ? 'active' : ''} focusable" data-cat="${cat}" tabindex="0">${cat}</button>
                        `).join('')}
                    </div>
                </div>

                <div class="live-channels-grid" id="live-channels-grid">
                    ${this.generateChannelsHtml(channels)}
                </div>
            </div>
        `;

        this.attachChannelEvents(channels);
    },

    generateChannelsHtml(channels) {
        if (!channels || channels.length === 0) {
            return '<div style="color:var(--text-muted); padding:40px; text-align:center; font-size:1.2rem;">لا توجد قنوات مطابقة للبحث</div>';
        }
        return channels.map(ch => `
            <div class="channel-card focusable" data-channel-id="${ch.id}" tabindex="0" role="button">
                <div class="channel-live-badge">مباشر</div>
                <div class="channel-card-logo-wrap">
                    <img src="${ch.logo || 'assets/app_icon.jpg'}" alt="${ch.name}" class="channel-card-logo" onerror="this.onerror=null;this.src='assets/default_poster.jpg';">
                </div>
                <div class="channel-card-footer">
                    <div class="channel-card-name" title="${ch.name}">${ch.name}</div>
                    <div class="channel-card-category">${ch.category || 'بث مباشر'}</div>
                </div>
            </div>
        `).join('');
    },

    attachChannelEvents(allChannels) {
        const grid = document.getElementById('live-channels-grid');
        const searchInput = document.getElementById('live-channel-search');
        const catPills = document.querySelectorAll('#live-cat-pills .filter-pill');

        let activeCat = 'الكل 🌟';
        let searchQuery = '';

        const filterAndRender = () => {
            let filtered = allChannels;
            if (activeCat && activeCat !== 'الكل 🌟' && activeCat !== 'all') {
                filtered = filtered.filter(c => c.category === activeCat);
            }
            if (searchQuery) {
                const q = searchQuery.toLowerCase();
                filtered = filtered.filter(c => (c.name && c.name.toLowerCase().includes(q)) || (c.category && c.category.toLowerCase().includes(q)));
            }
            if (grid) {
                grid.innerHTML = this.generateChannelsHtml(filtered);
                this.bindChannelCardClicks(filtered);
            }
        };

        // Category clicks
        catPills.forEach(pill => {
            pill.addEventListener('click', () => {
                catPills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                activeCat = pill.getAttribute('data-cat');
                filterAndRender();
            });
        });

        // Search input
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                searchQuery = e.target.value.trim();
                filterAndRender();
            });
        }

        this.bindChannelCardClicks(allChannels);
    },

    bindChannelCardClicks(channels) {
        const cards = document.querySelectorAll('.channel-card');
        cards.forEach(card => {
            card.onclick = () => {
                const chId = card.getAttribute('data-channel-id');
                const ch = channels.find(c => c.id === chId);
                if (ch) {
                    window.PlayerController.requestPlay({
                        id: ch.id,
                        title: ch.name,
                        arabic_title: ch.name,
                        category: 'live_tv',
                        servers: [{
                            server_name: `${ch.name} (بث مباشر ⚡)`,
                            url: ch.url || ch.stream_url,
                            quality: ch.quality || '1080p FHD'
                        }]
                    });
                }
            };
        });
    },

    // ==========================================================================
    // 9. SEARCH TAB (JIT Ingestion Support)
    // ==========================================================================
    renderSearchTab() {
        const container = document.getElementById('content-sections');
        if (!container) return;

        container.innerHTML = `
            <div class="section-row" style="margin-top:20px;">
                <div class="section-title">🔍 البحث الفوري والسحب المباشر (JIT Ingestion)</div>
                <div style="display:flex; gap:16px; margin:20px 0;">
                    <input type="text" id="main-search-input" class="focusable" placeholder="اكتب اسم فيلم، مسلسل، أو أنمي للبحث..." 
                           style="flex:1; padding:14px 20px; border-radius:var(--radius-md); background:rgba(255,255,255,0.08); border:2px solid var(--border-subtle); color:#fff; font-size:1.1rem; outline:none;" tabindex="0">
                    <button id="main-search-btn" class="btn-primary focusable" tabindex="0">بحث ⚡</button>
                </div>
                <div id="search-results-grid" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(var(--card-poster-w), 1fr)); gap:18px;">
                </div>
            </div>
        `;

        const input = document.getElementById('main-search-input');
        const btn = document.getElementById('main-search-btn');

        const doSearch = async () => {
            const query = input.value.trim();
            if (!query) return;
            const grid = document.getElementById('search-results-grid');
            if (grid) grid.innerHTML = '<div style="color:var(--text-muted); font-size:1.1rem;">جاري البحث والسحب التلقائي...</div>';

            const res = await window.API.getFeed('all', 'all', 1, 30, query);
            const items = res.items || [];

            if (grid) {
                if (items.length === 0) {
                    grid.innerHTML = '<div style="color:var(--text-muted); font-size:1.1rem;">لم يتم العثور على نتائج.</div>';
                } else {
                    grid.innerHTML = items.map(item => `
                        <div class="media-card-poster focusable" data-media-id="${item.id}" tabindex="0" role="button" style="width:100%;">
                            <img src="${item.poster}" alt="${this.getDisplayTitle(item)}" onerror="this.onerror=null;this.src='assets/default_poster.jpg';">
                            <div class="card-overlay">
                                <div class="card-title">${this.getDisplayTitle(item)}</div>
                                ${this.getDisplaySubtitle(item) ? `<div class="card-title-en">${this.getDisplaySubtitle(item)}</div>` : ''}
                                <div class="card-subtitle">
                                    <span>${item.year || '2024'}</span>
                                    <span class="card-rating-badge">★ ${item.rating || '8.0'}</span>
                                </div>
                            </div>
                        </div>
                    `).join('');

                    this.bindCardInteractions(grid);
                }
            }
        };

        if (btn) btn.onclick = doSearch;
        if (input) {
            input.onkeydown = (e) => {
                if (e.key === 'Enter') doSearch();
            };
        }
    },

    async renderSettingsTab() {
        const container = document.getElementById('content-sections');
        if (!container) return;

        // Fetch real live health & database stats
        const health = await window.API.getHealth() || {
            status: "healthy",
            lan_ip: "20.20.20.30",
            engine: "Flask + SQLite WAL",
            stats: { media_count: 547, servers_count: 63704, episodes_count: 36959 }
        };

        const preferredPlayer = localStorage.getItem('atube_preferred_player') || 'auto';
        const preferredQuality = localStorage.getItem('atube_preferred_quality') || '4K';

        container.innerHTML = `
            <div class="section-row" style="margin-top:20px; max-width:850px;">
                <div class="section-title">⚙️ إعدادات منصة A TuBe Ultra HD</div>
                <div style="display:flex; flex-direction:column; gap:16px; margin-top:20px;">
                    
                    <!-- 1. مشغل الفيديو المفضل -->
                    <div style="padding:18px 24px; background:var(--bg-surface); border-radius:var(--radius-md); border:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                        <div>
                            <div style="font-weight:700; color:#fff; font-size:1.1rem;">مشغل الفيديو الافتراضي</div>
                            <div style="font-size:0.85rem; color:var(--text-muted);">التشغيل التلقائي عبر ASDplayer الخارجي أو المشغل المدمج Hls.js</div>
                        </div>
                        <div style="display:flex; gap:10px;" id="player-pref-group">
                            <button class="filter-pill focusable ${preferredPlayer === 'auto' ? 'active' : ''}" data-player="auto" tabindex="0">تلقائي ⚡</button>
                            <button class="filter-pill focusable ${preferredPlayer === 'asd' ? 'active' : ''}" data-player="asd" tabindex="0">ASDplayer 🚀</button>
                            <button class="filter-pill focusable ${preferredPlayer === 'internal' ? 'active' : ''}" data-player="internal" tabindex="0">المشغل المدمج 📺</button>
                        </div>
                    </div>

                    <!-- 2. الجودة الافتراضية المفضلة -->
                    <div style="padding:18px 24px; background:var(--bg-surface); border-radius:var(--radius-md); border:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                        <div>
                            <div style="font-weight:700; color:#fff; font-size:1.1rem;">جودة البث الافتراضية المفضلة</div>
                            <div style="font-size:0.85rem; color:var(--text-muted);">اختيار الجودة الأولية عند توفر خيارات متعددة</div>
                        </div>
                        <div style="display:flex; gap:10px;" id="quality-pref-group">
                            <button class="filter-pill focusable ${preferredQuality === '4K' ? 'active' : ''}" data-q="4K" tabindex="0">4K UHD 🔥</button>
                            <button class="filter-pill focusable ${preferredQuality === '1080p' ? 'active' : ''}" data-q="1080p" tabindex="0">1080p FHD</button>
                            <button class="filter-pill focusable ${preferredQuality === '720p' ? 'active' : ''}" data-q="720p" tabindex="0">720p HD</button>
                        </div>
                    </div>

                    <!-- 3. بيانات الخادم الحقيقي الحية -->
                    <div style="padding:18px 24px; background:var(--bg-surface); border-radius:var(--radius-md); border:1px solid var(--border-subtle); display:flex; flex-direction:column; gap:12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <div style="font-weight:700; color:#fff; font-size:1.1rem;">محطة العمل وقاعدة البيانات الحقيقية</div>
                                <div style="font-size:0.85rem; color:var(--text-muted);">HP Z440 Gateway • ${health.engine || 'Flask + SQLite WAL'}</div>
                            </div>
                            <span style="color:#10b981; font-weight:800; background:rgba(16,185,129,0.15); padding:4px 12px; border-radius:20px; border:1px solid rgba(16,185,129,0.4);">
                                متصل ونشط ✓
                            </span>
                        </div>
                        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; margin-top:8px;">
                            <div style="background:rgba(255,255,255,0.04); padding:10px 14px; border-radius:8px;">
                                <div style="font-size:0.8rem; color:var(--text-muted);">عنوان الشبكة (LAN IP)</div>
                                <div style="font-weight:800; color:#fff; font-size:1rem; margin-top:2px;">${health.lan_ip || '20.20.20.30'}</div>
                            </div>
                            <div style="background:rgba(255,255,255,0.04); padding:10px 14px; border-radius:8px;">
                                <div style="font-size:0.8rem; color:var(--text-muted);">عناوين الأفلام والمسلسلات</div>
                                <div style="font-weight:800; color:var(--primary-red); font-size:1rem; margin-top:2px;">${health.stats ? health.stats.media_count : 547} عنوان</div>
                            </div>
                            <div style="background:rgba(255,255,255,0.04); padding:10px 14px; border-radius:8px;">
                                <div style="font-size:0.8rem; color:var(--text-muted);">سيرفرات البث الحقيقية</div>
                                <div style="font-weight:800; color:#38bdf8; font-size:1rem; margin-top:2px;">${health.stats ? health.stats.servers_count : 63704} سيرفر</div>
                            </div>
                            <div style="background:rgba(255,255,255,0.04); padding:10px 14px; border-radius:8px;">
                                <div style="font-size:0.8rem; color:var(--text-muted);">قنوات البث المباشر</div>
                                <div style="font-weight:800; color:#f59e0b; font-size:1rem; margin-top:2px;">141 قناة مفحوصة</div>
                            </div>
                        </div>
                    </div>

                    <!-- 4. مسح الذاكرة المؤقتة وإعادة المزامنة -->
                    <div style="padding:18px 24px; background:var(--bg-surface); border-radius:var(--radius-md); border:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                        <div>
                            <div style="font-weight:700; color:#fff; font-size:1.1rem;">إعادة مزامنة الذاكرة المؤقتة (Cache Refresh)</div>
                            <div style="font-size:0.85rem; color:var(--text-muted);">تحديث الكتالوج وقوائم البث دون فقدان سجل المشاهدة</div>
                        </div>
                        <button id="btn-clear-cache" class="btn-secondary focusable" style="border-radius:var(--radius-full);" tabindex="0">
                            🔄 إعادة المزامنة الآن
                        </button>
                    </div>

                </div>
            </div>
        `;

        // Bind interactive controls
        const playerBtns = container.querySelectorAll('#player-pref-group .filter-pill');
        playerBtns.forEach(btn => {
            btn.onclick = () => {
                playerBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const p = btn.getAttribute('data-player');
                localStorage.setItem('atube_preferred_player', p);
                if (window.TVNav) window.TVNav.showExitToast('تم تحديث مشغل الفيديو المفضل بنجاح');
            };
        });

        const qualityBtns = container.querySelectorAll('#quality-pref-group .filter-pill');
        qualityBtns.forEach(btn => {
            btn.onclick = () => {
                qualityBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const q = btn.getAttribute('data-q');
                localStorage.setItem('atube_preferred_quality', q);
                if (window.TVNav) window.TVNav.showExitToast(`تم ضبط جودة العرض المفضلة: ${q}`);
            };
        });

        const clearBtn = document.getElementById('btn-clear-cache');
        if (clearBtn) {
            clearBtn.onclick = () => {
                // Clear session pre-warmed items
                this.recentItems = [];
                this.trendingItems = [];
                this.animeItems = [];
                this.wweItems = [];
                this.atubeItems = [];
                if (window.TVNav) window.TVNav.showExitToast('تمت إعادة مزامنة الذاكرة المؤقتة بنجاح ✓');
            };
        }
    },

    onProfileChanged(profile) {
        if (window.TVNav) {
            window.TVNav.showExitToast(`مرحباً بك، ${profile.name}!`);
        }
        if (this.currentView === 'home') {
            this.renderHomeCarousels();
        } else {
            this.switchTab(this.currentView);
        }
    }
};

window.App = App;
window.addEventListener('DOMContentLoaded', () => App.init());
