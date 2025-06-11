<script setup>
    import Nav from './Nav.vue'
</script>

<template>
    <header class="layout__header">
        <RouterLink to="/" class="layout__header-logo">
            <img src="/logo.png" alt="Vector logo">
            <span>Vector</span>
        </RouterLink>
        <Nav class="layout__header-nav"></Nav>
    </header>
</template>