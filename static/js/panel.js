/* NextStep CRM — Slide-over form panel (Bootstrap 5 Offcanvas) */

document.addEventListener("DOMContentLoaded", function () {
    var panelEl = document.getElementById("quickAddPanel");
    var panelTitle = document.getElementById("quickAddPanelTitle");
    var panelBody = document.getElementById("quickAddPanelBody");
    if (!panelEl) return;

    var bsOffcanvas = new bootstrap.Offcanvas(panelEl);

    function showSpinner() {
        panelBody.textContent = "";
        var wrapper = document.createElement("div");
        wrapper.className = "text-center py-5";
        var spinner = document.createElement("div");
        spinner.className = "spinner-border text-primary";
        spinner.setAttribute("role", "status");
        var sr = document.createElement("span");
        sr.className = "visually-hidden";
        sr.textContent = "Loading...";
        spinner.appendChild(sr);
        wrapper.appendChild(spinner);
        panelBody.appendChild(wrapper);
    }

    /* Intercept clicks on [data-panel-url] links */
    document.addEventListener("click", function (e) {
        var link = e.target.closest("[data-panel-url]");
        if (!link) return;

        e.preventDefault();

        var url = link.getAttribute("data-panel-url");
        var title = link.getAttribute("data-panel-title") || "Quick Add";

        panelTitle.textContent = title;
        showSpinner();
        bsOffcanvas.show();

        fetch(url, {
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
        .then(function (resp) { return resp.text(); })
        .then(function (html) {
            /* Server returns trusted form HTML from our own templates */
            setPanelContent(html);
            bindPanelForm(url);
        })
        .catch(function () {
            /* Fallback: navigate to full page */
            window.location.href = url;
        });
    });

    function setPanelContent(trustedHTML) {
        /* This HTML comes from our own server-rendered Jinja2 templates,
           not from user input, so it is safe to inject. */
        var range = document.createRange();
        range.selectNode(panelBody);
        var fragment = range.createContextualFragment(trustedHTML);
        panelBody.textContent = "";
        panelBody.appendChild(fragment);
    }

    function bindPanelForm(actionUrl) {
        var form = panelBody.querySelector("form");
        if (!form) return;

        form.addEventListener("submit", function (e) {
            e.preventDefault();

            var formData = new FormData(form);
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = "";
                var spinnerSpan = document.createElement("span");
                spinnerSpan.className = "spinner-border spinner-border-sm me-1";
                submitBtn.appendChild(spinnerSpan);
                submitBtn.appendChild(document.createTextNode("Saving..."));
            }

            fetch(actionUrl, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": getCsrfToken() },
                body: formData
            })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                if (data.ok) {
                    bsOffcanvas.hide();
                    window.showToast(data.message || "Saved successfully.", "success");
                    setTimeout(function () {
                        location.reload();
                    }, 600);
                } else if (data.html) {
                    setPanelContent(data.html);
                    bindPanelForm(actionUrl);
                } else {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = "Save";
                    }
                }
            })
            .catch(function () {
                form.submit();
            });
        });
    }

});
