document.addEventListener('DOMContentLoaded', () => {
    const btnLive = document.getElementById('btn-live');
    const btnUploadProxy = document.getElementById('btn-upload-proxy');
    const videoUpload = document.getElementById('video-upload');
    const exerciseType = document.getElementById('exercise-type');
    
    const videoSection = document.getElementById('video-section');
    const videoFeed = document.getElementById('video-feed');
    const videoLoader = document.getElementById('video-loader');
    const btnClose = document.getElementById('btn-close');
    const videoTitle = document.getElementById('video-title');

    // Handle Live Camera Button
    btnLive.addEventListener('click', () => {
        const exercise = exerciseType.value;
        startVideoSession(`Live Tracking: ${formatExercise(exercise)}`, `0`, exercise);
    });

    // Handle Upload Button click proxy
    btnUploadProxy.addEventListener('click', () => {
        videoUpload.click();
    });

    // Handle File Upload
    videoUpload.addEventListener('change', async (e) => {
        if (!e.target.files.length) return;
        
        const file = e.target.files[0];
        const exercise = exerciseType.value;
        const formData = new FormData();
        formData.append('file', file);

        // Show uploading state
        btnUploadProxy.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><span>Uploading...</span>';
        btnUploadProxy.disabled = true;

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (response.ok) {
                startVideoSession(`Video Tracking: ${formatExercise(exercise)}`, data.filename, exercise);
            } else {
                alert('Upload failed: ' + data.error);
            }
        } catch (err) {
            alert('An error occurred during upload.');
            console.error(err);
        } finally {
            // Reset button
            btnUploadProxy.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i><span>Upload Video</span>';
            btnUploadProxy.disabled = false;
            videoUpload.value = ''; // Reset file input
        }
    });

    // Handle Close Session
    btnClose.addEventListener('click', () => {
        stopVideoSession();
    });

    function startVideoSession(title, source, exercise) {
        // Update UI
        videoTitle.textContent = title;
        videoSection.classList.remove('hidden');
        
        // Setup Video Feed
        videoFeed.style.display = 'none';
        videoLoader.style.display = 'flex';
        
        // Cache busting and query params
        const url = `/video_feed?source=${encodeURIComponent(source)}&exercise=${encodeURIComponent(exercise)}&t=${new Date().getTime()}`;
        
        videoFeed.onload = () => {
            videoLoader.style.display = 'none';
            videoFeed.style.display = 'block';
        };
        
        videoFeed.onerror = () => {
            videoLoader.innerHTML = '<p style="color: #ef4444;"><i class="fa-solid fa-triangle-exclamation"></i> Error loading video stream.</p>';
        };

        videoFeed.src = url;
        
        // Smooth scroll to video section
        setTimeout(() => {
            videoSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    }

    function stopVideoSession() {
        videoFeed.src = ''; // Stop the stream
        videoSection.classList.add('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function formatExercise(val) {
        return val.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }
});
