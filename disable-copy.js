// Disable Text Copying
(function() {
    'use strict';
    
    // Prevent text selection
    document.addEventListener('selectstart', function(e) {
        e.preventDefault();
        return false;
    });
    
    // Allow context menu (right-click) - removed blocking to allow inspect
    // document.addEventListener('contextmenu', function(e) {
    //     e.preventDefault();
    //     return false;
    // });
    
    // Prevent copy and cut
    document.addEventListener('copy', function(e) {
        e.preventDefault();
        return false;
    });
    
    document.addEventListener('cut', function(e) {
        e.preventDefault();
        return false;
    });
    
    // Allow paste - but only in input fields, textareas, and contenteditable elements
    document.addEventListener('paste', function(e) {
        const target = e.target;
        // Allow paste in input fields, textareas, and contenteditable elements
        if (target.tagName === 'INPUT' || 
            target.tagName === 'TEXTAREA' || 
            target.isContentEditable) {
            // Allow paste in form fields
            return true;
        }
        // Prevent paste elsewhere
        e.preventDefault();
        return false;
    });
    
    // Prevent keyboard shortcuts (Ctrl+C, Ctrl+A, Ctrl+X, Ctrl+S)
    // Allow Ctrl+V (paste) in input fields and textareas
    // Allow Developer Tools shortcuts (F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+Shift+C)
    document.addEventListener('keydown', function(e) {
        const target = e.target;
        const isFormField = target.tagName === 'INPUT' || 
                          target.tagName === 'TEXTAREA' || 
                          target.isContentEditable;
        
        // Allow Developer Tools shortcuts
        if (e.key === 'F12' || 
            (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'i' || 
                                          e.key === 'J' || e.key === 'j' || 
                                          e.key === 'C' || e.key === 'c'))) {
            return true; // Allow developer tools
        }
        
        // Allow Ctrl+V (paste) in form fields
        if (e.ctrlKey && (e.key === 'v' || e.key === 'V') && isFormField) {
            return true; // Allow paste in form fields
        }
        
        // Disable Ctrl+C, Ctrl+A, Ctrl+X, Ctrl+S
        if (e.ctrlKey && (e.key === 'c' || e.key === 'C' || 
                          e.key === 'x' || e.key === 'X' || 
                          e.key === 'a' || e.key === 'A' ||
                          e.key === 's' || e.key === 'S')) {
            e.preventDefault();
            return false;
        }
        
        // Disable Ctrl+V outside form fields
        if (e.ctrlKey && (e.key === 'v' || e.key === 'V') && !isFormField) {
            e.preventDefault();
            return false;
        }
    });
})();

