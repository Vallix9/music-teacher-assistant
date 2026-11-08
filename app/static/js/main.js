document.addEventListener('DOMContentLoaded', function () {
    // Автозакрытие уведомлений
    document.querySelectorAll('.alert').forEach(function (alert) {
        setTimeout(function () {
            var instance = bootstrap.Alert.getOrCreateInstance(alert);
            if (instance) instance.close();
        }, 5000);
    });

    // Мобильный сайдбар
    var sidebar = document.getElementById('sidebar');
    var backdrop = document.getElementById('sidebarBackdrop');
    var toggle = document.getElementById('sidebarToggle');

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('show');
    }

    if (toggle && sidebar) {
        toggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
            if (backdrop) backdrop.classList.toggle('show');
        });
    }
    if (backdrop) backdrop.addEventListener('click', closeSidebar);

    // Подсказки
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        new bootstrap.Tooltip(el);
    });
});
