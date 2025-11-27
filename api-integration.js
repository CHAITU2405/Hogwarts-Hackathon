// API Integration Script for Hogwarts Hackathon
// Include this script in your HTML files to connect frontend to backend

// Dynamically determine API base URL based on current host
// This works for localhost, port forwarding, dev tunnels, and deployed environments
function getApiBaseUrl() {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    const port = window.location.port;
    const fullHost = window.location.host; // includes port if present
    
    // Check if we're on localhost
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        // For localhost, Flask serves both frontend and backend on same port
        // Use same origin if port is specified, otherwise default to 5000
        if (port && port !== '5000') {
            // Frontend is on a different port, assume backend is on 5000
        return `http://localhost:5000/api`;
        }
        // Same origin - Flask serves both
        return `${protocol}//${hostname}${port ? ':' + port : ':5000'}/api`;
    }
    
    // Check if using dev tunnels (devtunnels.ms domain)
    // Flask serves both frontend and backend through the same tunnel
    if (hostname.includes('devtunnels.ms')) {
        // Always use same origin for dev tunnels (Flask serves both frontend and API)
        // This avoids mixed content and CORS issues
            return `${protocol}//${hostname}${port ? ':' + port : ''}/api`;
    }
    
    // For port forwarding: Flask serves both frontend and backend on the same port
    // Use same origin (same protocol, hostname, and port)
    // This is the most common case for forwarded ports
    if (port) {
        // Port is specified - Flask serves both on this port
        return `${protocol}//${hostname}:${port}/api`;
    }
    
    // Fallback: no port specified, assume Flask is on port 5000
    // Try to use same protocol as frontend
    return `${protocol}//${hostname}:5000/api`;
}

const API_BASE_URL = getApiBaseUrl();

