/* NextStep CRM — Delete confirmation modal handler + toast notifications + quick functions */

/* Global getCsrfToken helper */
window.getCsrfToken = function () {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
};

/* Global showToast — used by main.js and panel.js */
window.showToast = function (message, category) {
    var container = document.querySelector(".toast-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "toast-container position-fixed top-0 end-0 p-3";
        container.style.zIndex = "1090";
        document.body.appendChild(container);
    }

    var toastEl = document.createElement("div");
    toastEl.className = "toast align-items-center text-bg-" + category + " border-0";
    toastEl.setAttribute("role", "alert");

    var flex = document.createElement("div");
    flex.className = "d-flex";

    var body = document.createElement("div");
    body.className = "toast-body";
    var icon = document.createElement("i");
    icon.className = "bi bi-check-circle me-1";
    body.appendChild(icon);
    body.appendChild(document.createTextNode(message));
    flex.appendChild(body);

    var closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "btn-close btn-close-white me-2 m-auto";
    closeBtn.setAttribute("data-bs-dismiss", "toast");
    flex.appendChild(closeBtn);

    toastEl.appendChild(flex);
    container.appendChild(toastEl);

    var toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
};

/* Back-to-top button */
var btnTop = document.getElementById("btnBackToTop");
if (btnTop) {
    window.addEventListener("scroll", function () {
        btnTop.style.display = window.scrollY > 300 ? "" : "none";
    });
    btnTop.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
}

