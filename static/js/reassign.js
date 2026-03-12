/* NextStep CRM — Record reassignment (single, bulk, delegation) */

function getCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
}

document.addEventListener("DOMContentLoaded", function () {

    /* ── Single Reassign dropdown ── */
    document.querySelectorAll(".reassign-form").forEach(function (form) {
        var select = form.querySelector(".reassign-select");
        if (!select) return;

        select.addEventListener("change", function () {
            var userId = this.value;
            if (!userId) return;

            var cascade = form.querySelector("[name='cascade']");
            var payload = { target_user_id: parseInt(userId, 10) };
            if (cascade && cascade.checked) {
                payload.cascade = true;
            }

            fetch(form.action, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCsrfToken()
                },
                body: JSON.stringify(payload)
            })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                if (data.ok) {
                    window.showToast(data.message || "Reassigned.", "success");
                    setTimeout(function () { location.reload(); }, 600);
                } else {
                    window.showToast(data.error || "Reassignment failed.", "danger");
                }
            })
            .catch(function () {
                window.showToast("Network error.", "danger");
            });
        });
    });

    /* ── Bulk checkbox select-all ── */
    var selectAllCb = document.getElementById("bulkSelectAll");
    if (selectAllCb) {
        selectAllCb.addEventListener("change", function () {
            document.querySelectorAll(".bulk-select-cb").forEach(function (cb) {
                cb.checked = selectAllCb.checked;
            });
            updateBulkToolbar();
        });
    }

    document.querySelectorAll(".bulk-select-cb").forEach(function (cb) {
        cb.addEventListener("change", updateBulkToolbar);
    });

    function updateBulkToolbar() {
        var checked = document.querySelectorAll(".bulk-select-cb:checked");
        var toolbar = document.getElementById("bulkToolbar");
        var count = document.getElementById("bulkCount");
        if (toolbar) {
            toolbar.style.display = checked.length > 0 ? "" : "none";
        }
        if (count) {
            count.textContent = checked.length;
        }
    }

    /* ── Bulk Reassign submit ── */
    var bulkReassignBtn = document.getElementById("bulkReassignBtn");
    if (bulkReassignBtn) {
        bulkReassignBtn.addEventListener("click", function () {
            var select = document.getElementById("bulkReassignUser");
            var targetUserId = select ? select.value : "";
            if (!targetUserId) {
                window.showToast("Please select a target user.", "warning");
                return;
            }

            var ids = [];
            document.querySelectorAll(".bulk-select-cb:checked").forEach(function (cb) {
                ids.push(parseInt(cb.value, 10));
            });

            if (ids.length === 0) return;

            var url = bulkReassignBtn.getAttribute("data-url");
            fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCsrfToken()
                },
                body: JSON.stringify({ ids: ids, target_user_id: parseInt(targetUserId, 10) })
            })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                if (data.ok) {
                    window.showToast(data.message || "Bulk reassignment complete.", "success");
                    setTimeout(function () { location.reload(); }, 600);
                } else {
                    window.showToast(data.error || "Bulk reassignment failed.", "danger");
                }
            })
            .catch(function () {
                window.showToast("Network error.", "danger");
            });
        });
    }
});