// Registration form integration
function setupRegistrationForm() {
    const form = document.getElementById('registrationForm');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Collect form data
        const teamName = document.getElementById('teamNameInput').value.trim();
        const house = document.getElementById('houseInput').value;
        const teamSize = parseInt(document.getElementById('teamSizeInput').value);
        
        // Validate
        if (!teamName || !house || !teamSize) {
            alert('Please fill in all required fields');
            return;
        }
        
        // Collect member data
        const members = [];
        const memberBlocks = document.querySelectorAll('.member-block');
        
        if (memberBlocks.length !== teamSize) {
            alert('Please ensure all member fields are filled');
            return;
        }
        
        memberBlocks.forEach((block, index) => {
            const inputs = block.querySelectorAll('.magic-input');
            if (inputs.length >= 4) {
                members.push({
                    name: inputs[0].value.trim(),
                    email: inputs[1].value.trim(),
                    phone: inputs[2].value.trim(),
                    college: inputs[3].value.trim()
                });
            }
        });
        
        // Validate members
        for (let i = 0; i < members.length; i++) {
            if (!members[i].name || !members[i].email || !members[i].phone || !members[i].college) {
                alert(`Please fill in all fields including college name for member ${i + 1}`);
                return;
            }
        }
        
        // Get UTR/Transaction ID
        let utrTransactionId = '';
        // Find UTR input by looking for label with "UTR" text
        const labels = document.querySelectorAll('.magic-label');
        for (let label of labels) {
            if (label.textContent.toLowerCase().includes('utr') || 
                label.textContent.toLowerCase().includes('transaction')) {
                const formGroup = label.closest('.form-group');
                if (formGroup) {
                    const input = formGroup.querySelector('.magic-input');
                    if (input && input.type === 'text') {
                        utrTransactionId = input.value.trim();
                        break;
                    }
                }
            }
        }
        
        // Fallback: find by placeholder
        if (!utrTransactionId) {
            const allInputs = Array.from(document.querySelectorAll('input[type="text"]'));
            const utrInput = allInputs.find(inp => 
                inp.placeholder && inp.placeholder.toLowerCase().includes('upi')
            );
            if (utrInput) {
                utrTransactionId = utrInput.value.trim();
            }
        }
        
        if (!utrTransactionId) {
            alert('Please enter UTR/Transaction ID');
            return;
        }
        
        // Check terms and conditions checkbox
        const termsCheckbox = document.getElementById('termsCheckbox');
        if (!termsCheckbox || !termsCheckbox.checked) {
            alert('Please accept the Terms and Conditions to proceed');
            return;
        }
        
        // Get payment proof file
        const paymentProofInput = document.getElementById('paymentProof');
        const paymentProofFile = paymentProofInput ? paymentProofInput.files[0] : null;
        
        // Create FormData
        const formData = new FormData();
        formData.append('team_name', teamName);
        formData.append('house', house);
        formData.append('team_size', teamSize);
        formData.append('utr_transaction_id', utrTransactionId);
        
        if (paymentProofFile) {
            formData.append('payment_proof', paymentProofFile);
        }
        
        // Add member data (including college name for each member)
        members.forEach((member, index) => {
            formData.append(`member_${index + 1}_name`, member.name);
            formData.append(`member_${index + 1}_email`, member.email);
            formData.append(`member_${index + 1}_phone`, member.phone);
            formData.append(`member_${index + 1}_college`, member.college);
        });
        
        // Show loading
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Registering...';
        
        try {
            const apiUrl = `${getApiBaseUrl()}/register`;
            console.log('Registering team via:', apiUrl); // Debug log
            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData
            });
            
            // Parse response - only show ticket if we get confirmed success from server
            let data;
            
            try {
                const text = await response.text();
                if (!text) {
                    throw new Error('Empty response from server');
                }
                data = JSON.parse(text);
            } catch (parseError) {
                console.error('JSON parse error:', parseError);
                // Don't assume success on parsing errors - require explicit confirmation
                alert('Server response error. Please try again or contact support if the problem persists.');
                return;
            }
            
            // Only show ticket if we have explicit success confirmation from server
            // Status must be 201 (Created) AND data.success must be true
            if (response.status === 201 && data.success === true) {
                // Data is confirmed stored in database - show success ticket
                const ticketOverlay = document.getElementById('ticket-overlay');
                const ticketTeamName = document.getElementById('ticketTeamName');
                const finalTicket = document.getElementById('finalTicket');
                const ticketHouseLogo = document.getElementById('ticketHouseLogo');
                
                if (ticketOverlay && ticketTeamName) {
                    ticketTeamName.textContent = teamName;
                    finalTicket.className = 'hogwarts-ticket';
                    finalTicket.classList.add(house);
                    // Ensure logo path includes assets/ and handle case sensitivity
                    const houseLower = house.toLowerCase();
                    ticketHouseLogo.src = `assets/${houseLower}.png`;
                    ticketHouseLogo.alt = `${house} Logo`;
                    ticketOverlay.style.display = 'flex';
                }
                
                // Reset form
                form.reset();
            } else {
                // Show error message - registration failed
                const errorMsg = data.error || data.message || 'Registration failed. Please try again.';
                alert(errorMsg);
            }
        } catch (error) {
            console.error('Registration error:', error);
            console.error('Error details:', {
                message: error.message,
                stack: error.stack,
                name: error.name
            });
            
            // Check if it's a network error
            if (error.message && (error.message.includes('Failed to fetch') || error.message.includes('NetworkError'))) {
                alert('Network error. Please check your connection and try again.');
            } else {
                alert('An error occurred: ' + (error.message || 'Unknown error'));
            }
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    });
}

