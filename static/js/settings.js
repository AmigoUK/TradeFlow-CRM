/* NextStep CRM — Settings page interactions */

/**
 * Apply a theme to the document.
 * @param {string} theme - "light", "dark", or "auto"
 */
function applyTheme(theme) {
    var html = document.documentElement;
    html.setAttribute("data-bs-theme-setting", theme);

    if (theme === "dark") {
        html.setAttribute("data-bs-theme", "dark");
    } else if (theme === "auto") {
        var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        if (prefersDark) {
            html.setAttribute("data-bs-theme", "dark");
        } else {
            html.removeAttribute("data-bs-theme");
        }
    } else {
        html.removeAttribute("data-bs-theme");
    }
}

document.addEventListener("DOMContentLoaded", function () {

    /* Theme card click handler */
    document.querySelectorAll(".theme-option").forEach(function (card) {
        card.addEventListener("click", function () {
            var theme = this.getAttribute("data-theme");

            /* Update radio buttons */
            this.querySelector("input[type=radio]").checked = true;

            /* Update border highlight */
            document.querySelectorAll(".theme-option").forEach(function (c) {
                c.classList.remove("border-primary", "border-2");
            });
            this.classList.add("border-primary", "border-2");

            /* Apply theme immediately */
            applyTheme(theme);

            /* Re-attach OS listener if switching to auto */
            if (theme === "auto") {
                window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
                    if (document.documentElement.getAttribute("data-bs-theme-setting") === "auto") {
                        applyTheme("auto");
                    }
                });
            }

            /* AJAX save */
            fetch("/settings/theme", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCsrfToken()
                },
                body: JSON.stringify({ theme: theme })
            })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                if (data.ok) {
                    window.showToast("Theme updated to " + theme + ".", "success");
                }
            })
            .catch(function () {
                window.showToast("Failed to save theme.", "danger");
            });
        });
    });

    /* UI Preferences toggle handlers */
    document.querySelectorAll(".ui-pref-toggle").forEach(function (toggle) {
        toggle.addEventListener("change", function () {
            var pref = this.getAttribute("data-pref");
            var payload = {};
            payload[pref] = this.checked;

            /* Enable/disable page size selector when pagination toggles */
            if (pref === "pagination_enabled") {
                var pageSize = document.getElementById("prefPageSize");
                if (pageSize) {
                    pageSize.disabled = !this.checked;
                }
            }

            fetch("/settings/ui-preferences", {
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
                    window.showToast("UI preference updated.", "success");
                }
            })
            .catch(function () {
                toggle.checked = !toggle.checked;
                window.showToast("Failed to save preference.", "danger");
            });
        });
    });

    /* Page size selector handler */
    var pageSizeSelect = document.getElementById("prefPageSize");
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener("change", function () {
            fetch("/settings/ui-preferences", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCsrfToken()
                },
                body: JSON.stringify({ pagination_size: parseInt(this.value, 10) })
            })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                if (data.ok) {
                    window.showToast("Page size updated.", "success");
                }
            })
            .catch(function () {
                window.showToast("Failed to save page size.", "danger");
            });
        });
    }

    /* Quick function toggle switch AJAX handler */
    document.querySelectorAll(".settings-toggle").forEach(function (toggle) {
        toggle.addEventListener("change", function () {
            var url = this.getAttribute("data-toggle-url");
            var row = this.closest("tr");

            fetch(url, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": getCsrfToken() }
            })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                if (data.ok) {
                    if (data.is_active) {
                        row.classList.remove("text-muted");
                    } else {
                        row.classList.add("text-muted");
                    }
                    window.showToast(data.message, "success");
                }
            })
            .catch(function () {
                toggle.checked = !toggle.checked;
                window.showToast("Failed to update. Please try again.", "danger");
            });
        });
    });
});
