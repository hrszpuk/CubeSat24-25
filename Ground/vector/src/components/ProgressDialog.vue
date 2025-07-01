<script setup>
    import { inject, watch } from 'vue';
    import ProgressBar from 'primevue/progressbar';

    const dialogRef = inject("dialogRef");
    const progress = () => dialogRef.value?.data.progress;
    const total = dialogRef.value?.data.total;

    watch(() => progress(), progress => {
        if (progress/total * 100 === 100) {
            dialogRef.value?.close();            
        }
    });
</script>

<template>
    <ProgressBar :value="progress()/total * 100">{{ progress() }} / {{ total }} bytes</ProgressBar>
</template>