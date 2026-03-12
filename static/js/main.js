/* TradeFlow CRM — Delete confirmation modal handler + toast notifications */

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
});
