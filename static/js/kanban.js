/* NextStep CRM — Kanban board drag-and-drop with SortableJS */

document.addEventListener("DOMContentLoaded", function () {
    var containers = document.querySelectorAll(".kanban-items");

    containers.forEach(function (container) {
        new Sortable(container, {
            group: "pipeline",
            animation: 150,
            ghostClass: "kanban-ghost",
            dragClass: "kanban-drag",
            onEnd: function (evt) {
                var card = evt.item;
                var clientId = card.getAttribute("data-client-id");
                var newStatus = evt.to.getAttribute("data-status");
                var oldStatus = evt.from.getAttribute("data-status");

                if (newStatus === oldStatus) return;

                fetch("/clients/" + clientId + "/status", {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    body: JSON.stringify({ status: newStatus })
                })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    if (!data.ok) {
                        /* Rollback: move card back to original column */
                        evt.from.appendChild(card);
                        alert("Failed to update status: " + (data.error || "Unknown error"));
                    }
                    /* Update count badges */
                    updateColumnCounts();
                })
                .catch(function () {
                    /* Rollback on network error */
                    evt.from.appendChild(card);
                    updateColumnCounts();
                });
            }
        });
    });

    function updateColumnCounts() {
        containers.forEach(function (container) {
            var column = container.closest(".kanban-column");
            var countBadge = column.querySelector(".kanban-count");
            var cardCount = container.querySelectorAll(".kanban-card").length;
            countBadge.textContent = cardCount;
        });
    }
});
