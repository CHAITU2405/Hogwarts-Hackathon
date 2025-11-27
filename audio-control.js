// Background Music Control
(function() {
    'use strict';
    
    // Create audio element and preload
    const bgMusic = new Audio('assets/Harry bg.wav');
    bgMusic.loop = true;
    bgMusic.volume = 0.5; // Set volume to 50%
    bgMusic.preload = 'auto'; // Preload the audio
    
    // Check if user has previously enabled music (default is OFF)
    const musicEnabled = localStorage.getItem('bgMusicEnabled') === 'true';
    let isPlaying = musicEnabled; // OFF by default, user must enable it
    let audioReady = false;
    let hasUserInteracted = false;
    
    // Function to attempt playing audio
    function attemptPlay() {
        if (isPlaying && audioReady) {
            const playPromise = bgMusic.play();
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    // Successfully started playing
                    console.log('Audio started playing');
                }).catch(err => {
                    console.log('Auto-play prevented:', err);
                    // If autoplay is blocked, wait for user interaction
                    if (!hasUserInteracted) {
                        // Will be handled by user interaction listeners
                    }
                });
            }
        }
    }
    
    // Function to enable autoplay after user interaction
    function enableAutoplay() {
        hasUserInteracted = true;
        if (isPlaying && audioReady && bgMusic.paused) {
            bgMusic.play().catch(e => console.log('Play failed:', e));
        }
    }
    
    // Wait for audio to be ready before playing
    bgMusic.addEventListener('canplaythrough', function() {
        if (!audioReady) {
            audioReady = true;
            // Signal that audio is ready
            window.dispatchEvent(new CustomEvent('audioReady'));
            // Try to play immediately
            attemptPlay();
        }
    });
    
    // Also handle loadeddata event as fallback
    bgMusic.addEventListener('loadeddata', function() {
        if (!audioReady) {
            audioReady = true;
            window.dispatchEvent(new CustomEvent('audioReady'));
            // Try to play immediately
            attemptPlay();
        }
    });
    
    // Handle audio loading errors
    bgMusic.addEventListener('error', function(e) {
        console.error('Audio loading error:', e);
        console.error('Audio file path:', bgMusic.src);
        // Try alternative path if first one fails
        if (bgMusic.src.includes('harry bg.wav')) {
            bgMusic.src = 'assets/Harry bg.wav';
            bgMusic.load();
        }
    });
    
    // Listen for loading screen hide event to trigger play
    window.addEventListener('loadingScreenHidden', function() {
        // Small delay to ensure everything is ready
        setTimeout(function() {
            if (isPlaying && audioReady) {
                bgMusic.play().catch(err => {
                    console.log('Play after loading screen failed:', err);
                });
            }
        }, 300);
    });
    
    // Listen for user interaction to enable autoplay
    window.addEventListener('userInteraction', function() {
        enableAutoplay();
    });
    
    // Try to play on any user interaction (click, touch, etc.)
    const playOnInteraction = function() {
        enableAutoplay();
    };
    
    document.addEventListener('click', playOnInteraction, { once: true });
    document.addEventListener('touchstart', playOnInteraction, { once: true });
    document.addEventListener('keydown', playOnInteraction, { once: true });
    
    // Also try playing when page becomes visible
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden && isPlaying && audioReady && bgMusic.paused) {
            attemptPlay();
        }
    });
    
    // Start loading the audio immediately
    bgMusic.load();
    
    // Force play attempt after a short delay once audio is ready
    // This ensures it plays even if other events don't fire
    setTimeout(function() {
        if (isPlaying && audioReady && bgMusic.paused) {
            bgMusic.play().catch(err => {
                console.log('Delayed play attempt failed:', err);
            });
        }
    }, 1000);
    
    // Function to toggle music
    function toggleMusic() {
        const volumeBtn = document.getElementById('volumeControl');
        if (!volumeBtn) return;
        
        if (isPlaying) {
            bgMusic.pause();
            isPlaying = false;
            volumeBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
            volumeBtn.classList.remove('volume-on');
            volumeBtn.classList.add('volume-off');
            // Save that user disabled music
            localStorage.setItem('bgMusicEnabled', 'false');
        } else {
            // Ensure audio is ready before playing
            if (!audioReady) {
                // Wait for audio to be ready
                bgMusic.addEventListener('canplaythrough', function playWhenReady() {
                    bgMusic.removeEventListener('canplaythrough', playWhenReady);
                    bgMusic.play().catch(err => {
                        console.log('Play failed:', err);
                    });
                }, { once: true });
                bgMusic.load();
            } else {
                bgMusic.play().catch(err => {
                    console.log('Play failed:', err);
                });
            }
            isPlaying = true;
            volumeBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
            volumeBtn.classList.remove('volume-off');
            volumeBtn.classList.add('volume-on');
            // Save that music is enabled
            localStorage.setItem('bgMusicEnabled', 'true');
        }
    }
    
    // Initialize button state on page load
    document.addEventListener('DOMContentLoaded', function() {
        const volumeBtn = document.getElementById('volumeControl');
        if (volumeBtn) {
            // Set initial icon - always OFF by default
            volumeBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
            volumeBtn.classList.add('volume-off');
            volumeBtn.classList.remove('volume-on');
            
            // Add click event
            volumeBtn.addEventListener('click', toggleMusic);
        }
    });
    
    // Handle page visibility change (pause when tab is hidden)
    document.addEventListener('visibilitychange', function() {
        if (document.hidden && isPlaying) {
            bgMusic.pause();
        } else if (!document.hidden && isPlaying) {
            bgMusic.play().catch(err => {
                console.log('Resume play failed:', err);
            });
        }
    });
})();

