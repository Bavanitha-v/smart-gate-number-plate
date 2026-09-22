/* -------------------------------------------------------------
 * AI SMART GATE CONTROL SYSTEM - FRONTEND JAVASCRIPT ENGINE
 * ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    // Start Live Clock
    updateClock();
    setInterval(updateClock, 1000);

    // Initial Data Fetch
    fetchStatus();
    fetchLogs();
    fetchVehicles();

    // Start Polling Loops
    setInterval(fetchStatus, 1000);  // Status metrics poll every 1s
    setInterval(fetchLogs, 3000);    // Log entries poll every 3s
});

// Update Digital Clock
function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    document.getElementById('live-clock').textContent = timeStr;
}

// Fetch ANPR Recognition Status Metrics
async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) return;
        const data = await response.json();

        // Update Text Elements
        document.getElementById('metric-plate').textContent = data.detected_plate || "Scanning...";
        document.getElementById('metric-owner').textContent = data.owner_name || "-";
        document.getElementById('metric-decision').textContent = data.vehicle_status || "SCANNING";
        document.getElementById('metric-confidence').textContent = (data.confidence || 0) + "%";

        // Update Gate Status Banner
        const gateBanner = document.getElementById('gate-banner');
        const gateStatusText = document.getElementById('gate-status-text');
        const vehicleStatusSub = document.getElementById('vehicle-status-sub');
        const gateIcon = document.getElementById('gate-icon-i');

        if (data.gate_status === 'GATE OPEN') {
            gateBanner.className = 'gate-banner status-open';
            gateStatusText.textContent = 'GATE OPEN';
            vehicleStatusSub.textContent = `REGISTERED (${data.owner_name})`;
            gateIcon.className = 'fa-solid fa-lock-open';
        } else {
            gateBanner.className = 'gate-banner status-closed';
            gateStatusText.textContent = 'GATE CLOSED';
            vehicleStatusSub.textContent = data.vehicle_status === 'UNKNOWN VEHICLE' ? 'UNKNOWN VEHICLE' : data.vehicle_status;
            gateIcon.className = 'fa-solid fa-lock';
        }

        // Update Source Badge
        const sourceBadge = document.getElementById('source-badge');
        sourceBadge.textContent = `Source: ${data.source === 'webcam' ? 'Live Camera' : 'Test Video'}`;

    } catch (err) {
        console.error("Error fetching ANPR status:", err);
    }
}

// Fetch Access Entry Logs
async function fetchLogs() {
    try {
        const response = await fetch('/api/logs');
        if (!response.ok) return;
        const logs = await response.json();

        const tbody = document.getElementById('logs-table-body');
        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center">No access logs recorded yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(log => {
            const gateClass = log.access_status === 'GATE OPEN' ? 'tag-open' : 'tag-closed';
            const vehClass = log.vehicle_status === 'REGISTERED' ? 'tag-registered' : 'tag-unknown';

            return `
                <tr>
                    <td>#${log.id}</td>
                    <td>${log.timestamp}</td>
                    <td><strong style="color: #facc15;">${log.plate_number}</strong></td>
                    <td>${log.owner_name || 'Unknown'}</td>
                    <td><span class="${vehClass}">${log.vehicle_status}</span></td>
                    <td><span class="${gateClass}"><i class="fa-solid ${log.access_status === 'GATE OPEN' ? 'fa-door-open' : 'fa-door-closed'}"></i> ${log.access_status}</span></td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        console.error("Error fetching access logs:", err);
    }
}

// Fetch Registered Vehicles Database
async function fetchVehicles() {
    try {
        const response = await fetch('/api/vehicles');
        if (!response.ok) return;
        const vehicles = await response.json();

        document.getElementById('reg-count-badge').textContent = `${vehicles.length} Registered`;

        const tbody = document.getElementById('vehicles-table-body');
        if (vehicles.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center">No registered vehicles found.</td></tr>`;
            return;
        }

        tbody.innerHTML = vehicles.map(v => `
            <tr>
                <td><strong style="color: #6ee7b7;">${v.plate_number}</strong></td>
                <td>${v.owner_name}</td>
                <td>${v.vehicle_type}</td>
                <td>
                    <button class="btn-danger-sm" onclick="deleteVehicle('${v.plate_number}')">
                        <i class="fa-solid fa-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `).join('');

    } catch (err) {
        console.error("Error fetching vehicles:", err);
    }
}

// Register New Vehicle
async function registerVehicle(event) {
    event.preventDefault();
    const plateInput = document.getElementById('reg-plate');
    const ownerInput = document.getElementById('reg-owner');

    const plate = plateInput.value.trim();
    const owner = ownerInput.value.trim();

    if (!plate || !owner) return;

    try {
        const response = await fetch('/api/vehicles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plate_number: plate, owner_name: owner })
        });
        const result = await response.json();

        if (result.success) {
            plateInput.value = '';
            ownerInput.value = '';
            fetchVehicles();
            fetchStatus();
            alert(result.message);
        } else {
            alert("Error: " + result.message);
        }
    } catch (err) {
        alert("Failed to register vehicle: " + err);
    }
}

// Delete Registered Vehicle
async function deleteVehicle(plateNumber) {
    if (!confirm(`Are you sure you want to remove plate '${plateNumber}' from authorized list?`)) return;

    try {
        const response = await fetch('/api/vehicles', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plate_number: plateNumber })
        });
        const result = await response.json();

        if (result.success) {
            fetchVehicles();
            fetchStatus();
        } else {
            alert("Error deleting vehicle: " + result.message);
        }
    } catch (err) {
        alert("Failed to delete vehicle: " + err);
    }
}

// Switch Video Feed Source (Sample Video vs Webcam)
async function switchVideoSource(sourceType) {
    try {
        const response = await fetch('/api/toggle_source', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source: sourceType })
        });
        const result = await response.json();

        if (result.success) {
            // Update Active Buttons
            document.getElementById('btn-source-sample').classList.toggle('active', sourceType === 'sample');
            document.getElementById('btn-source-webcam').classList.toggle('active', sourceType === 'webcam');

            // Force Video Feed Refresh
            const videoStream = document.getElementById('video-stream');
            videoStream.src = '/video_feed?t=' + new Date().getTime();
            fetchStatus();
        }
    } catch (err) {
        console.error("Error switching video source:", err);
    }
}

// Manual Gate Override Trigger
async function triggerManualGate(action) {
    try {
        const response = await fetch('/api/manual_gate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });
        const result = await response.json();

        if (result.success) {
            fetchStatus();
            fetchLogs();
        }
    } catch (err) {
        console.error("Error triggering manual gate:", err);
    }
}
