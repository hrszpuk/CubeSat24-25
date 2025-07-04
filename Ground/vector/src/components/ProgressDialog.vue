<script setup>
    import { inject, ref, watch } from 'vue';
    import { useSocket } from '@/layout/composables/socket.js';
    import ProgressBar from 'primevue/progressbar';
    import formatBytes from '@/utils.js';

    const { getStatus } = useSocket();
    const dialogRef = inject("dialogRef");
    const value = ref(0);
    const total = dialogRef.value?.data.total;
    const progress = () => dialogRef.value?.data.progress;

    watch(progress, progress => {
        value.value = progress/total * 100;
        
        if (value.value === 100) {
            dialogRef.value?.close();
        }
    });
    
    watch(getStatus, () => dialogRef.value?.close());
</script>

<template>
    <ProgressBar :value>{{ formatBytes(progress()) }} / {{ formatBytes(total) }} {{ ["Bytes", "KB", "MB", "GB"][Math.floor(Math.log(total) / Math.log(1024))] }}</ProgressBar>
</template>