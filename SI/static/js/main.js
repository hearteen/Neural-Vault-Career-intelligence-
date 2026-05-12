document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.module-card');

    cards.forEach(card => {
        // Hover Scale Effect
        card.addEventListener('mouseenter', () => {
            card.classList.add('animate__pulse');
        });

        card.addEventListener('mouseleave', () => {
            card.classList.remove('animate__pulse');
        });

        // Click ripple effect logic
        card.addEventListener('click', function (e) {
            let ripple = document.createElement('span');
            ripple.classList.add('ripple');
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });
});