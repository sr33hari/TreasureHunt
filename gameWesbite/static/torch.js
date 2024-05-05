const container = document.getElementById('container');
const mask = document.getElementById('mask');
const overlay = document.getElementById('overlay');

container.addEventListener('mousemove', function(e) {
    mask.style.display = 'block';
    mask.style.left = e.pageX - 100 + 'px';
    mask.style.top = e.pageY - 100 + 'px'; 
    overlay.style['mask-image'] = `radial-gradient(circle 100px at ${e.pageX}px ${e.pageY}px, transparent 0, black 100px)`;
    overlay.style['-webkit-mask-image'] = `radial-gradient(circle 100px at ${e.pageX}px ${e.pageY}px, transparent 0, black 100px)`;
});

container.addEventListener('mouseleave', function() {
    mask.style.display = 'none'; 
    overlay.style['mask-image'] = '';
    overlay.style['-webkit-mask-image'] = '';
});

var n = 0;
var treasures = [
    {
        "question": "Click on the first thing that makes it look like a crime?",
        "x": 58,
        "y": 52
    },
    {
        "question": "Which thing suggests it's a Crime of Passion?",
        "x": 90,
        "y": 10
    },
    {
        "question": "Find the thing that can tell the time of struggle?",
        "x": 10,
        "y": 45
    },
    {
        "question": "Which of these things can have DNA evidence on them?",
        "x": 73,
        "y": 25
    },
    {
        "question": "Find the strangest thing that shines out?",
        "x": 29,
        "y": 90
    },
    {
        "question": "",
        "x": 0,
        "y": 0
    }
];

function treasureFound() {
    n++;

    if (n >= treasures.length - 1) {
        console.log("All treasures found!");
        return;
    }

    // Display next question
    var questionDiv = document.getElementById("question");
    questionDiv.textContent = treasures[n].question;

    // Set button's new position
    var button = document.getElementById("btn1"); 
    button.style.top = treasures[n].x + '%';
    button.style.left = treasures[n].y + '%';
    if (n == 1) button.style.padding = "100px 100px";
    else button.style.padding = "50px 50px";

    // Fetch timestamp
    var timestamp = new Date().toLocaleString();
    console.log("Treasure found at: " + timestamp);

    // Call API to send timestamp
    fetch('/treasures/timestamp', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ timestamp: timestamp })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Timestamp sent:', data);
    })
    .catch((error) => {
        console.error('Error sending timestamp:', error);
    });
}
