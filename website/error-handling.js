/**
 * error-handling.js
 * Provides comprehensive error handling for the application
 */

class ErrorHandler {
    constructor() {
        this.setupGlobalErrorHandling();
    }

    setupGlobalErrorHandling() {
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled Promise Rejection:', event.reason);
            this.showErrorToast('An unexpected error occurred. Please try again.');
        });

        // Handle global errors
        window.addEventListener('error', (event) => {
            console.error('Global Error:', event.error);
            this.showErrorToast('An unexpected error occurred. Please try again.');
        });
    }

    handleApiError(error) {
        console.error('API Error:', error);
        
        if (error.message.includes('404')) {
            return 'The requested resource was not found.';
        } else if (error.message.includes('401')) {
            return 'Authentication failed. Please check your credentials.';
        } else if (error.message.includes('403')) {
            return 'You do not have permission to perform this action.';
        } else if (error.message.includes('400')) {
            return 'Invalid request. Please check your input data.';
        } else if (error.message.includes('500')) {
            return 'Server error. Please try again later.';
        } else {
            return error.message || 'An unexpected error occurred. Please try again.';
        }
    }

    showErrorToast(message) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">❌</div>
                <div class="toast-message">${message}</div>
                <button class="toast-close">×</button>
            </div>
        `;
        
        // Add to body
        document.body.appendChild(toast);
        
        // Add close event
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.classList.add('toast-fade-out');
            setTimeout(() => {
                toast.remove();
            }, 300);
        });
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (document.body.contains(toast)) {
                toast.classList.add('toast-fade-out');
                setTimeout(() => {
                    if (document.body.contains(toast)) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 5000);
    }

    showSuccessToast(message) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'success-toast';
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">✅</div>
                <div class="toast-message">${message}</div>
                <button class="toast-close">×</button>
            </div>
        `;
        
        // Add to body
        document.body.appendChild(toast);
        
        // Add close event
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.classList.add('toast-fade-out');
            setTimeout(() => {
                toast.remove();
            }, 300);
        });
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (document.body.contains(toast)) {
                toast.classList.add('toast-fade-out');
                setTimeout(() => {
                    if (document.body.contains(toast)) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 3000);
    }
}