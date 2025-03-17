/**
 * user-management.js
 * Manages user-related functionality: creation, listing, and selection
 */

class UserManagement {
    constructor(apiService) {
        this.apiService = apiService;
        this.users = {
            candidate: [],
            recruiter: []
        };
        this.currentUserType = 'candidate';
    }

    init() {
        // Initialize form handling
        document.getElementById('create-user-form').addEventListener('submit', this.handleCreateUser.bind(this));
        
        // Initialize tab switching
        const tabButtons = document.querySelectorAll('#user-management .tab-btn');
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                this.currentUserType = button.dataset.type;
                this.renderUserList();
            });
        });

        // Load initial user data
        this.loadUserData();
    }

    async loadUserData() {
        try {
            // Load candidates
            this.users.candidate = await this.apiService.getUsers('candidate');
            
            // Load recruiters
            this.users.recruiter = await this.apiService.getUsers('recruiter');
            
            // Render user list based on current tab
            this.renderUserList();
            
            // Update user selection dropdowns
            this.updateUserSelects();
        } catch (error) {
            console.error('Failed to load user data:', error);
            this.showError('Failed to load users. Please try again.');
        }
    }

    async handleCreateUser(event) {
        event.preventDefault();
        const form = event.target;
        
        try {
            const userData = {
                name: form.name.value,
                email: form.email.value,
                user_type: form.user_type.value,
                priority: form.priority.value
            };
            
            const newUser = await this.apiService.createUser(userData);
            
            // Add to appropriate user list
            this.users[userData.user_type].push(newUser);
            
            // Refresh displays
            this.renderUserList();
            this.updateUserSelects();
            
            // Reset form
            form.reset();
            
            this.showSuccess(`${newUser.name} added successfully!`);
        } catch (error) {
            console.error('Failed to create user:', error);
            this.showError('Failed to create user. Please try again.');
        }
    }

    renderUserList() {
        const userList = document.getElementById('user-list');
        const users = this.users[this.currentUserType];
        
        if (users.length === 0) {
            userList.innerHTML = '<p class="empty-message">No users found</p>';
            return;
        }
        
        const userType = this.currentUserType.charAt(0).toUpperCase() + this.currentUserType.slice(1);
        
        userList.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Priority</th>
                    </tr>
                </thead>
                <tbody>
                    ${users.map(user => `
                        <tr>
                            <td>${user.id}</td>
                            <td>${user.name}</td>
                            <td>${user.email}</td>
                            <td>${user.priority || 'medium'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    updateUserSelects() {
        // Update all user select dropdowns in the application
        const selectors = [
            'user-select',
            'view-user-select',
            'interview-user-select',
            'candidate-select',
            'recruiter-select'
        ];
        
        selectors.forEach(selectorId => {
            const select = document.getElementById(selectorId);
            if (!select) return;
            
            // Clear existing options except the first one
            while (select.options.length > 1) {
                select.remove(1);
            }
            
            // Add appropriate user types
            let users;
            if (selectorId === 'candidate-select') {
                users = this.users.candidate;
            } else if (selectorId === 'recruiter-select') {
                users = this.users.recruiter;
            } else {
                // For general selectors, add all users
                users = [...this.users.candidate, ...this.users.recruiter];
            }
            
            // Add options
            users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.text = `${user.name} (${user.user_type})`;
                select.appendChild(option);
            });
        });
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