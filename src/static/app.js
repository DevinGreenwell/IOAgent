class IOAgent {
    constructor() {
        this.currentProject = null;
        this.currentUser = null;
        this.accessToken = null;
        
        // Configure API base URL based on environment
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // Local development
            this.apiBase = 'http://localhost:5001/api';
        } else {
            // Production - use same origin (whether on Render or other hosting)
            this.apiBase = window.location.origin + '/api';
        }
        
        this.init();
    }

    init() {
        // Check if user is already logged in
        this.checkExistingAuth();
    }

    checkExistingAuth() {
        const token = localStorage.getItem('ioagent_token');
        const user = localStorage.getItem('ioagent_user');
        
        console.log('Checking existing auth:', { hasToken: !!token, hasUser: !!user });
        
        // Always show auth overlay first to ensure UI is visible
        console.log('Showing auth overlay...');
        this.showAuthOverlay();
        
        // Check if we have stored authentication
        if (token && user) {
            this.accessToken = token;
            this.currentUser = JSON.parse(user);
            console.log('Found existing auth, restoring session for user:', this.currentUser.username);
            
            // Restore the main app with existing token
            this.showMainApp();
        } else {
            console.log('No existing auth found, showing login');
        }
    }

    showAuthOverlay() {
        document.getElementById('authOverlay').style.display = 'flex';
        document.getElementById('mainApp').style.display = 'none';
        this.setupAuthEventListeners();
    }

    showMainApp() {
        document.getElementById('authOverlay').style.display = 'none';
        document.getElementById('mainApp').style.display = 'block';
        
        // Update navbar with user info
        document.getElementById('username-display').textContent = this.currentUser.username;
        document.getElementById('user-info-nav').style.display = 'flex';
        
        // Initialize main app
        this.setupEventListeners();
        
        // Only load dashboard if we have a real token, not demo mode
        if (this.accessToken !== 'demo-token') {
            // For now, skip token validation and try loading dashboard directly
            console.log('Loading dashboard with token...');
            this.loadDashboard();
        } else {
            // Demo mode - show empty dashboard
            this.displayProjects([]);
            this.updateDashboardStats([]);
        }
        
        this.setupFileUpload();
    }

    async validateTokenAndLoadDashboard() {
        try {
            console.log('Validating token:', this.accessToken ? this.accessToken.substring(0, 20) + '...' : 'No token');
            
            // Test the token with a simple API call first
            const response = await fetch(`${this.apiBase}/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`,
                    'Content-Type': 'application/json'
                }
            });

            console.log('Token validation response status:', response.status);
            
            if (response.ok) {
                const userData = await response.json();
                console.log('Token is valid, user data:', userData);
                this.loadDashboard();
            } else {
                const errorData = await response.text();
                console.log('Token validation failed:', response.status, errorData);
                
                // Try to load dashboard anyway and see what happens
                console.log('Attempting to load dashboard despite token validation failure...');
                try {
                    await this.loadDashboard();
                } catch (dashboardError) {
                    console.log('Dashboard load failed, logging out');
                    this.logout();
                }
            }
        } catch (error) {
            console.error('Token validation network error:', error);
            this.showAlert('Connection error. Please check your internet connection.', 'warning');
            // Don't logout on network errors, just show empty dashboard
            this.displayProjects([]);
            this.updateDashboardStats([]);
        }
    }

    setupAuthEventListeners() {
        // Login form
        document.getElementById('authLoginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });

        // Register form
        document.getElementById('authRegisterForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.register();
        });
    }

    // Authentication Methods
    async login() {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        this.showAuthMessage('Logging in...', 'info');

        try {
            const response = await fetch(`${this.apiBase}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.success) {
                this.accessToken = data.access_token;
                this.currentUser = data.user;

                // Store in localStorage
                localStorage.setItem('ioagent_token', this.accessToken);
                localStorage.setItem('ioagent_user', JSON.stringify(this.currentUser));

                this.showAuthMessage('Login successful!', 'success');
                setTimeout(() => this.showMainApp(), 1000);
            } else {
                // If login fails and we're trying admin credentials, try to bootstrap
                if (username === 'admin' && data.error?.includes('Invalid credentials')) {
                    this.showAuthMessage('Creating admin user...', 'info');
                    await this.bootstrapAdminUser();
                } else {
                    this.showAuthMessage(data.error || 'Login failed', 'error');
                }
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showAuthMessage('Connection error. Please try again.', 'error');
        }
    }

    async register() {
        try {
            const username = document.getElementById('registerUsername').value;
            const email = document.getElementById('registerEmail').value;
            const password = document.getElementById('registerPassword').value;
            
            console.log('Register attempt:', { username, email, passwordLength: password.length });
            
            // Basic validation
            if (!username || !email || !password) {
                this.showAuthMessage('Please fill in all fields', 'error');
                return;
            }
            
            if (password.length < 8) {
                this.showAuthMessage('Password must be at least 8 characters', 'error');
                return;
            }

            this.showAuthMessage('Creating account...', 'info');

            const response = await fetch(`${this.apiBase}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, email, password })
            });

            const data = await response.json();

            if (data.success) {
                this.accessToken = data.access_token;
                this.currentUser = data.user;

                // Store in localStorage
                localStorage.setItem('ioagent_token', this.accessToken);
                localStorage.setItem('ioagent_user', JSON.stringify(this.currentUser));

                this.showAuthMessage('Registration successful!', 'success');
                setTimeout(() => this.showMainApp(), 1000);
            } else {
                this.showAuthMessage(data.error || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showAuthMessage('Connection error. Please try again.', 'error');
        }
    }

    async bootstrapAdminUser() {
        try {
            const response = await fetch(`${this.apiBase}/auth/bootstrap`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showAuthMessage('Admin user created! Trying login again...', 'success');
                setTimeout(() => {
                    // Auto-fill and try login again
                    document.getElementById('loginUsername').value = 'admin';
                    document.getElementById('loginPassword').value = 'AdminPass123!';
                    this.login();
                }, 2000);
            } else {
                this.showAuthMessage(data.error || 'Failed to create admin user', 'error');
            }
        } catch (error) {
            console.error('Bootstrap error:', error);
            this.showAuthMessage('Failed to create admin user', 'error');
        }
    }

    logout() {
        console.log('Logout called');
        
        // Clear stored data
        localStorage.removeItem('ioagent_token');
        localStorage.removeItem('ioagent_user');
        
        // Reset app state
        this.accessToken = null;
        this.currentUser = null;
        this.currentProject = null;
        
        // Add a small delay to prevent flash
        setTimeout(() => {
            // Show auth overlay
            this.showAuthOverlay();
            this.showAuthMessage('Session expired. Please login again.', 'info');
        }, 100);
    }

    showRegisterForm() {
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('registerForm').style.display = 'block';
        document.getElementById('authMessage').style.display = 'none';
    }

    showLoginForm() {
        document.getElementById('registerForm').style.display = 'none';
        document.getElementById('loginForm').style.display = 'block';
        document.getElementById('authMessage').style.display = 'none';
    }

    showAuthMessage(message, type) {
        const messageDiv = document.getElementById('authMessage');
        messageDiv.style.display = 'block';
        messageDiv.className = `alert mt-3 alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'}`;
        messageDiv.textContent = message;

        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 3000);
        }
    }

    // Helper method to make authenticated API calls
    async makeAuthenticatedRequest(url, options = {}) {
        const headers = {
            ...options.headers
        };

        // Don't set Content-Type for FormData - let browser set it with boundary
        if (!(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        // Always add Authorization header if token exists
        if (this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        } else {
            // No token, redirect to login
            console.log('No access token found, redirecting to login');
            this.logout();
            throw new Error('Authentication required');
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            // Handle 401 responses
            if (response.status === 401) {
                console.log('401 Unauthorized - token may be expired');
                // Clear stored auth and redirect to login
                this.logout();
                throw new Error('Authentication required');
            }

            return response;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    setupEventListeners() {
        // Use event delegation on the main app container for robustness
        const mainApp = document.getElementById('mainApp');

        // Main navigation
        const mainNav = document.getElementById('mainNav');
        if (mainNav) {
            mainNav.addEventListener('click', (e) => {
                if (e.target.tagName === 'A' && e.target.dataset.section) {
                    e.preventDefault();
                    this.showSection(e.target.dataset.section);
                }
            });
        }

        // Note: Logout button is handled by inline onclick in HTML

        // Attach handlers to forms for submission
        const createProjectForm = document.getElementById('createProjectForm');
        if (createProjectForm) {
            createProjectForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createProject();
            });
        }
        
        const addTimelineForm = document.getElementById('addTimelineForm');
        if (addTimelineForm) {
            addTimelineForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addTimelineEntry();
            });
        }
        
        const projectInfoForm = document.getElementById('projectInfoForm');
        if (projectInfoForm) {
            projectInfoForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveProjectInfo();
            });
        }
        
        // Sidebar close button
        const closeProjectBtn = document.getElementById('closeProjectBtn');
        if (closeProjectBtn) {
            closeProjectBtn.addEventListener('click', () => this.closeProject());
        }

        // Event delegation for dynamically loaded content
        if (mainApp) {
            mainApp.addEventListener('click', (e) => {
            const target = e.target;
            const targetId = target.id;
            const targetClosest = (selector) => target.closest(selector);

            // Create new project button
            if (targetId === 'newProjectBtnHeader' || targetClosest('#newProjectBtnHeader')) {
                this.showCreateProjectModal();
            }

            // Upload evidence button
            if (targetId === 'uploadEvidenceBtn' || targetClosest('#uploadEvidenceBtn')) {
                document.getElementById('fileInput').click();
            }

            // Add timeline entry button
            if (targetId === 'addTimelineModalBtn' || targetClosest('#addTimelineModalBtn')) {
                this.showAddTimelineModal();
            }

            // Run Causal Analysis button
            if (target.matches('.btn-run-analysis')) {
                this.runCausalAnalysis();
            }

            // Generate ROI button
            if (target.matches('.btn-generate-roi')) {
                this.generateROI();
            }
        });
        }

        this.setupFileUpload();
    }

    setupFileUpload() {
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (event) => {
                this.handleFileUpload(event.target.files);
            });
        }

        const uploadArea = document.querySelector('.upload-area');

        // Drag and drop
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                this.handleFileUpload(files);
            });
        }
    }

    showSection(sectionName) {
        try {
            console.log('showSection called with:', sectionName);
            
            // Hide all sections
            console.log('Hiding all content sections');
            document.querySelectorAll('.content-section').forEach(section => {
                section.style.display = 'none';
            });

            // Show selected section
            console.log('Showing section:', `${sectionName}-section`);
            const targetSection = document.getElementById(`${sectionName}-section`);
            if (targetSection) {
                targetSection.style.display = 'block';
            } else {
                console.error('Section not found:', `${sectionName}-section`);
            }

            // Update navigation
            console.log('Updating navigation');
            document.querySelectorAll('#mainNav .nav-link').forEach(link => {
                link.classList.remove('active');
            });
            const activeLink = document.querySelector(`[data-section="${sectionName}"]`);
            if (activeLink) {
                activeLink.classList.add('active');
            } else {
                console.error('Navigation link not found for section:', sectionName);
            }

            // Load section data
            console.log('Loading section data for:', sectionName);
            this.loadSectionData(sectionName);
            console.log('showSection completed');
        } catch (error) {
            console.error('Error in showSection:', error);
        }
    }

    loadSectionData(sectionName) {
        if (!this.currentProject) return;

        switch (sectionName) {
            case 'project-info':
                this.loadProjectInfo();
                break;
            case 'evidence':
                this.loadEvidence();
                break;
            case 'timeline':
                this.loadTimeline();
                break;
            case 'analysis':
                this.loadAnalysis();
                break;
            case 'roi-generator':
                this.checkReadiness();
                break;
        }
    }

    async loadDashboard() {
        try {
            const response = await this.makeAuthenticatedRequest(`${this.apiBase}/projects`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();

            if (data.success) {
                this.displayProjects(data.projects);
                this.updateDashboardStats(data.projects);
            } else {
                throw new Error(data.error || 'Failed to load projects');
            }
        } catch (error) {
            console.error('Error loading dashboard:', error);
            if (error.message !== 'Authentication required') {
                this.showAlert('Error loading projects: ' + error.message, 'danger');
            }
        }
    }

    displayProjects(projects) {
        const projectsList = document.getElementById('projectsList');
        
        if (projects.length === 0) {
            projectsList.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-folder-open fa-3x mb-3"></i>
                    <p>No projects found. Create your first investigation to get started.</p>
                </div>
            `;
            return;
        }

        projectsList.innerHTML = projects.map(project => `
            <div class="project-card" data-project-id="${project.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h5 class="mb-2">${this.escapeHtml(project.title)}</h5>
                        <p class="text-muted mb-2">
                            <i class="fas fa-calendar me-2"></i>
                            Created: ${new Date(project.created_at).toLocaleDateString()}
                        </p>
                        <p class="text-muted mb-0">
                            <i class="fas fa-clock me-2"></i>
                            Updated: ${new Date(project.updated_at).toLocaleDateString()}
                        </p>
                    </div>
                    <div>
                        <span class="project-status status-${project.status}">${project.status.toUpperCase()}</span>
                    </div>
                </div>
            </div>
        `).join('');

        // Add click handlers to project cards
        projectsList.querySelectorAll('.project-card').forEach(card => {
            card.addEventListener('click', () => {
                const projectId = card.dataset.projectId;
                this.openProject(projectId);
            });
        });
    }

    updateDashboardStats(projects) {
        document.getElementById('totalProjects').textContent = projects.length;
        document.getElementById('draftProjects').textContent = projects.filter(p => p.status === 'draft').length;
        document.getElementById('completeProjects').textContent = projects.filter(p => p.status === 'complete').length;
    }

    getFileIcon(fileType) {
        if (!fileType) return 'fas fa-file';
        const type = fileType.toLowerCase();
        if (type.startsWith('image/')) return 'fas fa-file-image';
        if (type.startsWith('audio/')) return 'fas fa-file-audio';
        if (type.startsWith('video/')) return 'fas fa-file-video';
        if (type.includes('pdf')) return 'fas fa-file-pdf';
        if (type.includes('word')) return 'fas fa-file-word';
        if (type.includes('excel') || type.includes('spreadsheet')) return 'fas fa-file-excel';
        if (type.includes('presentation') || type.includes('powerpoint')) return 'fas fa-file-powerpoint';
        if (type.includes('zip') || type.includes('archive')) return 'fas fa-file-archive';
        if (type.startsWith('text/')) return 'fas fa-file-alt';
        return 'fas fa-file';
    }

    escapeHtml(str) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str || ''));
        return div.innerHTML;
    }

    showCreateProjectModal() {
        const modal = new bootstrap.Modal(document.getElementById('createProjectModal'));
        modal.show();
    }

    async createProject() {
        // Prevent multiple simultaneous submissions
        if (this.creatingProject) {
            return;
        }
        this.creatingProject = true;
        
        const title = document.getElementById('newProjectTitle').value;
        const investigatingOfficer = document.getElementById('newInvestigatingOfficer').value;

        if (!title.trim()) {
            this.showAlert('Please enter a project title', 'warning');
            this.creatingProject = false;
            return;
        }

        try {
            this.showLoading('Creating project...');
            
            const response = await this.makeAuthenticatedRequest(`${this.apiBase}/projects`, {
                method: 'POST',
                body: JSON.stringify({
                    title: title.trim(),
                    investigating_officer: investigatingOfficer.trim()
                })
            });

            const data = await response.json();

            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('createProjectModal')).hide();
                document.getElementById('createProjectForm').reset();
                this.showAlert('Project created successfully', 'success');
                
                // Hide loading first, then load dashboard and open project
                this.hideLoading();
                this.creatingProject = false;
                
                // Add a small delay to ensure project is fully saved before opening
                setTimeout(() => {
                    this.loadDashboard();
                    this.openProject(data.project.id);
                }, 100);
                return; // Exit early to avoid the finally block
            } else {
                this.showAlert(data.error || 'Failed to create project', 'danger');
            }
        } catch (error) {
            console.error('Error creating project:', error);
            // Don't show error message if user was redirected to login due to authentication issues
            if (error.message !== 'Authentication required') {
                this.showAlert('Error creating project', 'danger');
            }
        } finally {
            this.hideLoading();
            this.creatingProject = false;
        }
    }

    async openProject(projectId, showLoadingOverlay = true) {
        try {
            console.log('Opening project:', projectId);
            if (showLoadingOverlay) {
                this.showLoading('Loading project...');
            }
            
            const response = await this.makeAuthenticatedRequest(`${this.apiBase}/projects/${projectId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();

            if (data.success) {
                this.currentProject = data.project;
                this.updateCurrentProjectDisplay();
                this.loadTimeline();
                this.showSection('project-info');
                this.showAlert('Project loaded successfully', 'success');
            } else {
                throw new Error(data.error || 'Failed to load project');
            }
        } catch (error) {
            console.error('Error loading project:', error);
            if (error.message !== 'Authentication required') {
                this.showAlert('Error loading project: ' + error.message, 'danger');
            }
        } finally {
            if (showLoadingOverlay) {
                this.hideLoading();
            }
        }
    }

    updateCurrentProjectDisplay() {
        const sidebar = document.getElementById('current-project-sidebar');
        
        // Check if sidebar elements exist before trying to update them
        if (!sidebar) {
            console.log('Project sidebar elements not found in DOM - skipping display update');
            return;
        }

        if (this.currentProject) {
            sidebar.style.display = 'block';
            
            const projectTitle = document.getElementById('sidebar-project-title');
            if (projectTitle) {
                projectTitle.textContent = this.currentProject.metadata.title;
            }
            
            const statusBadge = document.getElementById('sidebar-project-status');
            if (statusBadge) {
                const status = this.currentProject.metadata.status || 'draft';
                statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                statusBadge.className = `project-status status-${status.toLowerCase()}`;
            }
        } else {
            sidebar.style.display = 'none';
        }
    }

    closeProject() {
        this.currentProject = null;
        this.updateCurrentProjectDisplay();
        this.showSection('dashboard');
        this.loadDashboard();
    }

    loadProjectInfo() {
        if (!this.currentProject) return;

        const project = this.currentProject;
        document.getElementById('projectTitleInput').value = project.metadata.title || '';
        document.getElementById('investigatingOfficer').value = project.metadata.investigating_officer || '';
        document.getElementById('incidentDate').value = project.incident_info.incident_date ? 
            new Date(project.incident_info.incident_date).toISOString().slice(0, 16) : '';
        document.getElementById('incidentLocation').value = project.incident_info.location || '';
        document.getElementById('incidentType').value = project.incident_info.incident_type || '';
        document.getElementById('projectStatus').value = project.metadata.status || 'draft';
    }

    async saveProjectInfo() {
        if (!this.currentProject) {
            this.showAlert('No project selected', 'warning');
            return;
        }

        const formData = {
            title: document.getElementById('projectTitleInput')?.value || '',
            investigating_officer: document.getElementById('investigatingOfficer')?.value || '',
            status: document.getElementById('projectStatus')?.value || 'draft',
            incident_info: {
                incident_date: document.getElementById('incidentDate')?.value || '',
                location: document.getElementById('incidentLocation')?.value || '',
                incident_type: document.getElementById('incidentType')?.value || ''
            }
        };

        try {
            this.showLoading('Saving project...');
            
            const response = await this.makeAuthenticatedRequest(`${this.apiBase}/projects/${this.currentProject.id}`, {
                method: 'PUT',
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.currentProject = data.project;
                this.updateCurrentProjectDisplay();
                this.showAlert('Project information saved successfully', 'success');
            } else {
                throw new Error(data.error || 'Failed to save project');
            }
        } catch (error) {
            console.error('Error saving project:', error);
            if (error.message !== 'Authentication required') {
                this.showAlert('Error saving project: ' + error.message, 'danger');
            }
        } finally {
            this.hideLoading();
        }
    }

    async handleFileUpload(files) {
        if (!this.currentProject) {
            this.showAlert('Please select a project first', 'warning');
            return;
        }

        const fileList = files instanceof FileList ? files : [files];
        
        for (let file of fileList) {
            await this.uploadFile(file);
        }
        
        this.loadEvidence();
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('description', `Uploaded file: ${file.name}`);

        try {
            this.showLoading(`Uploading and analyzing ${file.name}...`);
            
            const response = await this.makeAuthenticatedRequest(`${this.apiBase}/projects/${this.currentProject.id}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showAlert(data.message || `File ${file.name} uploaded successfully`, 'success');
                
                // If timeline suggestions were found, show them
                if (data.timeline_suggestions && data.timeline_suggestions.length > 0) {
                    this.showTimelineSuggestions(data.timeline_suggestions);
                }
                
                // Reload project data to show new evidence
                await this.openProject(this.currentProject.id);
            } else {
                this.showAlert(`Failed to upload ${file.name}: ${data.error}`, 'danger');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            if (error.message !== 'Authentication required') {
                this.showAlert(`Error uploading ${file.name}: ${error.message}`, 'danger');
            }
        } finally {
            this.hideLoading();
        }
    }

    loadEvidence() {
        if (!this.currentProject || !this.currentProject.evidence_library) return;

        const evidenceList = document.getElementById('evidenceList');
        const evidence = this.currentProject.evidence_library;

        if (evidence.length === 0) {
            evidenceList.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-file-excel fa-2x mb-3"></i>
                    <p>No evidence uploaded yet.</p>
                </div>
            `;
            return;
        }

        evidenceList.innerHTML = evidence.map(item => `
            <div class="evidence-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6><i class="${this.getFileIcon(item.type)} me-2"></i>${this.escapeHtml(item.filename)}</h6>
                        <p class="mb-1">${this.escapeHtml(item.description)}</p>
                        <small class="text-muted">
                            Type: ${this.escapeHtml(item.type)} | 
                            Source: ${this.escapeHtml(item.source)} | 
                            Uploaded: ${new Date(item.uploaded_at || Date.now()).toLocaleString()}
                        </small>
                    </div>
                    <div class="ms-3">
                        <span class="badge bg-primary">${this.escapeHtml(item.reliability || 'Unrated')}</span>
                        <button class="btn btn-sm btn-outline-danger ms-2 btn-delete-evidence" data-evidence-id="${item.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // Add event listeners for delete buttons
        evidenceList.querySelectorAll('.btn-delete-evidence').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const evidenceId = btn.dataset.evidenceId;
                this.deleteEvidence(evidenceId);
            });
        });
    }

    async deleteEvidence(evidenceId) {
        if (!this.currentProject) return;

        // Simple confirmation dialog
        if (!confirm('Are you sure you want to delete this evidence? This action cannot be undone.')) {
            return;
        }

        try {
            this.showLoading('Deleting evidence...');
            const response = await this.makeAuthenticatedRequest(`${this.apiBase}/projects/${this.currentProject.id}/evidence/${evidenceId}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({ error: 'Unknown error' }));
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showAlert('Evidence deleted successfully', 'success');
                // Reload project data to reflect the deletion
                await this.openProject(this.currentProject.id);
            } else {
                throw new Error(data.error || 'Failed to delete evidence');
            }
        } catch (error) {
            console.error('Error deleting evidence:', error);
            if (error.message !== 'Authentication required') {
                this.showAlert('Error deleting evidence: ' + error.message, 'danger');
            }
        } finally {
            this.hideLoading();
        }
    }

    showTimelineSuggestions(suggestions) {
        // Create a modal to show suggestions
        const modalHtml = `
            <div class="modal fade" id="timelineSuggestionsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Timeline Entry Suggestions</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p class="text-muted">The AI has identified ${suggestions.length} potential timeline entries from the uploaded file. Select which ones to add:</p>
                            <div id="suggestionsList">
                                ${suggestions.map((suggestion, index) => `
                                    <div class="card mb-3">
                                        <div class="card-body">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" value="${index}" id="suggestion-${index}" checked>
                                                <label class="form-check-label" for="suggestion-${index}">
                                                    <div class="d-flex justify-content-between">
                                                        <strong>${new Date(suggestion.timestamp).toLocaleString()}</strong>
                                                        <span class="badge bg-${suggestion.type === 'event' ? 'danger' : suggestion.type === 'action' ? 'success' : 'info'}">${suggestion.type.toUpperCase()}</span>
                                                    </div>
                                                    <p class="mb-1">${this.escapeHtml(suggestion.description)}</p>
                                                    <small class="text-muted">
                                                        Confidence: ${suggestion.confidence || 'medium'}
                                                        ${suggestion.assumptions && suggestion.assumptions.length > 0 ? 
                                                            `<br>Assumptions: ${suggestion.assumptions.map(a => this.escapeHtml(a)).join(', ')}` : ''}
                                                        ${suggestion.personnel_involved && suggestion.personnel_involved.length > 0 ? 
                                                            `<br>Personnel: ${suggestion.personnel_involved.map(p => this.escapeHtml(p)).join(', ')}` : ''}
                                                    </small>
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="app.addSelectedTimelineEntries()">Add Selected Entries</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('timelineSuggestionsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Store suggestions for later use
        this.currentSuggestions = suggestions;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('timelineSuggestionsModal'));
        modal.show();
    }

    async addSelectedTimelineEntries() {
        const checkboxes = document.querySelectorAll('#suggestionsList input[type="checkbox"]:checked');
        const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.value));
        
        if (selectedIndices.length === 0) {
            this.showAlert('Please select at least one timeline entry', 'warning');
            return;
        }
        
        const selectedEntries = selectedIndices.map(index => this.currentSuggestions[index]);
        
        try {
            this.showLoading('Adding timeline entries...');
            
            const response = await this.makeAuthenticatedRequest(`${this.apiBase}/projects/${this.currentProject.id}/timeline/bulk`, {
                method: 'POST',
                body: JSON.stringify({ entries: selectedEntries })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('timelineSuggestionsModal')).hide();
                this.showAlert(`Successfully added ${data.created} timeline entries`, 'success');
                
                // Reload project data to get updated timeline (without showing loading overlay)
                await this.openProject(this.currentProject.id, false);
            } else {
                throw new Error(data.error || 'Failed to add timeline entries');
            }
        } catch (error) {
            console.error('Error adding timeline entries:', error);
            if (error.message !== 'Authentication required') {
                this.showAlert('Error adding timeline entries: ' + error.message, 'danger');
            }
            
            // Hide the modal even if there was an error
            const modal = bootstrap.Modal.getInstance(document.getElementById('timelineSuggestionsModal'));
            if (modal) {
                modal.hide();
            }
        } finally {
            this.hideLoading();
        }
    }

    showAddTimelineModal() {
        if (!this.currentProject) {
            this.showAlert('Please select a project first', 'warning');
            return;
        }
        
        const modal = new bootstrap.Modal(document.getElementById('addTimelineModal'));
        modal.show();
    }

    async addTimelineEntry() {
        if (!this.currentProject) return;

        const entryData = {
            timestamp: document.getElementById('entryTimestamp').value,
            type: document.getElementById('entryType').value,
            description: document.getElementById('entryDescription').value,
            confidence_level: document.getElementById('entryConfidence').value,
            is_initiating_event: document.getElementById('isInitiatingEvent').checked,
            assumptions: document.getElementById('entryAssumptions').value.split('\n').filter(a => a.trim())
        };

        if (!entryData.timestamp || !entryData.type || !entryData.description) {
            this.showAlert('Please fill in all required fields', 'warning');
            return;
        }

        try {
            const isEditing = !!this.editingTimelineId;
            this.showLoading(isEditing ? 'Updating timeline entry...' : 'Adding timeline entry...');
            
            const url = isEditing 
                ? `${this.apiBase}/projects/${this.currentProject.id}/timeline/${this.editingTimelineId}`
                : `${this.apiBase}/projects/${this.currentProject.id}/timeline`;
            
            const response = await this.makeAuthenticatedRequest(url, {
                method: isEditing ? 'PUT' : 'POST',
                body: JSON.stringify(entryData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('addTimelineModal')).hide();
                document.getElementById('addTimelineForm').reset();
                this.editingTimelineId = null; // Clear editing state
                this.showAlert(`Timeline entry ${isEditing ? 'updated' : 'added'} successfully`, 'success');
                
                // Reload project data to get updated timeline
                await this.openProject(this.currentProject.id);
                this.loadTimeline();
            } else {
                throw new Error(data.error || `Failed to ${isEditing ? 'update' : 'add'} timeline entry`);
            }
        } catch (error) {
            console.error('Error with timeline entry:', error);
            if (error.message !== 'Authentication required') {
                this.showAlert('Error: ' + error.message, 'danger');
            }
        } finally {
            this.hideLoading();
        }
    }

    loadTimeline() {
        console.log('Loading timeline for project:', this.currentProject?.id);
        console.log('Timeline data:', this.currentProject?.timeline);
        
        if (!this.currentProject || !this.currentProject.timeline) {
            console.log('No project or timeline data available');
            return;
        }

        const timelineList = document.getElementById('timelineList');
        if (!timelineList) {
            console.log('Timeline list element not found');
            return;
        }
        
        const timeline = this.currentProject.timeline;
        console.log(`Found ${timeline.length} timeline entries`);

        if (timeline.length === 0) {
            timelineList.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-history fa-2x mb-3"></i>
                    <p>No timeline entries yet. Add your first entry to get started.</p>
                </div>
            `;
            return;
        }

        // Sort timeline by timestamp
        const sortedTimeline = timeline.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        timelineList.innerHTML = sortedTimeline.map(entry => `
            <div class="timeline-entry ${entry.type}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-0">
                        <i class="fas fa-flag me-2"></i>
                        ${new Date(entry.timestamp).toLocaleString()}
                        ${entry.is_initiating_event ? '<span class="badge bg-danger ms-2">Initiating Event</span>' : ''}
                    </h6>
                    <div>
                        <span class="badge bg-secondary">${entry.type.toUpperCase()}</span>
                        <button class="btn btn-sm btn-outline-primary ms-2 btn-edit-timeline" data-entry-id="${entry.id}">
                            <i class="fas fa-pencil-alt"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger ms-2 btn-delete-timeline" data-entry-id="${entry.id}">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
                <p class="mb-2">${this.escapeHtml(entry.description)}</p>
                ${entry.assumptions && entry.assumptions.length > 0 ? `
                    <div class="small text-muted">
                        <strong>Assumptions:</strong> ${entry.assumptions.map(a => this.escapeHtml(a)).join(', ')}
                    </div>
                ` : ''}
                <div class="small text-muted">
                    Confidence: ${entry.confidence_level} | Evidence items: ${entry.evidence_ids ? entry.evidence_ids.length : 0}
                </div>
            </div>
        `).join('');

        // Add event listeners for timeline action buttons
        timelineList.querySelectorAll('.btn-edit-timeline').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const entryId = btn.dataset.entryId;
                this.editTimelineEntry(entryId);
            });
        });

        timelineList.querySelectorAll('.btn-delete-timeline').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const entryId = btn.dataset.entryId;
                this.deleteTimelineEntry(entryId);
            });
        });
    }

    async editTimelineEntry(entryId) {
        const entry = this.currentProject.timeline.find(e => e.id === entryId);
        if (!entry) return;

        // Populate modal with existing data
        document.getElementById('entryTimestamp').value = entry.timestamp.slice(0, 16); // Format for datetime-local
        document.getElementById('entryType').value = entry.type;
        document.getElementById('entryDescription').value = entry.description;
        document.getElementById('entryConfidence').value = entry.confidence_level || 'medium';
        document.getElementById('isInitiatingEvent').checked = entry.is_initiating_event || false;
        document.getElementById('entryAssumptions').value = (entry.assumptions || []).join('\n');

        // Store the entry ID for update
        this.editingTimelineId = entryId;

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('addTimelineModal'));
        modal.show();
    }

    async deleteTimelineEntry(entryId) {
        if (!confirm('Are you sure you want to delete this timeline entry?')) {
            return;
        }

        try {
            this.showLoading('Deleting timeline entry...');
            
            const response = await this.makeAuthenticatedRequest(`${this.apiBase}/projects/${this.currentProject.id}/timeline/${entryId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showAlert('Timeline entry deleted successfully', 'success');
                
                // Reload project data to get updated timeline
                await this.openProject(this.currentProject.id);
                this.loadTimeline();
            } else {
                throw new Error(data.error || 'Failed to delete timeline entry');
            }
        } catch (error) {
            console.error('Error deleting timeline entry:', error);
            if (error.message !== 'Authentication required') {
                this.showAlert('Error deleting timeline entry: ' + error.message, 'danger');
            }
        } finally {
            this.hideLoading();
        }
    }

    async runCausalAnalysis() {
        if (!this.currentProject) {
            this.showAlert('Please select a project first', 'warning');
            return;
        }

        if (!this.currentProject.timeline || this.currentProject.timeline.length === 0) {
            this.showAlert('Please add timeline entries before running causal analysis', 'warning');
            return;
        }

        try {
            this.showLoading('Running causal analysis...');
            
            const response = await this.makeAuthenticatedRequest(`${this.apiBase}/projects/${this.currentProject.id}/causal-analysis`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showAlert('Causal analysis completed successfully', 'success');
                
                // Reload project data to get updated causal factors
                await this.openProject(this.currentProject.id);
                this.loadAnalysis();
            } else {
                throw new Error(data.error || 'Failed to run causal analysis');
            }
        } catch (error) {
            console.error('Error running causal analysis:', error);
            if (error.message !== 'Authentication required') {
                this.showAlert('Error running causal analysis: ' + error.message, 'danger');
            }
        } finally {
            this.hideLoading();
        }
    }

    loadAnalysis() {
        if (!this.currentProject || !this.currentProject.causal_factors) return;

        const causalFactorsList = document.getElementById('causalFactorsList');
        const factors = this.currentProject.causal_factors;

        if (factors.length === 0) {
            causalFactorsList.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-atom fa-2x mb-3"></i>
                    <p>No causal analysis performed yet. Run analysis to identify contributing factors.</p>
                </div>
            `;
            return;
        }

        causalFactorsList.innerHTML = factors.map(factor => `
            <div class="causal-factor ${factor.category}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-0">${factor.title || 'Untitled Factor'}</h6>
                    <span class="badge bg-primary">${factor.category.toUpperCase()}</span>
                </div>
                <p class="mb-2">${factor.description}</p>
                ${factor.analysis_text ? `
                    <div class="small">
                        <strong>Analysis:</strong> ${factor.analysis_text}
                    </div>
                ` : ''}
                <div class="small text-muted mt-2">
                    Evidence support: ${factor.evidence_support ? factor.evidence_support.length : 0} items
                </div>
            </div>
        `).join('');
    }

    async generateROI() {
        if (!this.currentProject) {
            this.showAlert('Please select a project first', 'warning');
            return;
        }

        try {
            this.showLoading('Generating ROI document...');
            
            const response = await this.makeAuthenticatedRequest(`${this.apiBase}/projects/${this.currentProject.id}/generate-roi`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showAlert('ROI document generated successfully', 'success');
                
                // Add download link
                const generatedDocs = document.getElementById('generatedDocs');
                if (generatedDocs) {
                    generatedDocs.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6>ROI Document</h6>
                                <small class="text-muted">Generated: ${new Date().toLocaleString()}</small>
                            </div>
                            <a href="${data.download_url}" class="btn btn-outline-primary btn-sm">
                                <i class="fas fa-download me-2"></i>Download
                            </a>
                        </div>
                    `;
                }
            } else {
                throw new Error(data.error || 'Failed to generate ROI');
            }
        } catch (error) {
            console.error('Error generating ROI:', error);
            if (error.message !== 'Authentication required') {
                this.showAlert('Error generating ROI: ' + error.message, 'danger');
            }
        } finally {
            this.hideLoading();
        }
    }

    checkReadiness() {
        if (!this.currentProject) return;

        const project = this.currentProject;
        
        // Check project info
        const hasProjectInfo = project.metadata.title && project.incident_info.incident_date;
        document.getElementById('checkProjectInfo').className = `badge ${hasProjectInfo ? 'bg-success' : 'bg-warning'}`;
        document.getElementById('checkProjectInfo').textContent = hasProjectInfo ? 'Complete' : 'Incomplete';

        // Check evidence
        const hasEvidence = project.evidence_library && project.evidence_library.length > 0;
        document.getElementById('checkEvidence').className = `badge ${hasEvidence ? 'bg-success' : 'bg-warning'}`;
        document.getElementById('checkEvidence').textContent = hasEvidence ? 'Complete' : 'Incomplete';

        // Check timeline
        const hasTimeline = project.timeline && project.timeline.length > 0;
        document.getElementById('checkTimeline').className = `badge ${hasTimeline ? 'bg-success' : 'bg-warning'}`;
        document.getElementById('checkTimeline').textContent = hasTimeline ? 'Complete' : 'Incomplete';

        // Check analysis
        const hasAnalysis = project.causal_factors && project.causal_factors.length > 0;
        document.getElementById('checkAnalysis').className = `badge ${hasAnalysis ? 'bg-success' : 'bg-warning'}`;
        document.getElementById('checkAnalysis').textContent = hasAnalysis ? 'Complete' : 'Incomplete';
    }

    showLoading(message = 'Loading...') {
        console.log('showLoading called with message:', message);
        document.getElementById('loadingMessage').textContent = message;
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = 'flex';
        console.log('Loading overlay shown');
    }

    hideLoading() {
        console.log('hideLoading called');
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = 'none';
        console.log('Loading overlay hidden');
    }

    showAlert(message, type = 'info') {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert-dismissible');
        existingAlerts.forEach(alert => alert.remove());

        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at top of content area
        const contentArea = document.querySelector('.content-area');
        contentArea.insertBefore(alertDiv, contentArea.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Global functions for onclick handlers
function showLoginForm() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
    document.getElementById('authMessage').style.display = 'none';
}

function showRegisterForm() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
    document.getElementById('authMessage').style.display = 'none';
}

