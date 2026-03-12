/* NextStep CRM — Delete confirmation modal handler + toast notifications */

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
                headers: { "X-Requested-With": "XMLHttpRequest" }
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
