window.onload = function () {
    fetchScores();
    //ensure the function is called every 10 seconds
    setInterval(fetchScores, 1000);
    setTimeout(removeUsers, 18000);
}

function fetchScores() {
    fetch('/scores')
        .then(response => response.json())
        .then(data => {
            console.log(data);
            const scoresDiv = document.getElementById('scoresTable');
            let html = '<h3>User Scores:</h3>';
            html += '<table>';
            html += '<tr><th>User</th><th>Score</th></tr>';
            for (const user in data) {
                html += `<tr><td>${user}</td><td>${data[user]}</td></tr>`;
            }
            html += '</table>';
            scoresDiv.innerHTML = html;
            // Return the user with the highest score to be printed in the winnername class inside the winner class
            var winner = Object.keys(data).reduce((a, b) => data[a] > data[b] ? a : b);
            var winnername = document.getElementById("winnerName");
            winnername.textContent = winner;
        });
}

function removeUsers() {
    fetch('/removeUsers')
        .then(response => response.json())
        .then(data => {
            alert("All users have been removed from the lobby!")
            console.log(data);
            window.location.href = '/';
        });
}