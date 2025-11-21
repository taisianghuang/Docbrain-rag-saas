"use client";
import React, { useState } from "react";

export default function Page() {
  const [files, setFiles] = useState(null);
  const [message, setMessage] = useState("");
  const [resp, setResp] = useState("");

  const onFiles = (e) => setFiles(e.target.files);

  const upload = async (e) => {
    e.preventDefault();
    if (!files) return;
    const fd = new FormData();
    for (const f of files) fd.append("files", f);

    const res = await fetch("/api/py/api/ingest", { method: "POST", body: fd });
    const json = await res.json();
    alert("Inserted chunks: " + (json.inserted || 0));
  };

  const ask = async (e) => {
    e.preventDefault();
    setResp("");
    const r = await fetch("/api/py/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!r.ok) {
      setResp("Error: " + r.statusText);
      return;
    }
    const reader = r.body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    while (!done) {
      const { value, done: d } = await reader.read();
      done = d;
      if (value) setResp((s) => s + decoder.decode(value));
    }
  };

  return (
    <main style={{ padding: 24 }}>
      <h1>RAG SaaS — Admin Dashboard</h1>

      <section style={{ marginTop: 24 }}>
        <h2>Knowledge</h2>
        <form onSubmit={upload}>
          <input type="file" multiple onChange={onFiles} />
          <button type="submit">Upload & Ingest</button>
        </form>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Chat Tester</h2>
        <form onSubmit={ask}>
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask a question"
          />
          <button type="submit">Send</button>
        </form>
        <pre style={{ whiteSpace: "pre-wrap", marginTop: 12 }}>{resp}</pre>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Widget Snippet</h2>
        <p>
          Go to <a href="/settings">Settings</a> to copy the embed script for
          third-party sites.
        </p>
      </section>
    </main>
  );
}
