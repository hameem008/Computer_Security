/* Find the cache line size by running `getconf -a | grep CACHE` */
const LINESIZE = 64;

function readNlines(n) {
  // Allocate a buffer of size n * LINESIZE
  const buffer = new ArrayBuffer(n * LINESIZE);
  const view = new Uint8Array(buffer);

  // Array to store timing measurements for 10 iterations
  const times = [];

  // Perform 10 iterations
  for (let iter = 0; iter < 10; iter++) {
    const start = performance.now();

    // Read the buffer at intervals of LINESIZE
    for (let i = 0; i < n * LINESIZE; i += LINESIZE) {
      const v = view[i]; // Read a byte to access the cache line
    }

    const end = performance.now();
    times.push(end - start);
  }

  // Sort times to find the median
  times.sort((a, b) => a - b);

  // Return the median time in milliseconds
  return times[Math.floor(times.length / 2)];
}

self.addEventListener("message", function (e) {
  if (e.data === "start") {
    const results = {};

    // Test n values: 1, 10, 100, ..., 10,000,000
    const nValues = [1];
    for (let i = 1; i <= 7; i++) {
      nValues.push(Math.pow(10, i));
    }

    for (const n of nValues) {
      try {
        results[n] = readNlines(n);
      } catch (error) {
        console.error(`Failed for n=${n}: ${error.message}`);
        break; // Stop if the function fails (e.g., due to memory limits)
      }
    }

    self.postMessage(results);
  }
});