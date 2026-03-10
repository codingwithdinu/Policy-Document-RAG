// Handle policy document upload
document.getElementById("uploadForm").addEventListener("submit", async function (e) {
  e.preventDefault();
  const file = document.getElementById("fileInput").files[0];
  if (!file) {
    alert("Please select a file to upload.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    const result = await res.json();
    alert(result.message || "File uploaded successfully.");
  } catch (err) {
    console.error("Upload error:", err);
    alert("Failed to upload file. Please try again.");
  }
});

// Handle query submission
document.getElementById("queryForm").addEventListener("submit", async function (e) {
  e.preventDefault();
  const query = document.getElementById("queryInput").value;

  if (!query.trim()) {
    alert("Please enter a query.");
    return;
  }

  try {
    const res = await fetch("/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ query: query })
    });

    const data = await res.json();
    document.getElementById("responseBox").innerText = data.answer || "No response received.";
  } catch (err) {
    console.error("Query error:", err);
    document.getElementById("responseBox").innerText = "Error while processing the query.";
  }
});
