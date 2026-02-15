/**
 * Achievement Book Logic
 * Handles data management and rendering for the achievement book page.
 */

class AchievementBook {
    constructor(userId) {
        this.userId = userId; // To support multi-user if needed (namespacing localStorage)
        this.storageKey = `achievements_${this.userId}`;
        this.itemsPerPage = 12;
        this.currentCategory = 'all';
        this.currentPage = 1;
        
        // Load categories from server if available, else default
        if (window.SERVER_CATEGORIES) {
            this.categories = window.SERVER_CATEGORIES;
        } else {
            this.categories = [
                { id: 'all', name: '全部' },
                { id: '一般', name: '一般' }
            ];
        }

        this.init();
    }

    init() {
        this.loadData();
        this.renderTabs();
        this.renderPage();
        this.bindEvents();
    }

    loadData() {
        // Load data from server-injected variable
        if (window.SERVER_ACHIEVEMENTS) {
            this.achievements = window.SERVER_ACHIEVEMENTS;
        } else {
            this.achievements = [];
        }
    }

    saveData() {
        // No-op: Data is read-only from server in this view
    }

    getMockData() {
        return [];
    }

    getFilteredAchievements() {
        let filtered = this.achievements;
        if (this.currentCategory !== 'all') {
            filtered = filtered.filter(a => a.category === this.currentCategory);
        }
        
        // Sort: Unlocked first (date desc), then Locked
        return filtered.sort((a, b) => {
            if (a.isUnlocked && !b.isUnlocked) return -1;
            if (!a.isUnlocked && b.isUnlocked) return 1;
            if (a.isUnlocked && b.isUnlocked) {
                return new Date(b.unlockDate) - new Date(a.unlockDate);
            }
            return a.id - b.id;
        });
    }

    renderTabs() {
        const container = document.getElementById('category-tabs');
        if (!container) return;
        
        container.innerHTML = this.categories.map(cat => `
            <button class="tab tab-lg ${this.currentCategory === cat.id ? 'tab-active font-bold' : ''}" 
                    onclick="book.switchCategory('${cat.id}')">
                ${cat.name}
            </button>
        `).join('');
    }

    renderPage() {
        const list = this.getFilteredAchievements();
        const totalItems = list.length;
        const totalPages = Math.ceil(totalItems / this.itemsPerPage) || 1;
        
        // Adjust current page if out of bounds
        if (this.currentPage > totalPages) this.currentPage = totalPages;
        if (this.currentPage < 1) this.currentPage = 1;

        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        const pageItems = list.slice(start, end);

        const container = document.getElementById('achievements-grid');
        if (container) {
            container.innerHTML = pageItems.map(item => this.createAchievementCard(item)).join('');
            
            // Add animation class to new items
            requestAnimationFrame(() => {
                const cards = container.querySelectorAll('.achievement-card');
                cards.forEach((card, index) => {
                    setTimeout(() => {
                        card.classList.add('opacity-100', 'translate-y-0');
                    }, index * 50);
                });
            });
        }

        this.renderPagination(totalPages);
        this.updateStats(list);
    }

    createAchievementCard(item) {
        const statusClass = item.isUnlocked 
            ? 'bg-white border-stone-200 shadow-sm hover:shadow-md hover:border-indigo-300' 
            : 'bg-stone-50 border-stone-100 grayscale opacity-80';
        
        const iconBg = item.isUnlocked ? 'bg-indigo-50 text-indigo-500' : 'bg-stone-200 text-stone-400';
        const dateText = item.isUnlocked ? `获得于 ${item.unlockDate}` : '未获得';
        const checkMark = item.isUnlocked ? '<div class="absolute top-3 right-3 text-emerald-500"><i class="fas fa-check-circle"></i></div>' : '';

        // Handle Image Icons
        let iconContent = item.icon;
        if (item.isImage) {
            iconContent = `<img src="${item.iconUrl}" class="w-10 h-10 object-contain drop-shadow-sm">`;
        }

        return `
            <div class="achievement-card card ${statusClass} border transition-all duration-300 opacity-0 transform translate-y-4 relative group">
                <div class="card-body p-5 items-center text-center">
                    ${checkMark}
                    <div class="w-16 h-16 rounded-2xl ${iconBg} flex items-center justify-center text-3xl mb-3 shadow-inner">
                        ${iconContent}
                    </div>
                    <h3 class="font-bold text-stone-800 text-lg mb-1 group-hover:text-indigo-600 transition-colors">${item.name}</h3>
                    <div class="badge badge-sm badge-ghost mb-3 text-xs">${this.getCategoryName(item.category)}</div>
                    <p class="text-sm text-stone-500 mb-2 h-10 leading-snug line-clamp-2" title="${item.description}">${item.description}</p>
                    <div class="text-[10px] text-indigo-400 bg-indigo-50 px-2 py-1 rounded-full mb-2 font-mono" title="${item.condition || '无特殊条件'}">
                        ${item.condition || '无特殊条件'}
                    </div>
                    <div class="text-xs text-stone-400 font-mono mt-auto border-t border-stone-100 pt-3 w-full">
                        ${dateText}
                    </div>
                </div>
            </div>
        `;
    }

