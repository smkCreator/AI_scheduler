/**
 * interview-scheduling.js
 * Manages interview scheduling and management
 */

class InterviewScheduling {
    constructor(apiService) {
        this.apiService = apiService;
    }

    init() {
        // Initialize the scheduling form
        document.getElementById('schedule-form').addEventListener('submit', this.handleScheduleInterview.bind(this));
        
        // Initialize interview management
        document.getElementById('interview-user-select').addEventListener('change', this.handleUserInterviewsChange.bind(this));
    }

    async handleScheduleInterview(event) {
        event.preventDefault();
        
        const candidateId = parseInt(document.getElementById('candidate-select').value);
        const recruiterId = parseInt(document.getElementById('recruiter-select').value);
        const durationMinutes = parseInt(document.getElementById('duration').value);
        
        if (!candidateId || !recruiterId) {
            this.showError('Please select both a candidate and a recruiter');
            return;
        }
        
        if (durationMinutes < 15) {
            this.showError('Duration must be at least 15 minutes');
            return;
        }
        
        try {
            // Show loading state
            const submitButton = document.querySelector('#schedule-form button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.textContent = 'Finding optimal time...';
            submitButton.disabled = true;
            
            // Check if availability exists for both users
            const candidateAvail = await this.apiService.getUserAvailability(candidateId);
            const recruiterAvail = await this.apiService.getUserAvailability(recruiterId);
            
            if (!candidateAvail || candidateAvail.length === 0) {
                throw new Error('Candidate has no availability data. Please add availability first.');
            }
            
            if (!recruiterAvail || recruiterAvail.length === 0) {
                throw new Error('Recruiter has no availability data. Please add availability first.');
            }
            
            // Schedule the interview
            const result = await this.apiService.scheduleInterview(candidateId, recruiterId, durationMinutes);
            
            // Reset button state
            submitButton.textContent = originalText;
            submitButton.disabled = false;
            
            // Display the result
            this.displaySchedulingResult(result);
        } catch (error) {
            console.error('Failed to schedule interview:', error);
            
            // Reset button state
            const submitButton = document.querySelector('#schedule-form button[type="submit"]');
            submitButton.textContent = 'Find Optimal Time';
            submitButton.disabled = false;
            
            // Hide result card if there was an error
            document.getElementById('scheduling-result').classList.add('hidden');
            
            // Show more specific error message
            if (error.message && error.message.includes('availability')) {
                this.showError(error.message);
            } else {
                this.showError('An error occurred while scheduling: There might be a problem with the scheduling algorithm or the data format. Please check the backend logs for more details.');
            }
        }
    }

    displaySchedulingResult(result) {
        const resultContainer = document.getElementById('scheduling-result');
        const detailsContainer = document.getElementById('optimal-slot-details');
        
        // Format dates for display
        const formatDate = (dateString) => {
            return new Date(dateString).toLocaleString();
        };
        
        detailsContainer.innerHTML = `
            <div class="result-details">
                <p><strong>Candidate:</strong> ${result.candidate}</p>
                <p><strong>Recruiter:</strong> ${result.recruiter}</p>
                <p><strong>Start Time:</strong> ${formatDate(result.start_time)}</p>
                <p><strong>End Time:</strong> ${formatDate(result.end_time)}</p>
                <p><strong>Meeting Link:</strong> <a href="${result.meeting_link}" target="_blank">${result.meeting_link}</a></p>
                ${result.score ? `<p><strong>Match Score:</strong> ${result.score.toFixed(2)}</p>` : ''}
                <p>Calendar invites have been sent to both participants.</p>
            </div>
        `;
        
        // Show the result card
        resultContainer.classList.remove('hidden');
        
        // Refresh the interviews list for both participants
        this.refreshInterviewsForUser(result.candidate_id);
        this.refreshInterviewsForUser(result.recruiter_id);
    }

    async handleUserInterviewsChange(event) {
        const userId = event.target.value;
        if (!userId) {
            document.getElementById('interviews-list').innerHTML = '<p class="empty-message">No interviews scheduled</p>';
            return;
        }
        
        await this.refreshInterviewsForUser(userId);
    }

    async refreshInterviewsForUser(userId) {
        try {
            const interviews = await this.apiService.getUserInterviews(userId);
            this.displayInterviews(interviews);
        } catch (error) {
            console.error('Failed to fetch interviews:', error);
            document.getElementById('interviews-list').innerHTML = 
                '<p class="error-message">Failed to load interview data</p>';
        }
    }

    displayInterviews(interviews) {
        const container = document.getElementById('interviews-list');
        
        if (!interviews || interviews.length === 0) {
            container.innerHTML = '<p class="empty-message">No interviews scheduled</p>';
            return;
        }
        
        container.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Candidate</th>
                        <th>Recruiter</th>
                        <th>Start Time</th>
                        <th>End Time</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${interviews.map(interview => {
                        // Format dates for display - handle potential invalid dates
                        let startDate, endDate;
                        try {
                            startDate = new Date(interview.start_time);
                            endDate = new Date(interview.end_time);
                        } catch (e) {
                            console.error('Invalid date format:', e);
                            startDate = new Date();
                            endDate = new Date();
                        }
                        
                        const formatDate = (date) => {
                            return date instanceof Date && !isNaN(date) ? 
                                date.toLocaleString() : 'Invalid Date';
                        };
                        
                        return `
                            <tr>
                                <td>${interview.id}</td>
                                <td>${interview.candidate_name || 'Unknown'}</td>
                                <td>${interview.recruiter_name || 'Unknown'}</td>
                                <td>${formatDate(startDate)}</td>
                                <td>${formatDate(endDate)}</td>
                                <td>
                                    <span class="status-badge ${(interview.status || 'pending').toLowerCase()}">${interview.status || 'Pending'}</span>
                                </td>
                                <td>
                                    <select class="status-select" data-interview-id="${interview.id}">
                                        <option value="">Change Status</option>
                                        <option value="scheduled">Scheduled</option>
                                        <option value="completed">Completed</option>
                                        <option value="cancelled">Cancelled</option>
                                        <option value="rescheduled">Rescheduled</option>
                                    </select>
                                </td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;
        
        // Add event listeners to status selects
        const statusSelects = container.querySelectorAll('.status-select');
        statusSelects.forEach(select => {
            select.addEventListener('change', this.handleStatusChange.bind(this));
        });
    }

    async handleStatusChange(event) {
        const select = event.target;
        const interviewId = select.dataset.interviewId;
        const newStatus = select.value;
        
        if (!newStatus) {
            return; // User selected the placeholder option
        }
        
        try {
            await this.apiService.updateInterviewStatus(interviewId, newStatus);
            this.showSuccess(`Interview status updated to ${newStatus}`);
            
            // Refresh the interviews list
            const userSelect = document.getElementById('interview-user-select');
            if (userSelect.value) {
                await this.refreshInterviewsForUser(userSelect.value);
            }
        } catch (error) {
            console.error('Failed to update interview status:', error);
            this.showError('Failed to update interview status. Please try again.');
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