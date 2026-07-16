import { createBootstrap5BaselineComposition } from './runtime/bootstrap5-composition.js';

/**
 * Install the shared PowerCRUD lifecycle with the private Bootstrap adapter.
 * The dynamic import ensures the stable public entry does not self-install its
 * default DaisyUI composition before this selected presentation is supplied.
 */
window.__powercrudPrivateDeferInstall = true;

try {
    const { installPowercrudRuntime } = await import('../../../js/powercrud.js');
    installPowercrudRuntime({ createComposition: createBootstrap5BaselineComposition });
} finally {
    delete window.__powercrudPrivateDeferInstall;
}
