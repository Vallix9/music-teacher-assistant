document.addEventListener('DOMContentLoaded', function () {
    var flashList = document.querySelectorAll('.alert');
    flashList.forEach(function (alert) {
        setTimeout(function () {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    var tooltipList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipList.forEach(function (el) {
        new bootstrap.Tooltip(el);
    });
});
