class IOAgent {
    constructor() {
        this.currentProject = null;
        this.currentUser = null;
        this.accessToken = null;
        
        // Configure API base URL based on environment
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // Local development
            this.apiBase = 'http://localhost:5000/api';
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
        
        if (token && user) {
            this.accessToken = token;
            this.currentUser = JSON.parse(user);
            console.log('Found existing auth, showing main app');
            this.showMainApp();
        } else {
            console.log('No existing auth, showing login');
            this.showAuthOverlay();
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
        document.getElementById('currentUser').textContent = this.currentUser.username;
        document.getElementById('userInfo').style.display = 'inline';
        document.getElementById('logoutBtn').style.display = 'inline-block';
        document.getElementById('appTitle').style.display = 'none';
        
        // Initialize main app
        this.setupEventListeners();
        this.loadDashboard();
        this.setupFileUpload();
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
                this.showAuthMessage(data.error || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showAuthMessage('Connection error. Please try again.', 'error');
        }
    }

    async register() {
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (password !== confirmPassword) {
            this.showAuthMessage('Passwords do not match', 'error');
            return;
        }

        this.showAuthMessage('Creating account...', 'info');

        try {
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

    logout() {
        // Clear stored data
        localStorage.removeItem('ioagent_token');
        localStorage.removeItem('ioagent_user');
        
        // Reset app state
        this.accessToken = null;
        this.currentUser = null;
        this.currentProject = null;
        
        // Show auth overlay
        this.showAuthOverlay();
        this.showAuthMessage('Logged out successfully', 'success');
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
        // Demo mode: show alert instead of making real API calls
        if (this.accessToken === 'demo-token') {
            console.log('Demo mode: API call to', url);
            this.showAlert('Demo Mode: API calls are disabled. Please login with real credentials to access backend features.', 'info');
            return { 
                json: () => Promise.resolve({ 
                    success: false, 
                    error: 'Demo mode - authentication required for backend access',
                    projects: []
                })
            };
        }

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        const response = await fetch(url, {
            ...options,
            headers
        });

        // Handle token expiration
        if (response.status === 401) {
            this.logout();
            throw new Error('Session expired. Please login again.');
        }

        return response;
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('#mainNav .nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.closest('.nav-link').dataset.section;
                this.showSection(section);
            });
        });

        // Project info form
        document.getElementById('projectInfoForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProjectInfo();
        });

