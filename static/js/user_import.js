(function() {
    'use strict';

    const ImportWizard = {
        previewKey: null,
        validRows: [],
        skipRows: [],
        errorRows: [],
        importLogId: null,
        sendCredentialsEmail: false,

        init() {
            this.bindEvents();
        },

        bindEvents() {
            const modal = document.getElementById('importUsersModal');
            if (modal) {
                modal.addEventListener('show.bs.modal', () => this.resetWizard());
            }

            const dropZone = document.getElementById('dropZone');
            const fileInput = document.getElementById('importFile');
            const btnNext = document.getElementById('btnNextToPreview');
            const btnBack = document.getElementById('btnBackToUpload');
            const btnConfirm = document.getElementById('btnConfirmImport');
            const btnClose = document.getElementById('btnCloseAndRefresh');
            const removeFileBtn = document.getElementById('removeFile');

            if (dropZone && fileInput) {
                dropZone.addEventListener('click', () => fileInput.click());
                dropZone.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    dropZone.classList.add('border-primary');
                });
                dropZone.addEventListener('dragleave', () => {
                    dropZone.classList.remove('border-primary');
                });
                dropZone.addEventListener('drop', (e) => {
                    e.preventDefault();
                    dropZone.classList.remove('border-primary');
                    if (e.dataTransfer.files.length) {
                        fileInput.files = e.dataTransfer.files;
                        this.handleFileSelect(e.dataTransfer.files[0]);
                    }
                });
                fileInput.addEventListener('change', (e) => {
                    if (e.target.files.length) {
                        this.handleFileSelect(e.target.files[0]);
                    }
                });
            }

            if (removeFileBtn) {
                removeFileBtn.addEventListener('click', () => this.clearFile());
            }

            if (btnNext) {
                btnNext.addEventListener('click', () => this.uploadFile());
            }

            if (btnBack) {
                btnBack.addEventListener('click', () => this.goToStep(1));
            }

            if (btnConfirm) {
                btnConfirm.addEventListener('click', () => this.confirmImport());
            }

            if (btnClose) {
                btnClose.addEventListener('click', () => {
                    window.location.reload();
                });
            }
        },

        resetWizard() {
            this.previewKey = null;
            this.validRows = [];
            this.skipRows = [];
            this.errorRows = [];
            this.importLogId = null;

            const fileInput = document.getElementById('importFile');
            if (fileInput) fileInput.value = '';

            this.clearFile();
            this.goToStep(1);
            this.hideError();
        },

        handleFileSelect(file) {
            const fileName = document.getElementById('fileName');
            const fileInfo = document.getElementById('fileInfo');
            const btnNext = document.getElementById('btnNextToPreview');

            if (fileName && fileInfo) {
                fileName.textContent = file.name;
                fileInfo.classList.remove('d-none');
            }
            if (btnNext) {
                btnNext.disabled = false;
            }
        },

        clearFile() {
            const fileInput = document.getElementById('importFile');
            const fileInfo = document.getElementById('fileInfo');
            const btnNext = document.getElementById('btnNextToPreview');

            if (fileInput) fileInput.value = '';
            if (fileInfo) fileInfo.classList.add('d-none');
            if (btnNext) btnNext.disabled = true;
        },

        async uploadFile() {
            const form = document.getElementById('importUploadForm');
            const formData = new FormData(form);
            const spinner = document.getElementById('uploadSpinner');
            const btnNext = document.getElementById('btnNextToPreview');

            if (spinner) spinner.classList.remove('d-none');
            if (btnNext) btnNext.disabled = true;

            try {
                const response = await fetch('/admin/users/import/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': this.getCsrfToken(),
                    },
                });

                const data = await response.json();

                if (spinner) spinner.classList.add('d-none');
                if (btnNext) btnNext.disabled = false;

                if (data.success) {
                    this.previewKey = data.preview_key;
                    this.validRows = data.valid_rows || [];
                    this.skipRows = data.skip_rows || [];
                    this.errorRows = data.error_rows || [];
                    this.sendCredentialsEmail = formData.get('send_credentials_email') === 'on';

                    this.renderPreview();
                    this.goToStep(2);
                } else {
                    this.showError(data.errors ? data.errors.join(', ') : 'Gagal mengupload file.');
                }
            } catch (error) {
                if (spinner) spinner.classList.add('d-none');
                if (btnNext) btnNext.disabled = false;
                this.showError(`Terjadi kesalahan: ${error.message}`);
            }
        },

        renderPreview() {
            document.getElementById('validCount').textContent = this.validRows.length;
            document.getElementById('skipCount').textContent = this.skipRows.length;
            document.getElementById('errorCount').textContent = this.errorRows.length;
            document.getElementById('errorDetailCount').textContent = this.errorRows.length;

            const tbody = document.getElementById('previewTableBody');
            tbody.innerHTML = '';

            const allRows = [
                ...this.validRows.map(r => ({ ...r, status: 'valid' })),
                ...this.skipRows.map(r => ({ ...r, status: 'skip' })),
                ...this.errorRows.map(r => ({ ...r, status: 'error' })),
            ];

            const displayRows = allRows.slice(0, 20);

            displayRows.forEach((row, idx) => {
                const tr = document.createElement('tr');
                const badgeClass = row.status === 'valid' ? 'bg-success' : row.status === 'skip' ? 'bg-warning' : 'bg-danger';
                const statusText = row.status === 'valid' ? 'Valid' : row.status === 'skip' ? 'Skip' : 'Error';

                tr.innerHTML = `
                    <td>${row.row_number || idx + 1}</td>
                    <td>${row.first_name || ''} ${row.last_name || ''}</td>
                    <td>${row.email || ''}</td>
                    <td>${row.username || ''}</td>
                    <td>${row.teacher_id || row.student_id || ''}</td>
                    <td>${row.subject_specialization || row.class_grade || ''}</td>
                    <td><span class="badge ${badgeClass}" title="${row.error || ''}">${statusText}</span></td>
                `;
                tbody.appendChild(tr);
            });

            const errorTbody = document.getElementById('errorTableBody');
            errorTbody.innerHTML = '';

            this.errorRows.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.row_number || '-'}</td>
                    <td>${row.username || '-'}</td>
                    <td>${row.email || '-'}</td>
                    <td class="text-danger">${row.error || '-'}</td>
                `;
                errorTbody.appendChild(tr);
            });

            const btnConfirm = document.getElementById('btnConfirmImport');
            const warning = document.getElementById('allErrorWarning');
            if (this.validRows.length === 0) {
                if (btnConfirm) btnConfirm.disabled = true;
                if (warning) warning.classList.remove('d-none');
            } else {
                if (btnConfirm) btnConfirm.disabled = false;
                if (warning) warning.classList.add('d-none');
            }
        },

        async confirmImport() {
            const spinner = document.getElementById('confirmSpinner');
            const btnConfirm = document.getElementById('btnConfirmImport');

            if (spinner) spinner.classList.remove('d-none');
            if (btnConfirm) btnConfirm.disabled = true;

            try {
                const response = await fetch('/admin/users/import/confirm/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken(),
                    },
                    body: JSON.stringify({
                        preview_key: this.previewKey,
                    }),
                });

                const data = await response.json();

                if (spinner) spinner.classList.add('d-none');
                if (btnConfirm) btnConfirm.disabled = false;

                if (data.success) {
                    this.renderResult(data);
                    this.goToStep(3);
                } else {
                    this.showError(data.error || 'Gagal melakukan import.');
                }
            } catch (error) {
                if (spinner) spinner.classList.add('d-none');
                if (btnConfirm) btnConfirm.disabled = false;
                this.showError(`Terjadi kesalahan: ${error.message}`);
            }
        },

        renderResult(data) {
            document.getElementById('resultCreated').textContent = data.total_created || 0;
            document.getElementById('resultSkipped').textContent = data.total_skipped || 0;
            document.getElementById('resultFailed').textContent = data.total_failed || 0;

            const errorTbody = document.getElementById('resultErrorTableBody');
            errorTbody.innerHTML = '';

            const errorDetails = data.error_details || [];
            document.getElementById('resultErrorCount').textContent = errorDetails.length;

            errorDetails.slice(0, 50).forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.row || '-'}</td>
                    <td>${row.username || '-'}</td>
                    <td>${row.email || '-'}</td>
                    <td class="text-danger">${row.error || '-'}</td>
                `;
                errorTbody.appendChild(tr);
            });

            const emailSentInfo = document.getElementById('emailSentInfo');
            const manualPasswordInfo = document.getElementById('manualPasswordInfo');

            if (this.sendCredentialsEmail) {
                if (emailSentInfo) emailSentInfo.classList.remove('d-none');
                if (manualPasswordInfo) manualPasswordInfo.classList.add('d-none');
            } else {
                if (emailSentInfo) emailSentInfo.classList.add('d-none');
                if (manualPasswordInfo) manualPasswordInfo.classList.remove('d-none');
            }
        },

        goToStep(step) {
            const modalBody = document.getElementById('importModalBody');

            if (step === 1) {
                fetch('/admin/users/import/step1/')
                    .then(r => r.text())
                    .then(html => { modalBody.innerHTML = html; this.bindEvents(); });
            } else if (step === 2) {
                fetch('/admin/users/import/step2/')
                    .then(r => r.text())
                    .then(html => { modalBody.innerHTML = html; this.renderPreview(); this.bindEvents(); });
            } else if (step === 3) {
                fetch('/admin/users/import/step3/')
                    .then(r => r.text())
                    .then(html => { modalBody.innerHTML = html; this.bindEvents(); });
            }
        },

        showError(message) {
            const errorDiv = document.getElementById('uploadError');
            if (errorDiv) {
                errorDiv.textContent = message;
                errorDiv.classList.remove('d-none');
            }
        },

        hideError() {
            const errorDiv = document.getElementById('uploadError');
            if (errorDiv) {
                errorDiv.classList.add('d-none');
            }
        },

        getCsrfToken() {
            const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
            return input ? input.value : '';
        },
    };

    const ImportHistory = {
        init() {
            this.loadHistory();
        },

        async loadHistory() {
            const tbody = document.getElementById('importHistoryBody');
            if (!tbody) return;

            try {
                const response = await fetch('/admin/users/import/history/');
                const data = await response.json();

                if (data.history && data.history.length > 0) {
                    tbody.innerHTML = '';
                    data.history.forEach(log => {
                        const tr = document.createElement('tr');
                        const statusBadge = this.getStatusBadge(log.status);

                        tr.innerHTML = `
                            <td>${log.created_at}</td>
                            <td>${log.filename}</td>
                            <td>${log.imported_by}</td>
                            <td class="text-center"><span class="badge bg-success">${log.total_created}</span></td>
                            <td class="text-center"><span class="badge bg-warning">${log.total_skipped}</span></td>
                            <td class="text-center"><span class="badge bg-danger">${log.total_failed}</span></td>
                            <td>${statusBadge}</td>
                            <td>
                                <a href="/admin/users/import/${log.id}/report/" class="btn btn-sm btn-outline-primary" title="Download Laporan">
                                    <i class="ri-download-line"></i>
                                </a>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">Belum ada riwayat import.</td></tr>';
                }
            } catch (error) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-danger">Gagal memuat data.</td></tr>';
            }
        },

        getStatusBadge(status) {
            const badges = {
                pending: '<span class="badge bg-secondary">Pending</span>',
                processing: '<span class="badge bg-info">Processing</span>',
                completed: '<span class="badge bg-success">Completed</span>',
                failed: '<span class="badge bg-danger">Failed</span>',
            };
            return badges[status] || `<span class="badge bg-secondary">${status}</span>`;
        },
    };

    document.addEventListener('DOMContentLoaded', function() {
        ImportWizard.init();
        ImportHistory.init();
    });

    window.ImportWizard = ImportWizard;
    window.ImportHistory = ImportHistory;
})();
