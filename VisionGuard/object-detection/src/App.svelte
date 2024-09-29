<script>
  let videoElement;
  let detectionLabels = [];
  let errorMessage = null;
  let stream;
  let videoWidth = 640;
  let videoHeight = 480;
  let lastDetectionTime = 0;
  const detectionInterval = 1000; // Detect objects once every 1000ms (1 second)

  // Initialize video stream from user's webcam
  const startVideo = async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoElement.srcObject = stream;
      videoElement.play();
      videoElement.onloadedmetadata = () => {
        videoWidth = videoElement.videoWidth;
        videoHeight = videoElement.videoHeight;
      };
    } catch (error) {
      errorMessage = `Error accessing webcam: ${error.message}`;
      console.error(errorMessage);
    }
  };

  // Capture a frame from the video and send it to the backend
  const captureFrame = async () => {
    const canvas = document.createElement('canvas');
    canvas.width = videoWidth;
    canvas.height = videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

    // Convert the canvas to a Blob (image format)
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));

    const formData = new FormData();
    formData.append("image", blob, "frame.jpg");

    try {
      // Send the POST request with the video frame to Django backend
      const response = await fetch('http://localhost:8000/api/upload/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Unknown error occurred.");
      }

      const data = await response.json();
      detectionLabels = data.labels; // Process the labels received from the backend
    } catch (error) {
      errorMessage = `Error processing frame: ${error.message}`;
      console.error(errorMessage);
    }
  };

  // Continuously capture frames and perform detection at a controlled interval
  const detectInVideo = () => {
    const now = Date.now();
    if (now - lastDetectionTime > detectionInterval) {
      captureFrame();
      lastDetectionTime = now;
    }
    // Use requestAnimationFrame for smoother rendering
    requestAnimationFrame(detectInVideo);
  };

  // Draw bounding boxes and labels on the video frame
  const drawLabelsOnCanvas = (canvas, labels) => {
    const context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

    // Draw the labels as text on top of the video
    labels.forEach((label, index) => {
      context.font = '18px Arial';
      context.fillStyle = 'red';
      context.fillText(label, 10, 20 * (index + 1)); // Adjust position for each label
    });
  };

  // Start capturing frames and running detection
  const startDetection = () => {
    detectInVideo(); // Begin frame capture and detection loop
  };

  $: if (videoElement && detectionLabels.length) {
    const canvas = document.getElementById('overlay');
    drawLabelsOnCanvas(canvas, detectionLabels);
  }
</script>

<main>
  <h1>Real-time Object Detection</h1>

  <button on:click={startVideo}>Start Video</button>
  <button on:click={startDetection}>Start Detection</button>

  <!-- Video stream with canvas overlay for labels -->
  <div style="position: relative; display: inline-block;">
    <video bind:this={videoElement} autoplay></video>
    <canvas id="overlay" width={videoWidth} height={videoHeight} style="position: absolute; top: 0; left: 0;"></canvas>
  </div>

  {#if errorMessage}
    <p style="color: red;">{errorMessage}</p>
  {/if}

  <!-- Display detected labels -->
  {#if detectionLabels.length}
    <h2>Detected Objects:</h2>
    <ul>
      {#each detectionLabels as label}
        <li>{label}</li>
      {/each}
    </ul>
  {/if}
</main>

<style>
  video {
    width: 640px;
    height: 480px;
    border: 1px solid #ccc;
    display: block;
    margin-top: 10px;
  }

  button {
    margin-top: 10px;
    margin-right: 10px;
  }

  ul {
    list-style-type: none;
    padding: 0;
  }

  li {
    background-color: #e0e0e0;
    margin: 5px 0;
    padding: 10px;
    border-radius: 5px;
  }

  canvas {
    pointer-events: none; /* Allow interaction with the video behind the canvas */
  }
</style>
