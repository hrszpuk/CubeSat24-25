import ToastEventBus from 'primevue/toasteventbus';

export function useToast() {
    return {
        add: (message) => {
            ToastEventBus.emit('add', message);
        },
        remove: (message) => {
            ToastEventBus.emit('remove', message);
        },
        removeGroup: (group) => {
            ToastEventBus.emit('remove-group', group);
        },
        removeAllGroups: () => {
            ToastEventBus.emit('remove-all-groups');
        }
    };
};