class IOAgent {
    constructor() {
        this.currentProject = null;
        
        // Configure API base URL based on environment
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // Local development
            this.apiBase = 'http://localhost:5000/api';
        } else if (window.location.hostname.includes('github.io') || window.location.hostname.includes('netlify') || window.location.hostname.includes('vercel')) {
            // Static hosting - point to your deployed backend
            this.apiBase = 'https://ioagent.onrender.com/api';
        } else if (window.location.hostname.includes('onrender.com')) {
            // Running on Render - use same origin
            this.apiBase = window.location.origin + '/api';
        } else {
            // Default fallback to hosted backend
            this.apiBase = 'https://ioagent.onrender.com/api';
        }
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboard();
        this.setupFileUpload();
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
            const response = await fetch(`${this.apiBase}/projects`);
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
            
            const response = await fetch(`${this.apiBase}/projects`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
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
        
        // Dispose of any existing modal instance first
        const modalElement = document.getElementById('loadingModal');
        const existingModal = bootstrap.Modal.getInstance(modalElement);
        if (existingModal) {
            console.log('Disposing existing modal instance');
            existingModal.dispose();
        }
        
        const modal = new bootstrap.Modal(modalElement);
        console.log('Showing new modal instance');
        modal.show();
    }

    hideLoading() {
        try {
            console.log('hideLoading called');
            const modalElement = document.getElementById('loadingModal');
            const modal = bootstrap.Modal.getInstance(modalElement);
            
            if (modal) {
                console.log('Found modal instance, calling hide()');
                modal.hide();
                
                // Add event listener to clean up after modal is hidden
                modalElement.addEventListener('hidden.bs.modal', function cleanup() {
                    console.log('Modal hidden event fired, disposing modal');
                    modal.dispose();
                    modalElement.removeEventListener('hidden.bs.modal', cleanup);
                }, { once: true });
                
                // Fallback: force cleanup after 2 seconds if modal doesn't hide properly
                setTimeout(() => {
                    if (modalElement.classList.contains('show') || document.body.classList.contains('modal-open')) {
                        console.log('Modal did not hide properly, forcing cleanup');
                        this.forceCleanupModal();
                    }
                }, 2000);
            } else {
                console.log('No modal instance found, manual cleanup');
                // If no modal instance, remove backdrop and classes manually
                modalElement.classList.remove('show');
                modalElement.style.display = 'none';
                modalElement.setAttribute('aria-hidden', 'true');
                modalElement.removeAttribute('aria-modal');
                document.body.classList.remove('modal-open');
                
                const backdrops = document.querySelectorAll('.modal-backdrop');
                console.log('Removing', backdrops.length, 'modal backdrops');
                backdrops.forEach(backdrop => backdrop.remove());
            }
        } catch (error) {
            console.error('Error hiding loading modal:', error);
            // Force remove modal elements if there's an error
            this.forceCleanupModal();
        }
    }

    forceCleanupModal() {
        console.log('Force cleanup modal');
        const modalElement = document.getElementById('loadingModal');
        
        // Remove all modal classes and attributes
        modalElement.classList.remove('show', 'fade');
        modalElement.style.display = 'none';
        modalElement.setAttribute('aria-hidden', 'true');
        modalElement.removeAttribute('aria-modal');
        
        // Remove body classes
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('overflow');
        document.body.style.removeProperty('padding-right');
        
        // Remove all backdrops
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        // Dispose any modal instances
        try {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.dispose();
            }
        } catch (e) {
            console.log('Could not dispose modal:', e);
        }
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

