function joinLobby() {
    const username = document.getElementById('username').value;
    fetch('/join', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'username=' + encodeURIComponent(username)
    }).then(response => response.json())
      .then(data => {
          alert(data.message);
          if (data.status === 'success') {
              fetchLobbyUsers();
          }
      });
}

function fetchLobbyUsers() {
    fetch('/lobby')
        .then(response => response.json())
        .then(data => {
            const usersDiv = document.getElementById('users');
            usersDiv.innerHTML = '<h3>Users in Lobby:</h3>' + data.users.join(', ');
        });
}
