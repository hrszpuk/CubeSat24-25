<script setup>
    import { ref, watch } from 'vue';
    import { useSocket } from '@/layout/composables/socket.js';
    import Card from 'primevue/card';

    const { data } = useSocket();
    const cubeSatData = ref([]);

    watch(
        data,
        data => {
            if (typeof data === "string") {
                if (!data.localeCompare("File transfer started")) {
                    fileData.value = [];
                    receivedBytes.value = 0;
                    dialog.open(ProgressDialog, {
                        props: {header: "Receiving File from CubeSat...", modal: true, closable: false},
                        data: {
                            progress: receivedBytes,
                            total: fileMetadata.size
                        }
                    });
                } else if (!data.localeCompare("File transfer complete")) {
                    const file = new File(fileData.value, fileMetadata.name, {type: "application/zip"});
                    const fileURL = URL.createObjectURL(file);
                    const elem = document.createElement("a");
                    elem.href = fileURL;
                    elem.download = fileMetadata.name;
                    document.body.appendChild(elem);
                    elem.click();
                    document.body.removeChild(elem);
                    URL.revokeObjectURL(fileURL);
                    toast.add({severity: "info", summary: "File from CubeSat", detail: `Received file ${fileMetadata.name}`, life: 3000})
                } else if (data.localeCompare("pong")) {
                    let obj = JSON.parse(data);
                    
                    switch(obj.type) {
                        case "data":
                            cubeSatData.value.unshift(obj.data);
                            break;                        
                    }
                }
            }
        }
    );
</script>

<template>
    <Card>
        <template #title>Data</template>
        <template #content>
            <article v-for="record in cubeSatData">
                <code>{{ record }}</code>
            </article>
        </template>
    </Card>
</template>