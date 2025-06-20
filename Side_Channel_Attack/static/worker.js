/* Find the cache line size by running `getconf -a | grep CACHE` */
const LINESIZE = 64;
/* Find the L3 size by running `getconf -a | grep CACHE` */
const LLCSIZE = 8 * 1024 * 1024;
/* Collect traces for 10 seconds; you can vary this */
const TIME = 10000;
/* Collect traces every 10ms; you can vary this */
const P = 10; 

function sweep(P) {
    // Allocate a buffer of size LLCSIZE
    const buffer = new ArrayBuffer(LLCSIZE);
    const view = new Uint8Array(buffer);

    // Calculate number of measurements
    const K = TIME / P;
    const counts = new Array(K).fill(0);

    // Perform sweeps for TIME milliseconds
    for (let i = 0; i < K; i++) {
        const start = performance.now();
        let sweepCount = 0;

        // Sweep until P milliseconds have passed
        while (performance.now() - start < P) {
            for (let j = 0; j < LLCSIZE; j += LINESIZE) {
                view[j] = 0; // Access cache line
            }
            sweepCount++;
        }
        counts[i] = sweepCount;
    }

    return counts;
}

self.addEventListener('message', function(e) {
    if (e.data === "start") {
        const result = sweep(P);
        self.postMessage(result);
    }
});