document.addEventListener("DOMContentLoaded", function () {
    /* Delete modal */
    var deleteModal = document.getElementById("confirmDeleteModal");
    if (deleteModal) {
        deleteModal.addEventListener("show.bs.modal", function (event) {
            var button = event.relatedTarget;
            var itemName = button.getAttribute("data-item-name") || "this item";
            var deleteUrl = button.getAttribute("data-delete-url");

            document.getElementById("deleteItemName").textContent = itemName;
            document.getElementById("deleteForm").action = deleteUrl;
        });
    }

    /* Auto-show toast notifications */
    var toasts = document.querySelectorAll(".toast");
    toasts.forEach(function (toastEl) {
        var toast = new bootstrap.Toast(toastEl);
        toast.show();
    });

    /* Quick Function handler — event delegation */
    document.addEventListener("click", function (e) {
        var btn = e.target.closest(".btn-quick-function");
        if (!btn) return;
        e.preventDefault();

        var modal = document.getElementById("quickFunctionModal");
        if (!modal) return;

        document.getElementById("qfActionLabel").textContent = btn.getAttribute("data-action-label");
        document.getElementById("qfClientName").textContent = btn.getAttribute("data-client-name");
        document.getElementById("qfType").textContent = btn.getAttribute("data-action-type");
        document.getElementById("qfNotes").textContent = btn.getAttribute("data-action-notes");
        document.getElementById("qfDate").textContent = new Date().toLocaleDateString("en-GB");
        document.getElementById("qfActionId").value = btn.getAttribute("data-action-id");
        document.getElementById("qfForm").action = btn.getAttribute("data-action-url");

        var bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    });

    /* Quick Function form submit — AJAX */
    var qfForm = document.getElementById("qfForm");
    if (qfForm) {
        qfForm.addEventListener("submit", function (e) {
            e.preventDefault();

            var confirmBtn = document.getElementById("qfConfirmBtn");
            confirmBtn.disabled = true;
            confirmBtn.textContent = "";
            var spinnerSpan = document.createElement("span");
            spinnerSpan.className = "spinner-border spinner-border-sm me-1";
            confirmBtn.appendChild(spinnerSpan);
            confirmBtn.appendChild(document.createTextNode("Saving..."));

            var formData = new FormData(qfForm);
            fetch(qfForm.action, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": getCsrfToken() },
                body: formData
            })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                var modal = bootstrap.Modal.getInstance(document.getElementById("quickFunctionModal"));
                if (modal) modal.hide();

                if (data.ok) {
                    window.showToast(data.message, "success");
                    setTimeout(function () { location.reload(); }, 600);
                } else {
                    window.showToast(data.error || "Something went wrong.", "danger");
                    _resetQfConfirmBtn();
                }
            })
            .catch(function () {
                qfForm.submit();
            });
        });
    }

    function _resetQfConfirmBtn() {
        var confirmBtn = document.getElementById("qfConfirmBtn");
        confirmBtn.disabled = false;
        confirmBtn.textContent = "";
        var icon = document.createElement("i");
        icon.className = "bi bi-check-lg me-1";
        confirmBtn.appendChild(icon);
        confirmBtn.appendChild(document.createTextNode("Confirm"));
    }

    /* Reset quick function modal on close */
    var qfModal = document.getElementById("quickFunctionModal");
    if (qfModal) {
        qfModal.addEventListener("hidden.bs.modal", function () {
            _resetQfConfirmBtn();
        });
    }

    /* Attachment Preview Modal */
    var previewModal = document.getElementById("attachmentPreviewModal");
    if (previewModal) {
        previewModal.addEventListener("show.bs.modal", function (event) {
            var button = event.relatedTarget;
            var url = button.getAttribute("data-preview-url");
            var name = button.getAttribute("data-preview-name");
            var mime = button.getAttribute("data-preview-mime");
            var downloadUrl = button.getAttribute("data-download-url");

            document.getElementById("attachmentPreviewModalLabel").textContent = name;
            document.getElementById("attachmentPreviewOpenTab").href = url;
            document.getElementById("attachmentPreviewDownload").href = downloadUrl;

            var body = document.getElementById("attachmentPreviewBody");
            while (body.firstChild) { body.removeChild(body.firstChild); }

            if (mime && mime.startsWith("image/")) {
                var img = document.createElement("img");
                img.src = url;
                img.alt = name;
                img.className = "img-fluid rounded";
                img.style.maxHeight = "70vh";
                body.appendChild(img);
            } else if (mime === "application/pdf") {
                var iframe = document.createElement("iframe");
                iframe.src = url;
                iframe.style.width = "100%";
                iframe.style.height = "70vh";
                iframe.style.border = "none";
                body.appendChild(iframe);
            } else {
                var p = document.createElement("p");
                p.className = "text-muted py-5";
                p.textContent = "Preview not available for this file type.";
                body.appendChild(p);
                var a = document.createElement("a");
                a.href = downloadUrl;
                a.className = "btn btn-primary";
                var dlIcon = document.createElement("i");
                dlIcon.className = "bi bi-download me-1";
                a.appendChild(dlIcon);
                a.appendChild(document.createTextNode("Download"));
                body.appendChild(a);
            }
        });

        previewModal.addEventListener("hidden.bs.modal", function () {
            var body = document.getElementById("attachmentPreviewBody");
            while (body.firstChild) { body.removeChild(body.firstChild); }
        });
    }

    /* Follow-up completion → outcome flow */
    var navigatingAway = false;
    document.addEventListener("submit", function (e) {
        var form = e.target.closest(".complete-followup-form");
        if (!form) return;

        var isCompleted = form.getAttribute("data-completed") === "true";

        /* If reopening, just AJAX POST and reload */
        if (isCompleted) {
            e.preventDefault();
            fetch(form.action, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": getCsrfToken() }
            })
            .then(function () { location.reload(); })
            .catch(function () { form.submit(); });
            return;
        }

        /* Completing — AJAX POST then show outcome modal */
        e.preventDefault();
        fetch(form.action, {
            method: "POST",
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
        .then(function (resp) { return resp.json(); })
        .then(function (data) {
            if (data.status !== "completed") {
                location.reload();
                return;
            }

            /* Populate and show outcome modal */
            var modal = document.getElementById("completeOutcomeModal");
            document.getElementById("outcomeClientName").textContent = data.clientName;
            var notesPreview = document.getElementById("outcomeNotesPreview");
            var notesText = document.getElementById("outcomeNotesText");
            if (data.notes) {
                notesText.textContent = data.notes.substring(0, 120);
                notesPreview.style.display = "block";
            } else {
                notesPreview.style.display = "none";
            }

            /* Build "Log Interaction" URL with pre-fill */
            var today = new Date().toISOString().split("T")[0];
            var logUrl = "/contacts/new?client_id=" + data.clientId +
                         "&notes=" + encodeURIComponent("Follow-up: " + data.notes.substring(0, 200)) +
                         "&date=" + today;
            document.getElementById("outcomeLogInteraction").href = logUrl;

            var bsModal = new bootstrap.Modal(modal);
            bsModal.show();

            /* On modal hidden, reload page (unless navigating to Log Interaction) */
            modal.addEventListener("hidden.bs.modal", function handler() {
                modal.removeEventListener("hidden.bs.modal", handler);
                if (!navigatingAway) {
                    location.reload();
                }
            });
        })
        .catch(function () {
            form.submit();
        });
    });

    /* Track clicks on Log Interaction link */
    var logLink = document.getElementById("outcomeLogInteraction");
    if (logLink) {
        logLink.addEventListener("click", function () {
            navigatingAway = true;
        });
    }
});
