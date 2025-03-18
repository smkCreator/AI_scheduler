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
        
        // Initialize email scheduling buttons
        document.getElementById('manual-schedule-btn').addEventListener('click', this.handleManualScheduleInterview.bind(this));
        document.getElementById('auto-schedule-btn').addEventListener('click', this.handleAutoScheduleInterview.bind(this));
        
        // Initialize email scheduling form
        document.getElementById('email-schedule-form').addEventListener('submit', this.handleEmailScheduleInterview.bind(this));
        
        // Initialize tabs for email scheduling
        const emailSchedulingTabs = document.querySelectorAll('#email-schedule-form .tab-btn');
        emailSchedulingTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                // Remove active class from all tabs
                emailSchedulingTabs.forEach(t => t.classList.remove('active'));
                
                // Add active class to current tab
                e.target.classList.add('active');
                
                // Get the tab content ID
                const tabContentId = e.target.getAttribute('data-tab');
                
                // Hide all tab contents
                document.querySelectorAll('#email-schedule-form .tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Show the selected tab content
                document.getElementById(tabContentId).classList.add('active');
            });
        });
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

    async handleEmailScheduleInterview(event) {
        event.preventDefault();
        
        const candidateEmail = document.getElementById('candidate-email').value;
        const recruiterEmail = document.getElementById('recruiter-email').value;
        const date = document.getElementById('interview-date').value;
        const time = document.getElementById('interview-time').value;
        const durationMinutes = parseInt(document.getElementById('email-duration').value);
        
        if (!candidateEmail || !recruiterEmail || !date || !time) {
            this.showError('Please fill in all required fields');
            return;
        }
        
        try {
            // Show loading state
            const submitButton = document.querySelector('#email-schedule-form button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.textContent = 'Scheduling...';
            submitButton.disabled = true;
            
            // Schedule the interview using email
            const result = await this.apiService.scheduleInterviewByEmail(
                candidateEmail,
                recruiterEmail,
                date,
                time,
                durationMinutes
            );
            
            // Reset button state
            submitButton.textContent = originalText;
            submitButton.disabled = false;
            
            // Display success message
            alert('Interview scheduled successfully! Email notifications have been sent to both participants.');
            
            // Display the result in the result card
            this.displayEmailSchedulingResult(result);
            
            // Clear the form
            document.getElementById('email-schedule-form').reset();
            
        } catch (error) {
            console.error('Failed to schedule interview by email:', error);
            
            // Reset button state
            const submitButton = document.querySelector('#email-schedule-form button[type="submit"]');
            submitButton.textContent = 'Schedule & Send Notifications';
            submitButton.disabled = false;
            
            // Show error message
            this.showError(`Failed to schedule interview: ${error.message}`);
        }
    }
    
    async handleManualScheduleInterview(event) {
        event.preventDefault();
        
        const candidateEmail = document.getElementById('candidate-email').value;
        const recruiterEmail = document.getElementById('recruiter-email').value;
        const date = document.getElementById('interview-date').value;
        const time = document.getElementById('interview-time').value;
        const durationMinutes = parseInt(document.getElementById('email-duration-manual').value);
        
        if (!candidateEmail || !recruiterEmail || !date || !time) {
            this.showError('Please fill in all required fields');
            return;
        }
        
        try {
            // Show loading state
            const submitButton = document.getElementById('manual-schedule-btn');
            const originalText = submitButton.textContent;
            submitButton.textContent = 'Scheduling...';
            submitButton.disabled = true;
            
            // Schedule the interview using email
            const result = await this.apiService.scheduleInterviewByEmail(
                candidateEmail,
                recruiterEmail,
                date,
                time,
                durationMinutes
            );
            
            // Reset button state
            submitButton.textContent = originalText;
            submitButton.disabled = false;
            
            // Display success message
            this.showSuccess('Interview scheduled successfully! Email notifications have been sent to both participants.');
            
            // Display the result in the result card
            this.displayEmailSchedulingResult(result);
            
            // Clear the form
            document.getElementById('candidate-email').value = '';
            document.getElementById('recruiter-email').value = '';
            document.getElementById('interview-date').value = '';
            document.getElementById('interview-time').value = '';
            
        } catch (error) {
            console.error('Failed to schedule interview by email:', error);
            
            // Reset button state
            const submitButton = document.getElementById('manual-schedule-btn');
            submitButton.textContent = 'Schedule & Send Notifications';
            submitButton.disabled = false;
            
            // Show error message
            this.showError(`Failed to schedule interview: ${error.message}`);
        }
    }
    
    async handleAutoScheduleInterview(event) {
        event.preventDefault();
        
        const candidateEmail = document.getElementById('candidate-email').value;
        const recruiterEmail = document.getElementById('recruiter-email').value;
        const durationMinutes = parseInt(document.getElementById('email-duration-auto').value);
        
        if (!candidateEmail || !recruiterEmail) {
            this.showError('Please enter both candidate and recruiter email addresses');
            return;
        }
        
        try {
            // Show loading state
            const submitButton = document.getElementById('auto-schedule-btn');
            const originalText = submitButton.textContent;
            submitButton.textContent = 'Finding optimal time...';
            submitButton.disabled = true;
            
            // Auto-schedule the interview using email
            const result = await this.apiService.autoScheduleByEmail(
                candidateEmail,
                recruiterEmail,
                durationMinutes
            );
            
            // Reset button state
            submitButton.textContent = originalText;
            submitButton.disabled = false;
            
            // Display success message
            this.showSuccess('Automatically scheduled interview at optimal time! Email notifications have been sent to both participants.');
            
            // Display the result in the result card
            this.displayEmailSchedulingResult(result, true);
            
            // Clear the form
            document.getElementById('candidate-email').value = '';
            document.getElementById('recruiter-email').value = '';
            
        } catch (error) {
            console.error('Failed to auto-schedule interview:', error);
            
            // Reset button state
            const submitButton = document.getElementById('auto-schedule-btn');
            submitButton.textContent = 'Find Optimal Time & Schedule';
            submitButton.disabled = false;
            
            // Show error message
            this.showError(`Failed to auto-schedule interview: ${error.message}`);
        }
    }
    
    displayEmailSchedulingResult(result, isAutoScheduled = false) {
        const resultContainer = document.getElementById('scheduling-result');
        const detailsContainer = document.getElementById('optimal-slot-details');
        
        // Format the date for display
        const formatDate = (dateString) => {
            if (!dateString) return 'N/A';
            return new Date(dateString).toLocaleString();
        };
        
        let resultHTML = `
            <div class="result-details">
                <p><strong>Status:</strong> <span class="success">Successfully Scheduled</span></p>
                <p><strong>Interview ID:</strong> ${result.interview_id}</p>
        `;
        
        if (isAutoScheduled && result.start_time) {
            resultHTML += `
                <p><strong>AI-Selected Time:</strong> ${formatDate(result.start_time)}</p>
                <p><strong>End Time:</strong> ${formatDate(result.end_time)}</p>
                <p><strong>Match Score:</strong> ${result.score ? result.score.toFixed(2) : 'N/A'}</p>
            `;
        }
        
        resultHTML += `
                <p><strong>Notification Status:</strong> Email notifications and calendar invites sent</p>
                <p>The interview has been scheduled and email notifications with calendar invites have been automatically sent to both participants.</p>
            </div>
        `;
        
        detailsContainer.innerHTML = resultHTML;
        
        // Show the result card
        resultContainer.classList.remove('hidden');
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