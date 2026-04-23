<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Command Management</title>
    <script>
        let commandHistory = [];
        let commandId = 0;

        function sendCommand() {
            const commandType = document.getElementById('commandType').value;
            const panelSlot = document.getElementById('panelSlot').value;
            const status = 'Pending';
            commandId++;

            // Create command log
            const commandLog = {
                id: commandId,
                slot: panelSlot,
                action: commandType,
                status: status,
                created_at: new Date().toISOString()
            };

            commandHistory.push(commandLog);
            updateCommandHistory();
            executeCommand(commandType, panelSlot);
        }

        function executeCommand(commandType, panelSlot) {
            // Simulate command execution and status updates
            const interval = setInterval(() => {
                const commandLog = commandHistory.find(cmd => cmd.id === commandId);
                if (!commandLog) return;

                if (commandLog.status === 'Pending') {
                    commandLog.status = 'Executing';
                    updateCommandHistory();
                }
                // Randomly update the status
                commandLog.status = (Math.random() > 0.5) ? 'Success' : 'Failed';
                updateCommandHistory();
                clearInterval(interval);
            }, 2000);
        }

        function updateCommandHistory() {
            const tableBody = document.getElementById('commandHistoryBody');
            tableBody.innerHTML = '';
            commandHistory.forEach(log => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${log.id}</td><td>${log.slot}</td><td>${log.action}</td><td>${log.status}</td><td>${log.created_at}</td>`;
                tableBody.appendChild(row);
            });
        }
    </script>
</head>
<body>
    <h1>Interactive Command Management</h1>
    <label for="commandType">Command Type:</label>
    <select id="commandType">
        <option value="start_login">Start Login</option>
        <option value="start_loop">Start Loop</option>
        <option value="stop">Stop</option>
        <option value="clean_ram">Clean RAM</option>
        <option value="custom">Custom</option>
    </select>

    <label for="panelSlot">Panel Slot:</label>
    <select id="panelSlot">
        <option value="slot1">Slot 1</option>
        <option value="slot2">Slot 2</option>
        <option value="slot3">Slot 3</option>
        <option value="slot4">Slot 4</option>
    </select>

    <button onclick="sendCommand()">Send Command</button>

    <h2>Command History</h2>
    <table border="1">
        <thead>
            <tr>
                <th>ID</th>
                <th>Slot</th>
                <th>Action</th>
                <th>Status</th>
                <th>Created At</th>
            </tr>
        </thead>
        <tbody id="commandHistoryBody">
        </tbody>
    </table>
</body>
</html>
