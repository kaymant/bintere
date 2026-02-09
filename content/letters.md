---
title: "Submit a Letter"
layout: "single" 
url: "/letters"
summary: "Share your story of separation."
hidemeta: true
---

### The Letter Box
Some things are too heavy to carry alone. 

If you have a song that haunts you, or a memory of separation you wish to share anonymously, leave it here. We may feature selected stories on the homepage.

---

> *All submissions are read by a human. If selected, we will publish it anonymously.*

---
<form id="letter-form" action="https://formspree.io/f/mykdyvjr" method="POST">
  
  <label style="display: block; margin-bottom: 10px; color: #aaa;">
    Your Name (or Alias)
    <input type="text" name="name" required style="width: 100%; padding: 12px; margin-top: 5px; background: #222; border: 1px solid #444; color: #fff; border-radius: 4px;">
  </label>
  
  <label style="display: block; margin-bottom: 10px; color: #aaa;">
    The Song (Optional)
    <input type="text" name="song" style="width: 100%; padding: 12px; margin-top: 5px; background: #222; border: 1px solid #444; color: #fff; border-radius: 4px;">
  </label>

  <label style="display: block; margin-bottom: 10px; color: #aaa;">
    Your Letter
    <textarea name="message" rows="6" required style="width: 100%; padding: 12px; margin-top: 5px; background: #222; border: 1px solid #444; color: #fff; border-radius: 4px; font-family: inherit;"></textarea>
  </label>

  <button id="submit-btn" type="submit" style="background: #e0e0e0; color: #000; padding: 12px 24px; border: none; cursor: pointer; font-weight: bold; border-radius: 4px; margin-top: 10px; transition: all 0.2s;">
    Send Letter
  </button>
  
  <p id="form-status" style="margin-top: 15px; color: #4caf50; display: none;">Letter sent. Thank you for sharing.</p>
</form>



<script>
    var form = document.getElementById("letter-form");
    
    async function handleSubmit(event) {
        event.preventDefault();
        var status = document.getElementById("form-status");
        var btn = document.getElementById("submit-btn");
        var data = new FormData(event.target);
        
        btn.disabled = true;
        btn.innerText = "Sending...";

        fetch(event.target.action, {
            method: form.method,
            body: data,
            headers: {
                'Accept': 'application/json'
            }
        }).then(response => {
            if (response.ok) {
                status.style.display = "block";
                status.innerText = "Letter sent. Thank you for sharing.";
                status.style.color = "#4caf50"; // Green
                form.reset();
                btn.innerText = "Sent";
            } else {
                response.json().then(data => {
                    if (Object.hasOwn(data, 'errors')) {
                        status.innerText = data["errors"].map(error => error["message"]).join(", ");
                    } else {
                        status.innerText = "Oops! There was a problem submitting your form";
                    }
                    status.style.color = "#f44336"; // Red
                    btn.disabled = false;
                    btn.innerText = "Try Again";
                })
            }
        }).catch(error => {
            status.innerText = "Oops! There was a problem submitting your form";
            status.style.color = "#f44336"; // Red
            btn.disabled = false;
            btn.innerText = "Try Again";
        });
    }
    form.addEventListener("submit", handleSubmit);
</script>



