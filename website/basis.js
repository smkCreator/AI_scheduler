/**
 * basis.js
 * Main application file that initializes all components
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize services
    const apiService = new ApiService('http://0.0.0.0:8000');
    
    // Initialize components
    const userManagement = new UserManagement(apiService);
    const availabilityManagement = new AvailabilityManagement(apiService);
    const interviewScheduling = new InterviewScheduling(apiService);
    const demoUtils = new DemoUtils(apiService, userManagement, availabilityManagement, interviewScheduling);
    
    // Initialize all components
    userManagement.init();
    availabilityManagement.init();
    interviewScheduling.init();
    demoUtils.init();
    
    // Add some basic UI helpers
    addUiHelpers();
    
    // Ensure layout adapts to the available space
    optimizeLayout();
    
    // Add window resize listener to maintain optimal layout
    window.addEventListener('resize', optimizeLayout);
});

function optimizeLayout() {
    // Adjust height of main sections to fill available space
    const windowHeight = window.innerHeight;
    const headerHeight = document.querySelector('header').offsetHeight;
    const footerHeight = document.querySelector('footer').offsetHeight;
    
    // Calculate available content height
    const availableHeight = windowHeight - headerHeight - footerHeight;
    
    // Set minimum height for main content
    document.querySelector('main').style.minHeight = `${availableHeight}px`;
    
    // Ensure tables use full width
    document.querySelectorAll('table').forEach(table => {
        table.style.width = '100%';
    });
    
    // Ensure form inputs use full width
    document.querySelectorAll('input, select, textarea').forEach(input => {
        input.style.width = '100%';
    });
    
    // Add proper spacing between sections on mobile
    if (window.innerWidth < 768) {
        document.querySelectorAll('section').forEach(section => {
            section.style.marginBottom = '2rem';
        });
    }
}

function addUiHelpers() {
    // Common function to show alerts
    window.showAlert = function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        
        // Add to the document
        document.body.appendChild(alertDiv);
        
        // Remove after 5 seconds
        setTimeout(() => {
            alertDiv.classList.add('fade-out');
            setTimeout(() => {
                alertDiv.remove();
            }, 500);
        }, 5000);
    };
    
    // Override the default alert functions to use our custom alerts
    window.originalAlert = window.alert;
    window.alert = function(message) {
        showAlert(message);
    };
    
    // Handle form submissions to prevent default behavior
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', e => {
            e.preventDefault();
        });
    });
    
    // Make sure all cards take full width
    document.querySelectorAll('.card').forEach(card => {
        card.style.width = '100%';
    });
    
    // Improve the mobile experience
    if (!document.querySelector('meta[name="viewport"]')) {
        const meta = document.createElement('meta');
        meta.name = 'viewport';
        meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
        document.head.appendChild(meta);
    }
}