window.PowerCRUDAdapter = Object.freeze({
    apiVersion: 1,
    identity: 'external-browser-fixture',
    create() {
        return {
            fragment: {
                init(root) {
                    const documentObject = root instanceof Document ? root : root?.ownerDocument;
                    if (documentObject) {
                        documentObject.documentElement.dataset.externalPackAdapterInitialised = 'true';
                    }
                },
            },
        };
    },
});
