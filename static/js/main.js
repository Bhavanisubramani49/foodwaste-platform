/**
 * EcoSurplus AI - Main Client Script
 * Handles responsive menu toggle and interactive API health check test.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Navigation Toggle
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }

    // 2. Interactive REST API Health Check Test
    const testApiBtn = document.getElementById('testApiBtn');
    const apiResponseBox = document.getElementById('apiResponseBox');
    const apiJsonDisplay = document.getElementById('apiJsonDisplay');
    const closeApiBox = document.getElementById('closeApiBox');

    if (testApiBtn && apiResponseBox && apiJsonDisplay) {
        testApiBtn.addEventListener('click', async () => {
            apiResponseBox.style.display = 'block';
            apiJsonDisplay.textContent = 'Contacting Django REST API (/api/health/)...';

            try {
                const response = await fetch('/api/health/');
                if (!response.ok) {
                    throw new Error(`HTTP Error: ${response.status} ${response.statusText}`);
                }
                const data = await response.json();
                apiJsonDisplay.textContent = JSON.stringify(data, null, 2);
            } catch (err) {
                apiJsonDisplay.textContent = `Request failed: ${err.message}`;
            }
        });
    }

    if (closeApiBox && apiResponseBox) {
        closeApiBox.addEventListener('click', () => {
            apiResponseBox.style.display = 'none';
        });
    }
});
