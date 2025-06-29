<script setup>
    import { onMounted, onBeforeUnmount, reactive, ref, watch, markRaw } from 'vue';
    import { useDateFormat, useNow } from '@vueuse/core';
    import { useDialog } from 'primevue/usedialog';
    import { useSocket } from '@/layout/composables/socket.js';
    import { useToast } from '@/layout/composables/toast.js';
    import { useAudio } from '@/layout/composables/audio.js';
    import ArgumentsDialog from '@/components/ArgumentsDialog.vue';
    import DialogFooter from '@/components/DialogFooter.vue';
    import Button from 'primevue/button';
    import Card from 'primevue/card';
    import ScrollPanel from 'primevue/scrollpanel';
    import SplitButton from 'primevue/splitbutton';
    import Terminal from 'primevue/terminal';
    import TerminalService from 'primevue/terminalservice';
    import Toolbar from 'primevue/toolbar';
    
    const { getStatus, establishConnection, sendMessage, message, dropConnection } = useSocket();
    const dialog = useDialog();
    const toast = useToast();
    const {playLogSfx} = useAudio();
    const dateToday = useDateFormat(useNow(), "DD/MM/YYYY");
    const timeNow = useDateFormat(useNow(), "HH:mm:ss");
    const phase3Subphases = [{label: "Start Phase 3a", command: () => sendMessage("start_phase 3 a")}, {label: "Start Phase 3b", command: () => sendMessage("start_phase 3 b")}, {label: "Start Phase 3c", command: () => sendMessage("start_phase 3 c")}]
    const logs = ref([]);
    const messages = ref([]);
    const cubeSatData = ref([]);
    const fileMetadata = reactive({
        size: null,
        name: null,
    });
    const fileData = ref([]);    
    
    watch(
        message,
        message => {
            if (message !== "pong") {
                let obj = JSON.parse(message);            
                
                switch(obj.type) {
                    case "log":
                        playLogSfx();
                        logs.value.push(obj.data);
                        break;
                    case "data":
                        cubeSatData.value.push(obj.data);
                        break;
                    case "message":
                        if (obj.data.localeCompare("File send complete") === 0) {
                            let fileBlob = new Blob(fileData.value);
                            let fileURL = URL.createObjectURL(fileBlob);
                            const elem = document.createElement("a");
                            elem.href = fileURL;
                            elem.download = fileMetadata.name;
                            document.body.appendChild(elem);
                            elem.click();
                            document.body.removeChild(elem);
                            URL.revokeObjectURL(fileURL);
                        }
    
                        messages.value.push(obj);
                        toast.add({severity: "info", summary: "Message from CubeSat", detail: obj.data, life: 3000})
                        break;
                    case "filemetadata":
                        fileMetadata.size = obj.data.size;
                        fileMetadata.name = obj.data.name;
                        break;
                    case "filedata":
                        let data = decodeURIComponent(atob(obj.data).split('').map(function(c) {
                            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                        }).join(''));
                        fileData.value.push(data);
                        break;
                }
            }
        }
    );

    function handleCommand(message) {
        let response;
        let msg = message.split(" ");
        let cmd = msg[0];
        let args = msg.length > 1 ? msg.slice(1) : null;

        switch(cmd) {
            case "connect":
                if (args) {
                    let ip = args[0];
                    response = establishConnection(ip);
                } else {
                    response = "No IP provided!";
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

    function phase2Button() {
        dialog.open(ArgumentsDialog, {
            props: {header: "Enter Sequence for Phase 2", modal: true},
            templates: {
                footer: markRaw(DialogFooter)
            },
            data: {
                submitFunction: (record) => {
                    console.log("submit button clicked")
                    sendMessage(`start_phase 2 ${record.sequence}`);
                },
                fields: [
                    { id: "sequence", label: "Sequence", required: true }
                ],
                record: {},
                hasSubmitted: false
            }
        });
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
            <Button class="mr-2" label="Start Phase 1" :disabled="getStatus() !== 'OPEN'" @click="sendMessage('start_phase 1')"></Button>
            <Button class="mr-2" label="Start Phase 2" :disabled="getStatus() !== 'OPEN'" @click="phase2Button"></Button>
            <SplitButton class="mr-2" label="Start Phase 3" :model="phase3Subphases" :disabled="getStatus() !== 'OPEN'"></SplitButton>
            <Button severity="danger" label="Stop Phase" :disabled="getStatus() !== 'OPEN'"></Button>
        </template>
    </Toolbar>
    <Terminal welcomeMessage="Vector Terminal" prompt=">"></Terminal>
    <Card>
        <template #title>Log</template>
        <template #content>
            <ScrollPanel style="width: 100%; height: 200px">
                <code v-if="!logs.length" class="block">No log messages</code>
                <code v-else v-for="log in logs" class="block">{{ log }}</code>
            </ScrollPanel>
        </template>
    </Card>
    <Card>
        <template #title>Messages</template>
        <template #content>
            <ScrollPanel style="width: 100%; height: 200px">
                <code v-if="!messages.length" class="block">No messages from CubeSat</code>
                <code v-else v-for="message in messages" class="block">[{{ message.timestamp }}] {{ message.data }}</code>
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