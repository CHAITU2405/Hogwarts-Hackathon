// Loading Screen - Wait for assets to load
(function() {
    'use strict';
    
    // Create loading screen HTML
    const loadingHTML = `
        <div id="loadingScreen" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at center, #1f1f35 0%, #000000 100%);
            z-index: 99999;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            transition: opacity 0.5s ease, visibility 0.5s ease;
        ">
            <div style="
                text-align: center;
                color: #d4af37;
                font-family: 'Cinzel Decorative', serif;
            ">
                <h1 style="
                    font-size: 3rem;
                    font-weight: 900;
                    margin-bottom: 20px;
                    text-shadow: 0 0 20px rgba(212, 175, 55, 0.5);
                    animation: pulse 2s ease-in-out infinite;
                ">Hogwarts Hackathon</h1>
                <div style="
                    width: 50px;
                    height: 50px;
                    border: 4px solid rgba(212, 175, 55, 0.3);
                    border-top-color: #d4af37;
                    border-radius: 50%;
                    margin: 20px auto;
                    animation: spin 1s linear infinite;
                "></div>
                <p style="
                    font-size: 1.2rem;
                    margin-top: 20px;
                    opacity: 0.8;
                ">Loading magical assets...</p>
            </div>
        </div>
        <style>
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            #loadingScreen.hidden {
                opacity: 0;
                visibility: hidden;
            }
        </style>
    `;
    
    // Insert loading screen at the start of body
    document.addEventListener('DOMContentLoaded', function() {
        document.body.insertAdjacentHTML('afterbegin', loadingHTML);
        
        const loadingScreen = document.getElementById('loadingScreen');
        let assetsLoaded = false;
        let audioReady = false;
        let imagesLoaded = false;
        let fontsLoaded = false;
        
        // Check if all images are loaded
        function checkImages() {
            const images = document.querySelectorAll('img');
            if (images.length === 0) {
                imagesLoaded = true;
                return;
            }
            
            let loadedCount = 0;
            let totalImages = images.length;
            
            images.forEach(img => {
                if (img.complete) {
                    loadedCount++;
                } else {
                    img.addEventListener('load', function() {
                        loadedCount++;
                        if (loadedCount === totalImages) {
                            imagesLoaded = true;
                            checkAllAssets();
                        }
                    });
                    img.addEventListener('error', function() {
                        loadedCount++;
                        if (loadedCount === totalImages) {
                            imagesLoaded = true;
                            checkAllAssets();
                        }
                    });
                }
            });
            
            if (loadedCount === totalImages) {
                imagesLoaded = true;
            }
        }
        
        // Check if fonts are loaded
        function checkFonts() {
            if (document.fonts && document.fonts.ready) {
                document.fonts.ready.then(function() {
                    fontsLoaded = true;
                    checkAllAssets();
                });
            } else {
                // Fallback: wait a bit for fonts
                setTimeout(function() {
                    fontsLoaded = true;
                    checkAllAssets();
                }, 1000);
            }
        }
        
        // Listen for audio ready event
        window.addEventListener('audioReady', function() {
            audioReady = true;
            checkAllAssets();
        });
        
        // Check if all assets are loaded
        function checkAllAssets() {
            if (imagesLoaded && fontsLoaded && audioReady) {
                assetsLoaded = true;
                // Small delay for smooth transition
                setTimeout(function() {
                    if (loadingScreen) {
                        loadingScreen.classList.add('hidden');
                        // Trigger event that audio can listen to
                        window.dispatchEvent(new CustomEvent('loadingScreenHidden'));
                        setTimeout(function() {
                            if (loadingScreen && loadingScreen.parentNode) {
                                loadingScreen.parentNode.removeChild(loadingScreen);
                            }
                        }, 500);
                    }
                }, 300);
            }
        }
        
        // Add click handler to loading screen to enable autoplay
        // This allows audio to play when user interacts with the page
        if (loadingScreen) {
            const triggerInteraction = function() {
                // User interaction - this enables autoplay
                window.dispatchEvent(new CustomEvent('userInteraction'));
            };
            loadingScreen.addEventListener('click', triggerInteraction);
            loadingScreen.addEventListener('touchstart', triggerInteraction);
            // Also trigger on any key press
            document.addEventListener('keydown', triggerInteraction, { once: true });
        }
        
        // Start checking assets
        checkImages();
        checkFonts();
        
        // Fallback: hide loading screen after max 5 seconds
        setTimeout(function() {
            if (!assetsLoaded && loadingScreen) {
                assetsLoaded = true;
                loadingScreen.classList.add('hidden');
                // Trigger event that audio can listen to
                window.dispatchEvent(new CustomEvent('loadingScreenHidden'));
                setTimeout(function() {
                    if (loadingScreen && loadingScreen.parentNode) {
                        loadingScreen.parentNode.removeChild(loadingScreen);
                    }
                }, 500);
            }
        }, 5000);
    });
})();

