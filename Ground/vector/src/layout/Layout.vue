<script setup>
    import Button from 'primevue/button'
    import ConfirmDialog from 'primevue/confirmdialog'
    import DynamicDialog from 'primevue/dynamicdialog'
    import Toast from 'primevue/toast'
    import Header from './Header.vue'
</script>

<template>
    <Toast></Toast>
    <DynamicDialog></DynamicDialog>
    <ConfirmDialog>
        <template #container="{ message, acceptCallback, rejectCallback }">
            <section class="p-dialog-header pb-0 flex-col justify-center">
                <i :class="['p-confirmdialog-icon', message.icon]"></i>
                <span class="p-dialog-title my-4 text-2xl">{{ message.header }}</span>
            </section>
            <section class="p-dialog-content px-6 py-0 mb-6">
                <p class="p-confirmdialog-message w-full m-0 text-sm text-center">{{ message.message }}</p>
            </section>
            <section class="p-dialog-footer">
                <Button class="p-confirmdialog-reject-button grow" :label="message.rejectLabel" :icon="message.rejectIcon" severity="secondary" @click="rejectCallback"></Button>
                <Button class="p-confirmdialog-accept-button grow" :label="message.acceptLabel" :icon="message.acceptIcon" :severity="message.severity" autofocus @click="acceptCallback"></Button>
            </section>
        </template>
    </ConfirmDialog>
    <Header></Header>
    <main class="layout__main">
        <RouterView></RouterView>
    </main>
</template>