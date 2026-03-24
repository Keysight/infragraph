// Navigation: breadcrumb trail, back button, drill-down

var navigationStack = [];    // [{file, label}]
var breadcrumb, btnBack;

function initNavigation() {
    breadcrumb = document.getElementById('breadcrumb');
    btnBack = document.getElementById('btn-back');
    btnBack.addEventListener('click', goBack);

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Backspace' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            goBack();
        }
    });
}

function navigateTo(file, label) {
    showLoading();

    fetchGraphData(file).then(function (data) {
        navigationStack.push({ file: file, label: label });
        updateBreadcrumb();
        updateBackButton();

        var isInfra = navigationStack.length === 1;
        var options = isInfra ? fabricOptions : internalOptions;

        currentData = prepareData(data);
        render(currentData, options);

        if (typeof populateFilters === 'function') populateFilters(currentData);

        hideLoading();
    }).catch(function (err) {
        console.error('Failed to load graph data:', err);
        alert('Failed to load: ' + file + '\n\n' + err.message);
        hideLoading();
    });
}

function goBack() {
    if (navigationStack.length <= 1) return;
    navigationStack.pop();
    var prev = navigationStack[navigationStack.length - 1];
    navigationStack.pop();
    navigateTo(prev.file, prev.label);
}

function updateBreadcrumb() {
    breadcrumb.innerHTML = '';
    navigationStack.forEach(function (item, idx) {
        if (idx > 0) {
            var sep = document.createElement('span');
            sep.className = 'crumb-sep';
            sep.textContent = '\u203A';
            breadcrumb.appendChild(sep);
        }
        var crumb = document.createElement('span');
        crumb.className = 'crumb';
        crumb.textContent = item.label;
        crumb.dataset.file = item.file;
        if (idx === navigationStack.length - 1) {
            crumb.classList.add('active');
        } else {
            (function (i, f, l) {
                crumb.addEventListener('click', function () {
                    while (navigationStack.length > i) navigationStack.pop();
                    navigateTo(f, l);
                });
            })(idx, item.file, item.label);
        }
        breadcrumb.appendChild(crumb);
    });
}

function updateBackButton() {
    btnBack.disabled = navigationStack.length <= 1;
}