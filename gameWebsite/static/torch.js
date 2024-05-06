var socket = io.connect(window.location.origin);

socket.on('round over', function(data) {
    alert('Game is starting now!')
    window.location.href = data.url;
});

socket.on('treasure updates', function(data) {
    alert(data.message);
});
