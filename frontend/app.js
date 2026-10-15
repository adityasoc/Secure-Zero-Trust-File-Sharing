"use strict";

const API_BASE = "http://127.0.0.1:8000";
const TOKEN_KEY = "zt_access_token";
const EMAIL_KEY = "zt_user_email";

const $ = (id) => document.getElementById(id);
let authMode = "login";
let selectedFile = null;
let currentUser = null;

function setMessage(element, message, type = "") {
    element.textContent = message;
    element.className = "message" + (type ? " " + type : "");
}

function clearMessage(element) {
    element.textContent = "";
    element.className = "message hidden";
}

function getToken() {
    return sessionStorage.getItem(TOKEN_KEY);
}

async function apiRequest(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getToken();

    if (token) headers.set("Authorization", "Bearer " + token);

    const response = await fetch(API_BASE + path, {
        ...options,
        headers
    });

    if (response.status === 401 && token && path !== "/auth/login") {
        sessionStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem(EMAIL_KEY);
        currentUser = null;
        renderSignedOut();
    }

    return response;
}

async function readError(response) {
    try {
        const data = await response.json();
        if (typeof data.detail === "string") return data.detail;
        if (Array.isArray(data.detail)) {
            return data.detail.map((item) => item.msg || "Invalid input").join("; ");
        }
        return "Request failed with status " + response.status;
    } catch {
        return "Request failed with status " + response.status;
    }
}

function setStatus(id, label, type) {
    const element = $(id);
    element.textContent = label;
    element.className = "status-pill" + (type ? " " + type : "");
}

async function checkHealth() {
    $("apiBadge").innerHTML = '<span class="dot"></span> Checking API';
    $("healthValue").textContent = "Checking";
    setStatus("apiStatus", "Checking", "");
    setStatus("dbStatus", "Checking", "");

    try {
        const response = await fetch(API_BASE + "/health");
        if (!response.ok) throw new Error("API returned HTTP " + response.status);

        const data = await response.json();
        $("apiBadge").innerHTML = '<span class="dot"></span> API online';
        $("healthValue").textContent = "Operational";
        $("healthDetail").textContent = "Backend responded successfully";
        setStatus("apiStatus", "Online", "status-success");

        if (data.database === "connected") {
            setStatus("dbStatus", "Connected", "status-success");
        } else {
            setStatus("dbStatus", data.database || "Unknown", "status-error");
        }
    } catch {
        $("apiBadge").innerHTML = '<span class="dot" style="background:#ff777e"></span> API offline';
        $("healthValue").textContent = "Unavailable";
        $("healthDetail").textContent = "Start the FastAPI backend";
        setStatus("apiStatus", "Offline", "status-error");
        setStatus("dbStatus", "Unverified", "");
    }
}

function renderSignedOut() {
    $("authForms").classList.remove("hidden");
    $("signedInPanel").classList.add("hidden");
    $("logoutBtn").classList.add("hidden");
    $("authHeading").textContent = "Access your workspace";
    $("authDescription").textContent = "Sign in or create an account to access your private files.";
    $("authValue").textContent = "Signed out";
    $("authDetail").textContent = "Sign in to manage files";
    currentUser = null;
}

function renderSignedIn(user) {
    currentUser = user;
    $("authForms").classList.add("hidden");
    $("signedInPanel").classList.remove("hidden");
    $("logoutBtn").classList.remove("hidden");
    $("authHeading").textContent = "Workspace authenticated";
    $("authDescription").textContent = "Your account is signed in.";
    $("userEmail").textContent = user.email || sessionStorage.getItem(EMAIL_KEY) || "Authenticated user";
    $("authValue").textContent = "Authenticated";
    $("authDetail").textContent = "Token verified by backend";
}

async function verifySession() {
    if (!getToken()) {
        renderSignedOut();
        return;
    }

    try {
        const response = await apiRequest("/auth/me");
        if (!response.ok) {
            sessionStorage.removeItem(TOKEN_KEY);
            sessionStorage.removeItem(EMAIL_KEY);
            renderSignedOut();
            return;
        }

        const user = await response.json();
        renderSignedIn(user);
    } catch {
        $("authDetail").textContent = "Backend connection unavailable";
    }
}

document.querySelectorAll(".auth-tab").forEach((button) => {
    button.addEventListener("click", () => {
        authMode = button.dataset.mode;
        document.querySelectorAll(".auth-tab").forEach((tab) => {
            tab.classList.toggle("active", tab === button);
        });

        $("authSubmit").innerHTML = authMode === "login"
            ? 'Sign in securely <span>→</span>'
            : 'Create account <span>→</span>';

        $("authHeading").textContent = authMode === "login"
            ? "Access your workspace"
            : "Create your account";

        $("password").autocomplete = authMode === "login" ? "current-password" : "new-password";
        $("password").minLength = authMode === "register" ? 12 : 1;
        $("passwordHint").textContent = authMode === "register"
            ? "Use 12–128 characters. Choose a strong, unique password."
            : "Use your registered account credentials.";

        clearMessage($("authMessage"));
    });
});

