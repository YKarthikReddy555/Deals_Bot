document.addEventListener('DOMContentLoaded', function() {
    // 🎭 TAB SWITCHING LOGIC
    const navBtns = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    navBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = btn.getAttribute('data-tab');

            // Toggle Sidebar Active State
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Toggle Content Visibility
            tabContents.forEach(tab => tab.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');

            // Triggger Data Fetching for specific tabs
            if (tabId === 'explorer-tab') fetchExploreData();
            if (tabId === 'community-tab') fetchCommunityData();
        });
    });

    // 📊 CHART INITIALIZATION
    const ctx = document.getElementById('growthChart').getContext('2d');
    let growthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Deals Captured',
                data: [0, 0, 0, 0, 0, 0, 0],
                borderColor: '#38bdf8',
                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
    });

    // 📡 FETCH DASHBOARD STATS
    function fetchStats() {
        fetch('/api/stats')
            .then(res => res.json())
            .then(data => {
                growthChart.data.labels = data.labels;
                growthChart.data.datasets[0].data = data.deals_data;
                growthChart.update();
            });
    }

    // 🔎 FETCH EXPLORER DATA
    function fetchExploreData() {
        fetch('/api/deals/all')
            .then(res => res.json())
            .then(data => {
                const tbody = document.querySelector('#explorer-table tbody');
                tbody.innerHTML = '';
                data.deals.forEach(deal => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${deal.title}</td>
                        <td style="color: #4ade80;">${deal.price}</td>
                        <td>${deal.created_at.split('T')[0]}</td>
                        <td><span class="badge" style="background: rgba(56,189,248,0.1); color: var(--accent); padding: 0.2rem 0.5rem; border-radius: 0.4rem;">LIVE</span></td>
                    `;
                    tbody.appendChild(tr);
                });
            });
    }

    // 👥 FETCH COMMUNITY DATA
    function fetchCommunityData() {
        fetch('/api/community')
            .then(res => res.json())
            .then(data => {
                const tbody = document.querySelector('#community-table tbody');
                tbody.innerHTML = '';
                data.users.forEach(user => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${user.telegram_id}</td>
                        <td style="font-weight: 600;">@${user.username || 'unknown'}</td>
                        <td>${user.referred_by || 'NONE'}</td>
                        <td>${user.created_at.split('T')[0]}</td>
                    `;
                    tbody.appendChild(tr);
                });
            });
    }

    // 🛰️ LIVE LOG POLLING
    const logFeed = document.getElementById('log-feed');
    function updateLogs() {
        fetch('/api/logs')
            .then(res => res.json())
            .then(data => {
                logFeed.innerHTML = '';
                data.logs.forEach(line => {
                    const p = document.createElement('p');
                    if (line.includes('ERROR')) p.style.color = '#ef4444';
                    p.innerHTML = `<span style="color: #64748b;">></span> ${line}`;
                    logFeed.appendChild(p);
                });
                logFeed.scrollTop = logFeed.scrollHeight;
            });
    }

    // Initial load
    fetchStats();
    setInterval(updateLogs, 3000);
    updateLogs();
});
