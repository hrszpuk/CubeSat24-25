<script setup>
    import { inject, ref, onMounted } from 'vue';
    import InputText from 'primevue/inputtext';
    import Message from 'primevue/message';

    const dialogRef = inject("dialogRef");
    const fields = ref([]);
    const record = dialogRef.value?.data.record;

    onMounted(() => {
        fields.value = dialogRef.value?.data.fields;
    });

    function validateField(field) {
        return dialogRef.value?.data.hasSubmitted && field.required && !dialogRef.value?.data.record[field.id];
    }
</script>

<template>
    <form @submit.prevent="dialogRef.data.hasSubmitted = true">
        <article v-for="field in fields" class="flex flex-col gap-2">
            <label :for="field.id">{{ field.label }}<span v-if="field.required" title="required" class="required-indicator" aria-hidden="true">*</span></label>
            <InputText :id="field.id" v-model.trim="record[field.id]" :invalid="validateField(field)" fluid></InputText>
            <Message v-if="validateField(field)" severity="error" variant="simple" size="small">{{ field.label }} is a required field</Message>
        </article>
    </form>
</template>