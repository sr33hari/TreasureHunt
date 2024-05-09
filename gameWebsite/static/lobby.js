var socket = io.connect(window.location.origin);
socket.on('start game', function(data) {
    alert('Game is starting now!')
    window.location.href = data.url;
});


window.onload = function() {
    fetchLobbyUsers();
    // fetchScores(); // Call this function to load scores when the page loads
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
            console.log("Leader is checking if all users are ready");
            if (data.message === 'All users are ready, entering game now') {
                console.log("All users are ready, starting game now");
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


