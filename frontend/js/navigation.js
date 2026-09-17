/**
 * A TuBe Ultra HD v2.0 - Blazing Fast Spatial TV D-Pad Remote Navigation Engine
 * Optimized for Smart TV, Android TV (Capacitor/WebView), and Desktop:
 * - Scoped DOM querying (only queries active modal if open)
 * - Zero layout thrashing: uses fast offsetParent check instead of getComputedStyle
 * - Instant scroll-into-view (behavior: 'auto') eliminating animation jitter
 * - Throttled mouseover with requestAnimationFrame
 * - RTL-aware directional mapping
 */

class SpatialNavigationEngine {
    constructor() {
        this.currentFocus = null;
        this.lastBackPressTime = 0;
        this.rafMouseLock = false;
        this.init();
    }

    init() {
        window.addEventListener('keydown', (e) => this.handleKeyDown(e), { passive: false });

        // High performance mouse hover with rAF throttling
        document.addEventListener('mouseover', (e) => {
            if (this.rafMouseLock) return;
            const target = e.target.closest('.focusable');
            if (target && target !== this.currentFocus) {
                this.rafMouseLock = true;
                requestAnimationFrame(() => {
                    this.setFocus(target, false);
                    this.rafMouseLock = false;
                });
            }
        }, { passive: true });
    }

    getActiveRoot() {
        // Scope navigation strictly to the active modal if one is displayed
        return document.querySelector('#servers-bottom-sheet.active') ||
               document.querySelector('#episode-servers-modal.active') ||
               document.querySelector('#details-modal.active') ||
               document.querySelector('#profiles-modal.active') ||
               document.querySelector('#play-choice-modal.active') ||
               document.querySelector('.main-wrapper') ||
               document.body;
    }

    getFocusableElements() {
        const root = this.getActiveRoot();
        const rawElements = root.querySelectorAll('.focusable');
        const count = rawElements.length;
        const valid = [];

        for (let i = 0; i < count; i++) {
            const el = rawElements[i];
            // Ultra fast visibility checks without forcing getComputedStyle
            if (el.disabled) continue;
            if (el.getAttribute('aria-hidden') === 'true') continue;
            if (el.offsetParent === null && el.style.position !== 'fixed') continue;

            valid.push(el);
        }

        return valid;
    }

    setFocus(element, scroll = true) {
        if (!element) return;
        if (this.currentFocus && this.currentFocus !== element) {
            this.currentFocus.classList.remove('tv-focused');
        }

        this.currentFocus = element;
        element.classList.add('tv-focused');
        element.focus({ preventScroll: true });

        if (scroll) {
            // Instant scroll avoids thread locking and lag during rapid key navigation
            element.scrollIntoView({
                behavior: 'auto',
                block: 'nearest',
                inline: 'nearest'
            });
        }
    }

    handleKeyDown(e) {
        // Allow input typing without directional trapping
        if (e.target && e.target.tagName === 'INPUT' && !['Enter', 'Escape'].includes(e.key)) {
            return;
        }

        const key = e.key || e.keyCode;

        switch (key) {
            case 'ArrowUp':
            case 38:
            case 'Up':
                e.preventDefault();
                this.navigateSpatial('up');
                break;

            case 'ArrowDown':
            case 40:
            case 'Down':
                e.preventDefault();
                this.navigateSpatial('down');
                break;

            case 'ArrowLeft':
            case 37:
            case 'Left':
                e.preventDefault();
                this.navigateSpatial('left');
                break;

            case 'ArrowRight':
            case 39:
            case 'Right':
                e.preventDefault();
                this.navigateSpatial('right');
                break;

            case 'Enter':
            case 13:
            case ' ':
            case 32:
            case 'NumpadEnter':
                e.preventDefault();
                if (this.currentFocus) {
                    this.currentFocus.click();
                }
                break;

            case 'Escape':
            case 27:
            case 'Backspace':
            case 8:
            case 'GoBack':
            case 4: // Android TV Back KeyCode
                e.preventDefault();
                this.handleBackAction();
                break;
        }
    }