function logout() {
    if (window.app) {
        app.logout();
    }
}

function skipAuth() {
    // Temporary demo mode - bypass authentication
    if (window.app) {
        app.currentUser = { username: 'demo-user', email: 'demo@example.com' };
        app.accessToken = 'demo-token';
        app.showMainApp();
    }
}

function showCreateProjectModal() {
    if (window.app) {
        app.showCreateProjectModal();
    } else {
        console.error('App not initialized yet');
    }
}

function showAddTimelineModal() {
    if (window.app) {
        app.showAddTimelineModal();
    } else {
        console.error('App not initialized yet');
    }
}

function runCausalAnalysis() {
    if (window.app) {
        app.runCausalAnalysis();
    } else {
        console.error('App not initialized yet');
    }
}

function generateROI() {
    if (window.app) {
        app.generateROI();
    } else {
        console.error('App not initialized yet');
    }
}

function checkReadiness() {
    if (window.app) {
        app.checkReadiness();
    } else {
        console.error('App not initialized yet');
    }
}

function closeProject() {
    if (window.app) {
        app.closeProject();
    } else {
        console.error('App not initialized yet');
    }
}

function handleFileUpload(event) {
    if (window.app) {
        app.handleFileUpload(event.target.files);
    } else {
        console.error('App not initialized yet');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing IOAgent...');
    try {
        window.app = new IOAgent();
        console.log('IOAgent initialized successfully');
    } catch (error) {
        console.error('Failed to initialize IOAgent:', error);
    }
});

// Fallback initialization if DOMContentLoaded already fired
if (document.readyState === 'loading') {
    // Document is still loading
    console.log('Document still loading, waiting for DOMContentLoaded...');
} else {
    // Document has already loaded
    console.log('Document already loaded, initializing IOAgent immediately...');
    try {
        window.app = new IOAgent();
        console.log('IOAgent initialized successfully (immediate)');
    } catch (error) {
        console.error('Failed to initialize IOAgent (immediate):', error);
    }
}

