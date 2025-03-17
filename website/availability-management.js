/**
 * availability-management.js
 * Manages availability input, parsing, and display
 */

class AvailabilityManagement {
    constructor(apiService) {
        this.apiService = apiService;
        this.currentUserId = null;
    }

    init() {
        // Initialize tab switching
        const tabButtons = document.querySelectorAll('#availability-management .tab-btn');
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Hide all tab content
                document.querySelectorAll('#availability-management .tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Show selected tab content
                const tabId = button.dataset.tab;
                document.getElementById(tabId).classList.add('active');
            });
        });

        // Initialize user selection
        document.getElementById('user-select').addEventListener('change', (e) => {
            this.currentUserId = e.target.value;
        });

        document.getElementById('view-user-select').addEventListener('change', this.handleViewUserChange.bind(this));

        // Initialize parse button
        document.getElementById('parse-btn').addEventListener('click', this.handleParseAvailability.bind(this));

        // Initialize manual availability handling
        document.getElementById('add-slot-btn').addEventListener('click', this.addSlot.bind(this));
        document.getElementById('save-slots-btn').addEventListener('click', this.saveManualAvailability.bind(this));

        // Initialize event delegation for remove slot buttons
        document.getElementById('slots-container').addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-slot')) {
                this.removeSlot(e.target);
            }
        });
    }

    async handleViewUserChange(event) {
        const userId = event.target.value;
        if (!userId) {
            document.getElementById('availability-list').innerHTML = '<p class="empty-message">No availability data</p>';
            return;
        }
    
        try {
            const availability = await this.apiService.getUserAvailability(userId);
            console.log("Raw availability data:", availability); // Check the date format here
            this.displayAvailability(availability);
        } catch (error) {
            console.error('Failed to fetch availability:', error);
            document.getElementById('availability-list').innerHTML = 
                '<p class="error-message">Failed to load availability data</p>';
        }
    }

    async handleParseAvailability() {
        const userId = document.getElementById('user-select').value;
        const text = document.getElementById('availability-text').value.trim();
        
        if (!userId) {
            this.showError('Please select a user');
            return;
        }
        
        if (!text) {
            this.showError('Please enter availability text');
            return;
        }
        
        try {
            const parsedAvailability = await this.apiService.parseAvailability(userId, text);
            this.showSuccess(`Availability parsed! Found ${parsedAvailability.length} time slots.`);
            
            // Refresh the availability view if the same user is selected
            const viewUserSelect = document.getElementById('view-user-select');
            if (viewUserSelect.value === userId) {
                this.displayAvailability(parsedAvailability);
            }
        } catch (error) {
            console.error('Failed to parse availability:', error);
            this.showError('Failed to parse availability. Please try again.');
        }
    }

    addSlot() {
        const container = document.getElementById('slots-container');
        const slotRow = document.createElement('div');
        slotRow.className = 'slot-row';
        
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        // Format date for datetime-local input
        const formatDate = (date) => {
            return date.toISOString().slice(0, 16);
        };
        
        slotRow.innerHTML = `
            <div class="form-group">
                <label>From:</label>
                <input type="datetime-local" name="slot_start[]" value="${formatDate(today)}">
            </div>
            <div class="form-group">
                <label>To:</label>
                <input type="datetime-local" name="slot_end[]" value="${formatDate(tomorrow)}">
            </div>
            <button type="button" class="remove-slot">Remove</button>
        `;
        
        container.appendChild(slotRow);
    }

    removeSlot(button) {
        const slotRow = button.closest('.slot-row');
        if (document.querySelectorAll('.slot-row').length > 1) {
            slotRow.remove();
        } else {
            this.showError('At least one time slot is required');
        }
    }

    async saveManualAvailability() {
        const userId = document.getElementById('user-select').value;
        if (!userId) {
            this.showError('Please select a user');
            return;
        }
        
        const slotRows = document.querySelectorAll('.slot-row');
        const slots = [];
        
        for (const row of slotRows) {
            const startInput = row.querySelector('input[name="slot_start[]"]');
            const endInput = row.querySelector('input[name="slot_end[]"]');
            
            if (!startInput.value || !endInput.value) {
                this.showError('Please fill in all date and time fields');
                return;
            }
            
            const start = new Date(startInput.value);
            const end = new Date(endInput.value);
            
            if (start >= end) {
                this.showError('End time must be after start time');
                return;
            }
            
            slots.push({
                start: startInput.value,
                end: endInput.value
            });
        }
        
        try {
            await this.apiService.saveManualAvailability(userId, slots);
            this.showSuccess(`Availability saved! Added ${slots.length} time slots.`);
            
            // Refresh the availability view if the same user is selected
            const viewUserSelect = document.getElementById('view-user-select');
            if (viewUserSelect.value === userId) {
                const availability = await this.apiService.getUserAvailability(userId);
                this.displayAvailability(availability);
            }
        } catch (error) {
            console.error('Failed to save availability:', error);
            this.showError('Failed to save availability. Please try again.');
        }
    }
    displayAvailability(availability) {
        const container = document.getElementById('availability-list');
        
        if (!availability || availability.length === 0) {
            container.innerHTML = '<p class="empty-message">No availability data</p>';
            return;
        }
        
        container.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Start Time</th>
                        <th>End Time</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    ${availability.map(slot => {
                        // Parse the date strings correctly
                        const formatDate = (dateString) => {
                            try {
                                // Replace T with space for better parsing
                                const normalizedString = dateString.replace('T', ' ');
                                
                                // For dates in format '2025-03-17T15:00'
                                const [datePart, timePart] = normalizedString.split(' ');
                                
                                if (datePart && timePart) {
                                    const [year, month, day] = datePart.split('-');
                                    const [hour, minute] = timePart.split(':');
                                    
                                    // JavaScript months are 0-indexed
                                    const date = new Date(year, month - 1, day, hour, minute);
                                    
                                    // Verify valid date
                                    if (!isNaN(date.getTime())) {
                                        return date.toLocaleString();
                                    }
                                }
                                
                                // Fallback to direct parsing if the above format doesn't match
                                const date = new Date(dateString);
                                if (!isNaN(date.getTime())) {
                                    return date.toLocaleString();
                                }
                                
                                return 'Invalid Date Format';
                            } catch (e) {
                                console.error('Date parsing error:', e, dateString);
                                return 'Invalid Date Format';
                            }
                        };
                        
                        return `
                            <tr>
                                <td>${formatDate(slot.start_time || slot.start)}</td>
                                <td>${formatDate(slot.end_time || slot.end)}</td>
                                <td>${slot.description || slot.source_text || 'N/A'}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;
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