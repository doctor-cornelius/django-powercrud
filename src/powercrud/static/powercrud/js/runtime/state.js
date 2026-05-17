export function createWeakStateStore(defaultStateFactory) {
    const store = new WeakMap();
    return function ensureState(root) {
        if (!store.has(root)) {
            store.set(root, defaultStateFactory(root));
        }
        return store.get(root);
    };
}
