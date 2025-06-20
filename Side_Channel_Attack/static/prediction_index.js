function app() {
  return {
    /* This is the main app object containing all the application state and methods. */
    // The following properties are used to store the state of the application

    // results of cache latency measurements
    latencyResults: null,
    // local collection of trace data
    traceData: [],
    // Local collection of heatmap images
    heatmaps: [],
    // Prediction results
    predictions: [],

    // Current status message
    status: "",
    // Is any worker running?
    isCollecting: false,
    // Is the status message an error?
    statusIsError: false,
    // Show trace data in the UI?
    showingTraces: false,

    // Collect latency data using warmup.js worker
    async collectLatencyData() {
      this.isCollecting = true;
      this.status = "Collecting latency data...";
      this.latencyResults = null;
      this.statusIsError = false;
      this.showingTraces = false;

      try {
        // Create a worker
        let worker = new Worker("warmup.js");

        // Start the measurement and wait for result
        const results = await new Promise((resolve) => {
          worker.onmessage = (e) => resolve(e.data);
          worker.postMessage("start");
        });

        // Update results
        this.latencyResults = results;
        this.status = "Latency data collection complete!";

        // Terminate worker
        worker.terminate();
      } catch (error) {
        console.error("Error collecting latency data:", error);
        this.status = `Error: ${error.message}`;
        this.statusIsError = true;
      } finally {
        this.isCollecting = false;
      }
    },

    // Collect trace data using worker.js and send to backend
    async collectTraceData() {
      this.isCollecting = true;
      this.status = "Collecting trace data...";
      this.statusIsError = false;
      this.showingTraces = true;

      try {
        // Create a worker
        let worker = new Worker("worker.js");

        // Start the sweep and wait for result
        const trace = await new Promise((resolve) => {
          worker.onmessage = (e) => resolve(e.data);
          worker.postMessage("start");
        });

        // Send trace data to backend
        const response = await fetch('/collect_trace', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ trace })
        });

        if (response.ok) {
          const data = await response.json();
          this.traceData.push(trace);
          this.heatmaps.push({ 
            src: data.heatmap,
            prediction: data.prediction
          });
          this.status = `Trace collected! Predicted website: ${data.prediction.website} (${data.prediction.confidence.toFixed(1)}% confidence)`;
        } else {
          throw new Error("Failed to send trace to backend");
        }

        // Terminate worker
        worker.terminate();
      } catch (error) {
        console.error("Error collecting trace data:", error);
        this.status = `Error: ${error.message}`;
        this.statusIsError = true;
      } finally {
        this.isCollecting = false;
      }
    },

    // Download the trace data as JSON (array of arrays format for ML)
    async downloadTraces() {
      this.isCollecting = true;
      this.status = "Downloading traces...";
      this.statusIsError = false;

      try {
        const response = await fetch('/api/get_results');
        if (response.ok) {
          const data = await response.json();
          const traces = data.traces || [];
          const blob = new Blob([JSON.stringify(traces)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'traces.json';
          a.click();
          URL.revokeObjectURL(url);
          this.status = "Traces downloaded successfully!";
        } else {
          throw new Error("Failed to fetch traces from backend");
        }
      } catch (error) {
        console.error("Error downloading traces:", error);
        this.status = `Error: ${error.message}`;
        this.statusIsError = true;
      } finally {
        this.isCollecting = false;
      }
    },

    // Clear all results from the server
    async clearResults() {
      this.isCollecting = true;
      this.status = "Clearing results...";
      this.statusIsError = false;

      try {
        const response = await fetch('/api/clear_results', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
          this.traceData = [];
          this.heatmaps = [];
          this.latencyResults = null;
          this.showingTraces = false;
          this.status = "Results cleared successfully!";
        } else {
          throw new Error("Failed to clear results");
        }
      } catch (error) {
        console.error("Error clearing results:", error);
        this.status = `Error: ${error.message}`;
        this.statusIsError = true;
      } finally {
        this.isCollecting = false;
      }
    },
  };
}