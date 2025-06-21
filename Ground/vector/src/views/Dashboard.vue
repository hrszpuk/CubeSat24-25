<script setup>
    import { onMounted, onBeforeUnmount } from 'vue';
    import Button from 'primevue/button';
    import Card from 'primevue/card';
    import ScrollPanel from 'primevue/scrollpanel';
    import Terminal from 'primevue/terminal';
    import TerminalService from 'primevue/terminalservice';
    import Toolbar from 'primevue/toolbar';

    let socket = null;

    function handleCommand(message) {
        let response;
        let argsIndex = message.indexOf(' ');
        let command = argsIndex !== -1 ? message.substring(0, argsIndex) : message;

        switch(command) {
            case "connect":
                let ip = message.substring(argsIndex + 1)

                try {
                    socket = new WebSocket(`ws://${ip}:80`)
                    response = `Attempting to connect to CubeSat at ${ip}:80...`;
                    socket.onopen = function() {
                        TerminalService.emit("response", `Successfully connected to CubeSat at ${ip}:80`);
                        console.log(`socket opened and connected to ${ip}`);
                    }
                    socket.onmessage = function(event) {
                        TerminalService.emit("response", `CubeSat: ${event.data}`);
                    }
                    socket.onclose = function () {
                        console.log("socket closed");
                        TerminalService.emit("response", `Disconnected from CubeSat`);
                        socket = null;
                    }
                } catch(err) {
                    response = `Failed to connect to CubeSat: ${err}`;
                }

                break;
            default:
                try {
                    socket.send(message)
                } catch (err) {
                    response = err
                }
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