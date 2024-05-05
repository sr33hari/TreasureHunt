var socket = io.connect('http://0.0.0.0:6190');

socket.on('round over', function(data) {
    alert('Game is starting now!')
    window.location.href = data.url;
});

socket.on('treasure updates', function(data) {
    alert(data.message);
});
