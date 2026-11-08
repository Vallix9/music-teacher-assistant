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

    // Переключение светлой / тёмной темы
    var themeToggles = document.querySelectorAll('[data-theme-toggle]');

    function currentTheme() {
        return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
    }

    function syncThemeButtons(theme) {
        themeToggles.forEach(function (btn) {
            var icon = btn.querySelector('i');
            if (icon) icon.className = theme === 'light' ? 'bi bi-moon-stars' : 'bi bi-sun';
            var label = theme === 'light' ? 'Включить тёмную тему' : 'Включить светлую тему';
            btn.setAttribute('title', label);
            btn.setAttribute('aria-label', label);
        });
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        document.documentElement.setAttribute('data-bs-theme', theme);
        try { localStorage.setItem('ma-theme', theme); } catch (e) {}
        syncThemeButtons(theme);
    }

    themeToggles.forEach(function (btn) {
        btn.addEventListener('click', function () {
            applyTheme(currentTheme() === 'light' ? 'dark' : 'light');
        });
    });

    syncThemeButtons(currentTheme());

    // Подсказки
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        new bootstrap.Tooltip(el);
    });
});
