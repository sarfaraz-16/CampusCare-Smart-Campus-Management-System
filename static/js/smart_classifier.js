/**
 * CampusCare - Smart Real-time Categorization, Priority & Duplicate Detection Engine (Client-side)
 * Connects input events to backend keyword-rule analysis without paid APIs.
 */

document.addEventListener('DOMContentLoaded', () => {
    const titleInput = document.getElementById('issue-title');
    const descInput = document.getElementById('issue-description');
    const blockInput = document.getElementById('issue-block');
    const roomInput = document.getElementById('issue-room');
    const categorySelect = document.getElementById('issue-category');
    const prioritySelect = document.getElementById('issue-priority');
    
    // UI Preview Elements
    const previewContainer = document.getElementById('smart-analysis-preview');
    const catBadge = document.getElementById('smart-category-badge');
    const prioBadge = document.getElementById('smart-priority-badge');
    const prioReason = document.getElementById('smart-priority-reason');
    const keywordsContainer = document.getElementById('smart-keywords-chips');
    const applyBtn = document.getElementById('btn-apply-suggestion');
    const escalateBtn = document.getElementById('btn-action-escalate');
    const confidenceVal = document.getElementById('ai-confidence-val');
    const confidenceFill = document.getElementById('ai-confidence-bar-fill');
    const confidenceHint = document.getElementById('ai-confidence-hint');
    const deptName = document.getElementById('ai-dept-name');

    // Duplicate Alert Elements
    const dupAlert = document.getElementById('smart-duplicate-alert');
    const dupMessage = document.getElementById('dup-message');
    const dupTicketLink = document.getElementById('dup-ticket-link');

    // Department dictionary
    const deptDictionary = {
        'Electrical': 'Electrical & Power Wing',
        'Water & Plumbing': 'Plumbing & Water Works',
        'Internet/Wi-Fi': 'Campus IT & Networks',
        'Sanitation/Housekeeping': 'Housekeeping & Sanitation',
        'Classroom Infrastructure': 'Estate & Civil Maintenance',
        'Other': 'Campus Operations Wing'
    };

    // Check QR Code URL parameters on initial load (e.g. ?block=CSE&room=Lab-2)
    const urlParams = new URLSearchParams(window.location.search);
    const qrBlock = urlParams.get('block') || urlParams.get('location_block');
    const qrRoom = urlParams.get('room') || urlParams.get('location_room');

    if (qrBlock && blockInput && !blockInput.value) {
        blockInput.value = qrBlock;
        blockInput.style.borderColor = 'var(--secondary, #70D6C6)';
    }
    if (qrRoom && roomInput && !roomInput.value) {
        roomInput.value = qrRoom;
        roomInput.style.borderColor = 'var(--secondary, #70D6C6)';
    }

    // Init Drag and Drop Image Preview
    initImageDropzone();

    if (!titleInput || !descInput || !previewContainer) return;

    let debounceTimer;
    let latestAnalysis = null;

    function triggerAnalysis() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const title = titleInput.value.trim();
            const desc = descInput.value.trim();
            const block = blockInput ? blockInput.value.trim() : '';
            const room = roomInput ? roomInput.value.trim() : '';

            if (title.length < 3 && desc.length < 5) {
                if (confidenceVal) confidenceVal.textContent = '0%';
                if (confidenceFill) confidenceFill.style.width = '0%';
                if (confidenceHint) {
                    confidenceHint.textContent = 'Awaiting input keywords...';
                    confidenceHint.style.color = 'var(--text-muted)';
                }
                return;
            }

            fetch('/api/analyze-issue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: title,
                    description: desc,
                    location_block: block,
                    location_room: room
                })
            })
            .then(res => res.json())
            .then(data => {
                latestAnalysis = data;
                updateSmartPreview(data);
            })
            .catch(err => {
                console.error("Smart classifier analysis error:", err);
            });
        }, 280);
    }

    function updateSmartPreview(data) {
        if (!data) return;

        // 1. Update Confidence Bar & Readout
        const conf = data.category_confidence || (data.matched_category_keywords && data.matched_category_keywords.length > 0 ? 92 : 65);
        if (confidenceVal) {
            confidenceVal.textContent = `${conf}%`;
        }
        if (confidenceFill) {
            confidenceFill.style.width = `${conf}%`;
        }
        if (confidenceHint) {
            if (conf >= 85) {
                confidenceHint.textContent = `High-confidence heuristic pattern (${conf}%)`;
                confidenceHint.style.color = 'var(--secondary, #70D6C6)';
            } else if (conf >= 60) {
                confidenceHint.textContent = `Moderate confidence evaluation (${conf}%)`;
                confidenceHint.style.color = 'var(--status-warning, #E5B45C)';
            } else {
                confidenceHint.textContent = `General contextual heuristic (${conf}%)`;
                confidenceHint.style.color = 'var(--text-muted)';
            }
        }

        // 2. Update Department Route
        if (deptName) {
            deptName.textContent = deptDictionary[data.suggested_category] || 'Campus Operations Wing';
        }

        // 3. Update Category Badge
        if (catBadge) {
            catBadge.innerHTML = `
                <i class="fa-solid fa-folder-open" style="color: var(--secondary);"></i> 
                ${data.suggested_category}
            `;
        }

        // 4. Update Priority Badge
        if (prioBadge) {
            let badgeClass = 'badge-priority-low';
            let icon = 'fa-circle-check';

            if (data.suggested_priority === 'Urgent') {
                badgeClass = 'badge-priority-urgent';
                icon = 'fa-triangle-exclamation';
            } else if (data.suggested_priority === 'High') {
                badgeClass = 'badge-priority-high';
                icon = 'fa-bolt';
            } else if (data.suggested_priority === 'Medium') {
                badgeClass = 'badge-priority-medium';
                icon = 'fa-circle-exclamation';
            }

            prioBadge.className = `badge ${badgeClass}`;
            prioBadge.innerHTML = `<i class="fa-solid ${icon}"></i> ${data.suggested_priority}`;
        }

        // 5. Update Reason
        if (prioReason) {
            prioReason.innerText = data.priority_reason || 'Evaluated from issue details';
        }

        // 6. Update Matched Trigger Keywords Chips
        if (keywordsContainer) {
            keywordsContainer.innerHTML = '';
            const allMatched = [
                ...(data.matched_category_keywords || []),
                ...(data.matched_priority_keywords || [])
            ];

            const uniqueKeywords = [...new Set(allMatched)];
            if (uniqueKeywords.length > 0) {
                uniqueKeywords.forEach(kw => {
                    const chip = document.createElement('span');
                    chip.className = 'keyword-chip';
                    chip.innerHTML = `<i class="fa-solid fa-tag text-xs" style="color: var(--secondary);"></i> ${kw}`;
                    keywordsContainer.appendChild(chip);
                });
            }

            if (data.location_boost) {
                const locChip = document.createElement('span');
                locChip.className = 'keyword-chip';
                locChip.style.background = 'rgba(240, 120, 104, 0.18)';
                locChip.style.color = '#F07868';
                locChip.style.borderColor = 'rgba(240, 120, 104, 0.35)';
                locChip.innerHTML = `<i class="fa-solid fa-location-dot text-xs"></i> Critical Campus Zone`;
                keywordsContainer.appendChild(locChip);
            }

            if (uniqueKeywords.length === 0 && !data.location_boost) {
                keywordsContainer.innerHTML = '<span class="text-xs text-muted" style="color: var(--text-muted); font-size: 0.75rem;">General contextual heuristic</span>';
            }
        }

        // 7. Duplicate Ticket Alert Handling
        if (dupAlert && dupMessage) {
            if (data.duplicate && data.duplicate.is_duplicate) {
                dupAlert.style.display = 'flex';
                dupMessage.textContent = data.duplicate.message;
                if (dupTicketLink && data.duplicate.duplicate_ticket) {
                    dupTicketLink.href = `/track/${data.duplicate.duplicate_ticket.ticket_id}`;
                    dupTicketLink.style.display = 'inline-flex';
                }
            } else {
                dupAlert.style.display = 'none';
            }
        }
    }

    // Apply Button Click
    if (applyBtn) {
        applyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (!latestAnalysis) return;

            // Apply category if exists in select options
            if (categorySelect && latestAnalysis.suggested_category) {
                for (let option of categorySelect.options) {
                    if (option.value.toLowerCase() === latestAnalysis.suggested_category.toLowerCase()) {
                        categorySelect.value = option.value;
                        break;
                    }
                }
            }

            // Apply priority
            if (prioritySelect && latestAnalysis.suggested_priority) {
                prioritySelect.value = latestAnalysis.suggested_priority;
            }

            // Visual feedback
            applyBtn.innerHTML = `
                <span style="display: flex; align-items: center; gap: 0.45rem; color: var(--secondary);">
                    <i class="fa-solid fa-check"></i>
                    <span>Applied to Form!</span>
                </span>
                <i class="fa-solid fa-check text-xs" style="color: var(--secondary);"></i>
            `;
            setTimeout(() => {
                applyBtn.innerHTML = `
                    <span style="display: flex; align-items: center; gap: 0.45rem;">
                        <i class="fa-solid fa-wand-magic-sparkles" style="color: var(--primary);"></i>
                        <span>Apply Suggestions to Form</span>
                    </span>
                    <i class="fa-solid fa-arrow-right text-xs"></i>
                `;
            }, 2000);
        });
    }

    // Escalate Button Click
    if (escalateBtn) {
        escalateBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (prioritySelect) {
                prioritySelect.value = 'Urgent';
            }
            escalateBtn.innerHTML = `
                <span style="display: flex; align-items: center; gap: 0.45rem; color: var(--status-urgent);">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <span>Emergency Priority Armed!</span>
                </span>
                <i class="fa-solid fa-check text-xs" style="color: var(--status-urgent);"></i>
            `;
            escalateBtn.style.borderColor = 'var(--status-urgent)';
            setTimeout(() => {
                escalateBtn.innerHTML = `
                    <span style="display: flex; align-items: center; gap: 0.45rem;">
                        <i class="fa-solid fa-shield-halved" style="color: var(--status-urgent);"></i>
                        <span>Flag Life-Safety Emergency</span>
                    </span>
                    <i class="fa-solid fa-arrow-right text-xs"></i>
                `;
                escalateBtn.style.borderColor = '';
            }, 2500);
        });
    }

    // Bind event listeners with debounce
    titleInput.addEventListener('input', triggerAnalysis);
    descInput.addEventListener('input', triggerAnalysis);
    if (blockInput) blockInput.addEventListener('input', triggerAnalysis);
    if (roomInput) roomInput.addEventListener('input', triggerAnalysis);

    /* -------------------------------------------------------------
       Drag & Drop File Upload with Clean Thumbnail Preview
       ------------------------------------------------------------- */
    function initImageDropzone() {
        const dropzone = document.getElementById('file-dropzone');
        const fileInput = document.getElementById('file-input');
        const previewContainer = document.getElementById('file-preview-container');
        const previewImg = document.getElementById('file-preview-img');
        const fileMetaText = document.getElementById('file-meta-text');
        const removeBtn = document.getElementById('btn-remove-file');
        const dropzonePrompt = document.getElementById('dropzone-prompt');

        if (!dropzone || !fileInput) return;

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
                dropzone.style.borderColor = 'var(--primary-light, #818cf8)';
                dropzone.style.background = 'rgba(99, 102, 241, 0.08)';
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
                dropzone.style.borderColor = '';
                dropzone.style.background = '';
            });
        });

        dropzone.addEventListener('drop', (e) => {
            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
                fileInput.files = e.dataTransfer.files;
                handlePreview(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files && fileInput.files[0]) {
                handlePreview(fileInput.files[0]);
            }
        });

        function handlePreview(file) {
            if (!file.type.startsWith('image/')) {
                alert('Please upload an image file (PNG, JPG, JPEG, WEBP).');
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                if (previewImg && previewContainer) {
                    previewImg.src = e.target.result;
                    previewContainer.style.display = 'block';
                    if (fileMetaText) {
                        const sizeKB = (file.size / 1024).toFixed(1);
                        fileMetaText.innerHTML = `<strong>${file.name}</strong> (${sizeKB} KB)`;
                    }
                    if (dropzonePrompt) {
                        dropzonePrompt.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400"></i> Photo attached (${file.name})`;
                    }
                }
            };
            reader.readAsDataURL(file);
        }

        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                fileInput.value = '';
                if (previewContainer) previewContainer.style.display = 'none';
                if (previewImg) previewImg.src = '';
                if (dropzonePrompt) {
                    dropzonePrompt.innerHTML = `
                        <i class="fa-solid fa-cloud-arrow-up" style="font-size: 2.2rem; color: var(--primary-light); margin-bottom: 0.5rem;"></i>
                        <h5 style="font-size: 1rem; margin-bottom: 0.25rem;">Drag & drop photo here, or click to browse</h5>
                        <p style="font-size: 0.8rem; color: var(--text-muted);">Supports PNG, JPG, JPEG, WEBP up to 16MB</p>
                    `;
                }
            });
        }
    }
});
