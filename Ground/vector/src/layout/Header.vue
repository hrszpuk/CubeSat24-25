<script setup>
    import { useSocket } from '@/layout/composables/socket.js';
    import { useAudio } from '@/layout/composables/audio';
    import Button from 'primevue/button';
    import FloatLabel from 'primevue/floatlabel';
    import InputText from 'primevue/inputtext';
    import InputNumber from 'primevue/inputnumber';
    import Toolbar from 'primevue/toolbar';
    import Tag from 'primevue/tag';

    const { connection, getStatus, establishConnection, dropConnection, sendMessage } = useSocket();
    const { playShutdownSfx } = useAudio();

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
        <section class="layout__header-logo">
            <img src="/logo.png" alt="Vector logo">
            <span>Vector</span>
        </section>
        <Toolbar class="layout__header-toolbar">
            <template #center>
                <section class="flex gap-2">
                    <FloatLabel variant="on">
                        <InputText id="ip" v-model="connection.ip" type="text"></InputText>
                        <label for="ip">IP</label>
                    </FloatLabel>
                    <FloatLabel variant="on">
                        <InputNumber id="port" v-model="connection.port" :useGrouping="false"></InputNumber>
                        <label for="port">Port</label>
                    </FloatLabel>
                    <Button :severity="getStatus() === 'CONNECTING'  ? 'primary' : getStatus() === 'OPEN' ? 'danger' : 'success'" :label="getStatus() === 'CLOSED' ? 'Connect' : getStatus() === 'OPEN' ? 'Disconnect' : 'Connecting...'" :loading="getStatus() === 'CONNECTING'" @click="connectionButtonClick"></Button>
                    <Button v-if="getStatus() == 'OPEN'" severity="danger" label="Shutdown" @click="shutdownButtonClick"></Button>
                </section>
            </template>
        </Toolbar>
        <span>Status: <Tag :severity="getStatus() === 'CONNECTING'  ? 'info' : getStatus() === 'OPEN' ? 'success' : 'danger'" :value="getStatus() === 'CONNECTING'  ? 'CONNECTING' : getStatus() === 'OPEN' ? 'ONLINE' : 'OFFLINE'"></Tag></span>
    </header>
</template>