    renderPagination(totalPages) {
        const container = document.getElementById('pagination');
        if (!container) return;

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = `
            <div class="join">
                <button class="join-item btn btn-sm" onclick="book.changePage(-1)" ${this.currentPage === 1 ? 'disabled' : ''}>«</button>
                <button class="join-item btn btn-sm">Page ${this.currentPage} / ${totalPages}</button>
                <button class="join-item btn btn-sm" onclick="book.changePage(1)" ${this.currentPage === totalPages ? 'disabled' : ''}>»</button>
            </div>
        `;
        container.innerHTML = html;
    }

    updateStats(list) {
        const total = list.length;
        const unlocked = list.filter(a => a.isUnlocked).length;
        const el = document.getElementById('achievement-stats');
        if (el) {
            el.innerHTML = `已获得 <span class="font-bold text-indigo-600">${unlocked}</span> / ${total}`;
        }
    }

    getCategoryName(id) {
        const cat = this.categories.find(c => c.id === id);
        return cat ? cat.name : id;
    }

    switchCategory(id) {
        this.currentCategory = id;
        this.currentPage = 1;
        this.renderTabs();
        this.renderPage();
    }

    changePage(delta) {
        this.currentPage += delta;
        this.renderPage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    bindEvents() {
        // Add achievement form handler (Mock)
        const form = document.getElementById('add-achievement-form');
        if(form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                // Logic to add achievement...
                // Not strictly required by prompt ("Add form in profile"? No, prompt says "In the form to add new achievement... add category dropdown")
                // Wait, prompt says: "In the form to add new achievement, add category selection dropdown".
                // Does such a form exist? 
                // Currently I don't see an "Add Achievement" form in profile.html or anywhere.
                // The prompt might imply I should CREATE such a form in the achievement book page or assume it exists.
                // "3. Implement achievement category system... In the form for adding new achievements add a category selection dropdown"
                // Since this is a "pure HTML/CSS/JS" task without backend, I should probably add a button to "Add Achievement" in the new page for demonstration.
                this.addAchievementFromForm(new FormData(form));
            });
        }
    }

    addAchievementFromForm(formData) {
        const newId = Math.max(...this.achievements.map(a => a.id)) + 1;
        const newItem = {
            id: newId,
            name: formData.get('name'),
            description: formData.get('description'),
            icon: formData.get('icon') || '🏆',
            category: formData.get('category'),
            isUnlocked: formData.get('isUnlocked') === 'on',
            unlockDate: formData.get('isUnlocked') === 'on' ? new Date().toISOString().split('T')[0] : null
        };
        
        this.achievements.unshift(newItem); // Add to top
        this.saveData();
        this.renderPage();
        
        // Close modal if exists
        const modal = document.getElementById('add_achievement_modal');
        if(modal) modal.close();
        
        if(typeof showGlobalToast === 'function') showGlobalToast('成就添加成功', 'success');
    }
}

// Global instance
let book;
document.addEventListener('DOMContentLoaded', () => {
    // Initialize with current user ID passed from template
    // We can get it from a data attribute in the body or main container
    const container = document.getElementById('achievement-book-container');
    const userId = container ? container.dataset.userId : 'guest';
    book = new AchievementBook(userId);
});
