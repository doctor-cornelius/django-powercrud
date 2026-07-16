import { DEFAULT_MODAL_BOX_CLASSES } from './selectors.js';

const SIZE_CLASSES = {
    compact: 'max-w-sm',
    default: 'max-w-lg',
    wide: 'max-w-4xl',
    extra_wide: 'max-w-6xl',
};

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

// Private DaisyUI presentation adapter for native dialog lifecycle behavior.
// Core retains modal-trigger semantics and refresh-on-close decisions.
export function createDaisyuiModalLifecycleAdapter(context) {
    const { documentObject } = context;

    function cleanupDuplicates() {
        // HTMX swaps can leave an old dialog and a new dialog with the same id;
        // keep the open instance, otherwise keep the newest rendered instance.
        const modalsById = new Map();
        documentObject.querySelectorAll('[data-powercrud-modal]').forEach(modal => {
            if (!(modal instanceof HTMLDialogElement) || !modal.id) {
                return;
            }

            const existingModal = modalsById.get(modal.id);
            if (!(existingModal instanceof HTMLDialogElement)) {
                modalsById.set(modal.id, modal);
                return;
            }

            if (existingModal.open && !modal.open) {
                modal.remove();
                return;
            }

            if (!existingModal.open && modal.open) {
                existingModal.remove();
                modalsById.set(modal.id, modal);
                return;
            }

            existingModal.remove();
            modalsById.set(modal.id, modal);
        });
    }

    function applyTriggerClasses(modalTrigger, modal) {
        const modalBox = modal?.querySelector('[data-powercrud-modal-box]');
        if (!(modalBox instanceof HTMLElement)) {
            return false;
        }
        const content = modalBox.querySelector('[data-powercrud-modal-content]');
        if (modal instanceof HTMLDialogElement) {
            modal.className = modal.dataset.powercrudDefaultModalClasses || 'modal';
            modal.classList.remove('modal-top', 'modal-middle');
        }
        modalBox.style.maxWidth = '';
        modalBox.style.maxHeight = '';
        modalBox.style.width = '';
        modalBox.style.height = '';
        modalBox.style.borderRadius = '';
        modalBox.style.overflowY = '';
        if (content instanceof HTMLElement) {
            content.className = content.dataset.powercrudDefaultModalContentClasses
                || 'min-h-0 flex-1 overflow-y-auto py-4';
        }
        const defaultClasses = modalBox.dataset.powercrudDefaultModalBoxClasses || DEFAULT_MODAL_BOX_CLASSES;
        const requestedClasses = modalTrigger.getAttribute('data-powercrud-modal-box-classes');
        if (requestedClasses) {
            modalBox.className = requestedClasses;
            return true;
        }

        const source = hasPresentation(modalTrigger) ? modalTrigger : modalBox;
        if (!hasPresentation(source) || !(modal instanceof HTMLDialogElement)) {
            modalBox.className = defaultClasses;
            return true;
        }

        const presentation = getPresentation(source);
        modal.classList.remove('modal-top', 'modal-middle');
        if (!presentation.fullscreen) {
            modal.classList.add(
                presentation.verticalAlignment === 'top' ? 'modal-top' : 'modal-middle',
            );
        }

        modalBox.className = [
            'modal-box',
            'flex',
            'flex-col',
            SIZE_CLASSES[presentation.size] || SIZE_CLASSES.default,
        ].join(' ');
        modalBox.style.maxWidth = presentation.fullscreen
            ? 'none'
            : (presentation.maxWidth ? viewportBound(presentation.maxWidth, 'width') : '');
        modalBox.style.maxHeight = presentation.fullscreen
            ? 'none'
            : viewportBound(presentation.maxHeight, 'height');
        modalBox.style.width = presentation.fullscreen ? '100dvw' : '';
        modalBox.style.height = presentation.fullscreen ? '100dvh' : '';
        modalBox.style.borderRadius = presentation.fullscreen ? '0' : '';
        modalBox.style.overflowY = presentation.scroll === 'modal' ? 'auto' : 'hidden';

        if (content instanceof HTMLElement) {
            content.className = presentation.scroll === 'body'
                ? 'min-h-0 flex-1 overflow-y-auto py-4'
                : 'min-h-0 flex-1 py-4';
        }
        return true;
    }

    function closeAll(beforeClose) {
        documentObject.querySelectorAll('[data-powercrud-modal]').forEach(modal => {
            if (!(modal instanceof HTMLDialogElement) || typeof modal.close !== 'function') {
                return;
            }
            beforeClose?.(modal);
            modal.close();
        });
        cleanupDuplicates();
    }

    function bindClose(modal, callback) {
        if (!(modal instanceof HTMLDialogElement) || typeof callback !== 'function') {
            return false;
        }
        modal.addEventListener('close', callback);
        return true;
    }

    function show(modal) {
        if (modal instanceof HTMLDialogElement && !modal.open && typeof modal.showModal === 'function') {
            modal.showModal();
        }
    }

    function dispose() {
        // Native dialogs do not retain framework instances between HTMX swaps.
    }

    return {
        applyTriggerClasses,
        bindClose,
        cleanupDuplicates,
        closeAll,
        dispose,
        show,
    };
}