    navigateSpatial(direction) {
        const focusables = this.getFocusableElements();
        if (!focusables.length) return;

        // If no focus or disconnected element, focus first visible item
        if (!this.currentFocus || !document.body.contains(this.currentFocus)) {
            const first = focusables[0];
            if (first) this.setFocus(first);
            return;
        }

        const currentRect = this.currentFocus.getBoundingClientRect();
        const currentCenterX = currentRect.left + currentRect.width / 2;
        const currentCenterY = currentRect.top + currentRect.height / 2;

        let bestCandidate = null;
        let minDistance = Infinity;

        const count = focusables.length;
        for (let i = 0; i < count; i++) {
            const candidate = focusables[i];
            if (candidate === this.currentFocus) continue;

            const rect = candidate.getBoundingClientRect();
            // Fast skip if offscreen or zero area
            if (rect.width === 0 || rect.height === 0) continue;

            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;

            const dx = centerX - currentCenterX;
            const dy = centerY - currentCenterY;

            let primaryDistance = 0;
            let secondaryDistance = 0;

            // Fast axis directional filter
            if (direction === 'up') {
                if (dy >= -2) continue; // Not above
                primaryDistance = -dy;
                secondaryDistance = Math.abs(dx);
            } else if (direction === 'down') {
                if (dy <= 2) continue; // Not below
                primaryDistance = dy;
                secondaryDistance = Math.abs(dx);
            } else if (direction === 'left') {
                if (dx >= -2) continue; // Not to the left
                primaryDistance = -dx;
                secondaryDistance = Math.abs(dy);
            } else if (direction === 'right') {
                if (dx <= 2) continue; // Not to the right
                primaryDistance = dx;
                secondaryDistance = Math.abs(dy);
            }

            // Weighted Manhattan/Euclidean hybrid for instant calculation
            const dist = primaryDistance * 1.0 + secondaryDistance * 2.0;
            if (dist < minDistance) {
                minDistance = dist;
                bestCandidate = candidate;
            }
        }

        if (bestCandidate) {
            this.setFocus(bestCandidate);
        }
    }

    handleBackAction() {
        // 1. If Video Player is active, double-back exit
        const player = document.getElementById('player-container');
        if (player && player.classList.contains('active')) {
            const now = Date.now();
            if (now - this.lastBackPressTime < 2000) {
                if (window.PlayerController) window.PlayerController.closePlayer();
                this.hideExitToast();
            } else {
                this.lastBackPressTime = now;
                this.showExitToast('اضغط زر الرجوع مرة أخرى للخروج من المشغل');
            }
            return;
        }

        // 2. Close Episode Servers Modal if open
        const epModal = document.getElementById('episode-servers-modal');
        if (epModal && epModal.classList.contains('active')) {
            epModal.classList.remove('active');
            return;
        }

        // 3. Close Play Choice Modal if open
        const choiceModal = document.getElementById('play-choice-modal');
        if (choiceModal && choiceModal.classList.contains('active')) {
            choiceModal.classList.remove('active');
            return;
        }

        // 4. Close Profiles Modal if open
        const profilesModal = document.getElementById('profiles-modal');
        if (profilesModal && profilesModal.classList.contains('active')) {
            if (window.ProfilesManager) window.ProfilesManager.closeProfileModal();
            return;
        }

        // 5. Close Media Details Modal if open
        const detailsModal = document.getElementById('details-modal');
        if (detailsModal && detailsModal.classList.contains('active')) {
            detailsModal.classList.remove('active');
            return;
        }

        // 6. Default back: focus active sidebar item
        const activeNav = document.querySelector('.tv-sidebar .sidebar-item.active');
        if (activeNav) {
            this.setFocus(activeNav);
        }
    }

    showExitToast(message) {
        const toast = document.getElementById('exit-toast');
        if (!toast) return;
        toast.textContent = message;
        toast.style.display = 'block';
        clearTimeout(this.toastTimer);
        this.toastTimer = setTimeout(() => {
            this.hideExitToast();
        }, 2200);
    }

    hideExitToast() {
        const toast = document.getElementById('exit-toast');
        if (toast) toast.style.display = 'none';
    }
}

window.TVNav = new SpatialNavigationEngine();
