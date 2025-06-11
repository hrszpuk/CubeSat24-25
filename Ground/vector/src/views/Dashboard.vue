<script setup>
    import Button from 'primevue/button'
    import Terminal from 'primevue/terminal'
    import TerminalService from 'primevue/terminalservice'
    import Toolbar from 'primevue/toolbar'
</script>

<template>
    <Toolbar>
        <template #center>
            <Button label="Initiate Phase 1"></Button>
            <Button label="Initiate Phase 2"></Button>
            <Button label="Initiate Phase 3"></Button>
        </template>
    </Toolbar>
    <Terminal welcomeMessage="Vector Terminal" prompt=">"></Terminal>
</template>