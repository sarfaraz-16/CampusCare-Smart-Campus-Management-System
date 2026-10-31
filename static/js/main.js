/**
 * CampusCare - Core Application Scripts & UI Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    initAlerts();
    initCopyButtons();
    initFileDropzones();
    initModals();
    initMobileNav();
});

/* -------------------------------------------------------------
   Alerts & Notifications
   ------------------------------------------------------------- */
function initAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Auto-dismiss after 6 seconds
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(50px)';
            alert.style.transition = 'all 0.4s ease';
            setTimeout(() => alert.remove(), 400);
        }, 6000);

        const closeBtn = alert.querySelector('.alert-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(50px)';
                alert.style.transition = 'all 0.3s ease';
                setTimeout(() => alert.remove(), 300);
            });
        }
    });
}

function showToast(message, type = 'success') {
    let container = document.querySelector('.flash-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    const icon = type === 'success' ? 'fa-check-circle' : (type === 'danger' ? 'fa-triangle-exclamation' : 'fa-circle-info');
    
    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <div>${message}</div>
        <button type="button" class="alert-close">&times;</button>
    `;

    container.appendChild(toast);
    initAlerts();
}

/* -------------------------------------------------------------
   Copy to Clipboard (Tracking IDs)
   ------------------------------------------------------------- */
function initCopyButtons() {
    document.querySelectorAll('[data-copy]').forEach(el => {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            const textToCopy = el.getAttribute('data-copy') || el.innerText.trim();
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    showToast(`Copied Tracking ID: <strong>${textToCopy}</strong> to clipboard!`, 'success');
                }).catch(() => fallbackCopy(textToCopy));
            } else {
                fallbackCopy(textToCopy);
            }
        });
    });
}

function fallbackCopy(text) {
    const input = document.createElement('textarea');
    input.value = text;
    input.style.position = 'fixed';
    input.style.opacity = '0';
    document.body.appendChild(input);
    input.focus();
    input.select();
    try {
        document.execCommand('copy');
        showToast(`Copied Tracking ID: <strong>${text}</strong> to clipboard!`, 'success');
    } catch (err) {
        showToast('Failed to copy. Please copy manually.', 'warning');
    }
    document.body.removeChild(input);
}

/* -------------------------------------------------------------
   File Dropzone Preview
   ------------------------------------------------------------- */
function initFileDropzones() {
    const dropzone = document.querySelector('.file-dropzone');
    if (!dropzone) return;

    const fileInput = dropzone.querySelector('input[type="file"]');
    const previewContainer = document.querySelector('.file-preview');
    const previewImg = previewContainer ? previewContainer.querySelector('img') : null;
    const dropzonePrompt = dropzone.querySelector('.dropzone-prompt');

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    if (fileInput) {
        fileInput.addEventListener('change', handleFiles);
    }

    function handleFiles() {
        if (fileInput.files && fileInput.files[0]) {
            const file = fileInput.files[0];
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    if (previewImg && previewContainer) {
                        previewImg.src = e.target.result;
                        previewContainer.style.display = 'block';
                        if (dropzonePrompt) {
                            dropzonePrompt.innerHTML = `<i class="fa-solid fa-image text-emerald-400"></i> ${file.name} selected`;
                        }
                    }
                };
                reader.readAsDataURL(file);
            }
        }
    }
}

/* -------------------------------------------------------------
   Modals Management
   ------------------------------------------------------------- */
function initModals() {
    // Open Modal buttons
    document.querySelectorAll('[data-modal-target]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = btn.getAttribute('data-modal-target');
            const modal = document.getElementById(targetId);
            if (modal) {
                openModal(modal);
            }
        });
    });

    // Close Modal buttons
    document.querySelectorAll('[data-modal-close]').forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-backdrop');
            if (modal) {
                closeModal(modal);
            }
        });
    });

    // Close on backdrop click
    document.querySelectorAll('.modal-backdrop').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
    });

    // Close on ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-backdrop.active').forEach(m => closeModal(m));
        }
    });
}

function openModal(modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal(modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

/* -------------------------------------------------------------
   Mobile Navigation Toggle
   ------------------------------------------------------------- */
function initMobileNav() {
    const toggleBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    if (toggleBtn && navLinks) {
        toggleBtn.addEventListener('click', () => {
            if (navLinks.style.display === 'flex') {
                navLinks.style.display = 'none';
            } else {
                navLinks.style.display = 'flex';
                navLinks.style.flexDirection = 'column';
                navLinks.style.position = 'absolute';
                navLinks.style.top = '100%';
                navLinks.style.left = '0';
                navLinks.style.width = '100%';
                navLinks.style.background = 'rgba(9, 13, 22, 0.98)';
                navLinks.style.padding = '1.5rem';
                navLinks.style.borderBottom = '1px solid var(--border-glass)';
            }
        });
    }
}
