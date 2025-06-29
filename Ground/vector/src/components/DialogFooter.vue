<script setup>
    import { inject, ref, watch } from 'vue';
    import Button from 'primevue/button';

    const dialogRef = inject("dialogRef");
    const isProcessing = ref(false);

    function closeDialog() {
        dialogRef.value?.close();
    }

    function submit() {
        const fields = dialogRef.value?.data.fields;
        const record = dialogRef.value?.data.record;

        let isInputValid = true;

        fields.forEach((field) => {
            if (field.required && !record[field.id]) {
                isInputValid = false;
            }
        });

        if (isInputValid) {
            isProcessing.value = true;
            dialogRef.value?.data.submitFunction(record);
            isProcessing.value = false;
        }
    }

    watch(
        () => dialogRef.value?.data.hasSubmitted,
        hasSubmitted => {
            if (hasSubmitted) {
                submit();
            }
        }
    );
</script>

<template>
    <Button label="Cancel" severity="danger" text @click="closeDialog"></Button>
    <Button :class="isProcessing ? 'cursor-wait' : ''" label="Submit" iconPos="right" severity="success" :loading="isProcessing" @click="dialogRef.data.hasSubmitted = true"></Button>
</template>