// Teams page integration
async function loadTeamsFromAPI() {
    const teamGrid = document.getElementById('teamGrid');
    if (!teamGrid) return;
    
    try {
        // Get filter values
        const houseFilter = document.getElementById('houseFilter')?.value || '';
        const searchTerm = document.getElementById('teamSearch')?.value || '';
        
        // Build query string
        const params = new URLSearchParams();
        if (houseFilter) params.append('house', houseFilter);
        if (searchTerm) params.append('search', searchTerm);
        
        // Use relative URL - this works when Flask serves both frontend and backend
        const apiUrl = `/api/teams?${params.toString()}`;
        console.log('Fetching teams from:', apiUrl); // Debug log
        console.log('Full URL will be:', window.location.origin + apiUrl); // Debug log
        console.log('Current page URL:', window.location.href); // Debug log
        
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            // Use same-origin mode when using relative URLs
            mode: 'cors',
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Response error:', response.status, errorText);
            throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Teams data received:', data); // Debug log
        
        if (data.success && data.teams) {
            renderTeamsFromAPI(data.teams);
        } else {
            throw new Error(data.error || 'Failed to load teams');
        }
    } catch (error) {
        console.error('Error loading teams:', error);
        console.error('Error details:', {
            message: error.message,
            name: error.name,
            stack: error.stack
        });
        const teamGrid = document.getElementById('teamGrid');
        if (teamGrid) {
            const apiUrl = window.location.origin + '/api/teams';
            let errorMsg = `Error loading teams: ${error.message}`;
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMsg += '<br><br><strong>Possible issues:</strong><br>';
                errorMsg += '1. Backend server is not running<br>';
                errorMsg += '2. Backend is not accessible at the API URL<br>';
                errorMsg += '3. CORS or mixed content (HTTPS/HTTP) issue<br>';
                errorMsg += '4. Firewall or network blocking the connection<br>';
            }
            errorMsg += `<br><small>API URL: ${apiUrl}</small>`;
            errorMsg += `<br><small>Current Origin: ${window.location.origin}</small>`;
            teamGrid.innerHTML = `<p style="color: #ef5350; text-align: center; grid-column: 1/-1; font-family: 'Crimson Text'; padding: 40px; line-height: 1.6;">${errorMsg}</p>`;
        }
    }
}

function renderTeamsFromAPI(teams) {
    const grid = document.getElementById('teamGrid');
    if (!grid) return;
    
    // Show message if no teams
    if (!teams || teams.length === 0) {
        grid.innerHTML = '<p style="color: #aaa; text-align: center; grid-column: 1/-1; font-family: \'Crimson Text\'; padding: 40px;">No teams have registered yet. Be the first to register!</p>';
        return;
    }
    
    const crests = {
        'Gryffindor': 'assets/gryffindor.png',
        'Slytherin': 'assets/slytherin.png',
        'Ravenclaw': 'assets/ravenclaw.png',
        'Hufflepuff': 'assets/hufflepuff.png',
        'Muggles': 'assets/muggles.png'
    };
    
    grid.innerHTML = teams.map(team => {
        const crest = crests[team.house] || '';
        const status = team.approval_status || 'pending';
        // Ensure members is an array
        const membersList = Array.isArray(team.members) ? team.members : [];
        return `
            <div class='team-card' style="--crest: url('${crest}')" 
                 data-id='${team.id}' 
                 data-name='${team.name}' 
                 data-house='${team.house}' 
                 data-members='${membersList.join('|')}' 
                 data-url='${team.projectUrl || ''}' 
                 data-college='${team.college || ''}' 
                 data-description='${team.description || ''}'
                 data-status='${status}'>
                <span class='crest-bg' aria-hidden='true'></span>
                <span class='crest-front' aria-hidden='true'></span>
                <div class='team-house'>${team.house}</div>
                <div class='team-status ${status}'>${status}</div>
                <h3 class='team-name'>${team.name}</h3>
            </div>
        `;
    }).join('');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Setup registration form if on registration page
    if (document.getElementById('registrationForm')) {
        setupRegistrationForm();
    }
    
    // Setup teams page if on teams page
    if (document.getElementById('teamGrid')) {
        loadTeamsFromAPI();
        
        // Update filters to reload from API
        const houseSelect = document.getElementById('houseFilter');
        const searchInput = document.getElementById('teamSearch');
        
        if (houseSelect) {
            houseSelect.addEventListener('change', loadTeamsFromAPI);
        }
        if (searchInput) {
            searchInput.addEventListener('input', loadTeamsFromAPI);
        }
    }
});

