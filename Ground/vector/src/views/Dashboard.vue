<script setup>
    import { onMounted, onBeforeUnmount, reactive, ref, watch } from 'vue';
    import { useDateFormat, useFileSystemAccess, useNow } from '@vueuse/core';    
    import { useSocket } from '@/layout/composables/socket.js';
    import { useToast } from '@/layout/composables/toast.js';
    import Button from 'primevue/button';
    import Card from 'primevue/card';
    import ScrollPanel from 'primevue/scrollpanel';
    import SplitButton from 'primevue/splitbutton';
    import Terminal from 'primevue/terminal';
    import TerminalService from 'primevue/terminalservice';
    import Toolbar from 'primevue/toolbar';
    
    const { establishConnection, sendMessage, message, dropConnection } = useSocket();
    const toast = useToast();
    const dateToday = useDateFormat(useNow(), "DD/MM/YYYY");
    const timeNow = useDateFormat(useNow(), "HH:mm:ss");
    const { isSupported, data, file, fileName, fileMIME, fileSize, fileLastModified, create, open, save, saveAs, updateData } = useFileSystemAccess();
    const phase3_subphases = [{label: "Start Phase 3a", command: () => {}}, {label: "Start Phase 3b", command: () => {}}, {label: "Start Phase 3c", command: () => {}}]
    const log = ref([]);
    const messages = ref([]);
    const filemetadata = reactive({
        size: null,
        name: null,
    });
    
    watch(
        message,
        message => {
            let obj = JSON.parse(message);
            messages.value.push(obj);
            
            switch(obj.type) {
                case "log":
                    log.value.push(obj.data)
                    break;
                case "message":
                    toast.add({severity: "info", summary: "Message from CubeSat", detail: obj.data, life: 3000})
                    break;
                case "filemetadata":
                    filemetadata.size = obj.size;
                    filemetadata.name = obj.name;
                    break;
            }
        }
    );

    function handleCommand(message) {
        let response;
        let msg = message.split(" ");
        let cmd = msg[0];
        let args = msg.slice(1);

        switch(cmd) {
            case "connect":
                let ip = args[0]
                response = establishConnection(ip);

                break;
            case "start_phase":
                let phase = parseInt(args[0])

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
            <Button class="mr-2" label="Start Phase 1"></Button>
            <Button class="mr-2" label="Start Phase 2"></Button>
            <SplitButton class="mr-2" label="Start Phase 3" :model="phase3_subphases"></SplitButton>
            <Button severity="danger" label="Stop Phase"></Button>
        </template>
    </Toolbar>
    <Terminal welcomeMessage="Vector Terminal" prompt=">"></Terminal>
    <Card>
        <template #title>Log</template>
        <template #content>
            <ScrollPanel>
                <code v-if="!log.length" class="block">No log messages</code>
                <code v-else v-for="message in log" class="block">{{ message }}</code>
            </ScrollPanel>
        </template>
    </Card>
    <Card>
        <template #title>Messages</template>
        <template #content>
            <ScrollPanel>
                <code v-if="!messages.length" class="block">No messages</code>
                <code v-else v-for="message in messages" class="block">{{ message }}</code>
            </ScrollPanel>
        </template>
    </Card>
    <Card>
        <template #title>Status</template>
        <template #content>
            <code class="block">Date: {{ dateToday }}</code>
            <code class="block">Time: {{ timeNow }}</code>
        </template>
    </Card>
</template>