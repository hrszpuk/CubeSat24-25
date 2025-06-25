<script setup>
    import { onMounted, onBeforeUnmount, computed, ref, watch } from 'vue';
    import { useSocket } from '@/layout/composables/socket.js';
    import Button from 'primevue/button';
    import Card from 'primevue/card';
    import ScrollPanel from 'primevue/scrollpanel';    
    import Terminal from 'primevue/terminal';
    import TerminalService from 'primevue/terminalservice';
    import Toolbar from 'primevue/toolbar';
    
    const { establishConnection, sendMessage, data, dropConnection } = useSocket();
    const messages = ref([]);
    const getNow = computed(() => new Date());

    watch(
        data,
        message => {
            let obj = JSON.parse(message);
            messages.value.push(obj);

            switch(obj.type) {
                case "message":
                    alert(`CubeSat: ${obj.data}`)
                    break;
            }
        }
    );

    function handleCommand(message) {
        let response;
        let argsIndex = message.indexOf(' ');
        let command = argsIndex !== -1 ? message.substring(0, argsIndex) : message;

        switch(command) {
            case "connect":
                let ip = message.substring(argsIndex + 1)
                response = establishConnection(ip);

                break;
            case "start_phase":
                let phase = parseInt(message.substring(argsIndex + 1))

                switch(phase) {
                    case 1:
                        socket.send("start_phase 1");
                        break;
                    default:
                        response = `${phase} is not a valid phase!`;
                }
                break;
            case "disconnect":
                response = dropConnection();
                
                break;
            default:
                sendMessage(message)
        }

        TerminalService.emit("response", response)
    }

    onMounted(() => {
        TerminalService.on("command", handleCommand)
    })

    onBeforeUnmount(() => {
        TerminalService.off("command", handleCommand)
    })
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
    <ScrollPanel>
        <Card>
            <template #title>Messages</template>
            <template #content>
                <code>{{ messages }}</code>
            </template>
        </Card>
    </ScrollPanel>
    <Card>
        <template #title>Status</template>
        <template #content>
            Date: {{ getNow.toLocaleDateString() }}<br>
            Time: {{ getNow.toLocaleTimeString() }}
        </template>
    </Card>
    <Card>
        <template #title>Live Feed</template>
        <template #content>
            <img src="https://picsum.photos/600/400">
        </template>
    </Card>
</template>