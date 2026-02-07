
if (typeof StickerManager === 'undefined') {
    window.StickerManager = class StickerManager {
        constructor(pageType, targetUserId = null, readOnly = false) {
        this.pageType = pageType;
        this.targetUserId = targetUserId;
        this.readOnly = readOnly;
        this.canvas = document.getElementById('sticker-canvas');
        this.fab = document.getElementById('sticker-fab');
        this.drawer = document.getElementById('sticker-drawer');
        this.stickers = []; // {id, badge_id, badge_icon, x, y, rotation, scale, z_index, element}
        this.badges = []; // Available badges
        this.activeSticker = null;
        this.isDrawerOpen = false;
        this.isEditing = false;
        
        // Track usage limits
        this.badgeBaseUsage = {}; // badgeId -> (Total DB Usage - Current Page DB Usage)
        this.badgeLimits = {}; // badgeId -> Limit
        
        this.REFERENCE_WIDTH = 1200; // Baseline width for relative scaling
        
        this.init();
    }

    getResponsiveScaleFactor() {
        if (!this.canvas) return 1;
        // Calculate scale factor relative to reference width
        // We limit the factor to be at least 0.2 to avoid invisible stickers on tiny screens (unlikely)
        // and maybe limit max? No, let it scale up on huge screens.
        return Math.max(0.1, this.canvas.offsetWidth / this.REFERENCE_WIDTH);
    }

    updateStickerTransform(el, sticker) {
        const factor = this.getResponsiveScaleFactor();
        el.style.transform = `translate(-50%, -50%) rotate(${sticker.rotation}deg) scale(${sticker.scale * factor})`;
    }

    async init() {
        this.bindEvents();
        this.initBadgeData(); // Parse HTML data first
        await this.loadStickers();
        this.updateBaseUsage(); // Update base usage after loading current page stickers
        this.renderDrawer(); // Initial render to bind events and show counts
    }
    
    initBadgeData() {
        const options = document.querySelectorAll('.sticker-option');
        options.forEach(opt => {
            const bid = parseInt(opt.dataset.badgeId);
            const limit = parseInt(opt.dataset.stickerLimit || 1);
            const totalUsage = parseInt(opt.dataset.usedCount || 0);
            
            this.badgeLimits[bid] = limit;
            // Temporarily store total usage, will adjust after loadStickers
            this.badgeBaseUsage[bid] = totalUsage; 
        });
    }
    
    updateBaseUsage() {
        // Calculate current page usage from DB (loaded stickers)
        // And subtract from total to get "other pages usage"
        const currentPageCounts = {};
        this.stickers.forEach(s => {
            currentPageCounts[s.badge_id] = (currentPageCounts[s.badge_id] || 0) + 1;
        });
        
        for (const [bid, total] of Object.entries(this.badgeBaseUsage)) {
            const pageCount = currentPageCounts[bid] || 0;
            // Ensure we don't go negative (race conditions?)
            this.badgeBaseUsage[bid] = Math.max(0, total - pageCount);
        }
    }

    bindEvents() {
        if (this.readOnly) {
            if (this.fab) this.fab.style.display = 'none';
            if (this.drawer) this.drawer.style.display = 'none';
            return;
        }

        // FAB Click
        document.getElementById('sticker-fab').addEventListener('click', () => {
            if (this.isEditing && !this.isDrawerOpen) {
                this.expandDrawer();
            } else {
                this.toggleDrawer();
            }
        });

        // Save Button
        document.getElementById('sticker-save-btn').addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent header click from triggering
            this.saveStickers();
            this.closeDrawer();
        });

        // Close Drawer Button
        document.getElementById('sticker-close-btn').addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent header click from triggering
            this.closeDrawer();
        });
        
        // Drawer Header Click (Toggle Partial/Open)
        const header = this.drawer.querySelector('.sticker-drawer-header');
        if (header) {
            header.addEventListener('click', (e) => {
                if (e.target.closest('button')) return; // Ignore button clicks
                if (this.drawer.classList.contains('partial')) {
                    this.expandDrawer();
                } else if (this.isDrawerOpen) {
                     // Optional: allow clicking header to collapse to partial? 
                     // User didn't ask for this, but it might be nice.
                     // For now, let's strictly follow: "click a button to expand back"
                     // The user said: "add a button to slide up/down"
                     // So let's make the header toggle between open and partial if already editing
                     this.collapseDrawer();
                }
            });
        }

        // Click outside to deselect
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.sticker-item') && !e.target.closest('.sticker-fab') && !e.target.closest('.sticker-drawer')) {
                this.deselectAll();
            }
        });
        
        // Canvas Drag Over (Optional: prevent default)
        this.canvas.addEventListener('dragover', e => e.preventDefault());
        
        // Window Resize - Update all sticker transforms
        window.addEventListener('resize', () => {
            requestAnimationFrame(() => {
                this.stickers.forEach(s => {
                    if (s.element) {
                        this.updateStickerTransform(s.element, s);
                    }
                });
            });
        });
    }

    toggleDrawer() {
        if (this.isDrawerOpen) {
            this.closeDrawer();
        } else {
            this.openDrawer();
        }
    }

    openDrawer() {
        console.log('openDrawer');
        this.drawer.classList.remove('partial'); // Ensure partial is removed
        this.drawer.classList.add('open');
        this.canvas.classList.add('editing'); // Enable sticker interaction
        this.isDrawerOpen = true;
        this.isEditing = true;
        this.renderDrawer();
        // Hide FAB when drawer is open
        document.getElementById('sticker-fab').style.display = 'none';
        
        const dropZone = document.getElementById('sticker-drop-zone');
        if (dropZone) {
            dropZone.classList.remove('hidden');
        }

        // Special handling for profile page to allow drop through glass card
        if (this.pageType === 'profile') {
             const headerCard = document.querySelector('.group.z-10'); // The glass card
             if (headerCard) headerCard.style.pointerEvents = 'none';
        }

    }

    closeDrawer() {
        console.log('closeDrawer');
        this.drawer.classList.remove('open');
        this.drawer.classList.remove('partial'); // Ensure partial is removed
        this.canvas.classList.remove('editing'); // Disable sticker interaction
        this.deselectAll(); // Deselect any active sticker
        this.isDrawerOpen = false;
        this.isEditing = false;
        // Hide FAB when drawer is closed
        document.getElementById('sticker-fab').style.display = 'flex';
                // Hide drop zone
        const dropZone = document.getElementById('sticker-drop-zone');
        if (dropZone) {
            dropZone.classList.add('hidden');
        }
        
        // Restore pointer events for profile header if on profile page
        if (this.pageType === 'profile') {
             const headerCard = document.querySelector('.group.z-10'); // The glass card
             if (headerCard) headerCard.style.pointerEvents = '';
        }
    }

    collapseDrawer() {
        if (this.isDrawerOpen) {
            console.log('collapseDrawer: Collapsing drawer to partial state');
            this.drawer.classList.remove('open');
            this.drawer.classList.add('partial'); // Add partial class
            this.isDrawerOpen = false;
            // Keep isEditing = true
            // Hide FAB because we have the partial header visible as a "button"
            document.getElementById('sticker-fab').style.display = 'none'; 
        }
    }

    expandDrawer() {
        // Expand from partial or closed
        console.log('expandDrawer: Expanding drawer back');
        this.drawer.classList.remove('partial');
        this.drawer.classList.add('open');
        this.isDrawerOpen = true;
        // Keep isEditing = true
        // Hide FAB
        document.getElementById('sticker-fab').style.display = 'none';
    }

    async loadStickers() {
        try {
            let url = `/api/stickers/${this.pageType}`;
            if (this.targetUserId) {
                url += `?user_id=${this.targetUserId}`;
            }
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.stickers) {
                // Clear existing
                this.canvas.innerHTML = '';
                this.stickers = [];
                
                data.stickers.forEach(s => {
                    this.addStickerToCanvas(s, false);
                });
            }
        } catch (e) {
            console.error('Failed to load stickers:', e);
            // Optionally show a toast or alert if it's a permission error, so the user knows why it's empty
            if (e.message.includes("Permission denied")) {
                 // Maybe create a small toast or just log it
                 console.warn("User does not have permission to view these stickers.");
            }
        }
    }

    renderDrawer() {
        const options = document.querySelectorAll('.sticker-option');
        
        // Calculate current on-canvas counts
        const currentCanvasCounts = {};
        this.stickers.forEach(s => {
            currentCanvasCounts[s.badge_id] = (currentCanvasCounts[s.badge_id] || 0) + 1;
        });
        
        options.forEach(opt => {
            const badgeId = parseInt(opt.dataset.badgeId);
            const limit = this.badgeLimits[badgeId] || 1;
            const baseUsage = this.badgeBaseUsage[badgeId] || 0;
            const currentUsage = currentCanvasCounts[badgeId] || 0;
            const totalUsage = baseUsage + currentUsage;
            
            // Update Counter Badge
            const countBadge = opt.querySelector('.sticker-count-badge');
            if (countBadge) {
                countBadge.textContent = `${totalUsage}/${limit}`;
                if (totalUsage >= limit) {
                    countBadge.classList.add('badge-error');
                    countBadge.classList.remove('badge-neutral');
                } else {
                    countBadge.classList.remove('badge-error');
                    countBadge.classList.add('badge-neutral');
                }
            }
            
            // Visual feedback
            if (totalUsage >= limit) {
                opt.classList.add('opacity-50');
                // opt.style.pointerEvents = 'none'; // REMOVED: Allow clicking to show feedback
                // opt.style.pointerEvents = '';
            } else {
                opt.classList.remove('opacity-50');
            }
            
            // Re-bind click event
            opt.onclick = () => this.handleBadgeClick(opt, badgeId, opt.dataset.badgeIcon, totalUsage, limit);
        });
    }

    handleBadgeClick(element, badgeId, badgeIcon, currentUsage, limit) {
        // Re-calculate usage to be safe (race condition with rapid clicks?)
        // Relying on currentUsage passed from renderDrawer is okay because renderDrawer is called after every add.
        // BUT, since we want to allow rapid clicking, let's trust the passed value but we need to increment it locally if we don't re-render fast enough?
        // Actually, renderDrawer is sync, so it should be fine.
        
        if (currentUsage >= limit) {
            // Visual feedback: Red border flash
            element.classList.add('ring-2', 'ring-error', 'ring-offset-2');
            setTimeout(() => {
                element.classList.remove('ring-2', 'ring-error', 'ring-offset-2');
            }, 1000);
            return;
        }
        
        // Add
        const newSticker = {
            id: null, // New sticker
            badge_id: badgeId,
            badge_icon: badgeIcon,
            x: 50, // Center
            y: 50,
            rotation: 0,
            scale: 0.5,
            z_index: this.getNextZIndex()
        };
        this.addStickerToCanvas(newSticker, true);
        this.renderDrawer();
    }

    addStickerToCanvas(stickerData, isNew = false) {
        const el = document.createElement('div');
        el.className = 'sticker-item';
        el.style.left = `${stickerData.x}%`;
        el.style.top = `${stickerData.y}%`;
        el.style.zIndex = stickerData.z_index;
        this.updateStickerTransform(el, stickerData);
        
        // Content
        // Directly check if it looks like an image URL, otherwise treat as text/emoji
        // User requested NOT to check for empty/invalid specifically, but we still need to decide IMG vs TEXT tag.
        // The original logic was:
        // if (match image ext OR starts with /) -> IMG
        // else -> TEXT
        // We will revert to that simple logic without the extra "&& badge_icon" check I added, 
        // or simplify it further if the user implies "just render it".
        // But we need to know if we should render <img> or <div>.
        // Assuming the user wants the original permissive logic back or even simpler.
        // "请你不要检查 badge_icon 是否为空或不符合图片格式" -> means "don't fail/skip if empty", 
        // just try to render it.
        
        if (stickerData.badge_icon && (stickerData.badge_icon.match(/\.(jpeg|jpg|gif|png|svg|webp)$/i) || stickerData.badge_icon.startsWith('/'))) {
            el.innerHTML = `<img src="${stickerData.badge_icon}" draggable="false" />`;
        } else {
             el.innerHTML = `<div class="sticker-text flex items-center justify-center text-4xl">${stickerData.badge_icon || ''}</div>`;
        }

        if (!this.readOnly) {
            // Controls
            const handle = document.createElement('div');
            handle.className = 'sticker-control-handle sticker-handle-br';
            handle.innerHTML = `<svg class="sticker-handle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>`; // Resize/Rotate icon
            el.appendChild(handle);

            const delBtn = document.createElement('div');
            delBtn.className = 'sticker-delete-btn';
            delBtn.innerHTML = '×';
            delBtn.onclick = (e) => {
                e.stopPropagation();
                this.removeSticker(stickerData);
                this.renderDrawer();
            };
            el.appendChild(delBtn);
        }

        this.canvas.appendChild(el);
        
        // Link data
        stickerData.element = el;
        this.stickers.push(stickerData);

        // Events
        if (!this.readOnly) {
            this.makeInteractable(stickerData);

            if (isNew) {
                this.selectSticker(stickerData);
            }
        }
    }

    removeSticker(sticker) {
        if (sticker.element) {
            sticker.element.remove();
        }
        this.stickers = this.stickers.filter(s => s !== sticker);
    }

    selectSticker(sticker) {
        this.deselectAll();
        sticker.element.classList.add('selected');
        this.activeSticker = sticker;
        
        // Bring to front
        sticker.z_index = this.getNextZIndex();
        sticker.element.style.zIndex = sticker.z_index;
    }

    deselectAll() {
        this.stickers.forEach(s => s.element.classList.remove('selected'));
        this.activeSticker = null;
    }

    getNextZIndex() {
        if (this.stickers.length === 0) return 1;
        return Math.max(...this.stickers.map(s => s.z_index || 0)) + 1;
    }

    makeInteractable(sticker) {
        const el = sticker.element;
        
        // Remove old controls if any
        const existingControls = el.querySelectorAll('.sticker-control-handle, .sticker-delete-btn');
        existingControls.forEach(c => c.remove());

        // Create Rotate Handle (Top Center)
        const rotateHandle = document.createElement('div');
        rotateHandle.className = 'sticker-control-handle sticker-handle-rotate';
        rotateHandle.innerHTML = `<svg class="sticker-handle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>`;
        el.appendChild(rotateHandle);

        // Create Scale Handles
        const scaleHandles = [
            { pos: 'tl', cursor: 'nwse-resize' },
            { pos: 'bl', cursor: 'nesw-resize' },
            { pos: 'br', cursor: 'nwse-resize' }
        ];
        
        scaleHandles.forEach(h => {
            const handle = document.createElement('div');
            handle.className = `sticker-control-handle sticker-handle-scale-${h.pos}`;
            // Optional: icon for scale handles? Or just plain dots/squares.
            // Let's use simple circles as defined in CSS, maybe with small arrows icon?
            // For now, empty circles or small resize icon
            handle.innerHTML = `<svg class="sticker-handle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>`;
            el.appendChild(handle);
            
            // Bind Scale Events
            this.bindScaleEvents(handle, sticker, el);
        });

        // Create Delete Button (Top Right)
        const delBtn = document.createElement('div');
        delBtn.className = 'sticker-delete-btn';
        delBtn.innerHTML = '×';
        delBtn.onclick = (e) => {
            e.stopPropagation();
            this.removeSticker(sticker);
            this.renderDrawer();
        };
        el.appendChild(delBtn);

        // Bind Rotate Events
        this.bindRotateEvents(rotateHandle, sticker, el);

        // Drag Logic
        this.bindDragEvents(el, sticker);
        
        // Double Click to remove
        el.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            this.removeSticker(sticker);
            this.renderDrawer();
        });
    }

    bindDragEvents(el, sticker) {
        // Drag start logic
        const onDragStart = (startX, startY) => {
             // Auto collapse drawer on drag start
            this.collapseDrawer();
            
            const rect = this.canvas.getBoundingClientRect();
            // Convert % to pixels for calculation
            const initialLeftPx = (sticker.x / 100) * rect.width;
            const initialTopPx = (sticker.y / 100) * rect.height;

            return { startX, startY, rect, initialLeftPx, initialTopPx };
        };

        const onDragMove = (state, curX, curY) => {
             const deltaX = curX - state.startX;
             const deltaY = curY - state.startY;
                
             let newLeftPx = state.initialLeftPx + deltaX;
             let newTopPx = state.initialTopPx + deltaY;
                
             // Update %
             sticker.x = (newLeftPx / state.rect.width) * 100;
             sticker.y = (newTopPx / state.rect.height) * 100;
                
             el.style.left = `${sticker.x}%`;
             el.style.top = `${sticker.y}%`;

             // Check intersection with drop zone
             this.checkDropZoneIntersection(el);
        };
        
        const onDragEnd = () => {
             // Reset border
             el.style.border = '';
             // Auto expand drawer when drag ends
             this.expandDrawer();
        };

        // Mouse Drag
        el.addEventListener('mousedown', (e) => {
            if (e.target.closest('.sticker-control-handle') || e.target.closest('.sticker-delete-btn')) return;
            e.preventDefault();
            this.selectSticker(sticker);
            
            const state = onDragStart(e.clientX, e.clientY);

            const onMouseMove = (moveEvent) => {
                onDragMove(state, moveEvent.clientX, moveEvent.clientY);
            };

            const onMouseUp = () => {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
                onDragEnd();
            };

            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });

        // Touch Drag
        el.addEventListener('touchstart', (e) => {
            if (e.target.closest('.sticker-control-handle') || e.target.closest('.sticker-delete-btn')) return;
            // e.preventDefault(); 
            this.selectSticker(sticker);
            
            const touch = e.touches[0];
            const state = onDragStart(touch.clientX, touch.clientY);

            const onTouchMove = (moveEvent) => {
                moveEvent.preventDefault();
                const t = moveEvent.touches[0];
                onDragMove(state, t.clientX, t.clientY);
            };
            
            const onTouchEnd = () => {
                document.removeEventListener('touchmove', onTouchMove);
                document.removeEventListener('touchend', onTouchEnd);
                onDragEnd();
            };
            
            document.addEventListener('touchmove', onTouchMove, { passive: false });
            document.addEventListener('touchend', onTouchEnd);
        });
    }

    bindRotateEvents(handle, sticker, el) {
         const onRotateStart = (startX, startY) => {
            const rect = el.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const startRotation = sticker.rotation;
            const startAngle = Math.atan2(startY - centerY, startX - centerX);
            return { centerX, centerY, startRotation, startAngle };
         };

         const onRotateMove = (state, curX, curY) => {
             const curAngle = Math.atan2(curY - state.centerY, curX - state.centerX);
             const angleDeg = (curAngle - state.startAngle) * (180 / Math.PI);
             sticker.rotation = state.startRotation + angleDeg;
             this.updateStickerTransform(el, sticker);
         };

         // Mouse Rotate
         handle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            e.preventDefault();
            const state = onRotateStart(e.clientX, e.clientY);

            const onMouseMove = (moveEvent) => {
                onRotateMove(state, moveEvent.clientX, moveEvent.clientY);
            };
            const onMouseUp = () => {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
            };
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });

        // Touch Rotate
        handle.addEventListener('touchstart', (e) => {
            e.stopPropagation();
            e.preventDefault();
            const touch = e.touches[0];
            const state = onRotateStart(touch.clientX, touch.clientY);

            const onTouchMove = (moveEvent) => {
                moveEvent.preventDefault();
                const t = moveEvent.touches[0];
                onRotateMove(state, t.clientX, t.clientY);
            };
            const onTouchEnd = () => {
                document.removeEventListener('touchmove', onTouchMove);
                document.removeEventListener('touchend', onTouchEnd);
            };
            document.addEventListener('touchmove', onTouchMove, { passive: false });
            document.addEventListener('touchend', onTouchEnd);
        });
    }

    bindScaleEvents(handle, sticker, el) {
        const onScaleStart = (startX, startY) => {
            const rect = el.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const startScale = sticker.scale;
            const startDist = Math.hypot(startX - centerX, startY - centerY);
            return { centerX, centerY, startScale, startDist };
        };

        const onScaleMove = (state, curX, curY) => {
             const curDist = Math.hypot(curX - state.centerX, curY - state.centerY);
             const scaleRatio = curDist / state.startDist;
             sticker.scale = Math.max(0.2, state.startScale * scaleRatio);
             this.updateStickerTransform(el, sticker);
        };

        // Mouse Scale
        handle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            e.preventDefault();
            const state = onScaleStart(e.clientX, e.clientY);

            const onMouseMove = (moveEvent) => {
                onScaleMove(state, moveEvent.clientX, moveEvent.clientY);
            };
            const onMouseUp = () => {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
            };
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });

        // Touch Scale
        handle.addEventListener('touchstart', (e) => {
            e.stopPropagation();
            e.preventDefault();
            const touch = e.touches[0];
            const state = onScaleStart(touch.clientX, touch.clientY);

            const onTouchMove = (moveEvent) => {
                moveEvent.preventDefault();
                const t = moveEvent.touches[0];
                onScaleMove(state, t.clientX, t.clientY);
            };
            const onTouchEnd = () => {
                document.removeEventListener('touchmove', onTouchMove);
                document.removeEventListener('touchend', onTouchEnd);
            };
            document.addEventListener('touchmove', onTouchMove, { passive: false });
            document.addEventListener('touchend', onTouchEnd);
        });
    }

    checkDropZoneIntersection(el) {
        const dropZone = document.getElementById('sticker-drop-zone');
        if (!dropZone || dropZone.classList.contains('hidden')) return;

        // Use the inner dashed container for accurate bounds
        const zoneContainer = dropZone.firstElementChild;
        if (!zoneContainer) return;

        const stickerRect = el.getBoundingClientRect();
        const zoneRect = zoneContainer.getBoundingClientRect();

        // Calculate intersection area
        const intersectionW = Math.max(0, Math.min(stickerRect.right, zoneRect.right) - Math.max(stickerRect.left, zoneRect.left));
        const intersectionH = Math.max(0, Math.min(stickerRect.bottom, zoneRect.bottom) - Math.max(stickerRect.top, zoneRect.top));
        const intersectionArea = intersectionW * intersectionH;

        const stickerArea = stickerRect.width * stickerRect.height;
        
        // If > 50% overlap
        if (intersectionArea > stickerArea * 0.5) {
            el.style.border = '2px solid #22c55e'; // Green
        } else {
            // If dragging but not enough overlap, show red to indicate "outside" target
            // Only if it has *some* intersection? Or always red if not green?
            // User said: "if entire sticker has about half... green... if more than half is NOT in... red"
            // So if intersection > 0 but <= 0.5, red. 
            // If no intersection, maybe no border? Or red? 
            // "if more than half is not in the box, show red" implies we are trying to put it in.
            // Let's show red if there is ANY overlap but it's not enough.
            // Or maybe just always show red if we are in "dragging mode" and not green?
            // Let's stick to: if intersection > 0 && <= 0.5 -> Red.
            if (intersectionArea > 0) {
                el.style.border = '2px solid #ef4444'; // Red
            } else {
                 el.style.border = ''; // No border if completely outside
            }
        }
    }

    async saveStickers() {
        try {
            const payload = {
                stickers: this.stickers.map(s => ({
                    badge_id: s.badge_id,
                    x: s.x,
                    y: s.y,
                    rotation: s.rotation,
                    scale: s.scale,
                    z_index: s.z_index
                }))
            };
            
            await fetch(`/api/stickers/${this.pageType}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            // Show toast or feedback?
            // alert('Stickers saved!');
        } catch (e) {
            console.error('Save failed:', e);
        }
    }
}
}
