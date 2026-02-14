// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyBU5TOVYw8F3qbahqGgGncb-wndFJtjlYM",
    authDomain: "ai-code-review-assistant-2026.firebaseapp.com",
    projectId: "ai-code-review-assistant-2026",
    storageBucket: "ai-code-review-assistant-2026.firebasestorage.app",
    messagingSenderId: "266116433250",
    appId: "1:266116433250:web:65a77de62e5f9f144e583b",
    measurementId: "G-ML6QJXFRT1"
};

// Initialize Firebase
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}
const auth = firebase.auth();

// DOM Elements
const loginSection = document.getElementById('loginSection');
const appSection = document.getElementById('appSection');
const authActions = document.getElementById('authActions');
const loginButton = document.getElementById('loginButton');
const logoutButton = document.getElementById('logoutButton');
const userEmail = document.getElementById('userEmail');
const reviewButton = document.getElementById('reviewButton');
const loadingState = document.getElementById('loadingState');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const supportButton = document.getElementById('supportButton');
const supportModal = document.getElementById('supportModal');
const closeModal = document.getElementById('closeModal');
const helpButton = document.getElementById('helpButton');
const instructionModal = document.getElementById('instructionModal');
const closeInstructionModal = document.getElementById('closeInstructionModal');

// Auth State Observer
auth.onAuthStateChanged((user) => {
    if (user) {
        loginSection.classList.add('hidden');
        appSection.classList.remove('hidden');
        authActions.classList.remove('hidden');
        userEmail.textContent = user.email;
    } else {
        loginSection.classList.remove('hidden');
        appSection.classList.add('hidden');
        authActions.classList.add('hidden');
    }
});

// Login with Google
loginButton.addEventListener('click', async () => {
    const provider = new firebase.auth.GoogleAuthProvider();
    try {
        await auth.signInWithPopup(provider);
    } catch (error) {
        console.error('Login error:', error);
        showError('Authentication failed. Please verify your connection.');
    }
});

// Logout
logoutButton.addEventListener('click', async () => {
    try {
        await auth.signOut();
        location.reload(); // Reset state
    } catch (error) {
        console.error('Logout error:', error);
    }
});

// Review PR
reviewButton.addEventListener('click', async () => {
    const prUrl = document.getElementById('prUrl').value.trim();
    const githubToken = document.getElementById('githubToken').value.trim();
    const reviewQuery = document.getElementById('reviewQuery').value.trim();

    if (!prUrl || !githubToken) {
        showError('Required fields missing. Please provide a PR URL and personal access token.');
        return;
    }

    const prInfo = parsePRUrl(prUrl);
    if (!prInfo) {
        showError('Invalid GitHub URL. Use: https://github.com/owner/repo/pull/123');
        return;
    }

    // UI Reset
    hideAll();
    loadingState.classList.remove('hidden');
    resultsSection.classList.add('hidden');

    // Scroll to loading
    loadingState.scrollIntoView({ behavior: 'smooth', block: 'center' });

    try {
        const user = auth.currentUser;
        const idToken = await user.getIdToken();

        const response = await fetch('/github/review/pr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${idToken}`
            },
            body: JSON.stringify({
                repo_url: prInfo.repo,
                pr_number: prInfo.number,
                github_token: githubToken,
                query: reviewQuery || 'Technical review: focusing on security, logic, and architecture.'
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'The AI review service encountered an error.');
        }

        const result = await response.json();
        displayResults(result);

    } catch (error) {
        console.error('Review error:', error);
        showError(error.message);
    } finally {
        loadingState.classList.add('hidden');
    }
});

// Parse PR URL
function parsePRUrl(url) {
    const urlMatch = url.match(/github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/);
    if (urlMatch) {
        return {
            repo: `${urlMatch[1]}/${urlMatch[2]}`,
            number: parseInt(urlMatch[3])
        };
    }
    const shortMatch = url.match(/^([^\/]+\/[^#]+)#(\d+)$/);
    if (shortMatch) {
        return {
            repo: shortMatch[1],
            number: parseInt(shortMatch[2])
        };
    }
    return null;
}

// Display Results
function displayResults(result) {
    hideAll();
    resultsSection.classList.remove('hidden');

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    document.getElementById('resultSummary').textContent = result.summary;

    // Helper to render lists with Lucide icons
    const renderList = (elementId, items, iconName, emptyMsg) => {
        const container = document.getElementById(elementId);
        container.innerHTML = '';

        if (items && items.length > 0) {
            items.forEach(text => {
                const item = document.createElement('div');
                item.className = 'finding-item';
                item.innerHTML = `
                    <i data-lucide="${iconName}" class="finding-icon"></i>
                    <div class="finding-content">
                        <p>${text}</p>
                    </div>
                `;
                container.appendChild(item);
            });
        } else {
            container.innerHTML = `<p style="padding: 1rem; color: var(--text-muted); font-style: italic;">${emptyMsg}</p>`;
        }
    };

    renderList('resultRisks', result.risks, 'alert-triangle', 'No critical risks identified.');
    renderList('resultSuggestions', result.suggestions, 'lightbulb', 'No optimizations suggested for this change set.');

    // Files
    const filesList = document.getElementById('resultFiles');
    filesList.innerHTML = '';
    if (result.files_reviewed && result.files_reviewed.length > 0) {
        result.files_reviewed.forEach(file => {
            const chip = document.createElement('div');
            chip.style = "font-size: 0.75rem; background: #eef2ff; color: #4338ca; padding: 4px 10px; border-radius: 4px; border: 1px solid #c7d2fe;";
            chip.textContent = file;
            filesList.appendChild(chip);
        });
    }

    // Review URL
    if (result.review_url) {
        document.getElementById('reviewUrl').href = result.review_url;
        document.getElementById('reviewUrl').classList.remove('hidden');
    } else {
        document.getElementById('reviewUrl').classList.add('hidden');
    }

    // Re-initialize Lucide icons for injected content
    lucide.createIcons();
}

// Show Error
function showError(message) {
    hideAll();
    errorSection.classList.remove('hidden');
    document.getElementById('errorMessage').textContent = message;
    lucide.createIcons();
}

// Support Modal
if (supportButton) {
    supportButton.addEventListener('click', () => {
        supportModal.classList.remove('hidden');
    });
}

if (closeModal) {
    closeModal.addEventListener('click', () => {
        supportModal.classList.add('hidden');
    });
}

// Help Modal
if (helpButton) {
    helpButton.addEventListener('click', () => {
        instructionModal.classList.remove('hidden');
    });
}

if (closeInstructionModal) {
    closeInstructionModal.addEventListener('click', () => {
        instructionModal.classList.add('hidden');
    });
}

window.addEventListener('click', (event) => {
    if (event.target === supportModal) {
        supportModal.classList.add('hidden');
    }
    if (event.target === instructionModal) {
        instructionModal.classList.add('hidden');
    }
});

// Hide All Sections
function hideAll() {
    loadingState.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');
}
