<script setup>
    import { useSocket } from '@/layout/composables/socket.js';    
    import Button from 'primevue/button';
    import InputText from 'primevue/inputtext';
    import InputNumber from 'primevue/inputnumber';
    import Toolbar from 'primevue/toolbar';
    import Tag from 'primevue/tag';

    const { connection, getStatus, establishConnection, dropConnection } = useSocket();

    const buttonClick = () => {
        if (getStatus() === "OPEN") {
            dropConnection();
        } else if (getStatus() === "CLOSED") {
            establishConnection();
        }
    }
</script>

<template>
    <header class="layout__header">
        <div class="layout__header-logo">
            <img src="/logo.png" alt="Vector logo">
            <span>Vector</span>
        </div>
        <Toolbar class="layout__header-toolbar">
            <template #center>
                <span class="mr-2">IP: <InputText v-model="connection.ip" type="text"></InputText></span>
                <span class="mr-2">Port: <InputNumber v-model="connection.port" :useGrouping="false"></InputNumber></span>
                <Button :severity="getStatus() === 'CONNECTING'  ? 'primary' : getStatus() === 'OPEN' ? 'danger' : 'success'" :label="getStatus() === 'CLOSED' ? 'Connect' : getStatus() === 'OPEN' ? 'Disconnect' : 'Connecting...'" :loading="getStatus() === 'CONNECTING'" @click="buttonClick"></Button>
            </template>
        </Toolbar>
        Status: <Tag :severity="getStatus() === 'CONNECTING'  ? 'info' : getStatus() === 'OPEN' ? 'success' : 'danger'" :value="getStatus() === 'CONNECTING'  ? 'CONNECTING' : getStatus() === 'OPEN' ? 'ONLINE' : 'OFFLINE'"></Tag>
    </header>
</template>