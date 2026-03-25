import { useRef, useState, type ChangeEvent } from "react";
import { Input } from "@/common/components/Input";

const API_BASE = "http://localhost:8080";

export const TestImageUpload = () => {
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [result, setResult] = useState<{ url: string; filename: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setResult(null);
    setError(null);
    setStatus("idle");
    setPreview(URL.createObjectURL(file));
  };

  const handleUpload = async () => {
    const file = inputRef.current?.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setStatus("uploading");
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/upload/`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Upload failed");
      }

      const data = await response.json();
      setResult(data);
      setStatus("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setStatus("error");
    }
  };

  const handleDelete = async () => {
    if (!result?.filename) return;

    try {
      const response = await fetch(`${API_BASE}/upload/${result.filename}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Delete failed");

      setResult(null);
      setPreview(null);
      setStatus("idle");
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 space-y-4">
      <div className="space-y-2">
        <label htmlFor="picture" className="block text-sm font-medium text-gray-700">
          Picture
        </label>
        <Input
          ref={inputRef}
          id="picture"
          type="file"
          accept="image/png,image/jpeg,image/gif,application/pdf"
          onChange={handleFileChange}
          className="text-sm file:mr-4 file:rounded file:bg-blue-50 file:px-4 file:py-2 file:font-semibold file:text-blue-700 hover:file:bg-blue-100"
        />
        <p className="text-sm text-gray-500">Select a picture to upload (max 5MB).</p>
      </div>

      {preview && (
        <img src={preview} alt="Preview" className="w-full rounded-lg object-cover max-h-48" />
      )}

      <button
        onClick={handleUpload}
        disabled={status === "uploading" || !preview}
        className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg disabled:opacity-50 hover:bg-blue-700 transition"
      >
        {status === "uploading" ? "Uploading..." : "Upload"}
      </button>

      {status === "success" && result && (
        <div className="p-4 bg-green-50 rounded-lg space-y-2">
          <p className="text-green-700 text-sm font-medium">✓ Uploaded successfully</p>
          <p className="text-xs text-gray-500 break-all">Filename: {result.filename}</p>
          <button
            onClick={handleDelete}
            className="w-full py-1 px-3 bg-red-100 text-red-600 rounded text-sm hover:bg-red-200 transition"
          >
            Delete
          </button>
        </div>
      )}

      {status === "error" && error && (
        <p className="text-red-600 text-sm">✗ {error}</p>
      )}
    </div>
  );
};