$("authForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage($("authMessage"));

    const email = $("email").value.trim();
    const password = $("password").value;
    const submit = $("authSubmit");

    if (authMode === "register" && password.length < 12) {
        setMessage($("authMessage"), "Registration requires a password of at least 12 characters.", "error");
        return;
    }

    submit.disabled = true;
    submit.textContent = authMode === "login" ? "Signing in..." : "Creating account...";

    try {
        const response = await fetch(API_BASE + (authMode === "login" ? "/auth/login" : "/auth/register"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            setMessage($("authMessage"), await readError(response), "error");
            return;
        }

        const data = await response.json();

        if (authMode === "register") {
            setMessage($("authMessage"), "Account created successfully. Switch to Sign in and log in with your new account.", "success");
            document.querySelector('[data-mode="login"]').click();
            $("email").value = email;
            $("password").value = "";
            return;
        }

        if (!data.access_token) {
            setMessage($("authMessage"), "The backend did not return an access token.", "error");
            return;
        }

        sessionStorage.setItem(TOKEN_KEY, data.access_token);
        sessionStorage.setItem(EMAIL_KEY, email);

        const meResponse = await apiRequest("/auth/me");
        if (!meResponse.ok) {
            sessionStorage.removeItem(TOKEN_KEY);
            sessionStorage.removeItem(EMAIL_KEY);
            setMessage($("authMessage"), "Login succeeded, but session verification failed.", "error");
            return;
        }

        renderSignedIn(await meResponse.json());
        $("password").value = "";
        setMessage($("authMessage"), "Successfully signed in. Your private workspace is ready.", "success");
    } catch {
        setMessage($("authMessage"), "Cannot connect to the backend. Check that FastAPI is running on port 8000.", "error");
    } finally {
        submit.disabled = false;
        submit.innerHTML = authMode === "login"
            ? 'Sign in securely <span>→</span>'
            : 'Create account <span>→</span>';
    }
});

$("logoutBtn").addEventListener("click", () => {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(EMAIL_KEY);
    $("password").value = "";
    clearMessage($("authMessage"));
    renderSignedOut();
    setMessage($("authMessage"), "You have signed out.", "success");
});

$("fileInput").addEventListener("change", () => {
    selectedFile = $("fileInput").files[0] || null;
    $("selectedFile").textContent = selectedFile
        ? selectedFile.name + " · " + (selectedFile.size / 1024).toFixed(1) + " KB"
        : "No file selected";
    $("uploadBtn").disabled = !selectedFile || !getToken();
    clearMessage($("fileMessage"));
});

$("uploadForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage($("fileMessage"));

    if (!getToken()) {
        setMessage($("fileMessage"), "Please sign in before uploading files.", "error");
        return;
    }

    if (!selectedFile) {
        setMessage($("fileMessage"), "Choose a file first.", "error");
        return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
        setMessage($("fileMessage"), "File exceeds the 10 MB limit.", "error");
        return;
    }

    const allowed = [".txt", ".pdf", ".png", ".jpg", ".jpeg", ".csv"];
    const name = selectedFile.name.toLowerCase();
    if (!allowed.some((extension) => name.endsWith(extension))) {
        setMessage($("fileMessage"), "Unsupported extension. Choose TXT, PDF, PNG, JPG, JPEG or CSV.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    $("uploadBtn").disabled = true;
    $("uploadBtn").textContent = "Encrypting and uploading...";

    try {
        const response = await apiRequest("/files/upload", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            setMessage($("fileMessage"), await readError(response), "error");
            return;
        }

        const data = await response.json();
        $("fileId").value = data.file_id || "";

        const details = [
            data.message || "File uploaded successfully.",
            "File ID: " + (data.file_id || "Not provided"),
            "Encryption: " + (data.encryption_algorithm || "Backend encryption"),
            "Size: " + (data.size_bytes ?? selectedFile.size) + " bytes"
        ].join("\n");

        setMessage($("fileMessage"), details, "success");
        $("fileInput").value = "";
        selectedFile = null;
        $("selectedFile").textContent = "No file selected";
    } catch {
        setMessage($("fileMessage"), "Upload failed because the backend could not be reached.", "error");
    } finally {
        $("uploadBtn").disabled = !selectedFile || !getToken();
        $("uploadBtn").textContent = "Encrypt & upload";
    }
});

$("downloadForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage($("fileMessage"));

    if (!getToken()) {
        setMessage($("fileMessage"), "Please sign in before downloading files.", "error");
        return;
    }

    const fileId = $("fileId").value.trim();
    if (!/^[a-fA-F0-9]{32}$/.test(fileId)) {
        setMessage($("fileMessage"), "Enter a valid 32-character file ID.", "error");
        return;
    }

    $("downloadBtn").disabled = true;
    $("downloadBtn").textContent = "Downloading and decrypting...";

    try {
        const response = await apiRequest("/files/" + encodeURIComponent(fileId) + "/download");

        if (!response.ok) {
            setMessage($("fileMessage"), await readError(response), "error");
            return;
        }

        const blob = await response.blob();
        const disposition = response.headers.get("Content-Disposition") || "";
        const match = disposition.match(/filename="([^"]*)"/i);
        const filename = match && match[1] ? match[1] : "secure-download";
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);

        setMessage($("fileMessage"), "Download successful. The backend verified ownership and decrypted the file.", "success");
    } catch {
        setMessage($("fileMessage"), "Download failed because the backend could not be reached.", "error");
    } finally {
        $("downloadBtn").disabled = false;
        $("downloadBtn").textContent = "Download & decrypt";
    }
});

$("refreshHealth").addEventListener("click", checkHealth);

checkHealth();
verifySession();
