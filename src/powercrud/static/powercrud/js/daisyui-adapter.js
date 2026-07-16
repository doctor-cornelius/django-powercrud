import { createDaisyuiComposition } from './runtime/daisyui-composition.js';
import { createPublicHooksFromLegacyComposition } from './runtime/legacy-hooks.js';

window.PowerCRUDAdapter = Object.freeze({
    apiVersion: 1,
    identity: 'daisyui',
    create(context) {
        return createPublicHooksFromLegacyComposition(createDaisyuiComposition({
            global: context.window,
            documentObject: context.document,
            isElementVisible: context.isElementVisible,
            warnMissingDependency: context.warnMissingDependency,
        }));
    },
});
