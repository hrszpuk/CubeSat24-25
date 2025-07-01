<script setup>
    import { ref, watch } from 'vue';
    import { useDialog } from 'primevue/usedialog';
    import { useSocket } from '@/layout/composables/socket.js';
    import Button from 'primevue/button';
    import Card from 'primevue/card';
    import ProgressDialog from '@/components/ProgressDialog.vue';

    const dialog = useDialog();
    const { getStatus, sendMessage, data } = useSocket();
    const messages = ref([]);
    const blobs = ref([]);

    watch(data, data => {
        data instanceof Blob ? blobs.value.push(data) : messages.value.unshift(data)
    });

    function openDialog() {
        dialog.open(ProgressDialog, {
            props: {header: "Receiving File from CubeSat...", modal: true, closable: false},
            data: {
                progress: 0
            }
        });
    }
</script>

<template>
    <Button severity="secondary" label="Get File" :disabled="getStatus() !== 'OPEN'" @click="sendMessage('get_file health.txt')"></Button>
    <Button severity="secondary" label="Open Progress Dialog" @click="openDialog"></Button>
    <Card>
        <template #title>Messages</template>
        <template #content>
            <article v-for="message in messages">
                <code>{{ message }}</code>
            </article>
        </template>
    </Card>
</template>