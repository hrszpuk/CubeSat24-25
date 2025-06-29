<script setup>
    import { useSocket } from '@/layout/composables/socket.js';
    import { useAudio } from '@/layout/composables/audio';
    import Button from 'primevue/button';
    import InputText from 'primevue/inputtext';
    import InputNumber from 'primevue/inputnumber';
    import Toolbar from 'primevue/toolbar';
    import Tag from 'primevue/tag';

    const { connection, getStatus, establishConnection, dropConnection } = useSocket();
    const { playShutdownSfx } = useAudio;

    const connectionButtonClick = () => {
        if (getStatus() === "OPEN") {
            dropConnection();
        } else if (getStatus() === "CLOSED") {
            establishConnection();
        }
    }

    const shutdownButtonClick = () => {
        sendMessage("shutdown");
        playShutdownSfx();
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
                <Button :severity="getStatus() === 'CONNECTING'  ? 'primary' : getStatus() === 'OPEN' ? 'danger' : 'success'" :label="getStatus() === 'CLOSED' ? 'Connect' : getStatus() === 'OPEN' ? 'Disconnect' : 'Connecting...'" :loading="getStatus() === 'CONNECTING'" @click="connectionButtonClick"></Button>
                <Button v-if="getStatus() == 'OPEN'" class="mr-2" severity="danger" label="Shutdown" @click="shutdownButtonClick"></Button>
            </template>
        </Toolbar>
        Status: <Tag :severity="getStatus() === 'CONNECTING'  ? 'info' : getStatus() === 'OPEN' ? 'success' : 'danger'" :value="getStatus() === 'CONNECTING'  ? 'CONNECTING' : getStatus() === 'OPEN' ? 'ONLINE' : 'OFFLINE'"></Tag>
    </header>
</template>