window.onload = function() {
    fetch('/lobby')
        .then(response => response.json())
        .then(data => {
            const usersDiv = document.getElementById('users');
            usersDiv.innerHTML = '<h3>Users in Lobby:</h3>' + data.users.join(', ');
        });
};

function userReady() {
    const username = localStorage.getItem('username');
    fetch('/setReady', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'username=' + encodeURIComponent(username)
    }).then(response => response.json())
      .then(data => {
          console.log(data);
          if (localStorage.getItem('isLeader') === 'true') {
              checkAllReady();
          }
      });
}

function checkAllReady() {
    fetch('/checkReady')
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            if (data.message === 'All users ready, entering game now') {
                // Redirect to torch.html
                window.location.href = 'torch.html';
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
