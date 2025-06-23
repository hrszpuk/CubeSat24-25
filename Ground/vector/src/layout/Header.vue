<script setup>
    import { useSocket } from '@/layout/composables/socket.js';
    import Tag from 'primevue/tag';
    import Nav from './Nav.vue';

    const { isConnecting, isOnline } = useSocket();
</script>

<template>
    <header class="layout__header">
        <RouterLink to="/" class="layout__header-logo">
            <img src="/logo.png" alt="Vector logo">
            <span>Vector</span>
        </RouterLink>
        <Nav class="layout__header-nav"></Nav>
        Status: <Tag :severity="isConnecting ? 'info' : isOnline ? 'success' : 'danger'" :value="isConnecting ? 'Connecting...' : isOnline ? 'Online' : 'Offline'"></Tag>
    </header>
</template>