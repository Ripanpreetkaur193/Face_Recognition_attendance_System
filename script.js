document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    let name = document.getElementById('name').value;
    let password = document.getElementById('password').value;
    
    let response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, password })
    });

    let result = await response.json();
    if (response.status === 200) {
        alert("Login successful! Now verifying face...");
        verifyFace();
    } else {
        document.getElementById('error-msg').innerText = result.error;
    }
});

async function verifyFace() {
    let response = await fetch('/verify_face');
    let result = await response.json();

    if (response.status === 200) {
        alert(`Face verified as ${result.student}!`);
    } else {
        alert("Face verification failed!");
    }
}
