'use strict';
// SESSIE 77 - B0: bewust minimaal. De UI draait als gewone web-app over
// http://127.0.0.1:<poort> en heeft in dit prototype geen Node-bridge nodig.
// contextIsolation staat aan en nodeIntegration uit (veilige defaults).
// Latere fasen (B1+) kunnen hier desgewenst een smalle, expliciete API exposen
// via contextBridge; voor B0 laten we het leeg zodat het aanvalsoppervlak nul is.
