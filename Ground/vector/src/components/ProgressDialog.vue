<script setup>
    import { inject, ref, watch } from 'vue';
    import ProgressBar from 'primevue/progressbar';

    const dialogRef = inject("dialogRef");
    const value = ref(0);
    const total = dialogRef.value?.data.total;
    const progress = () => dialogRef.value?.data.progress;
    
    function formatBytes(bytes, decimals = 2) {
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return bytes === 0 ? 0 : parseFloat((bytes / Math.pow(k, i)).toFixed(dm));
    }

    watch(progress, progress => {
        value.value = progress/total * 100;

        if (progress/total * 100 === 100) {
            dialogRef.value?.close();            
        }
    });
</script>

<template>
    <ProgressBar :value>{{ formatBytes(progress()) }} / {{ formatBytes(total) }} {{ ["Bytes", "KB", "MB", "GB"][Math.floor(Math.log(total) / Math.log(1024))] }}</ProgressBar>
</template>