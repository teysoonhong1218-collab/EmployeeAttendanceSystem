document.addEventListener("DOMContentLoaded", function () {
    updateClock();
    setInterval(updateClock, 1000);

    const toggle = document.querySelector(".mobile-toggle");
    const sidebar = document.querySelector(".sidebar");
    if (toggle && sidebar) {
        toggle.addEventListener("click", function () {
            sidebar.classList.toggle("open");
        });
    }

    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.classList.remove("show");
            setTimeout(function () { alert.remove(); }, 150);
        }, 4000);
    });
});

function updateClock() {
    var el = document.getElementById("live-clock");
    if (!el) return;
    var now = new Date();
    var h = String(now.getHours()).padStart(2, "0");
    var m = String(now.getMinutes()).padStart(2, "0");
    var s = String(now.getSeconds()).padStart(2, "0");
    el.textContent = h + ":" + m + ":" + s;

    var dateEl = document.getElementById("live-date");
    if (dateEl) {
        var options = { weekday: "long", year: "numeric", month: "long", day: "numeric" };
        dateEl.textContent = now.toLocaleDateString("en-MY", options);
    }
}

function loadAttendanceChart(canvasId) {
    fetch("/api/attendance-stats")
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var ctx = document.getElementById(canvasId);
            if (!ctx) return;
            new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: ["Present", "Late", "Absent"],
                    datasets: [{
                        data: [data.present, data.late, data.absent],
                        backgroundColor: ["#16a34a", "#d97706", "#dc2626"],
                        borderWidth: 2,
                        borderColor: "#fff",
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "bottom" },
                    },
                },
            });
        });
}
