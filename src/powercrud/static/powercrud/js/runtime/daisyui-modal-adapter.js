import { DEFAULT_MODAL_BOX_CLASSES } from './selectors.js';

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
        const defaultClasses = modalBox.dataset.powercrudDefaultModalBoxClasses || DEFAULT_MODAL_BOX_CLASSES;
        const requestedClasses = modalTrigger.getAttribute('data-powercrud-modal-box-classes');
        modalBox.className = requestedClasses || defaultClasses;
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

    return {
        applyTriggerClasses,
        cleanupDuplicates,
        closeAll,
    };
}
