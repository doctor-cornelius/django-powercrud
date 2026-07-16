import { createBootstrap5BaselineComposition } from './runtime/bootstrap5-composition.js';
import { createBootstrap5PublicHooks } from './runtime/bootstrap5-public-hooks.js';

window.PowerCRUDAdapter = Object.freeze({
    apiVersion: 1,
    identity: 'bootstrap5',
    create(context) {
        return createBootstrap5PublicHooks(createBootstrap5BaselineComposition({
            global: context.window,
            documentObject: context.document,
            isElementVisible: context.isElementVisible,
            warnMissingDependency: context.warnMissingDependency,
        }));
    },
});
