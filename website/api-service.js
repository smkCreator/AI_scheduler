/**
 * api-service.js
 * Handles all API communications with the backend
 */

class ApiService {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl || window.location.origin;
    }

    async fetchJson(endpoint, options = {}) {
        try {
            const url = `${this.baseUrl}${endpoint}`;
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error: ${error.message}`);
            throw error;
        }
    }

    // User Management
    async getUsers(userType) {
        return this.fetchJson(`/users/?user_type=${userType}`);
    }

    async getUser(userId) {
        return this.fetchJson(`/users/${userId}`);
    }

    async createUser(userData) {
        return this.fetchJson('/users/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }

    // Availability Management
    async getUserAvailability(userId) {
        return this.fetchJson(`/availability/${userId}`);
    }

    async parseAvailability(userId, text) {
        return this.fetchJson('/availability/parse', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, text })
        });
    }

    async saveManualAvailability(userId, slots) {
        return this.fetchJson('/availability/manual', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, slots })
        });
    }

    // Interview Scheduling
    async scheduleInterview(candidateId, recruiterId, durationMinutes) {
        return this.fetchJson('/schedule', {
            method: 'POST',
            body: JSON.stringify({
                candidate_id: candidateId,
                recruiter_id: recruiterId,
                duration_minutes: durationMinutes
            })
        });
    }

    async getUserInterviews(userId) {
        return this.fetchJson(`/interviews/${userId}`);
    }

    async updateInterviewStatus(interviewId, status) {
        return this.fetchJson(`/interviews/${interviewId}?status=${status}`, {
            method: 'PUT'
        });
    }

    // Demo Data
    async initializeDemoData() {
        return this.fetchJson('/demo/init', {
            method: 'POST'
        });
    }
}

// Export as a singleton
const apiService = new ApiService();