document.addEventListener('DOMContentLoaded', () => {
  // Initialize particle background
  particlesJS('particles-js', {
      particles: {
          number: { value: 80, density: { enable: true, value_area: 800 } },
          color: { value: '#3b82f6' },
          shape: { type: 'circle' },
          opacity: { value: 0.5, random: false },
          size: { value: 3, random: true },
          line_linked: { enable: true, distance: 150, color: '#3b82f6', opacity: 0.4, width: 1 },
          move: { enable: true, speed: 2, direction: 'none', random: false, straight: false, out_mode: 'out', bounce: false }
      },
      interactivity: {
          detect_on: 'canvas',
          events: { onhover: { enable: true, mode: 'repulse' }, onclick: { enable: true, mode: 'push' }, resize: true },
          modes: { repulse: { distance: 100, duration: 0.4 }, push: { particles_nb: 4 } }
      },
      retina_detect: true

      
  });

  // Navbar scroll effect
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
          navbar.classList.add('scrolled');
      } else {
          navbar.classList.remove('scrolled');
      }
  });

  // Mobile menu toggle
  const menuToggle = document.getElementById('menu-toggle');
  const menu = document.getElementById('menu');
  menuToggle.addEventListener('click', () => {
      menu.classList.toggle('show');
  });

  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
          e.preventDefault();
          document.querySelector(this.getAttribute('href')).scrollIntoView({
              behavior: 'smooth'
          });
      });
  });

  // Add fade-in animation to main content
  const mainContent = document.querySelector('main');
  mainContent.classList.add('fade-in');

  // Add hover effect to buttons
  const buttons = document.querySelectorAll('.futuristic-button');
  buttons.forEach(button => {
      button.addEventListener('mouseover', createRipple);
      button.addEventListener('mouseout', removeRipple);
  });

  // Add typing effect to AI responses
  const aiResponses = document.querySelectorAll('.ai-response');
  aiResponses.forEach(response => {
      const text = response.textContent;
      response.textContent = '';
      typeWriter(response, text, 0);
  });

  // Add ripple effect to buttons
  document.querySelectorAll('.futuristic-button').forEach(button => {
    button.addEventListener('click', function(e) {
      let ripple = document.createElement('span');
      ripple.classList.add('ripple');
      this.appendChild(ripple);
      let x = e.clientX - e.target.offsetLeft;
      let y = e.clientY - e.target.offsetTop;
      ripple.style.left = `${x}px`;
      ripple.style.top = `${y}px`;
      setTimeout(() => {
        ripple.remove();
      }, 600);
    });
  });
  
});

function createRipple(event) {
  const button = event.currentTarget;
  const ripple = document.createElement('span');
  ripple.classList.add('ripple');
  button.appendChild(ripple);

  const rect = button.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  ripple.style.width = ripple.style.height = `${size}px`;

  const x = event.clientX - rect.left - size / 2;
  const y = event.clientY - rect.top - size / 2;
  ripple.style.left = `${x}px`;
  ripple.style.top = `${y}px`;
}

function removeRipple(event) {
  const button = event.currentTarget;
  const ripple = button.querySelector('.ripple');
  if (ripple) {
      ripple.remove();
  }
}

function typeWriter(element, text, index) {
  if (index < text.length) {
      element.textContent += text.charAt(index);
      setTimeout(() => typeWriter(element, text, index + 1), 20);
  }
}

document.addEventListener('DOMContentLoaded', (event) => {
  // Set the default active tab
  loginTab.click();
});
