document.addEventListener("DOMContentLoaded", function() {
    // Select links that are the only child of a paragraph (link on its own line)
    // OR links that explicitly have title="card"
    // Targeting both .markdown-body (Wiki) and .prose (Book) containers
    const links = document.querySelectorAll('.markdown-body p > a:only-child, .markdown-body a[title="card"], .prose p > a:only-child, .prose a[title="card"]');
    
    links.forEach(link => {
        // Skip internal links (anchors) or already processed ones
        if (link.getAttribute('href').startsWith('#') || link.classList.contains('card-processed')) return;
        
        link.classList.add('card-processed');
        const url = link.href;
        const originalText = link.textContent;
        
        // Create card container
        const card = document.createElement('a');
        card.href = url;
        card.className = 'link-card';
        card.target = '_blank';
        card.innerHTML = `
            <div class="link-card-text">
                <div class="link-card-title">${originalText}</div>
                <div class="link-card-meta">Loading preview...</div>
            </div>
        `;
        
        // Replace logic
        // If it's the only child of P, replace the P to avoid nested block-in-inline issues (though A is inline)
        // Actually, we want the card to be block-level, so replacing P is better.
        if (link.parentNode.tagName === 'P' && link.parentNode.childNodes.length === 1) {
             link.parentNode.replaceWith(card);
        } else {
             link.replaceWith(card);
        }

        // Fetch metadata
        fetch(`/api/link-preview?url=${encodeURIComponent(url)}`)
            .then(res => res.json())
            .then(data => {
                const { title, description, image } = data;
                // Use fetched title if available, otherwise original text
                const displayTitle = title || originalText;
                const displayDesc = description || '';
                const displayHost = new URL(url).hostname;
                
                card.innerHTML = `
                    <div class="link-card-text">
                        <div class="link-card-title">${displayTitle}</div>
                        <div class="link-card-desc">${displayDesc}</div>
                        <div class="link-card-meta">
                            ${image && !image.startsWith('http') ? `<img src="${image}" class="link-card-icon" />` : ''}
                            ${displayHost}
                        </div>
                    </div>
                    ${image ? `<div class="link-card-image" style="background-image: url('${image}')"></div>` : ''}
                `;
            })
            .catch(err => {
                // Fallback on error
                card.innerHTML = `
                    <div class="link-card-text">
                        <div class="link-card-title">${originalText}</div>
                        <div class="link-card-desc">${url}</div>
                    </div>
                `;
            });
    });
});
