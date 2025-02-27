// Listen for click on "Extract Prescription" button.
document.getElementById('extract-btn').addEventListener('click', () => {
  const fileInput = document.getElementById('prescription-input');
  if (fileInput.files.length === 0) {
    alert("Please select an image file.");
    return;
  }
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);

  // Send the image file to the backend for extraction using Google Cloud Vision.
  fetch('/extract_prescription', {
    method: 'POST',
    body: formData
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      const extractedText = data.extractedText;
      document.getElementById('extracted-text').innerText = extractedText;
      // Hide upload section and show processing message.
      document.getElementById('upload-section').classList.add('hidden');
      document.getElementById('processing-section').classList.remove('hidden');
      // Send the extracted text to the backend for further processing.
      processPrescription(extractedText);
    })
    .catch(err => {
      console.error(err);
      alert("Error extracting text.");
    });
});

// Call the backend endpoint to process the prescription.
function processPrescription(text) {
  fetch('/process_prescription', {
    method: 'POST',
    body: JSON.stringify({ text: text }),
    headers: { 'Content-Type': 'application/json' }
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      document.getElementById('processing-section').classList.add('hidden');
      // Instead of displaying the results on the same page,
      // store the result data in localStorage and redirect to result.html.
      localStorage.setItem("resultData", JSON.stringify(data));
      // The relative path "result.html" is used here.
      // This means the browser will look for result.html in the same directory as the current page.
      window.location.href = "result.html";
    })
    .catch(error => {
      console.error("Error processing prescription:", error);
      alert("Failed to process the prescription.");
    });
}

// Display medicine schedule and schedule reminders.
function displayMedicineSchedule(medicines) {
  const listDiv = document.getElementById('medicine-list');
  listDiv.innerHTML = "";
  if (!medicines || medicines.length === 0) {
    listDiv.innerHTML = "<p>No medicine details found.</p>";
  } else {
    medicines.forEach(med => {
      const medicineItem = document.createElement('div');
      medicineItem.classList.add('medicine-item');
      medicineItem.innerHTML = `
        <div>
          <h3>${med.name}</h3>
          <p><strong>Dosage:</strong> ${med.dosage}</p>
          <p><strong>Time:</strong> ${med.time}</p>
          ${med.summary ? `<p><strong>Summary:</strong> ${med.summary}</p>` : ""}
          ${med.precautions ? `<p><strong>Precautions:</strong> ${med.precautions}</p>` : ""}
        </div>
      `;
      listDiv.appendChild(medicineItem);
      // Schedule a voice reminder for each medicine.
      scheduleReminder(med.name, med.time);
      // Optionally, schedule a WhatsApp reminder.
      scheduleWhatsAppReminder(med.name, med.time);
    });
  }
  document.getElementById('schedule-section').classList.remove('hidden');
}

// Display the full AI response (raw JSON) on the page.
function displayAISummary(data) {
  const summaryPre = document.getElementById('ai-summary');
  summaryPre.innerText = JSON.stringify(data, null, 2);
  document.getElementById('summary-section').classList.remove('hidden');
}

// Schedule a voice reminder using the Web Speech API.
function scheduleReminder(medicineName, scheduledTime) {
  const now = new Date();
  const [hours, minutes] = scheduledTime.split(':').map(Number);
  const reminderTime = new Date();
  reminderTime.setHours(hours, minutes, 0, 0);
  if (reminderTime < now) {
    reminderTime.setDate(reminderTime.getDate() + 1);
  }
  const delay = reminderTime.getTime() - now.getTime();
  setTimeout(() => {
    speakReminder(medicineName);
  }, delay);
}

// Use the Web Speech API to announce the reminder.
function speakReminder(medicineName) {
  const message = `It's time to take your medicine: ${medicineName}`;
  const utterance = new SpeechSynthesisUtterance(message);
  speechSynthesis.speak(utterance);
}

// Optionally, call the backend to schedule a WhatsApp reminder.
function scheduleWhatsAppReminder(medicineName, scheduledTime) {
  fetch('/send_whatsapp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ medicine: medicineName, time: scheduledTime })
  })
    .then(response => response.json())
    .then(data => console.log("WhatsApp reminder:", data))
    .catch(error => console.error(error));
}
