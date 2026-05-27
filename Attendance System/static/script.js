// This script is used for basic frontend validation and toast animation.

function validateLoginForm() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    if (!username || !password) {
        alert('Both username and password are required.');
        return false;
    }
    return true;
}

function validateStudentForm() {
    const fullName = document.getElementById('full_name').value.trim();
    const email = document.getElementById('email').value.trim();
    const course = document.getElementById('course').value.trim();
    if (!fullName || !email || !course) {
        alert('Please complete all student fields before submitting.');
        return false;
    }
    return true;
}

window.addEventListener('DOMContentLoaded', () => {
    const toasts = document.querySelectorAll('.toast');
    if (toasts.length > 0) {
        setTimeout(() => {
            toasts.forEach((toast) => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-10px)';
            });
        }, 5000);
    }
});
