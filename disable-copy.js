// Disable Text Copying
(function() {
    'use strict';
    
    // Prevent text selection
    document.addEventListener('selectstart', function(e) {
        e.preventDefault();
        return false;
    });
    
    // Prevent context menu (right-click)
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        return false;
    });
    
    // Prevent copy, cut, and paste
    document.addEventListener('copy', function(e) {
        e.preventDefault();
        return false;
    });
    
    document.addEventListener('cut', function(e) {
        e.preventDefault();
        return false;
    });
    
    document.addEventListener('paste', function(e) {
        e.preventDefault();
        return false;
    });
    
    // Prevent keyboard shortcuts (Ctrl+C, Ctrl+A, Ctrl+X, Ctrl+V, etc.)
    document.addEventListener('keydown', function(e) {
        // Disable Ctrl+C, Ctrl+A, Ctrl+X, Ctrl+V, Ctrl+S, F12
        if (e.ctrlKey && (e.key === 'c' || e.key === 'C' || 
                          e.key === 'x' || e.key === 'X' || 
                          e.key === 'v' || e.key === 'V' || 
                          e.key === 'a' || e.key === 'A' ||
                          e.key === 's' || e.key === 'S')) {
            e.preventDefault();
            return false;
        }
        // Disable F12 (Developer Tools)
        if (e.key === 'F12') {
            e.preventDefault();
            return false;
        }
    });
})();

