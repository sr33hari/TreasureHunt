window.onload = function() {
    fetch('/lobby')
        .then(response => response.json())
        .then(data => {
            const usersDiv = document.getElementById('users');
            usersDiv.innerHTML = '<h3>Users in Lobby:</h3>' + data.users.join(', ');
        });
};

function userReady() {
    const username = localStorage.getItem('username'); // retrieve the username
    fetch(`/api/userReady?username=${username}`)
        .then(response => response.json())
        .then(data => console.log(data));
}

function fetchLobbyUsers() {
    fetch('/lobby')
        .then(response => response.json())
        .then(data => {
            const usersDiv = document.getElementById('users');
            usersDiv.innerHTML = '<h3>Users in Lobby:</h3>' + data.users.join(', ');
        });
}
