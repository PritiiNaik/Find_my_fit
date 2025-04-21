const container = document.getElementById('container');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');

registerBtn.addEventListener('click', () => {
    container.classList.add("active");
});

loginBtn.addEventListener('click', () => {
    container.classList.remove("active");
});

document.addEventListener('DOMContentLoaded', () => {
    // Registration
    const signUpForm = document.querySelector('.sign-up form');
    signUpForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const name = signUpForm.querySelector('input[placeholder="Name"]').value;
        const email = signUpForm.querySelector('input[placeholder="Email"]').value;
        const password = signUpForm.querySelector('input[placeholder="Password"]').value;

        fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ name, email, password })
        })
        .then(res => res.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                container.classList.remove("active");
            } else {
                alert(data.error || 'Registration failed');
            }
        });
    });

    // Login
    const signInForm = document.querySelector('.sign-in form');
    signInForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const email = signInForm.querySelector('input[placeholder="Email"]').value;
        const password = signInForm.querySelector('input[placeholder="Password"]').value;

        fetch('/signin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ email, password })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert('Login successful!');
                window.location.href = "/homw";
            } else {
                alert(data.message || 'Login failed');
            }
        });
    });
});
