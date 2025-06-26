<script setup>
    import DynamicDialog from 'primevue/dynamicdialog';
    import Toast from 'primevue/toast';
    import Header from './Header.vue';
</script>

<template>
    <Toast position="bottom-right"></Toast>
    <DynamicDialog></DynamicDialog>
    <Header></Header>
    <main class="layout__main">
        <RouterView></RouterView>
    </main>
</template>