        // Create project form
        document.getElementById('createProjectForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createProject();
        });

        // Timeline form
        document.getElementById('addTimelineForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addTimelineEntry();
        });

        // Button event listeners to replace onclick attributes
        this.setupButtonListeners();
    }

    setupButtonListeners() {
        // Find buttons by their onclick attribute text and add proper event listeners
        const buttons = document.querySelectorAll('button[onclick]');
        buttons.forEach(button => {
            const onclickText = button.getAttribute('onclick');
            button.removeAttribute('onclick'); // Remove the onclick attribute
            
            if (onclickText.includes('showCreateProjectModal')) {
                button.addEventListener('click', () => this.showCreateProjectModal());
            } else if (onclickText.includes('showAddTimelineModal')) {
                button.addEventListener('click', () => this.showAddTimelineModal());
            } else if (onclickText.includes('runCausalAnalysis')) {
                button.addEventListener('click', () => this.runCausalAnalysis());
            } else if (onclickText.includes('generateROI')) {
                button.addEventListener('click', () => this.generateROI());
            } else if (onclickText.includes('checkReadiness')) {
                button.addEventListener('click', () => this.checkReadiness());
            } else if (onclickText.includes('closeProject')) {
                button.addEventListener('click', () => this.closeProject());
            }
        });

        // File input
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (event) => {
                this.handleFileUpload(event.target.files);
            });
        }

        // Upload area clicks
        const uploadAreas = document.querySelectorAll('.upload-area');
        uploadAreas.forEach(area => {
            area.addEventListener('click', () => {
                document.getElementById('fileInput').click();
            });
        });
    }

    setupFileUpload() {
        const uploadArea = document.querySelector('.upload-area');
        const fileInput = document.getElementById('fileInput');

        // Drag and drop
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
            const data = await response.json();

            if (data.success) {
                this.displayProjects(data.projects);
                this.updateDashboardStats(data.projects);
            }
        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.showAlert('Error loading projects', 'danger');
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
            <div class="project-card" onclick="app.openProject('${project.id}')">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h5 class="mb-2">${project.title}</h5>
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
    }

    updateDashboardStats(projects) {
        document.getElementById('totalProjects').textContent = projects.length;
        document.getElementById('draftProjects').textContent = projects.filter(p => p.status === 'draft').length;
        document.getElementById('completeProjects').textContent = projects.filter(p => p.status === 'complete').length;
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
            this.showAlert('Error creating project', 'danger');
        } finally {
            this.hideLoading();
            this.creatingProject = false;
        }
    }

    async openProject(projectId) {
        try {
            console.log('Starting openProject for ID:', projectId);
            this.showLoading('Loading project...');
            
            console.log('Making fetch request to:', `${this.apiBase}/projects/${projectId}`);
            const response = await fetch(`${this.apiBase}/projects/${projectId}`);
            console.log('Fetch response received:', response.status, response.statusText);
            
            const data = await response.json();
            console.log('JSON data parsed:', data);

            if (data.success) {
                console.log('Setting currentProject');
                this.currentProject = data.project;
                console.log('Calling updateCurrentProjectDisplay');
                this.updateCurrentProjectDisplay();
                console.log('Calling showSection');
                this.showSection('project-info');
                console.log('Showing success alert');
                this.showAlert('Project loaded successfully', 'success');
            } else {
                console.log('API returned error:', data.error);
                this.showAlert(data.error || 'Failed to load project', 'danger');
            }
        } catch (error) {
            console.error('Error loading project:', error);
            this.showAlert('Error loading project: ' + error.message, 'danger');
        } finally {
            console.log('Hiding loading in finally block');
            this.hideLoading();
        }
    }

    updateCurrentProjectDisplay() {
        if (this.currentProject) {
            document.getElementById('currentProject').style.display = 'block';
            document.getElementById('projectTitle').textContent = this.currentProject.metadata.title;
            document.getElementById('projectStatus').textContent = `Status: ${this.currentProject.metadata.status}`;
        } else {
            document.getElementById('currentProject').style.display = 'none';
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
        if (!this.currentProject) return;

        const formData = {
            title: document.getElementById('projectTitleInput').value,
            investigating_officer: document.getElementById('investigatingOfficer').value,
            status: document.getElementById('projectStatus').value,
            incident_info: {
                incident_date: document.getElementById('incidentDate').value,
                location: document.getElementById('incidentLocation').value,
                incident_type: document.getElementById('incidentType').value
            }
        };

        try {
            this.showLoading('Saving project...');
            
            const response = await fetch(`${this.apiBase}/projects/${this.currentProject.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                this.currentProject = data.project;
                this.updateCurrentProjectDisplay();
                this.showAlert('Project information saved successfully', 'success');
            } else {
                this.showAlert(data.error || 'Failed to save project', 'danger');
            }
        } catch (error) {
            console.error('Error saving project:', error);
            this.showAlert('Error saving project', 'danger');
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
            this.showLoading(`Uploading ${file.name}...`);
            
            const response = await fetch(`${this.apiBase}/projects/${this.currentProject.id}/upload`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert(`File ${file.name} uploaded successfully`, 'success');
            } else {
                this.showAlert(`Failed to upload ${file.name}: ${data.error}`, 'danger');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            this.showAlert(`Error uploading ${file.name}`, 'danger');
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
                    <i class="fas fa-file fa-2x mb-3"></i>
                    <p>No evidence uploaded yet.</p>
                </div>
            `;
            return;
        }

        evidenceList.innerHTML = evidence.map(item => `
            <div class="evidence-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6><i class="fas fa-file me-2"></i>${item.filename}</h6>
                        <p class="mb-1">${item.description}</p>
                        <small class="text-muted">Type: ${item.type} | Source: ${item.source}</small>
                    </div>
                    <span class="badge bg-primary">${item.reliability}</span>
                </div>
            </div>
        `).join('');
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
            this.showLoading('Adding timeline entry...');
            
            const response = await fetch(`${this.apiBase}/projects/${this.currentProject.id}/timeline`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(entryData)
            });

            const data = await response.json();

            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('addTimelineModal')).hide();
                document.getElementById('addTimelineForm').reset();
                this.showAlert('Timeline entry added successfully', 'success');
                
                // Reload project data to get updated timeline
                const projectResponse = await fetch(`${this.apiBase}/projects/${this.currentProject.id}`);
                const projectData = await projectResponse.json();
                if (projectData.success) {
                    this.currentProject = projectData.project;
                    this.loadTimeline();
                }
            } else {
                this.showAlert(data.error || 'Failed to add timeline entry', 'danger');
            }
        } catch (error) {
            console.error('Error adding timeline entry:', error);
            this.showAlert('Error adding timeline entry', 'danger');
        } finally {
            this.hideLoading();
        }
    }

    loadTimeline() {
        if (!this.currentProject || !this.currentProject.timeline) return;

        const timelineList = document.getElementById('timelineList');
        const timeline = this.currentProject.timeline;

        if (timeline.length === 0) {
            timelineList.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-clock fa-2x mb-3"></i>
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
                        ${new Date(entry.timestamp).toLocaleString()}
                        ${entry.is_initiating_event ? '<span class="badge bg-danger ms-2">Initiating Event</span>' : ''}
                    </h6>
                    <span class="badge bg-secondary">${entry.type.toUpperCase()}</span>
                </div>
                <p class="mb-2">${entry.description}</p>
                ${entry.assumptions && entry.assumptions.length > 0 ? `
                    <div class="small text-muted">
                        <strong>Assumptions:</strong> ${entry.assumptions.join(', ')}
                    </div>
                ` : ''}
                <div class="small text-muted">
                    Confidence: ${entry.confidence_level} | Evidence items: ${entry.evidence_ids ? entry.evidence_ids.length : 0}
                </div>
            </div>
        `).join('');
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
            
            const response = await fetch(`${this.apiBase}/projects/${this.currentProject.id}/causal-analysis`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Causal analysis completed successfully', 'success');
                
                // Reload project data to get updated causal factors
                const projectResponse = await fetch(`${this.apiBase}/projects/${this.currentProject.id}`);
                const projectData = await projectResponse.json();
                if (projectData.success) {
                    this.currentProject = projectData.project;
                    this.loadAnalysis();
                }
            } else {
                this.showAlert(data.error || 'Failed to run causal analysis', 'danger');
            }
        } catch (error) {
            console.error('Error running causal analysis:', error);
            this.showAlert('Error running causal analysis', 'danger');
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
                    <i class="fas fa-search fa-2x mb-3"></i>
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
            
            const response = await fetch(`${this.apiBase}/projects/${this.currentProject.id}/generate-roi`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('ROI document generated successfully', 'success');
                
                // Add download link
                const generatedDocs = document.getElementById('generatedDocs');
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
            } else {
                this.showAlert(data.error || 'Failed to generate ROI', 'danger');
            }
        } catch (error) {
            console.error('Error generating ROI:', error);
            this.showAlert('Error generating ROI', 'danger');
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
    window.app = new IOAgent();
});

