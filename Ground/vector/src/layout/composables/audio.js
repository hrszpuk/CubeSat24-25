const connectSfx = new Audio("/connect_sfx.mp3");
const logSfx = new Audio("/log_sfx.mp3");
const log2Sfx = new Audio("/log2_sfx.mp3");
const messageSfx = new Audio("/message_sfx.mp3");
const errorSfx = new Audio("/error_sfx.mp3");
const error2Sfx = new Audio("/error2_sfx.mp3");
const disconnectSfx = new Audio("/disconnect_sfx.mp3");
const shutdownSfx = new Audio("/shutdown_sfx.mp3");

export function useAudio() {
    const playConnectSfx = () => connectSfx.play();
    const playLogSfx = () => Math.floor(Math.random() * (100 + 1)) < 50 ? logSfx.play() : log2Sfx.play();
    const playMessageSfx = () => messageSfx.play();
    const playErrorSfx = () => Math.floor(Math.random() * (100 + 1)) < 50 ? errorSfx.play() : error2Sfx.play();
    const playDisconnectSfx = () => disconnectSfx.play();
    const playShutdownSfx = () => shutdownSfx.play();

    return {playConnectSfx, playLogSfx, playMessageSfx, playErrorSfx, playDisconnectSfx, playShutdownSfx}
}