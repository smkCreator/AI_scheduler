/**
 * demo-utils.js
 * Handles demo data initialization and utility functions
 */

class DemoUtils {
    constructor(apiService, userManagement, availabilityManagement, interviewScheduling) {
        this.apiService = apiService;
        this.userManagement = userManagement;
        this.availabilityManagement = availabilityManagement;
        this.interviewScheduling = interviewScheduling;
    }

    init() {
        // Initialize demo data button
        document.getElementById('init-demo-btn').addEventListener('click', this.initializeDemoData.bind(this));
    }

    async initializeDemoData() {
        try {
            // Show loading state
            const demoBtn = document.getElementById('init-demo-btn');
            const originalText = demoBtn.textContent;
            demoBtn.textContent = 'Initializing...';
            demoBtn.disabled = true;
            
            const demoMessage = document.querySelector('.demo-message');
            demoMessage.textContent = 'Creating demo users and availability data...';
            
            // Call API to initialize demo data
            const result = await this.apiService.initializeDemoData();
            
            // Reset button state
            demoBtn.textContent = originalText;
            demoBtn.disabled = false;
            
            // Display success message
            demoMessage.textContent = `Demo data initialized! Created ${result.users.length} users and ${result.availabilities.length} availability slots.`;
            
            // Refresh all data
            await this.userManagement.loadUserData();
            
            // If a user is selected in the availability view, refresh their availability
            const viewUserSelect = document.getElementById('view-user-select');
            if (viewUserSelect.value) {
                const event = new Event('change');
                viewUserSelect.dispatchEvent(event);
            }
            
            // If a user is selected in the interviews view, refresh their interviews
            const interviewUserSelect = document.getElementById('interview-user-select');
            if (interviewUserSelect.value) {
                const event = new Event('change');
                interviewUserSelect.dispatchEvent(event);
            }
            
            this.showSuccess('Demo data initialized successfully!');
        } catch (error) {
            console.error('Failed to initialize demo data:', error);
            
            // Reset button state
            const demoBtn = document.getElementById('init-demo-btn');
            demoBtn.textContent = 'Initialize Demo Data';
            demoBtn.disabled = false;
            
            // Display error message
            document.querySelector('.demo-message').textContent = 'Failed to initialize demo data. Please try again.';
            
            this.showError('Failed to initialize demo data. Please try again.');
        }
    }

    showSuccess(message) {
        // Simple success message implementation
        alert(message);
    }

    showError(message) {
        // Simple error message implementation
        alert(message);
    }
}