function formatBytes(bytes, decimals = 2) {
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return bytes === 0 ? 0 : parseFloat((bytes / Math.pow(k, i)).toFixed(dm));
}