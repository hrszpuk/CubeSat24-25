<script setup>
    import { onMounted, onBeforeUnmount } from 'vue';
    import { useSocket } from '@/layout/composables/socket.js';
    import Button from 'primevue/button';
    import Card from 'primevue/card';
    import ScrollPanel from 'primevue/scrollpanel';    
    import Terminal from 'primevue/terminal';
    import TerminalService from 'primevue/terminalservice';
    import Toolbar from 'primevue/toolbar';
    
    const { establishConnection, sendMessage, dropConnection } = useSocket();

    const handleSocketMessages = (event) => {
        let res = JSON.parse(event.data);

        switch(res.type) {
            case "message":
                alert(`CubeSat: ${res.data}`)
                TerminalService.emit("response", res.data)
                break;
        }
    }

    function handleCommand(message) {
        let response;
        let argsIndex = message.indexOf(' ');
        let command = argsIndex !== -1 ? message.substring(0, argsIndex) : message;

        switch(command) {
            case "connect":
                let ip = message.substring(argsIndex + 1)
                response = establishConnection(ip, handleSocketMessages);

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
    <Terminal welcomeMessage="Vector Terminal" prompt=">"></Terminal>
    <Toolbar>
        <template #center>
            <Button label="Initiate Phase 1"></Button>
            <Button label="Initiate Phase 2"></Button>
            <Button label="Initiate Phase 3"></Button>
        </template>
    </Toolbar>
    <Card>
        <template #title>Status</template>
        <template #content>
            Lorem ipsum dolor sit amet consectetur adipisicing elit. Dolores cumque vel corrupti temporibus, quod iure quae laboriosam distinctio autem beatae magnam quisquam nesciunt! Nobis, laborum? Neque quibusdam eos ipsa quo.
        </template>
    </Card>
    <ScrollPanel>
        <Card>
            <template #title>Log</template>
            <template #content>
                <code>Lorem, ipsum dolor sit amet consectetur adipisicing elit. Culpa recusandae aliquid consequatur cum, vitae iste sint quo expedita dicta quasi error? Dignissimos enim et, aliquid voluptate odit omnis quisquam tempora.</code>
            </template>
        </Card>
    </ScrollPanel>
    <Card>
        <template #title>Live Feed</template>
        <template #content>
            <img src="https://picsum.photos/600/400">
        </template>
    </Card>
</template>