/**
 * Adapt Bootstrap modal instances to PowerCRUD's private modal lifecycle.
 *
 * Core owns when a modal is requested and whether a close refreshes a list;
 * this adapter owns Bootstrap instance creation, events, and disposal.
 */
export function createBootstrap5ModalLifecycleAdapter({ global, documentObject, warnMissingDependency }) {
    const SIZE_CLASSES = {
        compact: 'modal-sm',
        default: '',
        wide: 'modal-lg',
        extra_wide: 'modal-xl',
    };

    function getModalConstructor() {
        const constructor = global.bootstrap?.Modal;
        if (typeof constructor !== 'function') {
            warnMissingDependency('bootstrap', 'window.bootstrap.Modal. Load Bootstrap before the Bootstrap PowerCRUD entry.');
            return null;
        }
        return constructor;
    }

    function getDialog(modal) {
        const dialog = modal?.querySelector('[data-powercrud-modal-box]');
        return dialog instanceof HTMLElement ? dialog : null;
    }

    function isBootstrapModal(modal) {
        return modal instanceof HTMLElement && modal.matches('[data-powercrud-modal]');
    }

    function defaultDialogClasses(dialog) {
        return dialog?.dataset.powercrudDefaultModalBoxClasses || 'modal-dialog modal-dialog-scrollable';
    }

    function hasPresentation(source) {
        return source instanceof HTMLElement && source.hasAttribute('data-powercrud-modal-size');
    }

    function getPresentation(source) {
        return {
            size: source.dataset.powercrudModalSize || 'default',
            maxWidth: source.dataset.powercrudModalMaxWidth || '',
            maxHeight: source.dataset.powercrudModalMaxHeight || 'viewport',
            scroll: source.dataset.powercrudModalScroll || 'body',
            fullscreen: source.dataset.powercrudModalFullscreen === 'true',
            verticalAlignment: source.dataset.powercrudModalVerticalAlignment || 'center',
        };
    }

    function viewportBound(value, axis) {
        const viewport = axis === 'width' ? '100dvw - 2rem' : '100dvh - 2rem';
        return value === 'viewport' || !value ? `calc(${viewport})` : `min(${value}, calc(${viewport}))`;
    }

    function normalizeBootstrapDialogClasses(value, dialog) {
        const requested = value.trim().split(/\s+/).filter(Boolean);
        const hasBootstrapDialogModifier = requested.some(className => (
            className === 'modal-dialog'
            || className === 'modal-dialog-centered'
            || className === 'modal-dialog-scrollable'
            || /^modal-(?:sm|lg|xl|xxl|fullscreen(?:-[a-z]+-down)?)$/.test(className)
        ));
        if (!hasBootstrapDialogModifier) {
            return defaultDialogClasses(dialog);
        }

        // Bootstrap needs this structural class even when a PowerCRUD caller
        // supplies only size/scroll modifiers such as "modal-lg".
        return ['modal-dialog', ...requested.filter(className => className !== 'modal-dialog')].join(' ');
    }

    function cleanupDuplicates() {
        const modalsById = new Map();
        documentObject.querySelectorAll('[data-powercrud-modal]').forEach(modal => {
            if (!isBootstrapModal(modal) || !modal.id) {
                return;
            }
            const existing = modalsById.get(modal.id);
            if (!(existing instanceof HTMLElement)) {
                modalsById.set(modal.id, modal);
                return;
            }
            const keepCurrent = modal.classList.contains('show') && !existing.classList.contains('show');
            const discarded = keepCurrent ? existing : modal;
            getModalConstructor()?.getInstance(discarded)?.dispose();
            discarded.remove();
            if (keepCurrent) {
                modalsById.set(modal.id, modal);
            }
        });
    }

    function applyTriggerClasses(modalTrigger, modal) {
        const dialog = getDialog(modal);
        if (!(dialog instanceof HTMLElement)) {
            return false;
        }
        dialog.style.removeProperty('--bs-modal-width');
        dialog.style.removeProperty('--pc-modal-max-height');
        const requested = modalTrigger.getAttribute('data-powercrud-modal-box-classes') || '';
        if (requested) {
            dialog.className = normalizeBootstrapDialogClasses(requested, dialog);
            return true;
        }
        const source = hasPresentation(modalTrigger) ? modalTrigger : dialog;
        if (!hasPresentation(source)) {
            dialog.className = defaultDialogClasses(dialog);
            return true;
        }

        const presentation = getPresentation(source);
        dialog.className = [
            'modal-dialog',
            presentation.fullscreen ? 'modal-fullscreen' : SIZE_CLASSES[presentation.size],
            !presentation.fullscreen && presentation.verticalAlignment === 'center'
                ? 'modal-dialog-centered'
                : '',
            !presentation.fullscreen && presentation.scroll === 'body'
                ? 'modal-dialog-scrollable'
                : '',
            !presentation.fullscreen && presentation.scroll === 'modal'
                ? 'pc-bootstrap-modal-scroll-shell'
                : '',
        ].filter(Boolean).join(' ');
        if (presentation.fullscreen) {
        } else {
            if (presentation.maxWidth) {
                dialog.style.setProperty(
                    '--bs-modal-width',
                    viewportBound(presentation.maxWidth, 'width'),
                );
            } else {
                dialog.style.removeProperty('--bs-modal-width');
            }
            dialog.style.setProperty(
                '--pc-modal-max-height',
                viewportBound(presentation.maxHeight, 'height'),
            );
        }
        return true;
    }

    function show(modal) {
        if (!isBootstrapModal(modal) || modal.classList.contains('show')) {
            return;
        }
        getModalConstructor()?.getOrCreateInstance(modal).show();
    }

    function bindClose(modal, callback) {
        if (!isBootstrapModal(modal) || typeof callback !== 'function') {
            return false;
        }
        modal.addEventListener('hidden.bs.modal', callback);
        return true;
    }

    function closeAll(beforeClose) {
        documentObject.querySelectorAll('[data-powercrud-modal]').forEach(modal => {
            if (!isBootstrapModal(modal)) {
                return;
            }
            beforeClose?.(modal);
            const Modal = getModalConstructor();
            const instance = Modal?.getInstance(modal);
            if (instance) {
                instance.hide();
                return;
            }
            modal.classList.remove('show');
            modal.setAttribute('aria-hidden', 'true');
        });
        cleanupDuplicates();
    }

    function dispose(root = documentObject) {
        const candidates = root instanceof Element
            ? [root, ...root.querySelectorAll('[data-powercrud-modal]')]
            : documentObject.querySelectorAll('[data-powercrud-modal]');
        candidates.forEach(modal => {
            if (isBootstrapModal(modal)) {
                getModalConstructor()?.getInstance(modal)?.dispose();
            }
        });
    }

    return { applyTriggerClasses, bindClose, cleanupDuplicates, closeAll, dispose, show };
}
