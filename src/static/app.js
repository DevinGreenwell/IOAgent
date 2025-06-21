class IOAgent {
    constructor() {
        this.currentProject = null;
        
        // Configure API base URL based on environment
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // Local development
            this.apiBase = 'http://localhost:5000/api';
        } else {
            // Production - use same origin (whether on Render or other hosting)
            this.apiBase = window.location.origin + '/api';
        }
        
        // File upload configuration
        this.maxFileSize = 16 * 1024 * 1024; // 16MB
        this.allowedFileTypes = {
            'application/pdf': ['.pdf'],
            'application/msword': ['.doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'image/gif': ['.gif'],
            'video/mp4': ['.mp4'],
            'video/x-msvideo': ['.avi'],
            'audio/mpeg': ['.mp3'],
            'audio/wav': ['.wav']
        };
        
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
        const projectInfoForm = document.getElementById('projectInfoForm');
        if (projectInfoForm) {
            projectInfoForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveProjectInfo();
            });
        }

        // Create project form
        const createProjectForm = document.getElementById('createProjectForm');
        if (createProjectForm) {
            createProjectForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createProject();
            });
        }

        // Timeline form
        const addTimelineForm = document.getElementById('addTimelineForm');
        if (addTimelineForm) {
            addTimelineForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addTimelineEntry();
            });
        }

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
                const fileInput = document.getElementById('fileInput');
                if (fileInput) fileInput.click();
            });
        });
    }

    setupFileUpload() {
        const uploadArea = document.querySelector('.upload-area');
        const fileInput = document.getElementById('fileInput');

        if (!uploadArea || !fileInput) return;

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            });
        });

        // Handle dropped files
        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFileUpload(files);
        });
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    showSection(sectionName) {
        try {
            console.log('Showing section:', sectionName);
            
            // Hide all sections
            document.querySelectorAll('.content-section').forEach(section => {
                section.style.display = 'none';
            });

            // Show selected section
            const targetSection = document.getElementById(`${sectionName}-section`);
            if (targetSection) {
                targetSection.style.display = 'block';
            } else {
                console.error('Section not found:', `${sectionName}-section`);
                return;
            }

            // Update navigation
            document.querySelectorAll('#mainNav .nav-link').forEach(link => {
                link.classList.remove('active');
            });
            
            const activeLink = document.querySelector(`[data-section="${sectionName}"]`);
            if (activeLink) {
                activeLink.classList.add('active');
            }

            // Load section data
            this.loadSectionData(sectionName);
        } catch (error) {
            console.error('Error in showSection:', error);
            this.showAlert('Error loading section', 'danger');
        }
    }

    loadSectionData(sectionName) {
        if (!this.currentProject && sectionName !== 'dashboard') {
            this.showAlert('Please select a project first', 'warning');
            this.showSection('dashboard');
            return;
        }

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
            this.showAlert('Error loading projects: ' + error.message, 'danger');
        }
    }

    displayProjects(projects) {
        const projectsList = document.getElementById('projectsList');
        
        if (!projectsList) return;
        
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
        const totalProjectsEl = document.getElementById('totalProjects');
        const draftProjectsEl = document.getElementById('draftProjects');
        const completeProjectsEl = document.getElementById('completeProjects');
        
        if (totalProjectsEl) totalProjectsEl.textContent = projects.length;
        if (draftProjectsEl) draftProjectsEl.textContent = projects.filter(p => p.status === 'draft').length;
        if (completeProjectsEl) completeProjectsEl.textContent = projects.filter(p => p.status === 'complete').length;
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
        
        const titleInput = document.getElementById('newProjectTitle');
        const officerInput = document.getElementById('newInvestigatingOfficer');
        
        if (!titleInput || !officerInput) {
            this.showAlert('Form elements not found', 'danger');
            this.creatingProject = false;
            return;
        }
        
        const title = titleInput.value.trim();
        const investigatingOfficer = officerInput.value.trim();

        if (!title) {
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
                    title: title,
                    investigating_officer: investigatingOfficer
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                const modalEl = document.getElementById('createProjectModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
                
                document.getElementById('createProjectForm').reset();
                this.showAlert('Project created successfully', 'success');
                
                // Reload dashboard and open the new project
                await this.loadDashboard();
                this.openProject(data.project.id);
            } else {
                throw new Error(data.error || 'Failed to create project');
            }
        } catch (error) {
            console.error('Error creating project:', error);
            this.showAlert('Error creating project: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
            this.creatingProject = false;
        }
    }

    async openProject(projectId) {
        try {
            console.log('Opening project:', projectId);
            this.showLoading('Loading project...');
            
            const response = await fetch(`${this.apiBase}/projects/${projectId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();

            if (data.success) {
                this.currentProject = data.project;
                this.updateCurrentProjectDisplay();
                this.showSection('project-info');
                this.showAlert('Project loaded successfully', 'success');
            } else {
                throw new Error(data.error || 'Failed to load project');
            }
        } catch (error) {
            console.error('Error loading project:', error);
            this.showAlert('Error loading project: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    updateCurrentProjectDisplay() {
        const currentProjectDiv = document.getElementById('currentProject');
        const projectTitleEl = document.getElementById('projectTitle');
        const projectStatusEl = document.getElementById('projectStatus');
        
        if (this.currentProject && currentProjectDiv) {
            currentProjectDiv.style.display = 'block';
            if (projectTitleEl) {
                projectTitleEl.textContent = this.currentProject.metadata?.title || 'Untitled Project';
            }
            if (projectStatusEl) {
                projectStatusEl.textContent = `Status: ${this.currentProject.metadata?.status || 'unknown'}`;
            }
        } else if (currentProjectDiv) {
            currentProjectDiv.style.display = 'none';
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
        const metadata = project.metadata || {};
        const incidentInfo = project.incident_info || {};
        
        // Update form fields with null checks
        this.setInputValue('projectTitleInput', metadata.title);
        this.setInputValue('investigatingOfficer', metadata.investigating_officer);
        this.setInputValue('incidentDate', incidentInfo.incident_date ? 
            new Date(incidentInfo.incident_date).toISOString().slice(0, 16) : '');
        this.setInputValue('incidentLocation', incidentInfo.location);
        this.setInputValue('incidentType', incidentInfo.incident_type);
        this.setInputValue('projectStatus', metadata.status || 'draft');
    }

    setInputValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.value = value || '';
        }
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
            
            const response = await fetch(`${this.apiBase}/projects/${this.currentProject.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
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
            this.showAlert('Error saving project: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    async handleFileUpload(files) {
        if (!this.currentProject) {
            this.showAlert('Please select a project first', 'warning');
            return;
        }

        const fileList = Array.from(files);
        let uploadedCount = 0;
        let failedCount = 0;
        
        this.showLoading(`Uploading ${fileList.length} file(s)...`);
        
        for (const file of fileList) {
            const result = await this.uploadFile(file);
            if (result.success) {
                uploadedCount++;
            } else {
                failedCount++;
            }
        }
        
        this.hideLoading();
        
        if (uploadedCount > 0) {
            this.showAlert(`Successfully uploaded ${uploadedCount} file(s)${failedCount > 0 ? `, ${failedCount} failed` : ''}`, 
                failedCount > 0 ? 'warning' : 'success');
            this.loadEvidence();
        } else if (failedCount > 0) {
            this.showAlert(`Failed to upload ${failedCount} file(s)`, 'danger');
        }
    }

    validateFile(file) {
        // Check file size
        if (file.size > this.maxFileSize) {
            return {
                valid: false,
                error: `File "${file.name}" is too large. Maximum size is ${this.formatFileSize(this.maxFileSize)}.`
            };
        }

        // Check file type
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        let isValidType = false;

        // Check by MIME type
        for (const [mimeType, extensions] of Object.entries(this.allowedFileTypes)) {
            if (file.type === mimeType || extensions.includes(fileExtension)) {
                isValidType = true;
                break;
            }
        }

        if (!isValidType) {
            return {
                valid: false,
                error: `File type not supported: "${file.name}". Allowed types: PDF, Word documents, images, videos, and audio files.`
            };
        }

        return { valid: true };
    }

    async uploadFile(file) {
        // Validate file before upload
        const validation = this.validateFile(file);
        if (!validation.valid) {
            this.showAlert(validation.error, 'danger');
            return { success: false, error: validation.error };
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('description', `Uploaded file: ${file.name}`);
        formData.append('type', file.type);
        formData.append('source', 'user_upload');

        try {
            const response = await fetch(`${this.apiBase}/projects/${this.currentProject.id}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                return { success: true, data: data };
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            this.showAlert(`Error uploading "${file.name}": ${error.message}`, 'danger');
            return { success: false, error: error.message };
        }
    }

    loadEvidence() {
        if (!this.currentProject || !this.currentProject.evidence_library) return;

        const evidenceList = document.getElementById('evidenceList');
        if (!evidenceList) return;
        
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
                        <button class="btn btn-sm btn-outline-danger ms-2" onclick="app.deleteEvidence('${item.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    getFileIcon(fileType) {
        if (!fileType) return 'fas fa-file';
        
        if (fileType.includes('pdf')) return 'fas fa-file-pdf';
        if (fileType.includes('word') || fileType.includes('document')) return 'fas fa-file-word';
        if (fileType.includes('image')) return 'fas fa-file-image';
        if (fileType.includes('video')) return 'fas fa-file-video';
        if (fileType.includes('audio')) return 'fas fa-file-audio';
        
        return 'fas fa-file';
    }

    async deleteEvidence(evidenceId) {
        if (!confirm('Are you sure you want to delete this evidence?')) {
            return;
        }

        try {
            this.showLoading('Deleting evidence...');
            
            const response = await fetch(`${this.apiBase}/projects/${this.currentProject.id}/evidence/${evidenceId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showAlert('Evidence deleted successfully', 'success');
                // Reload project to get updated evidence list
                await this.openProject(this.currentProject.id);
                this.loadEvidence();
            } else {
                throw new Error(data.error || 'Failed to delete evidence');
            }
        } catch (error) {
            console.error('Error deleting evidence:', error);
            this.showAlert('Error deleting evidence: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    showAddTimelineModal() {
        if (!this.currentProject) {
            this.showAlert('Please select a project first', 'warning');
            return;
        }
        
        // Reset the modal for adding new entry
        this.resetTimelineModal();
        document.getElementById('addTimelineForm').reset();
        
        const modal = new bootstrap.Modal(document.getElementById('addTimelineModal'));
        modal.show();
    }

    async addTimelineEntry() {
        if (!this.currentProject) return;

        // Check if we're editing an existing entry
        if (this.editingEntryId) {
            return this.updateTimelineEntry();
        }

        const timestampEl = document.getElementById('entryTimestamp');
        const typeEl = document.getElementById('entryType');
        const descriptionEl = document.getElementById('entryDescription');
        const confidenceEl = document.getElementById('entryConfidence');
        const initiatingEl = document.getElementById('isInitiatingEvent');
        const assumptionsEl = document.getElementById('entryAssumptions');

        if (!timestampEl || !typeEl || !descriptionEl) {
            this.showAlert('Form elements not found', 'danger');
            return;
        }

        const entryData = {
            timestamp: timestampEl.value,
            type: typeEl.value,
            description: descriptionEl.value,
            confidence_level: confidenceEl?.value || 'medium',
            is_initiating_event: initiatingEl?.checked || false,
            assumptions: assumptionsEl?.value.split('\n').filter(a => a.trim()) || []
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

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                const modalEl = document.getElementById('addTimelineModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
                
                document.getElementById('addTimelineForm').reset();
                this.showAlert('Timeline entry added successfully', 'success');
                
                // Reload project data to get updated timeline
                await this.openProject(this.currentProject.id);
                this.loadTimeline();
            } else {
                throw new Error(data.error || 'Failed to add timeline entry');
            }
        } catch (error) {
            console.error('Error adding timeline entry:', error);
            this.showAlert('Error adding timeline entry: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    loadTimeline() {
        if (!this.currentProject || !this.currentProject.timeline) return;

        const timelineList = document.getElementById('timelineList');
        if (!timelineList) return;
        
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
        const sortedTimeline = [...timeline].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        timelineList.innerHTML = sortedTimeline.map(entry => `
            <div class="timeline-entry ${entry.type}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-0">
                        ${new Date(entry.timestamp).toLocaleString()}
                        ${entry.is_initiating_event ? '<span class="badge bg-danger ms-2">Initiating Event</span>' : ''}
                    </h6>
                    <div>
                        <span class="badge bg-secondary">${entry.type.toUpperCase()}</span>
                        <button class="btn btn-sm btn-outline-primary ms-2" onclick="app.editTimelineEntry('${entry.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger ms-2" onclick="app.deleteTimelineEntry('${entry.id}')">
                            <i class="fas fa-trash"></i>
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
    }

    async deleteTimelineEntry(entryId) {
        if (!confirm('Are you sure you want to delete this timeline entry?')) {
            return;
        }

        try {
            this.showLoading('Deleting timeline entry...');
            
            const response = await fetch(`${this.apiBase}/projects/${this.currentProject.id}/timeline/${entryId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showAlert('Timeline entry deleted successfully', 'success');
                await this.openProject(this.currentProject.id);
                this.loadTimeline();
            } else {
                throw new Error(data.error || 'Failed to delete timeline entry');
            }
        } catch (error) {
            console.error('Error deleting timeline entry:', error);
            this.showAlert('Error deleting timeline entry: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    editTimelineEntry(entryId) {
        // Find the entry to edit
        const entry = this.currentProject.timeline.find(e => e.id === entryId);
        if (!entry) {
            this.showAlert('Timeline entry not found', 'danger');
            return;
        }

        // Populate the form with existing data
        document.getElementById('entryTimestamp').value = entry.timestamp ? 
            new Date(entry.timestamp).toISOString().slice(0, 16) : '';
        document.getElementById('entryType').value = entry.type || '';
        document.getElementById('entryDescription').value = entry.description || '';
        document.getElementById('entryConfidence').value = entry.confidence_level || 'medium';
        document.getElementById('isInitiatingEvent').checked = entry.is_initiating_event || false;
        document.getElementById('entryAssumptions').value = entry.assumptions ? 
            entry.assumptions.join('\n') : '';

        // Store the entry ID for updating
        this.editingEntryId = entryId;

        // Change modal title and button text
        const modalTitle = document.querySelector('#addTimelineModal .modal-title');
        const submitBtn = document.querySelector('#addTimelineModal .btn-primary');
        if (modalTitle) modalTitle.textContent = 'Edit Timeline Entry';
        if (submitBtn) submitBtn.textContent = 'Update Entry';

        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('addTimelineModal'));
        modal.show();
    }

    async updateTimelineEntry() {
        if (!this.currentProject || !this.editingEntryId) return;

        const timestampEl = document.getElementById('entryTimestamp');
        const typeEl = document.getElementById('entryType');
        const descriptionEl = document.getElementById('entryDescription');
        const confidenceEl = document.getElementById('entryConfidence');
        const initiatingEl = document.getElementById('isInitiatingEvent');
        const assumptionsEl = document.getElementById('entryAssumptions');

        if (!timestampEl || !typeEl || !descriptionEl) {
            this.showAlert('Form elements not found', 'danger');
            return;
        }

        const entryData = {
            timestamp: timestampEl.value,
            type: typeEl.value,
            description: descriptionEl.value,
            confidence_level: confidenceEl?.value || 'medium',
            is_initiating_event: initiatingEl?.checked || false,
            assumptions: assumptionsEl?.value.split('\n').filter(a => a.trim()) || []
        };

        if (!entryData.timestamp || !entryData.type || !entryData.description) {
            this.showAlert('Please fill in all required fields', 'warning');
            return;
        }

        try {
            this.showLoading('Updating timeline entry...');
            
            const response = await fetch(`${this.apiBase}/projects/${this.currentProject.id}/timeline/${this.editingEntryId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(entryData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                const modalEl = document.getElementById('addTimelineModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
                
                // Reset form and editing state
                document.getElementById('addTimelineForm').reset();
                this.resetTimelineModal();
                this.editingEntryId = null;
                
                this.showAlert('Timeline entry updated successfully', 'success');
                
                // Reload project data to get updated timeline
                await this.openProject(this.currentProject.id);
                this.loadTimeline();
            } else {
                throw new Error(data.error || 'Failed to update timeline entry');
            }
        } catch (error) {
            console.error('Error updating timeline entry:', error);
            this.showAlert('Error updating timeline entry: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    resetTimelineModal() {
        // Reset modal title and button text
        const modalTitle = document.querySelector('#addTimelineModal .modal-title');
        const submitBtn = document.querySelector('#addTimelineModal .btn-primary');
        if (modalTitle) modalTitle.textContent = 'Add Timeline Entry';
        if (submitBtn) submitBtn.textContent = 'Add Entry';
        this.editingEntryId = null;
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
            this.showAlert('Error running causal analysis: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    loadAnalysis() {
        if (!this.currentProject || !this.currentProject.causal_factors) return;

        const causalFactorsList = document.getElementById('causalFactorsList');
        if (!causalFactorsList) return;
        
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
                    <h6 class="mb-0">${this.escapeHtml(factor.title || 'Untitled Factor')}</h6>
                    <span class="badge bg-primary">${factor.category.toUpperCase()}</span>
                </div>
                <p class="mb-2">${this.escapeHtml(factor.description)}</p>
                ${factor.analysis_text ? `
                    <div class="small">
                        <strong>Analysis:</strong> ${this.escapeHtml(factor.analysis_text)}
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

        // Check readiness first
        const isReady = this.checkReadiness(true);
        if (!isReady) {
            this.showAlert('Please complete all required sections before generating ROI', 'warning');
            return;
        }

        try {
            this.showLoading('Generating ROI document...');
            
            const response = await fetch(`${this.apiBase}/projects/${this.currentProject.id}/generate-roi`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.showAlert('ROI document generated successfully', 'success');
                
                // Update generated docs display
                const generatedDocs = document.getElementById('generatedDocs');
                if (generatedDocs) {
                    generatedDocs.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center p-3 border rounded">
                            <div>
                                <h6 class="mb-1">ROI Document</h6>
                                <small class="text-muted">Generated: ${new Date().toLocaleString()}</small>
                            </div>
                            <a href="${data.download_url}" class="btn btn-outline-primary btn-sm" download>
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
            this.showAlert('Error generating ROI: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    checkReadiness(returnResult = false) {
        if (!this.currentProject) {
            if (returnResult) return false;
            return;
        }

        const project = this.currentProject;
        let allReady = true;
        
        // Check project info
        const hasProjectInfo = project.metadata?.title && project.incident_info?.incident_date;
        this.updateReadinessCheck('checkProjectInfo', hasProjectInfo);
        if (!hasProjectInfo) allReady = false;

        // Check evidence
        const hasEvidence = project.evidence_library && project.evidence_library.length > 0;
        this.updateReadinessCheck('checkEvidence', hasEvidence);
        if (!hasEvidence) allReady = false;

        // Check timeline
        const hasTimeline = project.timeline && project.timeline.length > 0;
        this.updateReadinessCheck('checkTimeline', hasTimeline);
        if (!hasTimeline) allReady = false;

        // Check analysis
        const hasAnalysis = project.causal_factors && project.causal_factors.length > 0;
        this.updateReadinessCheck('checkAnalysis', hasAnalysis);
        if (!hasAnalysis) allReady = false;

        if (returnResult) {
            return allReady;
        }
    }

    updateReadinessCheck(elementId, isComplete) {
        const element = document.getElementById(elementId);
        if (element) {
            element.className = `badge ${isComplete ? 'bg-success' : 'bg-warning'}`;
            element.textContent = isComplete ? 'Complete' : 'Incomplete';
        }
    }

    showLoading(message = 'Loading...') {
        const loadingMessage = document.getElementById('loadingMessage');
        if (loadingMessage) {
            loadingMessage.textContent = message;
        }
        
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'flex';
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
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
            ${this.escapeHtml(message)}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at top of content area
        const contentArea = document.querySelector('.content-area');
        if (contentArea) {
            contentArea.insertBefore(alertDiv, contentArea.firstChild);
        }

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Utility functions
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Global functions for onclick handlers (maintain backwards compatibility)
window.showCreateProjectModal = function() {
    if (window.app) {
        app.showCreateProjectModal();
    }
};

window.showAddTimelineModal = function() {
    if (window.app) {
        app.showAddTimelineModal();
    }
};

window.runCausalAnalysis = function() {
    if (window.app) {
        app.runCausalAnalysis();
    }
};

window.generateROI = function() {
    if (window.app) {
        app.generateROI();
    }
};

window.checkReadiness = function() {
    if (window.app) {
        app.checkReadiness();
    }
};

window.closeProject = function() {
    if (window.app) {
        app.closeProject();
    }
};

window.handleFileUpload = function(event) {
    if (window.app && event.target.files) {
        app.handleFileUpload(event.target.files);
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new IOAgent();
    console.log('IOAgent initialized');
});